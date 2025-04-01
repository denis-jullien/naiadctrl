import time
import asyncio
import RPi.GPIO as GPIO
import threading
from collections import deque
import statistics  # For median calculation
# import pigpio # maybe we could use pigpio bitbang spi for CS1237 reading ?

# CS1237 Configuration Constants
CS1237_PGA_1 = 0
CS1237_PGA_2 = 1
CS1237_PGA_64 = 2
CS1237_PGA_128 = 3

CS1237_SPEED_10HZ = 0
CS1237_SPEED_40HZ = 1
CS1237_SPEED_640HZ = 2
CS1237_SPEED_1280HZ = 3

CS1237_CHANNEL_A = 0
CS1237_CHANNEL_TEMP = 1

CS1237_REFO_DISABLE = 0
CS1237_REFO_ENABLE = 1


class CS1237:
    def __init__(
        self,
        sck_pin,
        data_read_pin,
        data_write_pin,
        pga=CS1237_PGA_1,
        speed=CS1237_SPEED_10HZ,
        channel=CS1237_CHANNEL_A,
        refo=CS1237_REFO_DISABLE,
        sample_buffer_size=20,
    ):
        """
        Initialize CS1237 ADC

        Args:
            sck_pin: Clock pin
            data_read_pin: Data read pin
            data_write_pin: Data write pin (inverted output)
            pga: Programmable Gain Amplifier setting
            speed: Sampling speed
            channel: Input channel
            refo: Reference output enable
            sample_buffer_size: Size of the sample buffer for averaging
        """
        self.sck_pin = sck_pin
        self.data_read_pin = data_read_pin
        self.data_write_pin = data_write_pin
        self.pga = pga
        self.speed = speed
        self.channel = channel
        self.refo = refo

        # Internal state variables
        self._data_ready = False
        self._raw_data = 0
        self._voltage = 0.0
        self._running = False
        self._ref_thread = None
        self._lock = threading.Lock()

        # Sample buffer for averaging
        self._sample_buffer_size = sample_buffer_size
        self._voltage_buffer = deque(maxlen=sample_buffer_size)

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.sck_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.data_read_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(
            self.data_write_pin, GPIO.OUT, initial=GPIO.LOW
        )  # Keep low for reading

        print(
            f"CS1237 initialized with pins: SCK={sck_pin}, DATA_READ={data_read_pin}, DATA_WRITE={data_write_pin}"
        )

    async def initialize(self):
        """Initialize the CS1237 and configure it"""
        # Power up the CS1237
        GPIO.output(self.sck_pin, GPIO.HIGH)
        await asyncio.sleep(0.001)
        GPIO.output(self.sck_pin, GPIO.LOW)

        # Wait for data ready (DOUT goes low)
        timeout = asyncio.get_event_loop().time() + 0.5  # 500ms timeout
        while GPIO.input(self.data_read_pin) == GPIO.HIGH:
            if asyncio.get_event_loop().time() > timeout:
                print("CS1237 initialization timeout!")
                return False
            await asyncio.sleep(0.001)

        # Configure the CS1237
        config_byte = (
            (self.speed & 0x03)
            | ((self.pga & 0x03) << 2)
            | ((self.channel & 0x01) << 4)
            | ((self.refo & 0x01) << 5)
        )

        self._write_config(config_byte)

        # Verify configuration
        read_config = self._read_config()
        if read_config is None:
            print("Failed to read configuration")
            return False

        print(
            f"CS1237 configured: PGA={self.pga}, SPEED={self.speed}, CHANNEL={self.channel}, REFO={self.refo}"
        )
        print(f"Config byte: 0x{config_byte:02X}, Read config: 0x{read_config:02X}")

        return True

    def start(self):
        """Start continuous data acquisition"""
        if self._running:
            return

        self._running = True
        self._ref_thread = threading.Thread(target=self._ref_loop)
        self._ref_thread.daemon = True
        self._ref_thread.start()
        print("CS1237 data acquisition started")

    def stop(self):
        """Stop data acquisition"""
        self._running = False
        if self._ref_thread:
            self._ref_thread.join(timeout=1.0)
            self._ref_thread = None
        print("CS1237 data acquisition stopped")

    def get_data(self):
        """Get the latest voltage reading"""
        with self._lock:
            return self._voltage

    def get_raw_data(self):
        """Get the latest raw ADC reading"""
        with self._lock:
            return self._raw_data

    def get_averaged_data(self, num_samples=None, use_median=True, median_window=5):
        """
        Get averaged voltage reading with optional median filtering

        Args:
            num_samples: Number of samples to average (default: use all available samples)
            use_median: Whether to apply median filtering before averaging
            median_window: Size of the median filter window (default: 5)

        Returns:
            float: Averaged voltage reading
        """
        with self._lock:
            if not self._voltage_buffer:
                return self._voltage

            if num_samples is None or num_samples > len(self._voltage_buffer):
                num_samples = len(self._voltage_buffer)

            # Get the most recent n samples
            recent_samples = list(self._voltage_buffer)[-num_samples:]

            if use_median and len(recent_samples) >= median_window:
                # Apply median filter to remove outliers
                # For each window of median_window consecutive samples, replace with median
                filtered_samples = []
                for i in range(len(recent_samples) - (median_window - 1)):
                    window = recent_samples[i : i + median_window]
                    filtered_samples.append(statistics.median(window))

                return sum(filtered_samples) / len(filtered_samples)
            else:
                # Simple averaging without median filtering
                return sum(recent_samples) / len(recent_samples)

    def _ref_loop(self):
        """Background thread for continuous data acquisition"""
        while self._running:
            self._ref()
            time.sleep(0.001)  # 1ms interval

    def _ref(self):
        """Read data from CS1237 (called periodically)"""
        # Check if data is ready (DOUT is low)
        if GPIO.input(self.data_read_pin) == GPIO.HIGH:
            return

        # Keep data_write_pin low for reading
        GPIO.output(self.data_write_pin, GPIO.LOW)

        # Read 24 bits
        raw_data = 0
        for i in range(24):
            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)  # 1µs delay

            bit = GPIO.input(self.data_read_pin)
            raw_data = (raw_data << 1) | bit

            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)  # 1µs delay

        # Additional clock cycles (25-26) to complete the reading
        for i in range(3):
            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)

        # if clocks are too streched (python sleep uncertainty) we may need to send pulses to have DRDY back high
        for i in range(5):
            if GPIO.input(self.data_read_pin):
                break
            # print("Error DOUT not pulled high")
            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)

        # Convert to signed value
        if raw_data & 0x800000:
            raw_data = raw_data - 0x1000000

        # Calculate voltage (assuming 3.3V reference)
        voltage = (raw_data / 0x7FFFFF) * 3.3 / 2.0

        # Update values with lock to prevent race conditions
        with self._lock:
            self._raw_data = raw_data
            self._voltage = voltage
            self._data_ready = True

            # Add to sample buffers for averaging
            self._voltage_buffer.append(voltage)

        # sleep to next sample
        rate_values = {
            CS1237_SPEED_10HZ: 0.1,
            CS1237_SPEED_40HZ: 0.025,
            CS1237_SPEED_640HZ: 0.0015625,
            CS1237_SPEED_1280HZ: 0.00078125,
        }
        sleep = rate_values.get(self.speed, 0.001)
        # print(f"{sleep} : {voltage:.6f}v")
        time.sleep(sleep * 0.95)

    def _write_config(self, config_byte):
        """Write configuration to CS1237"""
        # Wait for data ready
        timeout = time.time() + 0.5  # 500ms timeout
        while GPIO.input(self.data_read_pin) == GPIO.HIGH:
            if time.time() > timeout:
                print("CS1237 write config timeout!")
                return False
            time.sleep(0.001)

        # Read 24 bits (discard)
        for i in range(24):
            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)

        # 25th to 26th SCLKs - read register write operation status
        for i in range(2):
            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)

        # 27th SCLK - pulls DRDY/DOUT high
        GPIO.output(self.sck_pin, GPIO.HIGH)
        time.sleep(0.000001)
        GPIO.output(self.sck_pin, GPIO.LOW)
        time.sleep(0.000001)

        # 28th to 29th SCLK - switch DRDY/DOUT to input
        for i in range(2):
            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)

        # 30th to 36th SCLK - input register command word (7 bits)
        # Send write command (0x65 = 0b01100101)
        command = 0x65
        for i in range(7):
            bit = (command >> (6 - i)) & 0x01

            # Set data write pin before clock goes high
            # Invert the bit value for data_write_pin (inverted output)
            GPIO.output(self.data_write_pin, not bit)

            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)

        # 37th SCLK - switch direction (for write, DRDY/DOUT remains input)
        GPIO.output(self.sck_pin, GPIO.HIGH)
        time.sleep(0.000001)
        GPIO.output(self.sck_pin, GPIO.LOW)
        time.sleep(0.000001)

        # 38th to 45th SCLK - input register data (8 bits)
        for i in range(8):
            bit = (config_byte >> (7 - i)) & 0x01

            # Set data write pin before clock goes high
            # Invert the bit value for data_write_pin (inverted output)
            GPIO.output(self.data_write_pin, not bit)

            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)

        # Reset data write pin to low for reading
        GPIO.output(self.data_write_pin, GPIO.LOW)

        return True

    def _read_config(self):
        """Read configuration from CS1237"""
        # Wait for data ready
        timeout = time.time() + 0.5  # 500ms timeout
        while GPIO.input(self.data_read_pin) == GPIO.HIGH:
            if time.time() > timeout:
                print("CS1237 read config timeout!")
                return None
            time.sleep(0.001)

        # Read 24 bits (discard)
        for i in range(24):
            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)

        # 25th to 26th SCLKs - read register write operation status
        for i in range(2):
            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)

        # 27th SCLK - pulls DRDY/DOUT high
        GPIO.output(self.sck_pin, GPIO.HIGH)
        time.sleep(0.000001)
        GPIO.output(self.sck_pin, GPIO.LOW)
        time.sleep(0.000001)

        # 28th to 29th SCLK - switch DRDY/DOUT to input
        for i in range(2):
            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)

        # 30th to 36th SCLK - input register command word (7 bits)
        # Send read command (0x56 = 0b01010110)
        command = 0x56
        for i in range(7):
            bit = (command >> (6 - i)) & 0x01

            # Set data write pin before clock goes high
            # Invert the bit value for data_write_pin (inverted output)
            GPIO.output(self.data_write_pin, not bit)

            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)

        # 37th SCLK - switch direction (for read, DRDY/DOUT becomes output)
        GPIO.output(self.sck_pin, GPIO.HIGH)
        time.sleep(0.000001)
        GPIO.output(self.sck_pin, GPIO.LOW)
        time.sleep(0.000001)

        # 38th to 45th SCLK - read register data (8 bits)
        config_byte = 0
        for i in range(8):
            GPIO.output(self.sck_pin, GPIO.HIGH)
            time.sleep(0.000001)

            # Read bit from data_read_pin
            bit = GPIO.input(self.data_read_pin)
            config_byte = (config_byte << 1) | bit

            GPIO.output(self.sck_pin, GPIO.LOW)
            time.sleep(0.000001)

        # Reset data write pin to low for reading
        GPIO.output(self.data_write_pin, GPIO.LOW)

        return config_byte

    def close(self):
        """Clean up resources"""
        self.stop()
        GPIO.cleanup([self.sck_pin, self.data_read_pin, self.data_write_pin])
        print("CS1237 resources cleaned up")
