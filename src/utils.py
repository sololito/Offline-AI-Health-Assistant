# /src/utils.py

import re

def clean_symptom_input(symptom):
    """
    Cleans and standardizes a single symptom string.
    - Lowercases
    - Removes punctuation/special characters
    - Strips whitespace
    """
    if not isinstance(symptom, str):
        return ""
    symptom = symptom.lower()
    symptom = re.sub(r"[^\w\s]", "", symptom)  # remove punctuation
    symptom = re.sub(r"\s+", " ", symptom)     # normalize spaces
    return symptom.strip()

def clean_symptom_list(symptom_list):
    """
    Applies clean_symptom_input to a list of symptoms.
    """
    return [clean_symptom_input(s) for s in symptom_list if isinstance(s, str)]
