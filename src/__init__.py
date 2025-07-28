"""
Health Assistant - Core Package

This package contains the core functionality for the Health Assistant application,
including symptom matching, data loading, and assistant logic.
"""

# Import key components to make them available at the package level
from .assistant import HealthAssistant
from .data_loader import load_disease_symptom_data
from .symptom_matcher import SymptomMatcher

__all__ = [
    'HealthAssistant',
    'load_disease_symptom_data',
    'SymptomMatcher'
]