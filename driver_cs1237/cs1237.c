/*
 * CS1237 ADC Linux Driver
 *
 * Copyright (C) 2023
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 */

#include "cs1237.h"

/* Forward declarations */
static int cs1237_read_raw(struct iio_dev *indio_dev,
                          struct iio_chan_spec const *chan,
                          int *val, int *val2, long mask);
static int cs1237_write_raw(struct iio_dev *indio_dev,
                           struct iio_chan_spec const *chan,
                           int val, int val2, long mask);

/* IIO channel specification */
static const struct iio_chan_spec cs1237_channels[] = {
    {
        .type = IIO_VOLTAGE,
        .indexed = 1,
        .channel = 0,
        .info_mask_separate = BIT(IIO_CHAN_INFO_RAW) |
                             BIT(IIO_CHAN_INFO_SCALE),
        .info_mask_shared_by_type = BIT(IIO_CHAN_INFO_OFFSET) |
                                   BIT(IIO_CHAN_INFO_SAMP_FREQ),
    },
};

/* IIO operations structure */
static const struct iio_info cs1237_info = {
    .read_raw = cs1237_read_raw,
    .write_raw = cs1237_write_raw,
};

/* Helper function to set data pin direction */
static void cs1237_set_data_direction(struct cs1237_dev *cs1237, bool output)
{
    if (cs1237->shared_data_pin) {
        if (output) {
            gpiod_direction_output(cs1237->dout_gpio, 1);
        } else {
            gpiod_direction_input(cs1237->dout_gpio);
        }
    } else {
        /* If separate pins, we don't need to change direction */
    }
}

/* Helper function to read data bit */
static int cs1237_read_bit(struct cs1237_dev *cs1237)
{
    int bit;

    /* Set SCLK high */
    gpiod_set_value(cs1237->sclk_gpio, 1);
    udelay(CS1237_T_SCLK_HIGH_US);

    /* Read data bit */
    bit = gpiod_get_value(cs1237->dout_gpio);

    /* Set SCLK low */
    gpiod_set_value(cs1237->sclk_gpio, 0);
    udelay(CS1237_T_SCLK_LOW_US);

    return bit;
}

/* Helper function to write data bit */
static void cs1237_write_bit(struct cs1237_dev *cs1237, int bit)
{
    /* Set data pin to output mode if shared */
    cs1237_set_data_direction(cs1237, true);

    /* Set data value */
    if (cs1237->shared_data_pin) {
        gpiod_set_value(cs1237->dout_gpio, bit);
    } else if (cs1237->din_gpio) {
        gpiod_set_value(cs1237->din_gpio, bit);
    }

    /* Set SCLK high */
    gpiod_set_value(cs1237->sclk_gpio, 1);
    udelay(CS1237_T_SCLK_HIGH_US);

    /* Set SCLK low */
    gpiod_set_value(cs1237->sclk_gpio, 0);
    udelay(CS1237_T_SCLK_LOW_US);

    /* Set data pin back to input mode if shared */
    if (cs1237->shared_data_pin) {
        cs1237_set_data_direction(cs1237, false);
    }
}

/* Read a 24-bit value from the CS1237 */
static int cs1237_read_value(struct cs1237_dev *cs1237)
{
    int i;
    int value = 0;
    int ready = 0;
    unsigned long timeout;

    /* Set data pin to input mode */
    cs1237_set_data_direction(cs1237, false);

    /* Wait for DOUT to go low (ready) */
    timeout = jiffies + msecs_to_jiffies(100); /* 100ms timeout */
    while (!ready && time_before(jiffies, timeout)) {
        ready = (gpiod_get_value(cs1237->dout_gpio) == 0);
        if (!ready)
            usleep_range(100, 200);
    }

    if (!ready) {
        dev_err(cs1237->dev, "Timeout waiting for CS1237 to be ready\n");
        return -ETIMEDOUT;
    }

    /* Read 24 bits of data */
    for (i = 0; i < 24; i++) {
        value = (value << 1) | cs1237_read_bit(cs1237);
    }

    /* Sign extension for 24-bit 2's complement */
    if (value & 0x800000)
        value |= 0xFF000000;

    return value;
}

/* Write a register to the CS1237 */
static int cs1237_write_register(struct cs1237_dev *cs1237, u8 reg, u8 value)
{
    int i;
    u8 cmd;

    /* Set data pin to input mode */
    cs1237_set_data_direction(cs1237, false);

    /* Wait for DOUT to go low (ready) */
    for (i = 0; i < 100; i++) {
        if (gpiod_get_value(cs1237->dout_gpio) == 0)
            break;
        usleep_range(100, 200);
    }

    if (i >= 100) {
        dev_err(cs1237->dev, "Timeout waiting for CS1237 to be ready\n");
        return -ETIMEDOUT;
    }

    /* Read 24 bits of data (and discard) */
    for (i = 0; i < 24; i++) {
        cs1237_read_bit(cs1237);
    }

    /* Send 29th pulse to enter command mode */
    cs1237_read_bit(cs1237);

    /* Send command (4 bits) */
    cmd = 0x08 | (reg & 0x03);
    for (i = 3; i >= 0; i--) {
        cs1237_write_bit(cs1237, (cmd >> i) & 0x01);
    }

    /* Send data (8 bits) */
    for (i = 7; i >= 0; i--) {
        cs1237_write_bit(cs1237, (value >> i) & 0x01);
    }

    /* Send 37th pulse to exit command mode */
    cs1237_read_bit(cs1237);

    return 0;
}

/* Read a register from the CS1237 */
static int cs1237_read_register(struct cs1237_dev *cs1237, u8 reg, u8 *value)
{
    int i;
    u8 cmd;
    u8 reg_val = 0;

    /* Set data pin to input mode */
    cs1237_set_data_direction(cs1237, false);

    /* Wait for DOUT to go low (ready) */
    for (i = 0; i < 100; i++) {
        if (gpiod_get_value(cs1237->dout_gpio) == 0)
            break;
        usleep_range(100, 200);
    }

    if (i >= 100) {
        dev_err(cs1237->dev, "Timeout waiting for CS1237 to be ready\n");
        return -ETIMEDOUT;
    }

    /* Read 24 bits of data (and discard) */
    for (i = 0; i < 24; i++) {
        cs1237_read_bit(cs1237);
    }

    /* Send 29th pulse to enter command mode */
    cs1237_read_bit(cs1237);

    /* Send command (4 bits) */
    cmd = 0x0C | (reg & 0x03);
    for (i = 3; i >= 0; i--) {
        cs1237_write_bit(cs1237, (cmd >> i) & 0x01);
    }

    /* Read data (8 bits) */
    for (i = 0; i < 8; i++) {
        reg_val = (reg_val << 1) | cs1237_read_bit(cs1237);
    }

    /* Send 37th pulse to exit command mode */
    cs1237_read_bit(cs1237);

    *value = reg_val;
    return 0;
}

/* Initialize the CS1237 device */
static int cs1237_init(struct cs1237_dev *cs1237)
{
    int ret;
    u8 config;

    /* Reset the device by holding SCLK high for >50ms */
    gpiod_set_value(cs1237->sclk_gpio, 1);
    msleep(60);
    gpiod_set_value(cs1237->sclk_gpio, 0);

    /* Wait for startup time */
    usleep_range(CS1237_T_STARTUP_US, CS1237_T_STARTUP_US + 1000);

    /* Read current configuration */
    ret = cs1237_read_register(cs1237, CS1237_REG_CONFIG, &config);
    if (ret < 0)
        return ret;

    /* Update configuration with default values */
    config &= ~(CS1237_CONFIG_SPEED_MASK | CS1237_CONFIG_GAIN_MASK |
               CS1237_CONFIG_CHANNEL_MASK | CS1237_CONFIG_BUF_MASK |
               CS1237_CONFIG_PGA_MASK);
    
    config |= (cs1237->speed << 6) | (cs1237->gain << 4) |
              (cs1237->channel << 2) | (cs1237->buffer_enabled << 1) |
              (cs1237->pga_enabled << 0);

    /* Write updated configuration */
    ret = cs1237_write_register(cs1237, CS1237_REG_CONFIG, config);
    if (ret < 0)
        return ret;

    /* Verify configuration */
    ret = cs1237_read_register(cs1237, CS1237_REG_CONFIG, &config);
    if (ret < 0)
        return ret;

    dev_info(cs1237->dev, "CS1237 initialized with config: 0x%02x\n", config);

    return 0;
}

/* IIO read_raw implementation */
static int cs1237_read_raw(struct iio_dev *indio_dev,
                          struct iio_chan_spec const *chan,
                          int *val, int *val2, long mask)
{
    struct cs1237_dev *cs1237 = iio_priv(indio_dev);
    int ret;

    switch (mask) {
    case IIO_CHAN_INFO_RAW:
        mutex_lock(&cs1237->lock);
        ret = cs1237_read_value(cs1237);
        mutex_unlock(&cs1237->lock);
        if (ret < 0)
            return ret;
        *val = ret;
        return IIO_VAL_INT;

    case IIO_CHAN_INFO_SCALE:
        /* Calculate scale based on gain setting */
        switch (cs1237->gain) {
        case CS1237_GAIN_1:
            *val = 1;
            *val2 = 8388608; /* 2^23 for 24-bit ADC */
            break;
        case CS1237_GAIN_2:
            *val = 1;
            *val2 = 16777216; /* 2^24 */
            break;
        case CS1237_GAIN_64:
            *val = 1;
            *val2 = 536870912; /* 2^29 */
            break;
        case CS1237_GAIN_128:
            *val = 1;
            *val2 = 1073741824; /* 2^30 */
            break;
        default:
            return -EINVAL;
        }
        return IIO_VAL_FRACTIONAL;

    case IIO_CHAN_INFO_OFFSET:
        *val = cs1237->offset;
        return IIO_VAL_INT;

    case IIO_CHAN_INFO_SAMP_FREQ:
        switch (cs1237->speed) {
        case CS1237_SPEED_10HZ:
            *val = 10;
            break;
        case CS1237_SPEED_40HZ:
            *val = 40;
            break;
        case CS1237_SPEED_640HZ:
            *val = 640;
            break;
        case CS1237_SPEED_1280HZ:
            *val = 1280;
            break;
        default:
            return -EINVAL;
        }
        return IIO_VAL_INT;

    default:
        return -EINVAL;
    }
}

/* IIO write_raw implementation */
static int cs1237_write_raw(struct iio_dev *indio_dev,
                           struct iio_chan_spec const *chan,
                           int val, int val2, long mask)
{
    struct cs1237_dev *cs1237 = iio_priv(indio_dev);
    int ret;
    u8 config;

    switch (mask) {
    case IIO_CHAN_INFO_SAMP_FREQ:
        /* Set sampling frequency */
        if (val == 10)
            cs1237->speed = CS1237_SPEED_10HZ;
        else if (val == 40)
            cs1237->speed = CS1237_SPEED_40HZ;
        else if (val == 640)
            cs1237->speed = CS1237_SPEED_640HZ;
        else if (val == 1280)
            cs1237->speed = CS1237_SPEED_1280HZ;
        else
            return -EINVAL;

        mutex_lock(&cs1237->lock);
        ret = cs1237_read_register(cs1237, CS1237_REG_CONFIG, &config);
        if (ret < 0) {
            mutex_unlock(&cs1237->lock);
            return ret;
        }

        config &= ~CS1237_CONFIG_SPEED_MASK;
        config |= (cs1237->speed << 6);

        ret = cs1237_write_register(cs1237, CS1237_REG_CONFIG, config);
        mutex_unlock(&cs1237->lock);
        return ret;

    case IIO_CHAN_INFO_OFFSET:
        /* Set offset value */
        cs1237->offset = val;
        mutex_lock(&cs1237->lock);
        ret = cs1237_write_register(cs1237, CS1237_REG_OFFSET, val & 0xFF);
        mutex_unlock(&cs1237->lock);
        return ret;

    default:
        return -EINVAL;
    }
}

/* Probe function */
static int cs1237_probe(struct platform_device *pdev)
{
    struct device *dev = &pdev->dev;
    struct cs1237_dev *cs1237;
    struct iio_dev *indio_dev;
    int ret;

    indio_dev = devm_iio_device_alloc(dev, sizeof(*cs1237));
    if (!indio_dev)
        return -ENOMEM;

    cs1237 = iio_priv(indio_dev);
    cs1237->dev = dev;

    /* Get GPIO descriptors */
    cs1237->sclk_gpio = devm_gpiod_get(dev, "sclk", GPIOD_OUT_LOW);
    if (IS_ERR(cs1237->sclk_gpio)) {
        dev_err(dev, "Failed to get SCLK GPIO\n");
        return PTR_ERR(cs1237->sclk_gpio);
    }

    cs1237->dout_gpio = devm_gpiod_get(dev, "dout", GPIOD_IN);
    if (IS_ERR(cs1237->dout_gpio)) {
        dev_err(dev, "Failed to get DOUT GPIO\n");
        return PTR_ERR(cs1237->dout_gpio);
    }

    /* Try to get DIN GPIO, if not available, use shared pin mode */
    cs1237->din_gpio = devm_gpiod_get_optional(dev, "din", GPIOD_OUT_HIGH);
    cs1237->shared_data_pin = (cs1237->din_gpio == NULL);

    if (cs1237->shared_data_pin) {
        dev_info(dev, "Using shared data pin mode\n");
    } else {
        dev_info(dev, "Using separate data pins mode\n");
    }

    /* Initialize mutex */
    mutex_init(&cs1237->lock);

    /* Set default configuration */
    cs1237->gain = CS1237_GAIN_1;
    cs1237->channel = CS1237_CHANNEL_A;
    cs1237->speed = CS1237_SPEED_10HZ;
    cs1237->buffer_enabled = false;
    cs1237->pga_enabled = true;
    cs1237->offset = 0;

    /* Override defaults from device tree if available */
    of_property_read_u8(dev->of_node, "gain", &cs1237->gain);
    of_property_read_u8(dev->of_node, "channel", &cs1237->channel);
    of_property_read_u8(dev->of_node, "speed", &cs1237->speed);
    cs1237->buffer_enabled = of_property_read_bool(dev->of_node, "buffer-enabled");
    cs1237->pga_enabled = of_property_read_bool(dev->of_node, "pga-enabled");

    /* Setup IIO device */
    indio_dev->name = "cs1237";
    indio_dev->dev.parent = dev;
    indio_dev->info = &cs1237_info;
    indio_dev->modes = INDIO_DIRECT_MODE;
    indio_dev->channels = cs1237_channels;
    indio_dev->num_channels = ARRAY_SIZE(cs1237_channels);

    platform_set_drvdata(pdev, indio_dev);

    /* Initialize CS1237 */
    ret = cs1237_init(cs1237);
    if (ret < 0) {
        dev_err(dev, "Failed to initialize CS1237: %d\n", ret);
        return ret;
    }

    /* Register IIO device */
    ret = devm_iio_device_register(dev, indio_dev);
    if (ret < 0) {
        dev_err(dev, "Failed to register IIO device: %d\n", ret);
        return ret;
    }

    dev_info(dev, "CS1237 ADC driver initialized\n");
    return 0;
}

/* Remove function */
static int cs1237_remove(struct platform_device *pdev)
{
    /* Resources are automatically freed by the devm_* functions */
    return 0;
}

/* Device tree match table */
static const struct of_device_id cs1237_of_match[] = {
    { .compatible = "chipsen,cs1237", },
    { }
};
MODULE_DEVICE_TABLE(of, cs1237_of_match);

/* Platform driver structure */
static struct platform_driver cs1237_driver = {
    .probe = cs1237_probe,
    .remove = cs1237_remove,
    .driver = {
        .name = "cs1237",
        .of_match_table = cs1237_of_match,
    },
};

module_platform_driver(cs1237_driver);

MODULE_AUTHOR("denisj");
MODULE_DESCRIPTION("CS1237 ADC driver");
MODULE_LICENSE("GPL");