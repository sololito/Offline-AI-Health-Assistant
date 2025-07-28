# sensors/glucose_meter.py

import random
import time

class GlucoseMeter:
    def __init__(self, simulate=True):
        self.simulate = simulate

    def read_glucose_level(self):
        if self.simulate:
            # Simulate glucose reading in mg/dL
            # Normal fasting: 70–99 mg/dL
            # After meal: <140 mg/dL
            return round(random.uniform(65, 180), 1)
        else:
            # Real device read logic should be implemented here
            # Example: read from serial, USB, or SDK
            return 0.0  # Placeholder


if __name__ == "__main__":
    meter = GlucoseMeter(simulate=True)
    while True:
        glucose = meter.read_glucose_level()
        print(f"Glucose Level: {glucose} mg/dL")
        time.sleep(3)
