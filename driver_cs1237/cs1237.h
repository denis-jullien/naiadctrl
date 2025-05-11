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

#ifndef CS1237_H
#define CS1237_H

#include <linux/types.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_gpio.h>
#include <linux/gpio/consumer.h>
#include <linux/delay.h>
#include <linux/iio/iio.h>
#include <linux/mutex.h>

/* CS1237 Gain settings */
#define CS1237_GAIN_1      0x00
#define CS1237_GAIN_2      0x01
#define CS1237_GAIN_64     0x02
#define CS1237_GAIN_128    0x03

/* CS1237 Channel settings */
#define CS1237_CHANNEL_A   0x00
#define CS1237_CHANNEL_TEMP 0x02
#define CS1237_CHANNEL_SHORT 0x01
#define CS1237_CHANNEL_AVDD 0x03

/* CS1237 Speed settings */
#define CS1237_SPEED_10HZ  0x00
#define CS1237_SPEED_40HZ  0x01
#define CS1237_SPEED_640HZ 0x02
#define CS1237_SPEED_1280HZ 0x03

/* CS1237 Register addresses */
#define CS1237_REG_CONFIG  0x00
#define CS1237_REG_OFFSET  0x01
#define CS1237_REG_GAIN    0x02

/* CS1237 Configuration bits */
#define CS1237_CONFIG_SPEED_MASK   (0x03 << 6)
#define CS1237_CONFIG_GAIN_MASK    (0x03 << 4)
#define CS1237_CONFIG_CHANNEL_MASK (0x03 << 2)
#define CS1237_CONFIG_BUF_MASK     (0x01 << 1)
#define CS1237_CONFIG_PGA_MASK     (0x01 << 0)

/* CS1237 Timing parameters (in microseconds) */
#define CS1237_T_STARTUP_US    5000    /* 5ms startup time */
#define CS1237_T_SETUP_US      1       /* 1µs setup time */
#define CS1237_T_HOLD_US       1       /* 1µs hold time */
#define CS1237_T_SCLK_HIGH_US  1       /* 1µs SCLK high time */
#define CS1237_T_SCLK_LOW_US   1       /* 1µs SCLK low time */

/* CS1237 device structure */
struct cs1237_dev {
    struct device *dev;
    struct mutex lock;
    struct gpio_desc *sclk_gpio;
    struct gpio_desc *dout_gpio;
    struct gpio_desc *din_gpio;  /* May be NULL if shared with dout */
    bool shared_data_pin;
    u8 gain;
    u8 channel;
    u8 speed;
    bool buffer_enabled;
    bool pga_enabled;
    u32 offset;
    u32 full_scale;
};

#endif /* CS1237_H */