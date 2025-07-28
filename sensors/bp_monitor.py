# sensors/bp_monitor.py

import random
import time


class BloodPressureMonitor:
    def __init__(self, simulate=True):
        self.simulate = simulate

    def read(self):
        if self.simulate:
            systolic = random.randint(100, 140)
            diastolic = random.randint(70, 90)
            pulse = random.randint(60, 100)
        else:
            # Real serial/Bluetooth read logic should go here
            systolic, diastolic, pulse = 0, 0, 0  # Placeholder
        return {
            "systolic": systolic,
            "diastolic": diastolic,
            "pulse": pulse
        }


if __name__ == "__main__":
    bp = BloodPressureMonitor()
    while True:
        reading = bp.read()
        print(f"Systolic: {reading['systolic']} mmHg | Diastolic: {reading['diastolic']} mmHg | Pulse: {reading['pulse']} BPM")
        time.sleep(3)
