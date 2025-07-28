import os
import json
import sys
from typing import List, Dict, Any, Optional

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.symptom_matcher import SymptomMatcher

# Initialize symptom matcher
symptom_matcher = SymptomMatcher()

# Load drug reference data
DRUG_REFERENCE = {}
DRUG_REFERENCE_FILE = os.path.join(project_root, 'data', 'drug_reference.json')

try:
    with open(DRUG_REFERENCE_FILE, 'r', encoding='utf-8') as f:
        DRUG_REFERENCE = json.load(f)
except Exception as e:
    print(f"Warning: Could not load drug reference data: {e}")
    DRUG_REFERENCE = {}

def get_medication_recommendations(condition: str) -> Optional[Dict[str, Any]]:
    """
    Get medication recommendations for a specific condition.
    Returns a dictionary with medication information or None if no match found.
    """
    if not condition or not DRUG_REFERENCE:
        return None
        
    # Try to find the best match in our drug reference
    condition_lower = condition.lower()
    
    # First try exact match
    for ref_condition, meds in DRUG_REFERENCE.items():
        if condition_lower == ref_condition.lower():
            return {
                'condition': ref_condition,
                'medications': meds.get('otc_medications', []),
                'home_remedies': meds.get('home_remedies', []),
                'medical_attention': meds.get('medical_attention', ''),
                'emergency_note': meds.get('emergency_note', '')
            }
    
    # Then try partial match
    for ref_condition, meds in DRUG_REFERENCE.items():
        if condition_lower in ref_condition.lower() or ref_condition.lower() in condition_lower:
            return {
                'condition': ref_condition,
                'medications': meds.get('otc_medications', []),
                'home_remedies': meds.get('home_remedies', []),
                'medical_attention': meds.get('medical_attention', ''),
                'emergency_note': meds.get('emergency_note', '')
            }
    
    return None

def format_condition_name(condition: str) -> str:
    """Format condition name for display."""
    # Remove extra spaces and clean up the name
    return ' '.join(word.capitalize() for word in condition.strip().split())



def get_diagnosis(vitals: Dict, symptoms: str) -> Dict:
    """
    Analyze symptoms to provide a diagnosis based on the disease-symptom database.
    Returns a dictionary with diagnosis, recommendations, and medication info.
    """
    # Process user input
    user_symptoms = [s.strip().lower() for s in symptoms.split(',') if s.strip()]
    print(f"\n=== Processing symptoms ===")
    print(f"User symptoms: {', '.join(user_symptoms)}")
    
    if not user_symptoms:
        return {
            "error": "No symptoms provided. Please enter your symptoms separated by commas.",
            "symptoms_entered": ""
        }
    
    # Get matching conditions from symptom matcher
    try:
        matches = symptom_matcher.match_symptoms(user_symptoms, top_n=5)
        print(f"Found {len(matches)} potential matches")
        
        # Prepare response
        response = {
            "symptoms_entered": ", ".join(user_symptoms),
            "possible_conditions": [],
            "disclaimer": "This information is not a substitute for professional medical advice. Always consult with a healthcare provider for proper diagnosis and treatment."
        }
        
        # Process matches
        for match in matches:
            if match['match_score'] > 0:
                condition = {
                    "disease": format_condition_name(match['disease']),
                    "confidence": f"{int(match['match_score'] * 100)}%",
                    "matched_symptoms": match['matching_symptoms'],
                    "total_symptoms": match['known_symptom_count']
                }
                
                # Get medication info for this condition
                med_info = get_medication_recommendations(match['disease'])
                if med_info:
                    condition["treatment"] = {
                        "medications": med_info.get('medications', []),
                        "home_remedies": med_info.get('home_remedies', []),
                        "medical_attention": med_info.get('medical_attention', ''),
                        "emergency_note": med_info.get('emergency_note', '')
                    }
                
                response["possible_conditions"].append(condition)
        
        # If no conditions found with significant match
        if not response["possible_conditions"]:
            response["message"] = "No specific conditions matched your symptoms. Please consult a healthcare provider for further evaluation."
        
        return response
        
    except Exception as e:
        print(f"Error in diagnosis: {str(e)}")
        return {
            "error": f"An error occurred while processing your symptoms: {str(e)}",
            "symptoms_entered": ", ".join(user_symptoms)
        }
    
    return response


# Example test
if __name__ == "__main__":
    test_vitals = {
        "temperature": {"object_temp": 38.4},
        "blood_pressure": {"systolic": 145, "diastolic": 95, "pulse": 105},
        "glucose_level": 180,
        "oxygen": 92
    }
    test_symptoms = "headache fatigue chills cough"

    result = get_diagnosis(test_vitals, test_symptoms)
    print("Possible Diagnosis:")
    for d in result["diagnosis"]:
        print(f"[DIAGNOSIS] {d}")
    print("\nRecommendations:")
    for r in result["recommendations"]:
        print(f"- {r}")
