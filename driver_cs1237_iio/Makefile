# Makefile for CS1237 ADC driver (out-of-tree build)

# If KERNELRELEASE is defined, we've been invoked from the
# kernel build system and can use its language.
ifneq ($(KERNELRELEASE),)
	obj-m := cs1237.o

# Otherwise we were called directly from the command line.
# Invoke the kernel build system.
else

KERNEL_DIR ?= /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

# Target for building the module
all:
	$(MAKE) -C $(KERNEL_DIR) M=$(PWD) modules

# Target for installing the module
install:
	$(MAKE) -C $(KERNEL_DIR) M=$(PWD) modules_install
	depmod -a

# Target for cleaning build files
clean:
	$(MAKE) -C $(KERNEL_DIR) M=$(PWD) clean

# Target for building and installing the device tree overlay
dtbo:
	dtc -@ -I dts -O dtb -o cs1237-overlay.dtbo cs1237-overlay.dts

# Target for installing the device tree overlay
dtbo-install: dtbo
	sudo cp cs1237-overlay.dtbo /boot/overlays/
	@echo "Don't forget to add 'dtoverlay=cs1237' to /boot/config.txt"

# Target for building everything
all-build: all dtbo

# Target for installing everything
all-install: install dtbo-install

endif