# sensors/temperature_sensor.py

import random
import time

try:
    from smbus2 import SMBus
    REAL_SENSOR_AVAILABLE = True
except ImportError:
    REAL_SENSOR_AVAILABLE = False


class TemperatureSensor:
    def __init__(self, simulate=False, address=0x5A, bus_num=1):
        self.simulate = simulate or not REAL_SENSOR_AVAILABLE
        self.address = address
        self.bus_num = bus_num
        if not self.simulate:
            self.bus = SMBus(bus_num)

    def _read_raw_temp(self, reg):
        data = self.bus.read_word_data(self.address, reg)
        return ((data << 8) & 0xFF00) + (data >> 8)

    def get_object_temp(self):
        if self.simulate:
            return round(random.uniform(36.0, 38.5), 2)
        raw = self._read_raw_temp(0x07)
        return round(raw * 0.02 - 273.15, 2)

    def get_ambient_temp(self):
        if self.simulate:
            return round(random.uniform(25.0, 30.0), 2)
        raw = self._read_raw_temp(0x06)
        return round(raw * 0.02 - 273.15, 2)


if __name__ == "__main__":
    sensor = TemperatureSensor(simulate=True)
    while True:
        print(f"Ambient: {sensor.get_ambient_temp()} °C | Object: {sensor.get_object_temp()} °C")
        time.sleep(2)
