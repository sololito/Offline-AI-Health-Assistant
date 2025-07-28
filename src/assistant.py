# /src/assistant.py

from src.symptom_matcher import SymptomMatcher
import os

class HealthAssistant:
    def __init__(self, matcher=None):
        self.matcher = matcher or SymptomMatcher()

    def diagnose(self, user_symptoms, top_n=5):
        """
        Returns top disease matches based on symptoms with prescription information.
        
        Args:
            user_symptoms (list): List of symptoms entered by the user
            top_n (int): Number of top matches to return
            
        Returns:
            list: List of dictionaries containing disease information, match scores, and prescriptions
        """
        if not user_symptoms or not isinstance(user_symptoms, list):
            raise ValueError("Expected a non-empty list of symptoms.")

        # Get matches from symptom matcher
        matches = self.matcher.match_symptoms(user_symptoms, top_n=top_n)
        
        # Format the results for the frontend
        formatted_results = []
        for match in matches:
            result = {
                'disease': match['disease'],
                'confidence': f"{int(match['match_score'] * 100)}%",
                'matched_symptoms': match['matching_symptoms'],
                'total_symptoms': match['known_symptom_count'],
                'recommendations': []
            }
            
            # Add prescription information if available
            if 'prescription' in match and 'recommendations' in match['prescription']:
                result['recommendations'] = match['prescription']['recommendations']
            
            formatted_results.append(result)
        
        return formatted_results

    def explain(self, match_result):
        """
        Optional method to provide an explanation for a given match.
        Could include overlapping symptoms, severity, etc.
        """
        explanation = (
            f"Disease: {match_result['disease']}\n"
            f"- Match Score: {match_result['match_score']}\n"
            f"- Matching Symptoms: {match_result['matching_symptoms']}\n"
            f"- Total Known Symptoms: {match_result['known_symptom_count']}\n"
            f"- Your Input Count: {match_result['user_symptom_count']}"
        )
        return explanation
