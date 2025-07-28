# analysis/vitals_analyzer.py

def analyze_temperature(temp_celsius):
    if temp_celsius < 35.0:
        return "Hypothermia detected (Low body temperature)"
    elif 35.0 <= temp_celsius <= 37.5:
        return "Normal temperature"
    elif 37.5 < temp_celsius <= 38.5:
        return "Mild fever detected"
    else:
        return "High fever detected"

def analyze_blood_pressure(systolic, diastolic):
    if systolic < 90 or diastolic < 60:
        return "Low blood pressure (Hypotension)"
    elif 90 <= systolic <= 120 and 60 <= diastolic <= 80:
        return "Normal blood pressure"
    elif 120 < systolic <= 139 or 80 < diastolic <= 89:
        return "Prehypertension"
    else:
        return "High blood pressure (Hypertension)"

def analyze_pulse(pulse):
    if pulse < 60:
        return "Bradycardia (Low heart rate)"
    elif 60 <= pulse <= 100:
        return "Normal pulse rate"
    else:
        return "Tachycardia (High heart rate)"

def analyze_vitals(vitals_dict):
    """
    Expects format:
    {
        'temperature': {
            'object_temp': float,
            'ambient_temp': float
        },
        'blood_pressure': {
            'systolic': int,
            'diastolic': int,
            'pulse': int
        }
    }
    Returns analysis dict.
    """
    object_temp = vitals_dict['temperature']['object_temp']
    systolic = vitals_dict['blood_pressure']['systolic']
    diastolic = vitals_dict['blood_pressure']['diastolic']
    pulse = vitals_dict['blood_pressure']['pulse']

    return {
        "object_temp_status": analyze_temperature(object_temp),
        "bp_status": analyze_blood_pressure(systolic, diastolic),
        "pulse_status": analyze_pulse(pulse)
    }


# Test in isolation
if __name__ == "__main__":
    sample_data = {
        "temperature": {"object_temp": 38.2, "ambient_temp": 27.1},
        "blood_pressure": {"systolic": 145, "diastolic": 95, "pulse": 105}
    }

    result = analyze_vitals(sample_data)
    print("Analysis Result:")
    for key, value in result.items():
        print(f"{key}: {value}")
