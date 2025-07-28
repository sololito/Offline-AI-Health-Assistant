# commands.py
import os
import re
import time
import logging
from typing import Optional
from voice_assistant.speaker import VoiceSpeaker

# Configure logging
logger = logging.getLogger(__name__)

class CommandHandler:
    def __init__(self, health_assistant=None):
        """
        Initialize the CommandHandler with optional health assistant integration.
        
        Args:
            health_assistant: Optional health assistant instance for health-related commands
        """
        self.speaker = VoiceSpeaker()
        self.health_assistant = health_assistant
        self.last_command_time = time.time()
        
        # System commands that don't require health assistant
        self.system_commands = {
            'exit': self._handle_exit,
            'quit': self._handle_exit,
            'hello': self._handle_hello,
            'hi': self._handle_hello,
            'help': self._handle_help,
            'time': self._handle_time,
            'date': self._handle_date,
            'clear': self._handle_clear,
            'open calculator': self._open_calculator,
            'open notepad': self._open_notepad
        }
    
    def handle_command(self, command: str) -> Optional[str]:
        """
        Process and execute the given command.
        
        Args:
            command: The command string to process
            
        Returns:
            Optional response string or None if no response needed
        """
        if not command or not command.strip():
            return None
            
        command = command.lower().strip()
        self.last_command_time = time.time()
        print(f"📝 Command received: {command}")
        
        # Check for exact matches in system commands first
        if command in self.system_commands:
            return self.system_commands[command]()
            
        # Check for partial matches for multi-word commands (like 'open calculator')
        for cmd, handler in self.system_commands.items():
            if ' ' in cmd and cmd in command:
                return handler()
        
        # If no system command matched, check if we have a health assistant
        if self.health_assistant:
            # Check for health-related terms in the command
            health_terms = ['symptom', 'pain', 'ache', 'feel', 'hurt', 'hurting', 'not feeling well']
            if any(term in command for term in health_terms):
                return self._handle_health_command(command)
        
        # If no command matched, provide a helpful response
        return "I'm not sure how to help with that. You can say 'help' for a list of available commands."
    
    def _handle_hello(self) -> str:
        """Handle greeting commands."""
        greetings = [
            "Hello! How can I assist you today?",
            "Hi there! What can I help you with?",
            "Greetings! How can I be of service?"
        ]
        # Convert the time-based index to an integer
        index = int(time.time()) % len(greetings)
        greeting = greetings[index]
        self.speaker.speak(greeting)
        return greeting
    
    def _handle_help(self) -> str:
        """Provide help information."""
        help_text = """
        I can help you with various tasks. Here are some examples:
        
        General Commands:
        - Hello / Hi - Greet the assistant
        - What time is it? - Get current time
        - What's today's date? - Get current date
        - Open calculator - Launch calculator
        - Open notepad - Open text editor
        - Exit / Quit - Close the application
        
        Health Commands:
        - I have a headache
        - My stomach hurts
        - I'm not feeling well
        - I need help with my symptoms
        """
        return help_text
    
    def _handle_time(self) -> str:
        """Return the current time."""
        current_time = time.strftime("%I:%M %p")
        return f"The current time is {current_time}"
    
    def _handle_date(self) -> str:
        """Return the current date."""
        current_date = time.strftime("%A, %B %d, %Y")
        return f"Today is {current_date}"
    
    def _handle_clear(self) -> str:
        """Clear the console."""
        os.system('cls' if os.name == 'nt' else 'clear')
        return "Console cleared."
    
    def _open_calculator(self) -> str:
        """Open the system calculator."""
        try:
            os.system("start calc" if os.name == 'nt' else "gnome-calculator")
            return "Opening calculator."
        except Exception as e:
            return f"Failed to open calculator: {str(e)}"
    
    def _open_notepad(self) -> str:
        """Open the system text editor."""
        try:
            os.system("notepad" if os.name == 'nt' else "gedit")
            return "Opening text editor."
        except Exception as e:
            return f"Failed to open text editor: {str(e)}"
    
    def _extract_symptoms(self, command: str) -> list:
        """
        Extract symptoms from the user's command with improved pattern matching.
        
        Handles various natural language patterns like:
        - "I have a headache"
        - "My stomach hurts"
        - "I'm feeling nauseous"
        - "Experiencing back pain"
        """
        command = command.lower().strip()
        logger.debug(f"Extracting symptoms from: {command}")
        symptoms = []
        
        # Expanded symptom phrases and their variations
        symptom_map = {
            'headache': [
                'headache', 'head pain', 'head hurts', 'head ache', 'hurting head',
                'pain in head', 'aching head', 'throbbing head', 'pounding head'
            ],
            'stomachache': [
                'stomachache', 'stomach pain', 'stomach hurts', 'stomach ache',
                'tummy ache', 'belly ache', 'abdominal pain', 'upset stomach',
                'stomach cramps', 'stomach discomfort'
            ],
            'fever': [
                'fever', 'high temperature', 'running a temperature',
                'elevated temperature', 'have a temperature'
            ],
            'nausea': [
                'nausea', 'feeling sick', 'feel sick', 'queasy', 'nauseous',
                'sick to my stomach', 'feeling queasy'
            ],
            'dizziness': [
                'dizziness', 'dizzy', 'lightheaded', 'feeling faint',
                'room spinning', 'off balance', 'unsteady'
            ],
            'fatigue': [
                'fatigue', 'tiredness', 'feeling tired', 'exhaustion',
                'low energy', 'lethargy', 'run down', 'worn out'
            ],
            'cough': [
                'cough', 'coughing', 'hacking cough', 'dry cough',
                'persistent cough', 'chesty cough', 'tickly throat',
                'coughing fits'
            ],
            'sore throat': [
                'sore throat', 'throat pain', 'throat hurts', 'scratchy throat',
                'irritated throat', 'painful throat', 'hoarse voice'
            ],
            'back pain': [
                'back pain', 'backache', 'back hurts', 'hurting back',
                'sore back', 'lower back pain', 'upper back pain',
                'stiff back'
            ],
            'chest pain': [
                'chest pain', 'chest hurts', 'pain in chest', 'chest discomfort',
                'tightness in chest', 'pressure in chest', 'chest tightness'
            ]
        }
        
        # Common patterns for symptom reporting
        patterns = [
            r'(?:i\s+(?:have|am\s+having|feel|am\s+feeling|experience|am\s+experiencing|got|have\s+got))\s+(?:a\s+)?([\w\s]+?)(?:\s+in\s+my\s+[\w\s]+?|\.|$)',
            r'(?:my\s+[\w\s]+?\s+)(hurts|aches|is\s+sore|is\s+painful|is\s+aching|is\s+throbbing|is\s+burning|is\s+tingling)',
            r'(?:i\'m\s+)(?:feeling\s+)?([\w\s]+?)(?:\s+in\s+my\s+[\w\s]+?|\.|$)',
            r'(?:i\s+have\s+a\s+)([\w\s]+?)(?:\s+in\s+my\s+[\w\s]+?|\.|$)'
        ]
        
        # Try to extract symptom phrases using patterns first
        extracted_phrases = []
        for pattern in patterns:
            matches = re.finditer(pattern, command)
            for match in matches:
                phrase = match.group(1).strip() if match.groups() else ''
                if phrase and len(phrase.split()) <= 3:  # Limit to 3-word phrases
                    extracted_phrases.append(phrase)
        
        logger.debug(f"Extracted phrases: {extracted_phrases}")
        
        # Check extracted phrases against symptom map
        for phrase in extracted_phrases:
            for symptom, variations in symptom_map.items():
                if any(variation in phrase or phrase in variation for variation in variations):
                    symptoms.append(symptom)
        
        # If no matches from patterns, try direct matching
        if not symptoms:
            for symptom, variations in symptom_map.items():
                if any(variation in command for variation in variations):
                    symptoms.append(symptom)
        
        # If still no matches, try word-level matching with fuzzy matching
        if not symptoms:
            words = re.findall(r'\b\w+\b', command)
            for symptom, variations in symptom_map.items():
                for variation in variations:
                    variation_words = variation.split()
                    if any(word in words for word in variation_words):
                        symptoms.append(symptom)
                        break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_symptoms = [s for s in symptoms if not (s in seen or seen.add(s))]
        
        logger.debug(f"Final extracted symptoms: {unique_symptoms}")
        return unique_symptoms
    
    def _handle_health_command(self, command: str) -> str:
        """Handle health-related commands using the health assistant."""
        if not self.health_assistant:
            return "I'm sorry, the health assistant is not available right now."
            
        try:
            # Extract symptoms from the command
            symptoms = self._extract_symptoms(command)
            
            if not symptoms:
                return "I'm not sure what symptoms you're experiencing. Could you please describe them?"
            
            # Get diagnosis from the health assistant
            diagnosis = self.health_assistant.diagnose(symptoms)
            
            if not diagnosis:
                return "I couldn't find any matching conditions for those symptoms. Please consult a healthcare professional for an accurate diagnosis."
            
            # Format the response
            response = "Based on your symptoms, here are some possible conditions:\n\n"
            
            for i, condition in enumerate(diagnosis[:3], 1):  # Show top 3 matches
                response += f"{i}. {condition['disease']} (Confidence: {condition['confidence']})\n"
                if condition.get('recommendations'):
                    response += f"   Recommendations: {', '.join(condition['recommendations'])}\n"
                response += "\n"
            
            response += "Please note that this is not a medical diagnosis. Always consult with a healthcare professional for medical advice."
            
            return response
            
        except Exception as e:
            import traceback
            traceback.print_exc()  # Print full traceback for debugging
            return f"I'm sorry, I encountered an error processing your request: {str(e)}"
    
    def _handle_exit(self) -> str:
        """Handle exit commands."""
        self.speaker.speak("Goodbye!")
        exit(0)
