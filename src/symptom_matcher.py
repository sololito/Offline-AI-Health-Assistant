# /src/symptom_matcher.py

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

class SymptomMatcher:
    """
    Matches user-reported symptoms against a database of diseases and their symptoms.
    Also provides prescription information when available.
    """
    
    def __init__(self, data_path: str = None):
        """
        Initialize the SymptomMatcher with disease and symptom data.
        
        Args:
            data_path: Path to the disease-symptom CSV file. If not provided, will use the default path.
        """
        if data_path is None:
            project_root = Path(__file__).parent.parent
            data_path = project_root / 'data' / 'disease_symptom_database_300.csv'
            data_path = str(data_path)

        self.data_path = data_path
        logger.info(f"Initializing SymptomMatcher with data from: {self.data_path}")
        
        try:
            from src.data_loader import load_disease_symptom_data
            self.disease_data = load_disease_symptom_data(self.data_path)
            logger.info(f"Loaded {len(self.disease_data)} disease entries")
        except Exception as e:
            logger.error(f"Failed to load disease data: {e}", exc_info=True)
            raise
            
        # Load prescription data
        self.prescription_data = self._load_prescription_data()
        logger.info(f"Loaded prescription data for {len(self.prescription_data)} conditions")
        
    def _load_prescription_data(self) -> Dict[str, Any]:
        """
        Load prescription data from the drug reference JSON file.
        
        Returns:
            Dictionary containing prescription information keyed by condition name.
        """
        try:
            project_root = Path(__file__).parent.parent
            drug_ref_path = project_root / 'data' / 'drug_reference.json'
            
            if not drug_ref_path.exists():
                logger.warning(f"Prescription data file not found at: {drug_ref_path}")
                return {}
                
            logger.info(f"Loading prescription data from: {drug_ref_path}")
            with open(drug_ref_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Successfully loaded prescription data for {len(data)} conditions")
                return data
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse prescription data: {e}", exc_info=True)
            return {}
        except Exception as e:
            logger.error(f"Error loading prescription data: {e}", exc_info=True)
            return {}
    
    def _get_prescription_info(self, disease_name):
        """Get prescription information for a specific disease."""
        if not self.prescription_data:
            return None
            
        # Try to find an exact match first
        for condition_name, condition_data in self.prescription_data.items():
            if condition_name.lower() == disease_name.lower():
                return self._format_prescription_info(condition_data)
                
        # Try partial match if no exact match found
        for condition_name, condition_data in self.prescription_data.items():
            if disease_name.lower() in condition_name.lower():
                return self._format_prescription_info(condition_data)
                
        return None
        
    def _format_prescription_info(self, condition_data):
        """Format prescription information from the condition data."""
        recommendations = []
        
        # Add OTC medications if available
        if 'otc_medications' in condition_data and condition_data['otc_medications']:
            for med in condition_data['otc_medications']:
                recommendations.append(f"{med['name']}: {med['dosage']} - {med['purpose']}")
        
        # Add home remedies if available
        if 'home_remedies' in condition_data and condition_data['home_remedies']:
            recommendations.extend(condition_data['home_remedies'])
        
        # Add medical attention note if available
        if 'medical_attention' in condition_data and condition_data['medical_attention']:
            recommendations.append(f"Medical Attention: {condition_data['medical_attention']}")
        
        # Add a note to consult a doctor if symptoms persist
        recommendations.append("If symptoms persist or worsen, please consult a healthcare professional.")
        
        return {
            'recommendations': recommendations
        }

    def _symptom_similarity(self, symptom1: str, symptom2: str) -> float:
        """Calculate similarity between two symptoms using Levenshtein distance."""
        # Simple implementation - can be replaced with more sophisticated string similarity if needed
        if not symptom1 or not symptom2:
            return 0.0
            
        # Exact match
        if symptom1 == symptom2:
            return 1.0
            
        # Check for substring matches
        if symptom1 in symptom2 or symptom2 in symptom1:
            return 0.8
            
        # Check for common words
        words1 = set(symptom1.split())
        words2 = set(symptom2.split())
        common_words = words1.intersection(words2)
        
        if common_words:
            # More weight to matches with more common words
            return min(0.7, 0.3 + 0.1 * len(common_words))
            
        return 0.0
        
    def _find_best_symptom_match(self, user_symptom: str, known_symptoms: set) -> tuple:
        """Find the best matching symptom from known symptoms."""
        best_match = None
        best_score = 0.5  # Minimum threshold
        
        for known_symptom in known_symptoms:
            score = self._symptom_similarity(user_symptom, known_symptom)
            if score > best_score:
                best_score = score
                best_match = known_symptom
                
        return best_match, best_score

    def match_symptoms(self, user_symptoms: List[str], top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Match user symptoms against known diseases and return top matches.
        
        Args:
            user_symptoms: List of symptoms reported by the user
            top_n: Maximum number of top matches to return
            
        Returns:
            List of dictionaries containing disease matches and scores, sorted by match score (highest first).
            Each dictionary contains:
            - disease: Name of the disease
            - match_score: Float between 0 and 1 indicating match strength
            - matching_symptoms: List of symptoms that matched
            - known_symptom_count: Total number of known symptoms for this disease
            - prescription: Dictionary with prescription info if available, empty dict otherwise
        """
        if not user_symptoms or not isinstance(user_symptoms, (list, set)):
            logger.warning("Invalid user_symptoms provided. Expected a non-empty list.")
            return []
            
        # Clean and normalize user symptoms
        try:
            user_symptoms = {s.strip().lower() for s in user_symptoms if s and isinstance(s, str)}
            if not user_symptoms:
                logger.warning("No valid symptoms provided after cleaning.")
                return []
                
            logger.info(f"Matching against symptoms: {user_symptoms}")
            
            results = []
            total_diseases = 0
            diseases_with_matches = 0
            
            # Process each disease in the database
            for _, row in self.disease_data.iterrows():
                try:
                    total_diseases += 1
                    disease = row.get('disease', 'Unknown Disease')
                    known_symptoms = set(row.get('symptoms', []))
                    
                    if not known_symptoms:
                        logger.debug(f"No symptoms found for disease: {disease}")
                        continue
                        
                    # Calculate matching symptoms with similarity scores
                    matching_symptoms = {}
                    
                    # Try to match each user symptom to the best matching known symptom
                    for user_symptom in user_symptoms:
                        best_match, score = self._find_best_symptom_match(user_symptom, known_symptoms)
                        if best_match and score > 0.5:  # Only consider good matches
                            matching_symptoms[best_match] = max(matching_symptoms.get(best_match, 0), score)
                    
                    if matching_symptoms:
                        # Calculate match score with weights
                        match_ratio = sum(matching_symptoms.values()) / len(known_symptoms)
                        symptom_coverage = len(matching_symptoms) / len(user_symptoms)
                        
                        # More weight to diseases where we matched more of the user's symptoms
                        match_score = (match_ratio * 0.6) + (symptom_coverage * 0.4)
                        
                        # Boost score for more specific symptoms (longer symptom descriptions)
                        symptom_specificity = sum(len(s.split()) for s in matching_symptoms) / len(matching_symptoms)
                        match_score = min(1.0, match_score * (1.0 + 0.1 * symptom_specificity))
                        
                        logger.debug(f"Match found for {disease}: {matching_symptoms} (score: {match_score:.2f})")
                        diseases_with_matches += 1
                        
                        # Get prescription info if available
                        prescription = self._get_prescription_info(disease)
                        
                        results.append({
                            'disease': disease,
                            'match_score': round(match_score, 4),
                            'matching_symptoms': sorted(matching_symptoms.keys()),
                            'known_symptom_count': len(known_symptoms),
                            'prescription': prescription or {},
                            'match_quality': round(sum(matching_symptoms.values()) / len(matching_symptoms), 2)
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing disease {disease}: {e}", exc_info=True)
                    continue
            
            # Sort by match score (descending) and get top N
            results.sort(key=lambda x: (-x['match_score'], -x['known_symptom_count']))
            
            logger.info(f"Processed {total_diseases} diseases, found {diseases_with_matches} with matching symptoms")
            logger.info(f"Returning top {min(top_n, len(results))} matches out of {len(results)} total matches")
            
            # Log the top matches for debugging
            for i, result in enumerate(results[:min(3, len(results))], 1):
                logger.info(f"Match #{i}: {result['disease']} (score: {result['match_score']:.2f}), "
                           f"matching symptoms: {result['matching_symptoms']}")
            
            return results[:top_n]
            
        except Exception as e:
            logger.error(f"Error in match_symptoms: {e}", exc_info=True)
            return []
            return []
