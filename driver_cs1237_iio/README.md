# CS1237 Linux IIO Driver

This is a Linux Industrial I/O (IIO) subsystem driver for the Chipsea CS1237 24-bit ADC chip, commonly used in weight scales and precision measurement applications.

## Overview

The CS1237 is a high-precision 24-bit analog-to-digital converter (ADC) that uses a custom communication protocol similar to SPI but with some unique timing sequences. This driver implements this protocol using GPIO bitbanging to interface with the CS1237 chip.

## Features

- Full support for the CS1237 ADC using the Linux IIO subsystem
- Configurable PGA (Programmable Gain Amplifier) settings: 1, 2, 64, 128
- Configurable sampling rates: 10Hz, 40Hz, 640Hz, 1280Hz
- Support for both analog input and temperature sensor channel
- Continuous sampling with a buffer for data averaging
- Adjustable buffer size for averaging and median filtering
- Sysfs attributes for driver control and statistics

## Hardware Setup

The CS1237 requires three GPIO pins for communication:
- SCK: Clock pin (output from SBC)
- DOUT: Data output from CS1237 (input to SBC)
- DIN: Data input to CS1237 (output from SBC)

## Device Tree Configuration

Example Device Tree Overlay for Raspberry Pi:

```dts
// Overlay for Chipsea CS1237 24-bit ADC
/dts-v1/;
/plugin/;

/ {
    compatible = "brcm,bcm2835";
    
    fragment@0 {
        target-path = "/";
        __overlay__ {
            cs1237_adc: cs1237_adc {
                compatible = "chipsea,cs1237";
                status = "okay";
                
                /* Define GPIOs: SCK, DOUT, DIN */
                sck-gpios = <&gpio 17 0>;   /* GPIO 17 as SCK pin */
                dout-gpios = <&gpio 27 0>;  /* GPIO 27 as DOUT pin */
                din-gpios = <&gpio 22 0>;   /* GPIO 22 as DIN pin */
                
                /* Configuration */
                chipsea,pga = <0>;      /* PGA = 1 */
                chipsea,speed = <1>;    /* 40Hz sampling rate */
                chipsea,channel = <0>;  /* Channel A */
                chipsea,refo = <0>;     /* Reference output disabled */
                chipsea,buffer-size = <20>; /* 20 samples buffer size */
            };
        };
    };
};
```

## Device Tree Properties

| Property            | Description                                         | Values                                         |
|---------------------|-----------------------------------------------------|------------------------------------------------|
| sck-gpios           | GPIO pin for clock signal                           | GPIO descriptor                                |
| dout-gpios          | GPIO pin for data output from CS1237                | GPIO descriptor                                |
| din-gpios           | GPIO pin for data input to CS1237                   | GPIO descriptor                                |
| chipsea,pga         | Programmable Gain Amplifier setting                 | 0 (PGA=1), 1 (PGA=2), 2 (PGA=64), 3 (PGA=128) |
| chipsea,speed       | Sampling rate setting                               | 0 (10Hz), 1 (40Hz), 2 (640Hz), 3 (1280Hz)     |
| chipsea,channel     | Input channel selection                             | 0 (Analog), 1 (Temperature)                    |
| chipsea,refo        | Reference output enable                             | 0 (Disabled), 1 (Enabled)                      |
| chipsea,buffer-size | Buffer size for averaging and statistics            | Number of samples (default: 20)                |

## Sysfs Interface

The driver provides several sysfs attributes for control and monitoring:

| Attribute           | Access | Description                                        |
|---------------------|--------|----------------------------------------------------|
| cs1237_reset        | W      | Trigger a reset and reconfiguration of the device  |
| cs1237_running      | RW     | Control or check data acquisition state            |
| cs1237_samples      | R      | Number of samples collected since start            |
| cs1237_mean         | R      | Mean value of all samples                          |
| cs1237_clear_stats  | W      | Clear statistics (mean and sample count)           |

## Using IIO attributes

The driver provides standard IIO attributes for reading and configuring the ADC:

### Reading raw values

```bash
# Read raw value from analog channel (default)
cat /sys/bus/iio/devices/iio:device0/in_voltage0_raw

# Read raw value from temperature channel
cat /sys/bus/iio/devices/iio:device0/in_temp1_raw
```

### Reading processed values (with scale applied)

```bash
# Read voltage in volts
cat /sys/bus/iio/devices/iio:device0/in_voltage0_raw
cat /sys/bus/iio/devices/iio:device0/in_voltage_scale
# Multiply raw * scale to get voltage in volts

# Read temperature
cat /sys/bus/iio/devices/iio:device0/in_temp1_raw  
cat /sys/bus/iio/devices/iio:device0/in_temp_scale
# Multiply raw * scale to get temperature in degrees C
```

### Configuring sampling rate

```bash
# Available sampling rates
cat /sys/bus/iio/devices/iio:device0/sampling_frequency_available
# Returns: 10 40 640 1280

# Set sampling rate to 40Hz
echo 40 > /sys/bus/iio/devices/iio:device0/sampling_frequency
```

### Using custom attributes

```bash
# Reset the device
echo 1 > /sys/bus/iio/devices/iio:device0/cs1237_reset

# Stop data acquisition
echo 0 > /sys/bus/iio/devices/iio:device0/cs1237_running

# Start data acquisition
echo 1 > /sys/bus/iio/devices/iio:device0/cs1237_running

# Get number of samples collected
cat /sys/bus/iio/devices/iio:device0/cs1237_samples

# Get mean value of all samples
cat /sys/bus/iio/devices/iio:device0/cs1237_mean

# Clear statistics
echo 1 > /sys/bus/iio/devices/iio:device0/cs1237_clear_stats
```

## Building and Installing

1. Add the driver to the kernel source tree in `drivers/iio/adc/cs1237.c`
2. Add the following line to `drivers/iio/adc/Kconfig`:
   ```
   config CS1237
       tristate "Chipsea CS1237 24-bit ADC driver"
       depends on GPIOLIB
       help
         Say yes here to build support for the Chipsea CS1237 24-bit
         analog-to-digital converter (ADC).
         
         This driver can also be built as a module. If so, the module will
         be called cs1237.
   ```
3. Add the following line to `drivers/iio/adc/Makefile`:
   ```
   obj-$(CONFIG_CS1237) += cs1237.o
   ```
4. Enable the driver in kernel configuration:
   ```
   Device Drivers -> Industrial I/O support -> Analog to digital converters -> Chipsea CS1237 24-bit ADC driver
   ```
5. Build and install the kernel or module
6. Compile and install your device tree overlay

## Temp install 

```
make
make dtbo
sudo modprobe industrialio
sudo insmod cs1237.ko
sudo dtoverlay cs1237-overlay.dtbo

```
remove :
```
sudo rmmod cs1237
sudo dtoverlay -r cs1237-overlay
```


## Troubleshooting

- **No device in sysfs**: Check your GPIO pin configuration and connections
- **ADC readings unstable**: Try lowering the sampling rate or increasing the buffer size
- **Timeout errors in dmesg**: Check the connections to the CS1237, especially the DOUT pin
- **Configuration errors**: Verify that your configuration settings in the device tree are valid

## License

This driver is provided under the GPL v2 license.