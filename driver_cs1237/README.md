# Linux Device Driver for CS1237 ADC

This driver implements the CS1237 as an Industrial I/O (IIO) device, which is the standard Linux subsystem for ADCs and similar devices. 
It supports both shared and separate data pin configurations and provides access to all the chip's features through the IIO sysfs interface.

## Device Tree Example

Here's an example of how to configure the CS1237 in your device tree:

```dts
cs1237@0 {
    compatible = "chipsen,cs1237";
    
    /* GPIO pins */
    sclk-gpios = <&gpio0 17 GPIO_ACTIVE_HIGH>;
    dout-gpios = <&gpio0 18 GPIO_ACTIVE_HIGH>;
    din-gpios = <&gpio0 19 GPIO_ACTIVE_HIGH>;  /* Optional, omit for shared pin mode */
    
    /* Configuration */
    gain = <0>;          /* 0=1x, 1=2x, 2=64x, 3=128x */
    channel = <0>;       /* 0=A, 1=SHORT, 2=TEMP, 3=AVDD */
    speed = <0>;         /* 0=10Hz, 1=40Hz, 2=640Hz, 3=1280Hz */
    buffer-enabled;      /* Include if buffer should be enabled */
    pga-enabled;         /* Include if PGA should be enabled */
};
```

## Usage Instructions

1. Build the driver:
   ```bash
   make
   ```

2. Install the driver:
   ```bash
   sudo make install
   ```

3. Load the driver:
   ```bash
   sudo modprobe cs1237
   ```

4. Read ADC values:
   ```bash
   cat /sys/bus/iio/devices/iio:device0/in_voltage0_raw
   ```

5. Configure sampling rate:
   ```bash
   echo 40 > /sys/bus/iio/devices/iio:device0/in_voltage_sampling_frequency
   ```

