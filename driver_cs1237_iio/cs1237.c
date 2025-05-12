// SPDX-License-Identifier: GPL-2.0-only
/*
 * Chipsea CS1237 24-bit ADC driver
 *
 * Copyright (C) 2025 Denis
 *
 * Datasheet: CS1237 24-bit ADC
 */

#include <linux/module.h>
#include <linux/init.h>
#include <linux/platform_device.h>
#include <linux/delay.h>
#include <linux/mutex.h>
#include <linux/err.h>
#include <linux/spi/spi.h>
#include <linux/gpio/consumer.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/of_gpio.h>
#include <linux/iio/iio.h>
#include <linux/iio/sysfs.h>
#include <linux/iio/buffer.h>
#include <linux/iio/trigger.h>
#include <linux/iio/triggered_buffer.h>
#include <linux/iio/trigger_consumer.h>
#include <linux/kthread.h>
#include <linux/slab.h>

/* CS1237 Configuration Constants */
#define CS1237_PGA_1             0
#define CS1237_PGA_2             1
#define CS1237_PGA_64            2
#define CS1237_PGA_128           3

#define CS1237_SPEED_10HZ        0
#define CS1237_SPEED_40HZ        1
#define CS1237_SPEED_640HZ       2
#define CS1237_SPEED_1280HZ      3

#define CS1237_CHANNEL_A         0
#define CS1237_CHANNEL_TEMP      1

#define CS1237_REFO_DISABLE      0
#define CS1237_REFO_ENABLE       1

/* Register commands */
#define CS1237_CMD_WRITE_REG     0x65
#define CS1237_CMD_READ_REG      0x56

/* Sample rates in Hz */
static const int cs1237_sample_rates[] = {10, 40, 640, 1280};

struct cs1237_state {
    struct device *dev;
    struct mutex lock;
    struct task_struct *conv_task;
    bool running;
    
    struct gpio_desc *sck_gpio;
    struct gpio_desc *dout_gpio;
    struct gpio_desc *din_gpio;
    
    /* Configuration */
    int pga;
    int speed;
    int channel;
    int refo;
    
    /* Data */
    s32 raw_data;
    int raw_counter;
    bool data_ready;
    
    /* Buffer for continuous sampling */
    s32 *sample_buffer;
    int buffer_head;
    int buffer_size;
    
    /* For statistics */
    s64 sum;
    int samples_count;
};

/* IIO channel specification */
static const struct iio_chan_spec cs1237_channels[] = {
    {
        .type = IIO_VOLTAGE,
        .indexed = 1,
        .channel = 0,
        .info_mask_separate = BIT(IIO_CHAN_INFO_RAW) |
                             BIT(IIO_CHAN_INFO_SCALE),
        .info_mask_shared_by_type = BIT(IIO_CHAN_INFO_SAMP_FREQ),
        .scan_index = 0,
        .scan_type = {
            .sign = 's',
            .realbits = 24,
            .storagebits = 32,
            .endianness = IIO_CPU,
        },
    },
    {
        .type = IIO_TEMP,
        .indexed = 1,
        .channel = 1,
        .info_mask_separate = BIT(IIO_CHAN_INFO_RAW) |
                             BIT(IIO_CHAN_INFO_SCALE),
        .info_mask_shared_by_type = BIT(IIO_CHAN_INFO_SAMP_FREQ),
        .scan_index = 1,
        .scan_type = {
            .sign = 's',
            .realbits = 24,
            .storagebits = 32,
            .endianness = IIO_CPU,
        },
    },
};

static void cs1237_pulse_clock(struct cs1237_state *state)
{
    gpiod_set_value(state->sck_gpio, 1);
    ndelay(500); /* 500ns delay - adjust as needed */
    gpiod_set_value(state->sck_gpio, 0);
    ndelay(500); /* 500ns delay - adjust as needed */
}

static bool cs1237_wait_data_ready(struct cs1237_state *state, unsigned int timeout_ms)
{
    unsigned long timeout = jiffies + msecs_to_jiffies(timeout_ms);
    
    while (gpiod_get_value(state->dout_gpio) == 1) {
        if (time_after(jiffies, timeout))
            return false;
        usleep_range(100, 200);
    }
    
    return true;
}

static int cs1237_write_config(struct cs1237_state *state, u8 config_byte)
{
    int i;
    
    /* Wait for data ready (DOUT goes low) */
    if (!cs1237_wait_data_ready(state, 500)) {
        dev_err(state->dev, "Timeout waiting for DOUT to go low during config write\n");
        return -ETIMEDOUT;
    }
    
    /* Read 24 bits (discard) */
    for (i = 0; i < 24; i++)
        cs1237_pulse_clock(state);
    
    /* 25th to 26th SCLKs - read register operation status */
    for (i = 0; i < 2; i++)
        cs1237_pulse_clock(state);
    
    /* 27th SCLK - pulls DRDY/DOUT high */
    cs1237_pulse_clock(state);
    
    /* 28th to 29th SCLK - switch DRDY/DOUT to input */
    for (i = 0; i < 2; i++)
        cs1237_pulse_clock(state);
    
    /* 30th to 36th SCLK - input register command word (7 bits) */
    /* Send write command (0x65 = 0b01100101) */
    for (i = 0; i < 7; i++) {
        /* Set data write pin before clock goes high */
        /* Note: The pin is inverted in hardware, so we invert the bit */
        gpiod_set_value(state->din_gpio, !((CS1237_CMD_WRITE_REG >> (6 - i)) & 0x01));
        cs1237_pulse_clock(state);
    }
    
    /* 37th SCLK - switch direction (for write, DRDY/DOUT remains input) */
    cs1237_pulse_clock(state);
    
    /* 38th to 45th SCLK - input register data (8 bits) */
    for (i = 0; i < 8; i++) {
        /* Set data write pin before clock goes high (inverted) */
        gpiod_set_value(state->din_gpio, !((config_byte >> (7 - i)) & 0x01));
        cs1237_pulse_clock(state);
    }
    
    /* Reset data write pin to low for reading */
    gpiod_set_value(state->din_gpio, 0);
    
    return 0;
}

static int cs1237_read_config(struct cs1237_state *state, u8 *config_byte)
{
    int i;
    u8 result = 0;
    
    /* Wait for data ready (DOUT goes low) */
    if (!cs1237_wait_data_ready(state, 500)) {
        dev_err(state->dev, "Timeout waiting for DOUT to go low during config read\n");
        return -ETIMEDOUT;
    }
    
    /* Read 24 bits (discard) */
    for (i = 0; i < 24; i++)
        cs1237_pulse_clock(state);
    
    /* 25th to 26th SCLKs - read register operation status */
    for (i = 0; i < 2; i++)
        cs1237_pulse_clock(state);
    
    /* 27th SCLK - pulls DRDY/DOUT high */
    cs1237_pulse_clock(state);
    
    /* 28th to 29th SCLK - switch DRDY/DOUT to input */
    for (i = 0; i < 2; i++)
        cs1237_pulse_clock(state);
    
    /* 30th to 36th SCLK - input register command word (7 bits) */
    /* Send read command (0x56 = 0b01010110) */
    for (i = 0; i < 7; i++) {
        /* Set data write pin before clock goes high (inverted) */
        gpiod_set_value(state->din_gpio, !((CS1237_CMD_READ_REG >> (6 - i)) & 0x01));
        cs1237_pulse_clock(state);
    }
    
    /* 37th SCLK - switch direction (for read, DRDY/DOUT becomes output) */
    cs1237_pulse_clock(state);
    
    /* 38th to 45th SCLK - read register data (8 bits) */
    for (i = 0; i < 8; i++) {
        cs1237_pulse_clock(state);
        /* Read bit from data_read_pin */
        result = (result << 1) | gpiod_get_value(state->dout_gpio);
    }
    
    /* Reset data write pin to low for reading */
    gpiod_set_value(state->din_gpio, 0);
    
    *config_byte = result;
    return 0;
}

static int cs1237_read_raw_value(struct cs1237_state *state, s32 *value)
{
    int i;
    s32 raw_data = 0;
    
    /* Check if data is ready (DOUT is low) */
    if (gpiod_get_value(state->dout_gpio)){
        dev_warn(state->dev, "DOUT is high during data read\n");
        return -EBUSY;
    }

    /* Keep data_write_pin low for reading */
    // GPIO.output(self.data_write_pin, GPIO.LOW)
    gpiod_set_value(state->din_gpio, 0);
    
    /* Read 24 bits */
    for (i = 0; i < 24; i++) {
        gpiod_set_value(state->sck_gpio, 1);
        ndelay(500);
        
        raw_data = (raw_data << 1) | gpiod_get_value(state->dout_gpio);
        
        gpiod_set_value(state->sck_gpio, 0);
        ndelay(500);
    }
    
    /* Additional clock cycles (25-27) to complete the reading */
    for (i = 0; i < 3; i++)
        cs1237_pulse_clock(state);
    
    /* Make sure DOUT goes high again - send a few clock pulses if needed */
    for (i = 0; i < 5; i++) {
        if (gpiod_get_value(state->dout_gpio))
            break;
        cs1237_pulse_clock(state);
    }
    
    /* Convert to signed value */
    if (raw_data & 0x800000)
        raw_data = raw_data - 0x1000000;
    
    *value = raw_data;
    return 0;
}

static int cs1237_conv_thread(void *data)
{
    struct cs1237_state *state = data;
    s32 value;
    int sleep_time_us;
    int ret;
    
    /* Calculate sleep time based on configured speed */
    switch (state->speed) {
    case CS1237_SPEED_10HZ:
        sleep_time_us = 100000; /* ~95% of 100ms */
        break;
    case CS1237_SPEED_40HZ:
        sleep_time_us = 25000; /* ~95% of 25ms */
        break;
    case CS1237_SPEED_640HZ:
        sleep_time_us = 1563;  /* ~95% of 1562.5µs */
        break;
    case CS1237_SPEED_1280HZ:
        sleep_time_us = 782;   /* ~95% of 781.25µs */
        break;
    default:
        sleep_time_us = 1000;
        break;
    }
    
    while (!kthread_should_stop()) {
        if (!state->running) {
            msleep(10);
            continue;
        }
        
        ret = cs1237_read_raw_value(state, &value);
        if (ret == 0) {
            mutex_lock(&state->lock);
            state->raw_data = value;
            state->data_ready = true;
            state->raw_counter++;
            
            /* Store data in circular buffer if available */
            if (state->sample_buffer) {
                state->sample_buffer[state->buffer_head] = value;
                state->buffer_head = (state->buffer_head + 1) % state->buffer_size;
            }
            
            /* Update statistics */
            state->sum += value;
            state->samples_count++;
            mutex_unlock(&state->lock);
        }
        
        usleep_range(sleep_time_us, sleep_time_us + 100);
    }
    
    return 0;
}

static int cs1237_read_raw(struct iio_dev *indio_dev,
                         struct iio_chan_spec const *chan,
                         int *val, int *val2, long mask)
{
    struct cs1237_state *state = iio_priv(indio_dev);
    int ret;
    
    switch (mask) {
    case IIO_CHAN_INFO_RAW:
        /* Make sure the correct channel is selected */
        if (state->channel != chan->channel) {
            u8 config_byte = (state->speed & 0x03) |
                           ((state->pga & 0x03) << 2) |
                           ((chan->channel & 0x01) << 4) |
                           ((state->refo & 0x01) << 5);
            
            mutex_lock(&state->lock);
            ret = cs1237_write_config(state, config_byte);
            if (ret) {
                mutex_unlock(&state->lock);
                return ret;
            }
            state->channel = chan->channel;
            mutex_unlock(&state->lock);
            
            /* Wait for a new reading to be available */
            msleep(100);
        }
        
        mutex_lock(&state->lock);
        if (!state->data_ready) {
            mutex_unlock(&state->lock);
            return -EBUSY;
        }
        *val = state->raw_data;
        mutex_unlock(&state->lock);
        return IIO_VAL_INT;
        
    case IIO_CHAN_INFO_SCALE:
        /* Scale factor calculation (3.3V reference with various PGA settings) */
        /* For 24-bit ADC, full scale is 2^23 (8388608) */
        *val = 3300; /* voltage in mV */
        
        switch (state->pga) {
        case CS1237_PGA_1:
            *val2 = 8388608; /* Divide by 2^23 */
            break;
        case CS1237_PGA_2:
            *val2 = 8388608 * 2; /* Additional factor of 2 */
            break;
        case CS1237_PGA_64:
            *val2 = 8388608 * 64; /* Additional factor of 64 */
            break;
        case CS1237_PGA_128:
            *val2 = 8388608 * 128; /* Additional factor of 128 */
            break;
        default:
            *val2 = 8388608;
            break;
        }
        return IIO_VAL_FRACTIONAL;
        
    case IIO_CHAN_INFO_SAMP_FREQ:
        *val = cs1237_sample_rates[state->speed];
        return IIO_VAL_INT;
        
    default:
        return -EINVAL;
    }
}

static int cs1237_write_raw(struct iio_dev *indio_dev,
                          struct iio_chan_spec const *chan,
                          int val, int val2, long mask)
{
    struct cs1237_state *state = iio_priv(indio_dev);
    int ret;
    u8 speed_setting = state->speed;
    u8 pga_setting = state->pga;
    u8 config_byte;
    
    switch (mask) {
    case IIO_CHAN_INFO_SAMP_FREQ:
        /* Convert sample frequency to speed setting */
        if (val == 10)
            speed_setting = CS1237_SPEED_10HZ;
        else if (val == 40)
            speed_setting = CS1237_SPEED_40HZ;
        else if (val == 640)
            speed_setting = CS1237_SPEED_640HZ;
        else if (val == 1280)
            speed_setting = CS1237_SPEED_1280HZ;
        else
            return -EINVAL;
        
        break;
        
    case IIO_CHAN_INFO_SCALE:
        /* We only allow changing the PGA setting */
        if (val != 3300 || val2 == 0)
            return -EINVAL;
            
        /* Determine the PGA setting based on the denominator */
        if (val2 == 8388608)
            pga_setting = CS1237_PGA_1;
        else if (val2 == 8388608 * 2)
            pga_setting = CS1237_PGA_2;
        else if (val2 == 8388608 * 64)
            pga_setting = CS1237_PGA_64;
        else if (val2 == 8388608 * 128)
            pga_setting = CS1237_PGA_128;
        else
            return -EINVAL;
            
        break;
        
    default:
        return -EINVAL;
    }
    
    /* Apply new settings */
    mutex_lock(&state->lock);
    config_byte = (speed_setting & 0x03) |
                 ((pga_setting & 0x03) << 2) |
                 ((state->channel & 0x01) << 4) |
                 ((state->refo & 0x01) << 5);
                 
    ret = cs1237_write_config(state, config_byte);
    if (ret) {
        mutex_unlock(&state->lock);
        return ret;
    }
    
    state->speed = speed_setting;
    state->pga = pga_setting;
    mutex_unlock(&state->lock);
    
    return 0;
}

static int cs1237_read_avail(struct iio_dev *indio_dev,
                           struct iio_chan_spec const *chan,
                           const int **vals, int *type, int *length,
                           long mask)
{
    static const int samp_freq_avail[] = {10, 40, 640, 1280};
    
    switch (mask) {
    case IIO_CHAN_INFO_SAMP_FREQ:
        *vals = samp_freq_avail;
        *type = IIO_VAL_INT;
        *length = ARRAY_SIZE(samp_freq_avail);
        return IIO_AVAIL_LIST;
    default:
        return -EINVAL;
    }
}



/* Buffer operations not implemented yet */

static ssize_t cs1237_reset_store(struct device *dev,
                                struct device_attribute *attr,
                                const char *buf, size_t count)
{
    struct iio_dev *indio_dev = dev_to_iio_dev(dev);
    struct cs1237_state *state = iio_priv(indio_dev);
    bool running;
    u8 config_byte;
    int ret;
    
    /* Power cycle the CS1237 by toggling SCK */
    mutex_lock(&state->lock);
    running = state->running;
    state->running = false;
    mutex_unlock(&state->lock);
    
    msleep(10);
    
    /* Power up sequence */
    gpiod_set_value(state->sck_gpio, 1);
    msleep(1);
    gpiod_set_value(state->sck_gpio, 0);
    
    /* Wait for data ready */
    if (!cs1237_wait_data_ready(state, 500)) {
        dev_err(state->dev, "CS1237 reset failed: device did not respond\n");
        return -EIO;
    }
    
    /* Reconfigure the device */
    mutex_lock(&state->lock);
    config_byte = (state->speed & 0x03) |
                 ((state->pga & 0x03) << 2) |
                 ((state->channel & 0x01) << 4) |
                 ((state->refo & 0x01) << 5);
                 
    ret = cs1237_write_config(state, config_byte);
    if (ret) {
        mutex_unlock(&state->lock);
        return ret;
    }
    
    /* Verify configuration */
    ret = cs1237_read_config(state, &config_byte);
    if (ret) {
        mutex_unlock(&state->lock);
        return ret;
    }
    
    state->running = running;
    mutex_unlock(&state->lock);
    
    dev_info(state->dev, "CS1237 reset complete, config=0x%02x\n", config_byte);
    
    return count;
}

static ssize_t cs1237_running_show(struct device *dev,
                                 struct device_attribute *attr,
                                 char *buf)
{
    struct iio_dev *indio_dev = dev_to_iio_dev(dev);
    struct cs1237_state *state = iio_priv(indio_dev);
    
    return sysfs_emit(buf, "%d\n", state->running ? 1 : 0);
}

static ssize_t cs1237_running_store(struct device *dev,
                                  struct device_attribute *attr,
                                  const char *buf, size_t count)
{
    struct iio_dev *indio_dev = dev_to_iio_dev(dev);
    struct cs1237_state *state = iio_priv(indio_dev);
    bool val;
    int ret;
    
    ret = kstrtobool(buf, &val);
    if (ret)
        return ret;
    
    mutex_lock(&state->lock);
    state->running = val;
    mutex_unlock(&state->lock);
    
    return count;
}

static ssize_t cs1237_samples_show(struct device *dev,
                                 struct device_attribute *attr,
                                 char *buf)
{
    struct iio_dev *indio_dev = dev_to_iio_dev(dev);
    struct cs1237_state *state = iio_priv(indio_dev);
    int samples;
    
    mutex_lock(&state->lock);
    samples = state->raw_counter;
    mutex_unlock(&state->lock);
    
    return sysfs_emit(buf, "%d\n", samples);
}

static ssize_t cs1237_mean_show(struct device *dev,
                              struct device_attribute *attr,
                              char *buf)
{
    struct iio_dev *indio_dev = dev_to_iio_dev(dev);
    struct cs1237_state *state = iio_priv(indio_dev);
    s64 sum;
    int count;
    
    mutex_lock(&state->lock);
    sum = state->sum;
    count = state->samples_count;
    mutex_unlock(&state->lock);
    
    if (count == 0)
        return sysfs_emit(buf, "0\n");
    
    return sysfs_emit(buf, "%lld\n", div_s64(sum, count));
}

static ssize_t cs1237_clear_stats_store(struct device *dev,
                                      struct device_attribute *attr,
                                      const char *buf, size_t count)
{
    struct iio_dev *indio_dev = dev_to_iio_dev(dev);
    struct cs1237_state *state = iio_priv(indio_dev);
    
    mutex_lock(&state->lock);
    state->sum = 0;
    state->samples_count = 0;
    mutex_unlock(&state->lock);
    
    return count;
}

static IIO_DEVICE_ATTR_WO(cs1237_reset, 0);
static IIO_DEVICE_ATTR_RW(cs1237_running, 0);
static IIO_DEVICE_ATTR_RO(cs1237_samples, 0);
static IIO_DEVICE_ATTR_RO(cs1237_mean, 0);
static IIO_DEVICE_ATTR_WO(cs1237_clear_stats, 0);

static struct attribute *cs1237_attributes[] = {
    &iio_dev_attr_cs1237_reset.dev_attr.attr,
    &iio_dev_attr_cs1237_running.dev_attr.attr,
    &iio_dev_attr_cs1237_samples.dev_attr.attr,
    &iio_dev_attr_cs1237_mean.dev_attr.attr,
    &iio_dev_attr_cs1237_clear_stats.dev_attr.attr,
    NULL
};

static const struct attribute_group cs1237_attribute_group = {
    .attrs = cs1237_attributes,
};

static const struct iio_info cs1237_info = {
    .attrs = &cs1237_attribute_group,
    .read_raw = cs1237_read_raw,
    .write_raw = cs1237_write_raw,
    .read_avail = cs1237_read_avail,
};

static int cs1237_probe(struct platform_device *pdev)
{
    struct device *dev = &pdev->dev;
    struct cs1237_state *state;
    struct iio_dev *indio_dev;
    u8 config_byte, read_config;
    int ret;

    dev_info(dev, "Probing CS1237 ADC ...\n");

    indio_dev = devm_iio_device_alloc(dev, sizeof(*state));
    if (!indio_dev)
        return -ENOMEM;
    
    state = iio_priv(indio_dev);
    state->dev = dev;
    mutex_init(&state->lock);
    
    /* Get GPIO descriptors */
    state->sck_gpio = devm_gpiod_get(dev, "sck", GPIOD_OUT_LOW);
    if (IS_ERR(state->sck_gpio)){
        dev_err(dev, "Failed to get SCK GPIO\n");
        return PTR_ERR(state->sck_gpio);
    }
        
    state->dout_gpio = devm_gpiod_get(dev, "dout", GPIOD_IN);
    if (IS_ERR(state->dout_gpio)){
        dev_err(dev, "Failed to get DOUT GPIO\n");
        return PTR_ERR(state->dout_gpio);
    }

    state->din_gpio = devm_gpiod_get(dev, "din", GPIOD_OUT_LOW);
    if (IS_ERR(state->din_gpio)) {
        dev_err(dev, "Failed to get DIN GPIO\n");
        return PTR_ERR(state->din_gpio);
    }
    
    /* Get device properties */
    ret = device_property_read_u32(dev, "chipsea,pga", &state->pga);
    if (ret)
        state->pga = CS1237_PGA_1; /* Default PGA = 1 */
    
    ret = device_property_read_u32(dev, "chipsea,speed", &state->speed);
    if (ret)
        state->speed = CS1237_SPEED_10HZ; /* Default speed = 10Hz */
    
    ret = device_property_read_u32(dev, "chipsea,channel", &state->channel);
    if (ret)
        state->channel = CS1237_CHANNEL_A; /* Default channel = A */
    
    ret = device_property_read_u32(dev, "chipsea,refo", &state->refo);
    if (ret)
        state->refo = CS1237_REFO_DISABLE; /* Default refo = disabled */
    
    /* Initialize buffer */
    ret = device_property_read_u32(dev, "chipsea,buffer-size", &state->buffer_size);
    if (ret || state->buffer_size <= 0)
        state->buffer_size = 20; /* Default buffer size */
    
    state->sample_buffer = devm_kmalloc_array(dev, state->buffer_size,
                                            sizeof(*state->sample_buffer),
                                            GFP_KERNEL);
    if (!state->sample_buffer)
        return -ENOMEM;
    
    /* Initialize IIO device */
    indio_dev->name = "cs1237";
    indio_dev->dev.parent = dev;
    indio_dev->info = &cs1237_info;
    indio_dev->modes = INDIO_DIRECT_MODE;
    indio_dev->channels = cs1237_channels;
    indio_dev->num_channels = ARRAY_SIZE(cs1237_channels);

    // ret = iio_device_register_sysfs_group(indio_dev, &cs1237_attribute_group);
    // if (ret)
    //     return ret;
    
    platform_set_drvdata(pdev, indio_dev);
    
    /* Power up sequence */
    gpiod_set_value(state->sck_gpio, 1);
    msleep(1);
    gpiod_set_value(state->sck_gpio, 0);
    
    /* Wait for data ready */
    if (!cs1237_wait_data_ready(state, 500)) {
        dev_err(dev, "CS1237 initialization failed: device did not respond\n");
        return -EIO;
    }
    
    /* Configure the device */
    config_byte = (state->speed & 0x03) |
                 ((state->pga & 0x03) << 2) |
                 ((state->channel & 0x01) << 4) |
                 ((state->refo & 0x01) << 5);
                 
    ret = cs1237_write_config(state, config_byte);
    if (ret) {
        dev_err(dev, "Failed to write CS1237 configuration\n");
        return ret;
    }
    
    /* Verify configuration */
    ret = cs1237_read_config(state, &read_config);
    if (ret) {
        dev_err(dev, "Failed to read back CS1237 configuration\n");
        return ret;
    }
    
    dev_info(dev, "CS1237 configured: PGA=%d, SPEED=%d, CHANNEL=%d, REFO=%d",
             state->pga, state->speed, state->channel, state->refo);
    
    dev_info(dev, "Config byte: 0x%02X, Read config: 0x%02X", config_byte, read_config);
    
    /* Start conversion thread */
    state->conv_task = kthread_run(cs1237_conv_thread, state, "cs1237-conv");
    if (IS_ERR(state->conv_task)) {
        ret = PTR_ERR(state->conv_task);
        dev_err(dev, "Failed to create conversion thread, error %d\n", ret);
        return ret;
    }
    
    /* Start data acquisition */
    state->running = true;
    
    ret = devm_iio_device_register(dev, indio_dev);
    if (ret) {
        dev_err(dev, "Failed to register IIO device, error %d\n", ret);
        kthread_stop(state->conv_task);
        return ret;
    }
    
    dev_info(dev, "CS1237 24-bit ADC driver initialized");
    return 0;
}

static void cs1237_remove(struct platform_device *pdev)
{
    struct iio_dev *indio_dev = platform_get_drvdata(pdev);
    struct cs1237_state *state = iio_priv(indio_dev);
    
    /* Stop data acquisition */
    state->running = false;
    
    /* Stop and clean up the conversion thread */
    if (state->conv_task)
        kthread_stop(state->conv_task);
    
    return;
}

#ifdef CONFIG_OF
static const struct of_device_id cs1237_dt_ids[] = {
    { .compatible = "chipsea,cs1237", },
    { }
};
MODULE_DEVICE_TABLE(of, cs1237_dt_ids);
#endif

static struct platform_driver cs1237_driver = {
    .driver = {
        .name   = "cs1237",
        .of_match_table = of_match_ptr(cs1237_dt_ids),
    },
    .probe  = cs1237_probe,
    .remove = cs1237_remove,
};

module_platform_driver(cs1237_driver);

MODULE_AUTHOR("Denis");
MODULE_DESCRIPTION("Chipsea CS1237 24-bit ADC driver");
MODULE_LICENSE("GPL");