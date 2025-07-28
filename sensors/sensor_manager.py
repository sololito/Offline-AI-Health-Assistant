# sensors/sensor_manager.py

from sensors.temperature_sensor import TemperatureSensor
from sensors.bp_monitor import BloodPressureMonitor


class SensorManager:
    def __init__(self, simulate=True):
        self.temp_sensor = TemperatureSensor(simulate=simulate)
        self.bp_monitor = BloodPressureMonitor(simulate=simulate)

    def get_all_vitals(self):
        temperature = {
            "object_temp": self.temp_sensor.get_object_temp(),
            "ambient_temp": self.temp_sensor.get_ambient_temp()
        }

        bp = self.bp_monitor.read()

        return {
            "temperature": temperature,
            "blood_pressure": bp
        }


if __name__ == "__main__":
    manager = SensorManager(simulate=True)
    vitals = manager.get_all_vitals()
    print(vitals)
