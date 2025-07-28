#!/usr/bin/env python3
"""
Main entry point for the Offline AI Health Assistant.
Handles both voice and text input/output, and coordinates between different components.
"""

import os
import sys
import logging
import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('health_assistant.log')
    ]
)
logger = logging.getLogger(__name__)

# Set up Python paths
import setup_paths  # This will add the project root and src to sys.path

# Import voice assistant components
try:
    from voice_assistant.recognizer import VoiceRecognizer
    from voice_assistant.speaker import VoiceSpeaker
    from voice_assistant.commands import CommandHandler
    from health_voice_interface import HealthVoiceInterface
    
    # Try to import from src directory
    try:
        from src.assistant import HealthAssistant
        from src.data_loader import load_disease_symptom_data
        logger.info("Successfully imported modules from src directory")
    except ImportError as e:
        logger.error(f"Could not import from src directory: {e}", exc_info=True)
        # Create dummy classes if imports fail
        class HealthAssistant:
            def __init__(self, *args, **kwargs):
                pass
            def process_query(self, query):
                return f"Health assistant is not fully initialized. You asked: {query}"
        
        class DataLoader:
            def __init__(self, *args, **kwargs):
                pass
            
        class KnowledgeBase:
            def __init__(self):
                pass
                
        class NLPProcessor:
            def __init__(self):
                pass
                
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    print(f"Error: {e}. Please make sure all dependencies are installed.")
    sys.exit(1)

class VoiceAssistant:
    """Main voice assistant class that coordinates all components."""
    
    def __init__(self, text_mode: bool = True):
        """Initialize the voice assistant.
        
        Args:
            text_mode: If True, uses text input mode (default: True)
        """
        self.text_mode = text_mode
        self.running = False
        self.health_assistant = self._initialize_health_assistant()
        # Always initialize voice interface for voice output, even in text mode
        self.voice_interface = self._initialize_voice_interface()
        # Load disease symptom database
        self.disease_symptom_db = self._load_disease_symptom_database()
        
    def _initialize_health_assistant(self) -> HealthAssistant:
        """Initialize the health assistant component."""
        try:
            # Initialize with default parameters
            return HealthAssistant()
        except Exception as e:
            logger.error(f"Failed to initialize health assistant: {e}")
            # Return a basic health assistant if initialization fails
            return HealthAssistant()
    
    def _initialize_voice_interface(self):
        """Initialize the voice interface."""
        try:
            from voice_assistant.speaker import VoiceSpeaker
            speaker = VoiceSpeaker()
            logger.info("Voice interface initialized successfully")
            return speaker
        except ImportError as e:
            logger.warning(f"Could not initialize voice interface: {e}")
            return None
            
    def _load_disease_symptom_database(self) -> dict:
        """Load the disease symptom database from CSV file."""
        import csv
        from pathlib import Path
        
        db_path = Path("data/disease_symptom_database_300.csv")
        disease_db = {}
        
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    disease = row.get('Disease', '').strip()
                    symptoms = row.get('Symptoms', '').strip()
                    if disease and symptoms:
                        # Clean up the symptoms and split into a list
                        symptoms_list = [s.strip() for s in symptoms.split(',') if s.strip()]
                        disease_db[disease.lower()] = symptoms_list
            logger.info(f"Loaded {len(disease_db)} diseases from symptom database")
            return disease_db
            
        except Exception as e:
            logger.error(f"Error loading disease symptom database: {e}", exc_info=True)
            return {}
    
    def _lookup_disease_symptoms(self, disease_name: str) -> tuple:
        """Look up symptoms for a specific disease.
        
        Args:
            disease_name: Name of the disease to look up
            
        Returns:
            tuple: (found, response_text, voice_response)
        """
        if not self.disease_symptom_db:
            return False, "I'm sorry, the symptom database is not available.", \
                   "I'm sorry, I can't access the symptom database right now."
        
        # Try to find the best matching disease
        disease_name = disease_name.lower()
        matching_diseases = [d for d in self.disease_symptom_db if disease_name in d]
        
        if not matching_diseases:
            return False, f"I couldn't find information about '{disease_name}' in my database.", \
                   f"I don't have information about {disease_name} in my database."
        
        # Use the first match (most specific)
        matched_disease = matching_diseases[0]
        symptoms = self.disease_symptom_db[matched_disease]
        
        # Format the response
        disease_display = matched_disease.capitalize()
        symptoms_text = ", ".join(symptoms)
        
        text_response = (
            f"{disease_display} is typically associated with the following symptoms:\n"
            f"{symptoms_text}\n\n"
            "Note: This is for informational purposes only. Please consult a healthcare "
            "professional for a proper diagnosis."
        )
        
        voice_response = (
            f"{disease_display} is typically associated with these symptoms: "
            f"{', '.join(symptoms)}. "
            "Remember, this is general information and not a diagnosis. "
            "Please consult a healthcare professional for medical advice."
        )
        
        return True, text_response, voice_response
            
    def _load_disease_symptom_database(self) -> dict:
        """Load the disease symptom database from CSV file."""
        import csv
        from pathlib import Path
        
        db_path = Path("data/disease_symptom_database_300.csv")
        disease_db = {}
        
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    disease = row.get('Disease', '').strip()
                    symptoms = row.get('Symptoms', '').strip()
                    if disease and symptoms:
                        # Clean up the symptoms and split into a list
                        symptoms_list = [s.strip() for s in symptoms.split(',') if s.strip()]
                        disease_db[disease.lower()] = symptoms_list
            logger.info(f"Loaded {len(disease_db)} diseases from symptom database")
            return disease_db
            
        except Exception as e:
            logger.error(f"Error loading disease symptom database: {e}", exc_info=True)
            return {}
    
    def _lookup_disease_symptoms(self, disease_name: str) -> tuple:
        """Look up symptoms for a specific disease.
        
        Args:
            disease_name: Name of the disease to look up
            
        Returns:
            tuple: (found, response_text, voice_response)
        """
        if not self.disease_symptom_db:
            return False, "I'm sorry, the symptom database is not available.", \
                   "I'm sorry, I can't access the symptom database right now."
        
        # Try to find the best matching disease
        disease_name = disease_name.lower()
        matching_diseases = [d for d in self.disease_symptom_db if disease_name in d]
        
        if not matching_diseases:
            return False, f"I couldn't find information about '{disease_name}' in my database.", \
                   f"I don't have information about {disease_name} in my database."
        
        # Use the first match (most specific)
        matched_disease = matching_diseases[0]
        symptoms = self.disease_symptom_db[matched_disease]
        
        # Format the response
        disease_display = matched_disease.capitalize()
        symptoms_text = ", ".join(symptoms)
        
        text_response = (
            f"{disease_display} is typically associated with the following symptoms:\n"
            f"{symptoms_text}\n\n"
            "Note: This is for informational purposes only. Please consult a healthcare "
            "professional for a proper diagnosis."
        )
        
        voice_response = (
            f"{disease_display} is typically associated with these symptoms: "
            f"{', '.join(symptoms)}. "
            "Remember, this is general information and not a diagnosis. "
            "Please consult a healthcare professional for medical advice."
        )
        
        return True, text_response, voice_response
    
    def _extract_symptoms(self, text: str) -> list:
        """Extract symptoms from user's text input."""
        # Simple keyword-based symptom extraction
        symptom_keywords = [
            'pain', 'ache', 'fever', 'headache', 'nausea', 'vomit', 'dizzy', 'dizziness',
            'cough', 'sore throat', 'fatigue', 'tired', 'weak', 'chills', 'sweat',
            'rash', 'itch', 'itchy', 'swell', 'swelling', 'redness', 'bleed', 'bleeding',
            'shortness of breath', 'difficulty breathing', 'chest pain', 'stomach pain',
            'nausea', 'vomiting', 'diarrhea', 'constipation', 'dizziness', 'faint', 'fainting'
        ]
        
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Find matching symptoms
        symptoms = []
        for keyword in symptom_keywords:
            if keyword in text_lower and keyword not in symptoms:
                symptoms.append(keyword)
        
        return symptoms
    
    def _format_symptom_analysis(self, matches):
        """Format the symptom analysis results."""
        if not matches:
            msg = "I couldn't find any conditions that match your symptoms. Please consult a healthcare professional."
            return msg, msg
            
        # Get the top match
        top_match = matches[0]
        disease = top_match.get('disease', 'a condition')
        confidence = top_match.get('confidence', '0%')
        matched_symptoms = ", ".join(top_match.get('matched_symptoms', []))
        
        # Create voice response (shorter, more natural)
        voice_text = f"Based on your symptoms, the most likely condition is {disease} with {confidence} confidence. "
        
        if top_match.get('recommendations'):
            voice_text += "Here's what I recommend: " + ". ".join(top_match['recommendations']) + ". "
        
        voice_text += "Remember, this is not a diagnosis. Please consult a healthcare professional."
        
        # Create full text response (more detailed, for display)
        response = [f"Based on your symptoms, the most likely condition is {disease} (Confidence: {confidence})\n"]
        response.append(f"Matching symptoms: {matched_symptoms}\n")
        
        if top_match.get('recommendations'):
            response.append("Recommendations:")
            for rec in top_match['recommendations']:
                response.append(f"- {rec}")
        
        response.append("\nNote: This is for informational purposes only and not a substitute for professional medical advice.")
        
        return "\n".join(response), voice_text
        
    def process_text_input(self, text: str) -> dict:
        """Process text input and return the assistant's response."""
        try:
            if not text.strip():
                return {'text': "I didn't catch that. Could you please repeat?"}
                
            # Log the user's input
            logger.info(f"User: {text}")
            
            # Convert to lowercase for case-insensitive matching
            text_lower = text.lower()
            
            # Check if this is a disease symptom query
            symptom_query_prefixes = [
                'what are the symptoms of',
                'symptoms of',
                'what symptoms does',
                'what are signs of',
                'signs of',
                'what does',
                'tell me about the symptoms of'
            ]
                
            # Check if the text contains any of the symptom query prefixes
            is_symptom_query = any(prefix in text_lower for prefix in symptom_query_prefixes)
                
            if is_symptom_query:
                # Extract the disease name from the query
                for prefix in symptom_query_prefixes:
                    if prefix in text_lower:
                        disease_name = text_lower.split(prefix, 1)[1].strip()
                        # Remove question marks and other punctuation
                        disease_name = disease_name.rstrip('?').strip()
                        if disease_name:
                            found, response_text, voice_response = self._lookup_disease_symptoms(disease_name)
                            if found:
                                return {'text': response_text, 'voice': voice_response}
                            else:
                                return {'text': response_text}
                    
                # If we couldn't extract a disease name
                return {'text': "I'm sorry, I didn't catch the disease name. Could you please rephrase your question?"}
                
            # Check if the input describes symptoms
            symptoms = self._extract_symptoms(text)
                
            if symptoms:
                # If symptoms are detected, analyze them
                try:
                    from src.assistant import HealthAssistant
                    assistant = HealthAssistant()
                    matches = assistant.diagnose(symptoms, top_n=3)
                    response_text, voice_response = self._format_symptom_analysis(matches)
                except Exception as e:
                    logger.error(f"Error in symptom analysis: {e}", exc_info=True)
                    error_msg = "I encountered an error while analyzing your symptoms. Please try again or consult a healthcare professional."
                    response_text = voice_response = error_msg
            else:
                # If no symptoms detected, provide a general response
                response_text = (
                    "Hello, and welcome to the Offline AI Health Assistant. "
                    "I'm here to support you with health-related information and guidance. "
                    "You can describe how you're feeling or ask a question about your health. "
                    "For example, you could say: "
                    "I'm having breathlessness, chest pain, chills, and a high fever. "
                    "Or: I feel abdominal pain, itching, and nausea. "
                    "Or: What are the symptoms of pneumonia?"
                )
                voice_response = "Hello, and welcome to the Offline AI Health Assistant. I'm here to support you with health-related information and guidance. You can describe how you're feeling or ask a question about your health. For example, you could say,What are the symptoms of pneumonia?"
                
            # Log the assistant's response
            logger.info(f"Assistant: {response_text}")
                
            # Use voice_response for speaking if available, otherwise use response_text
            speech_text = voice_response if 'voice_response' in locals() else response_text
                
            return {
                'text': response_text,
                'speech': speech_text,
                'type': 'symptom_analysis' if symptoms else 'general_response'
            }
                
        except Exception as e:
            error_msg = f"I encountered an error: {str(e)}"
            logger.error(f"Error processing input '{text}': {e}", exc_info=True)
            return {'text': error_msg}
            
    def speak_response(self, text: str, wait: bool = True) -> None:
        """Speak the response using voice output.
            
        Args:
            text: The text to speak
            wait: Whether to wait for speech to complete before returning
        """
        if not text:
            return
                
        try:
            # Ensure we have a voice interface
            if not hasattr(self, 'voice_interface') or self.voice_interface is None:
                self.voice_interface = self._initialize_voice_interface()
                if self.voice_interface is None:
                    logger.warning("No voice interface available for speech output")
                    return
                        
            # Clean up the text for better speech output
            text = self._clean_text_for_speech(text)
                
            # Log the text that will be spoken
            logger.info(f"Speaking: {text[:100]}..." if len(text) > 100 else f"Speaking: {text}")
                
            # Try different methods to speak the text
            if hasattr(self.voice_interface, '_speak_audio_response'):
                self.voice_interface._speak_audio_response(text, wait=wait)
            elif hasattr(self.voice_interface, 'speak'):
                self.voice_interface.speak(text, wait=wait)
            elif hasattr(self.voice_interface, 'say'):
                self.voice_interface.say(text, wait=wait)
            else:
                logger.warning("Voice interface has no recognized speak method")
                    
        except Exception as e:
            logger.error(f"Error in speech synthesis: {e}", exc_info=True)
            # Continue without voice if there's an error
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean up text for better speech output."""
        if not text:
            return ""
                
        # Remove any markdown formatting
        text = str(text).replace('*', '').replace('_', '').replace('`', '')
            
        # Replace common abbreviations
        replacements = {
            '\n': ' ',  # Replace newlines with spaces
            '  ': ' ',    # Replace double spaces with single space
            'Dr.': 'Doctor',
            'Mr.': 'Mister',
            'Mrs.': 'Missus',
            'Ms.': 'Miss',
            ' vs ': ' versus ',
            ' e.g.': ' for example',
            ' i.e.': ' that is',
        }
            
        for old, new in replacements.items():
            text = text.replace(old, new)
                
        return text.strip()
        
    def _show_help(self) -> None:
        """Display help information about using the assistant and read it aloud."""
        # Text to display in the console
        help_text = """
            
🤖 Offline AI Health Assistant - Help
==================================

This assistant can help you with:

1. Symptom Analysis:
   - Describe your symptoms to get information about possible conditions
   - Example: "I have breathlessness, chest pain, chills, cough, fast heart rate, fatigue and high fever"
   - Example: "I have abdominal pain, itching, loss of appetite and nausea"
   - Example: "I have cough with mucus, fatigue, mild fever, chest discomfort and shortness of breath"
   - Example: "I have abdominal pain, belly pain, chills, constipation, diarrhoea, fatigue and high fever"

2. General Health Information:
   - Ask about common health conditions
   - Example: "What are the symptoms of pneumonia?"
   - Example: "How to manage high blood pressure?"

3. Commands:
   - help: Show this help message
   - exit or quit: Exit the application

Note: This assistant provides general health information only and is not a substitute for professional medical advice.
        """
        
        # Voice version of the help text (more natural for speech)
        voice_help = """
        I can help you with several health-related tasks. 
        
        First, I can help analyze your symptoms. You can describe how you're feeling, 
        and I'll provide information about possible conditions. 
        For example, you could say: "I have a cough with mucus, fatigue, mild fever, and shortness of breath."
        
        Second, I can provide general health information. You can ask me about symptoms of conditions, 
        treatment options, or general health advice. For example: "What are the warning signs of a heart attack?"
        
        You can say 'help' at any time to hear this message again, 
        or 'exit' to close the application.
        
        Remember, I provide general information only and am not a substitute for professional medical advice.
        """
        
        # Speak the voice help text first
        self.speak_response(voice_help, wait=True)
        
        # Then display the formatted help text
        print(help_text)
        
        # Add a small delay to ensure the speech starts
        time.sleep(0.5)

    def run_interactive(self):
        """Run the assistant in interactive mode with text input and voice output."""
        self.running = True
        
        # Display welcome message
        welcome_message = """
        =========================================================
          🤖 AI Health Assistant - Interactive Mode
        =========================================================
        I'm here to help you monitor your health, answer your questions, 
        and guide you with useful tips.
        
        Type 'help' for a list of commands
        Type 'exit' or 'quit' to end the session
        =========================================================
        """
        print(welcome_message)
        
        # Initial voice greeting
        greeting = (
            "Hello! I am your AI Health Assistant. "
            "I'm here to help you monitor your health, answer your questions, "
            "and guide you with useful tips. How can I assist you today?"
        )
        self.speak_response(greeting, wait=True)
        
        # Show example inputs
        print("\nYou can describe your symptoms or ask health-related questions like:")
        print("  • I have breathlessness, chest pain, chills, cough, fast heart rate, fatigue and high fever")
        print("  • I have abdominal pain, itching, loss of appetite and nausea")
        print("  • I have cough with mucus, fatigue, mild fever, chest discomfort and shortness of breath")
        print("  • I have abdominal pain, belly pain, chills, constipation, diarrhoea, fatigue and high fever\n")
        
        last_command_time = time.time()
        min_command_interval = 1.0  # Minimum seconds between commands
        
        try:
            while self.running:
                try:
                    current_time = time.time()
                    time_since_last = current_time - last_command_time
                    
                    # Rate limiting to prevent rapid command processing
                    if time_since_last < min_command_interval:
                        time.sleep(min_command_interval - time_since_last)
                    
                    # Get user input
                    try:
                        user_input = input("\nYou: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        # Handle Ctrl+D (EOF) or Ctrl+C gracefully
                        print("\n")
                        user_input = "exit"
                    
                    # Skip empty input
                    if not user_input:
                        continue
                        
                    last_command_time = time.time()
                    
                    # Process special commands
                    if user_input.lower() in ['exit', 'quit']:
                        self.speak_response("Goodbye! Take care of your health!")
                        break
                    elif user_input.lower() in ['help', '?']:
                        self._show_help()
                        continue
                    
                    # Process the input and get response
                    response = self.process_text_input(user_input)
                    
                    # Display and speak the response
                    if response:
                        # Display the full text response
                        if 'text' in response:
                            print(f"\n🤖 Assistant: {response['text']}")
                        
                        # Speak the response (use speech text if available, otherwise use text)
                        speech_text = response.get('speech', response.get('text', ''))
                        if speech_text:
                            self.speak_response(speech_text, wait=True)
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {e}", exc_info=True)
                    error_msg = "I'm sorry, I encountered an error. Please try again."
                    print(f"\n{error_msg}")
                    self.speak_response(error_msg)
                    
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.running = False
        # Clean up any resources if needed

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Offline AI Health Assistant')
    parser.add_argument('--text', action='store_true', help='Run in text-only mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--voice', action='store_true', help='Run in voice mode (used by web interface)')
    return parser.parse_args()

def run_interactive(self):
    """Run the assistant in interactive mode with text input and voice output."""
    self.running = True
    
    # Display welcome message
    welcome_message = """
    =========================================================
      Offline AI Health Assistant - Interactive Mode
      Type 'exit' or 'quit' to end the session
      Type 'help' for a list of commands
    =========================================================
    """
    print(welcome_message)
    
    # Initial voice greeting
    self.speak_response("Welcome to the Offline AI Health Assistant. I'm here to help with your health questions.")
    print("\nYou can describe your symptoms or ask health-related questions.")
    print("For example:")
    print("- I have a headache and fever")
    print("- What are the symptoms of the flu?")
    print("- I'm feeling nauseous and dizzy\n")
    
    last_command_time = time.time()
    min_command_interval = 1.0  # Minimum seconds between commands
    
    try:
        while self.running:
            try:
                current_time = time.time()
                time_since_last = current_time - last_command_time
                
                # Rate limiting to prevent rapid command processing
                if time_since_last < min_command_interval:
                    time.sleep(min_command_interval - time_since_last)
                
                # Get user input
                try:
                    user_input = input("\nYou: ").strip()
                except (EOFError, KeyboardInterrupt):
                    # Handle Ctrl+D (EOF) or Ctrl+C gracefully
                    print("\n")
                    user_input = "exit"
                
                # Skip empty input
                if not user_input:
                    continue
                    
                last_command_time = time.time()
                
                # Process special commands
                if user_input.lower() in ['exit', 'quit']:
                    self.speak_response("Goodbye! Take care of your health!")
                    break
                elif user_input.lower() in ['help', '?']:
                    self._show_help()
                    continue
                
                # Process the input and get response
                response = self.process_text_input(user_input)
                
                # Display the response
                if response and 'text' in response:
                    response_text = response['text']
                    print(f"\n🤖 Assistant: {response_text}")
                    
                    # Speak the response
                    self.speak_response(response_text, wait=True)
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                error_msg = "I'm sorry, I encountered an error. Please try again."
                print(f"\n{error_msg}")
                self.speak_response(error_msg)
    
    finally:
        self.cleanup()
    
    def _show_help(self) -> None:
        """Display help information about using the assistant and read it aloud."""
        # Text to display in the console
        help_text = """
        
🤖 Offline AI Health Assistant - Help
==================================

This assistant can help you with:

1. Symptom Analysis:
   - Describe your symptoms to get information about possible conditions
   - Example: "I have breathlessness, chest pain, chills, cough, fast heart rate, fatigue and high fever"
   - Example: "I have abdominal pain, itching, loss of appetite and nausea"
   - Example: "I have cough with mucus, fatigue, mild fever, chest discomfort and shortness of breath"
   - Example: "I have abdominal pain, belly pain, chills, constipation, diarrhoea, fatigue and high fever"

2. General Health Information:
   - Ask about common health conditions
   - Example: "What are the symptoms of pneumonia?"
   - Example: "How to manage high blood pressure?"

3. Commands:
   - help: Show this help message
   - exit or quit: Exit the application

Note: This assistant provides general health information only and is not a substitute for professional medical advice.
        """
        
        # Voice version of the help text (more natural for speech)
        voice_help = """
        I can help you with several health-related tasks. 
        
        First, I can help analyze your symptoms. You can describe how you're feeling, 
        and I'll provide information about possible conditions. 
        For example, you could say: "I have a cough with mucus, fatigue, mild fever, and shortness of breath."
        
        Second, I can provide general health information. You can ask me about symptoms of conditions, 
        treatment options, or general health advice. For example: "What are the warning signs of a heart attack?"
        
        You can say 'help' at any time to hear this message again, 
        or 'exit' to close the application.
        
        Remember, I provide general information only and am not a substitute for professional medical advice.
        """
        
        # Speak the voice help text first
        self.speak_response(voice_help, wait=True)
        
        # Then display the formatted help text
        print(help_text)
        
        # Add a small delay to ensure the speech starts
        time.sleep(0.5)

def cleanup(self) -> None:
    """Clean up resources."""
    self.running = False
    # Clean up any resources if needed

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Offline AI Health Assistant')
    parser.add_argument('--text', action='store_true', help='Run in text-only mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--voice', action='store_true', help='Run in voice mode (used by web interface)')
    return parser.parse_args()

def main():
    """Main function to run the voice assistant."""
    args = parse_arguments()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Configure logging to not interfere with web interface when run as subprocess
    if args.voice:
        # Redirect stdout and stderr to log file only in voice mode
        log_file = open('voice_assistant.log', 'a')
        sys.stdout = log_file
        sys.stderr = log_file
        
        # Keep the process alive until explicitly terminated
        import signal
        def handle_signal(signum, frame):
            logger.info("Received signal %s, shutting down...", signum)
            log_file.close()
            sys.exit(0)
            
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)
    
    try:
        # Initialize and run the voice assistant
        assistant = VoiceAssistant(text_mode=args.text)
        
        if args.voice:
            # In voice mode, just run the voice interface without interactive input
            logger.info("Starting voice assistant in voice mode")
            print("Voice assistant is running in background mode...")
            
            # Keep the process alive
            while True:
                time.sleep(1)
        else:
            # In normal mode, run interactive shell
            assistant.run_interactive()
            
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        if not args.voice:  # Only print to console if not in voice mode
            print(f"\nA critical error occurred: {e}")
            print("Please check the log file for more details.")
        return 1
    finally:
        if args.voice:
            log_file.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
