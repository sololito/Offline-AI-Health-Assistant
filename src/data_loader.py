# /src/data_loader.py

import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

def load_disease_symptom_data(csv_path):
    """
    Loads disease-symptom data from a CSV file and parses symptoms into lists.
    
    Args:
        csv_path (str): Path to the CSV file containing disease and symptoms data
        
    Returns:
        pd.DataFrame: DataFrame with 'disease' and 'symptoms' columns
    """
    logger.info(f"Loading disease-symptom data from: {csv_path}")
    
    if not os.path.exists(csv_path):
        error_msg = f"CSV file not found at: {csv_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        # Read the CSV file with explicit encoding and handle potential parsing issues
        df = pd.read_csv(csv_path, encoding='utf-8', on_bad_lines='warn')
        
        # Clean up column names
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        # Check for required columns
        if 'disease' not in df.columns or 'symptoms' not in df.columns:
            # Try to find the columns with different cases or extra spaces
            disease_cols = [col for col in df.columns if 'disease' in col.lower()]
            symptom_cols = [col for col in df.columns if 'symptom' in col.lower()]
            
            if len(disease_cols) > 0 and len(symptom_cols) > 0:
                df = df.rename(columns={
                    disease_cols[0]: 'disease',
                    symptom_cols[0]: 'symptoms'
                })
            else:
                error_msg = "CSV must contain 'Disease' and 'Symptoms' columns."
                logger.error(f"{error_msg} Found columns: {list(df.columns)}")
                raise ValueError(error_msg)
        
        # Clean and process symptoms with better normalization
        def clean_symptom_list(symptoms_str):
            if not isinstance(symptoms_str, str):
                return []
            
            # Split by comma and clean each symptom
            symptoms = []
            for symptom in symptoms_str.split(','):
                symptom = symptom.strip().lower()
                # Remove any extra spaces and special characters
                symptom = ' '.join(symptom.split())
                if symptom and len(symptom) > 2:  # Only include non-trivial symptoms
                    symptoms.append(symptom)
            return symptoms
        
        # Apply cleaning to symptoms
        df['symptoms'] = df['symptoms'].apply(clean_symptom_list)
        
        # Remove any rows with missing or empty data
        df = df.dropna(subset=['disease', 'symptoms'])
        df = df[df['symptoms'].apply(len) > 0]
        
        # Add a cleaned disease name column
        df['disease_clean'] = df['disease'].str.lower().str.strip()
        
        # Log some stats
        total_symptoms = sum(len(symptoms) for symptoms in df['symptoms'])
        logger.info(f"Loaded {len(df)} diseases with {total_symptoms} total symptom occurrences")
        
        logger.info(f"Successfully loaded {len(df)} disease-symptom entries")
        return df
        
    except Exception as e:
        logger.error(f"Error loading disease-symptom data: {str(e)}", exc_info=True)
        raise
