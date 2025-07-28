import json
import random
import re
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple, Callable

# Import voice assistant components
from voice_assistant.recognizer import VoiceRecognizer
from voice_assistant.speaker import VoiceSpeaker
from voice_assistant.commands import CommandHandler

logger = logging.getLogger(__name__)

class HealthVoiceInterface:
    """
    Interface between the voice assistant and comprehensive health assistant functionality.
    Handles voice commands, processes them using the ComprehensiveHealthAssistant, and provides voice responses.
    """
    
    def __init__(self, health_assistant=None, text_mode: bool = False):
        """
        Initialize the HealthVoiceInterface.
        
        Args:
            health_assistant: Instance of the ComprehensiveHealthAssistant to handle health-related queries
            text_mode: If True, runs in text-only mode without voice
        """
        self.recognizer = VoiceRecognizer()
        self.speaker = VoiceSpeaker() if not text_mode else None
        self.command_handler = CommandHandler(health_assistant=health_assistant)
        self.health_assistant = health_assistant
        self.conversation_context = {}
        self.listening = False
        self.last_interaction_time = time.time()
        self.text_mode = text_mode
        
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
            'emergency': self._handle_emergency
        }
        
    def listen(self, timeout: int = 10) -> str:
        """
        Listen for voice input and return transcribed text.
        
        Args:
            timeout: Maximum time in seconds to listen for input
            
        Returns:
            str: Transcribed text or empty string if no input
        """
        try:
            self.listening = True
            self.last_interaction_time = time.time()
            
            if self.text_mode:
                return input("Type your input: ").strip()
                
            # Use the recognizer to get voice input
            text = self.recognizer.listen(timeout)
            return text.strip() if text else ""
            
        except Exception as e:
            logger.error(f"Error in listen: {str(e)}")
            return ""
        finally:
            self.listening = False
    
    def _format_health_response(self, text: str) -> str:
        """Format the health response for display and speech.
        
        Args:
            text: The text to format
            
        Returns:
            str: Formatted text with improved readability
        """
        if not text:
            return ""
            
        # Clean up the text
        text = text.strip()
        
        # Add proper spacing around punctuation for better readability
        text = re.sub(r'([.,!?])([^\s])', r'\1 \2', text)
        
        # Capitalize the first letter of the response
        if text:
            text = text[0].upper() + text[1:]
            
        # Ensure the response ends with appropriate punctuation
        if text and not text[-1] in '.!?':
            text += '.'
            
            # Ensure proper punctuation
            if not text.endswith(('.', '!', '?', ':')):
                text += '.'
                
        return text
    
    def _speak_response(self, text: str, wait: bool = True) -> None:
        """
        Speak and display the response with proper formatting.
        
        Args:
            text: The text to speak and display
            wait: Whether to wait for speech to complete before returning
        """
        if not text:
            return
            
        try:
            # Format the response for display
            formatted_text = self._format_health_response(text)
            
            # Display the response in the console
            print(f"\n🤖 Assistant: {formatted_text}\n")
            
            # Handle audio response if not in text-only mode
            if not self.text_mode:
                self._speak_audio_response(formatted_text, wait)
                    
        except Exception as e:
            logger.error(f"Error in _speak_response: {e}")
            print(f"Error: {str(e)}")
    
    def _speak_audio_response(self, text: str, wait: bool = True) -> None:
        """
        Convert text to speech and play it.
        
        Args:
            text: The text to convert to speech
            wait: Whether to wait for speech to complete before returning
        """
        if not text or not hasattr(self, 'speaker') or not self.speaker:
            return
            
        try:
            # Clean and prepare text for speech
            speech_text = self._prepare_text_for_speech(text)
            
            # Speak the response
            self.speaker.speak(speech_text, wait=wait)
            
            # Add a small delay after speaking to prevent speech overlap
            if wait:
                time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error in speech synthesis: {e}")
            print("[Speech synthesis error, continuing with text only]")
    
    def _prepare_text_for_speech(self, text: str) -> str:
        """
        Prepare text for speech synthesis by cleaning and formatting it.
        
        Args:
            text: The text to prepare for speech
            
        Returns:
            str: Cleaned and formatted text for speech synthesis
        """
        if not text:
            return ""
            
        # Remove any markdown formatting
        text = re.sub(r'[*_`#]', '', text)
        
        # Replace common patterns for better speech
        replacements = {
            r'\n': '. ',  # Convert newlines to pauses
            r'\s+': ' ',   # Replace multiple spaces with a single space
            r'\[.*?\]\(.*?\)': '',  # Remove markdown links
            r'```.*?```': '',  # Remove code blocks
            r'`([^`]+)`': r'\1',  # Remove inline code formatting
            r'\*\*([^*]+)\*\*': r'\1',  # Remove bold formatting
            r'\*([^*]+)\*': r'\1',  # Remove italic formatting
            r'\[([^\]]+)\]\([^)]+\)': r'\1',  # Replace markdown links with link text
            r'#+\s*': '',  # Remove markdown headers
            r'\[\^[^\]]+\]': ''  # Remove footnotes
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.DOTALL)
            
        # Clean up any remaining special characters
        text = re.sub(r'[\r\t]', ' ', text)  # Replace tabs and carriage returns with spaces
        text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
        
        # Add a period at the end if there's no punctuation
        if text and not text[-1] in '.!?':
            text += '.'
            
        return text
    
    def process_command(self, command: str, return_audio: bool = False) -> dict:
        """Process a command and return the response.
        
        Args:
            command: The user's command
            return_audio: If True, returns a dict with both text and audio response
            
        Returns:
            dict: A dictionary containing 'text' and optionally 'audio' response
        """
        if not command or not command.strip():
            response_text = "I didn't catch that. Could you please repeat?"
            return self._format_response(response_text, return_audio)
            
        command = command.strip()
        logger.info(f"Processing command: {command}")
        
        try:
            # First try the command handler if available
            if hasattr(self, 'command_handler') and self.command_handler:
                response = self.command_handler.handle_command(command)
                if response:
                    return self._format_response(response, return_audio)
            
            # If no specific response, try to process it as a health query
            if self.health_assistant:
                # Check if this is a symptom/diagnosis query
                symptoms = self._extract_symptoms(command)
                if symptoms:
                    try:
                        logger.info(f"Extracted symptoms: {symptoms}")
                        # Get diagnosis for the symptoms
                        diagnosis = self.health_assistant.diagnose(symptoms)
                        response_text = self._format_diagnosis(diagnosis)
                        return self._format_response(response_text, return_audio)
                    except Exception as e:
                        logger.error(f"Error processing health query: {e}", exc_info=True)
                        error_msg = f"I'm sorry, I had trouble processing your health query: {str(e)}"
                        return self._format_response(error_msg, return_audio)
            
            # If we get here, we couldn't process the command
            response_text = (
                "I'm not sure how to help with that. "
                "You can ask me about symptoms, or say 'help' for a list of commands."
            )
            return self._format_response(response_text, return_audio)
            
        except Exception as e:
            logger.error(f"Error processing command: {e}", exc_info=True)
            error_msg = f"I'm sorry, I encountered an error: {str(e)}"
            return self._format_response(error_msg, return_audio)
    
    def _format_response(self, text: str, include_audio: bool = False) -> dict:
        """Format the response with optional audio.
        
        Args:
            text: The text response
            include_audio: If True, includes audio data in the response
            
        Returns:
            dict: A dictionary with text and optionally audio data
        """
        response = {
            'text': text,
            'timestamp': time.time()
        }
        
        # Add audio if requested and not in text-only mode
        if include_audio and not self.text_mode and hasattr(self, 'speaker') and self.speaker:
            try:
                # This is a placeholder - in a real implementation, you would generate
                # and return the actual audio data here
                response['audio'] = {
                    'status': 'success',
                    'format': 'mp3',
                    'length': len(text)  # Placeholder for actual audio length
                }
                
                # Speak the response asynchronously
                self._speak_audio_response(text, wait=False)
                
            except Exception as e:
                logger.error(f"Error generating audio response: {e}")
                response['audio'] = {
                    'status': 'error',
                    'message': str(e)
                }
        
        return response
    
    def _extract_symptoms(self, text: str) -> list:
        """
        Extract symptoms from natural language text.
        This is a simple implementation that can be enhanced with NLP.
        """
        # Convert to lowercase for case-insensitive matching
        text = text.lower()
        
        # Common symptom phrases to look for
        symptom_phrases = [
            "headache", "stomach ache", "sore throat", "fever", "cough",
            "nausea", "dizziness", "fatigue", "pain", "ache", "hurts", "hurting"
        ]
        
        # Find matching symptoms in the text
        symptoms = []
        for phrase in symptom_phrases:
            if phrase in text:
                symptoms.append(phrase)
        
        # If no specific symptoms found, try to extract them from the text
        if not symptoms and "i'm feeling" in text:
            # Extract text after "i'm feeling"
            feeling_part = text.split("i'm feeling", 1)[-1].strip()
            if feeling_part:
                symptoms.append(feeling_part)
        
        return symptoms if symptoms else ["general discomfort"]
    
    def _format_diagnosis(self, diagnosis_results):
        """Format the diagnosis results into a user-friendly message."""
        if not diagnosis_results:
            return "I couldn't find any matching conditions based on your symptoms."
        
        response = "Based on your symptoms, here are some possible conditions:\n\n"
        
        for i, result in enumerate(diagnosis_results[:3], 1):  # Show top 3 results
            response += f"{i}. {result.get('disease', 'Unknown condition')} "
            response += f"(Match: {result.get('match_score', 0):.1%})\n"
            
            # Add matching symptoms if available
            matching_symptoms = result.get('matching_symptoms', [])
            if matching_symptoms:
                response += "   Matching symptoms: " + ", ".join(matching_symptoms) + "\n"
            
            response += "\n"
        
        response += "\nPlease note that this is not a medical diagnosis. "
        response += "Consult a healthcare professional for proper medical advice."
        
        return response
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if hasattr(self, 'speaker') and self.speaker:
                self.speaker.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def start(self, text_mode: bool = False):
        """Start the voice interface in listening mode.
        
        Args:
            text_mode: If True, runs in text-only mode without voice
        """
        self.text_mode = text_mode
        if not text_mode and not self.speaker:
            self.speaker = VoiceSpeaker()
            
        self._speak_response("Health Assistant is now active. How can I help you today?")
        self.listening = True
        
        try:
            while self.listening:
                try:
                    # Get user input
                    if text_mode:
                        command = input("\nYou: ").strip()
                    else:
                        print("\n🎤 Listening... (or type your question)")
                        command = self.recognizer.listen()
                        if command:
                            print(f"\nYou: {command}")
                    
                    # Check for exit command
                    if command and command.lower() in ('exit', 'quit', 'goodbye'):
                        self._speak_response("Goodbye! Have a great day!")
                        self.listening = False
                        break
                        
                    if command:
                        response = self.process_command(command)
                        if response:
                            self._speak_response(response)
                    
                    # Small delay to prevent CPU overuse
                    time.sleep(0.1)
                    
                except KeyboardInterrupt:
                    self._speak_response("Goodbye!")
                    self.listening = False
                    break
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    print(f"\n{error_msg}")
                    logger.error(error_msg, exc_info=True)
                    self._speak_response("I encountered an error. Please try again.")
                    
        finally:
            self.cleanup()
    
    def _handle_hello(self, command: str = "") -> str:
        """Handle hello/greeting commands."""
        return self._handle_greeting()
        
    def _handle_greeting(self, command: str = "") -> str:
        """Handle greeting and general questions."""
        greetings = [
            "Hello! I'm your health assistant. I can help with symptoms, medications, conditions, and general health advice. What can I help you with today?",
            "Hi there! I'm here to assist with your health questions. You can ask me about symptoms, medications, or general health topics.",
            "Greetings! I'm your health assistant. How can I assist you with your health questions today?"
        ]
        return random.choice(greetings)
    
    def _handle_emergency(self, command: str = "") -> str:
        """Handle emergency situations."""
        emergency_response = (
            "This sounds serious. Please call your local emergency number immediately. "
            "If you're in the United States, dial 911. Would you like me to help you find "
            "the nearest medical facility?"
        )
        return emergency_response
    
    def _handle_help(self, command: str = "") -> str:
        """Provide help information about available commands."""
        help_text = """
I'm your comprehensive health assistant. Here's what I can help you with:

HEALTH INFORMATION:
- Symptoms and conditions (e.g., "I have a headache", "What are the symptoms of flu?")
- Medications and side effects (e.g., "side effects of ibuprofen")
- First aid guidance (e.g., "how to treat a burn")
- General health advice (e.g., "how to lower blood pressure")
- Women's health, pediatric, and geriatric health topics
- Nutrition and mental health information

SYSTEM COMMANDS:
- "hello" or "hi" - Greet the assistant
- "help" - Show this help message
- "time" - Get current time
- "date" - Get current date
- "emergency" - Get emergency assistance information
- "exit" or "quit" - Close the application

You can ask me anything health-related in natural language, like:
- "What should I take for a headache?"
- "How do I know if I have the flu?"
- "What are the side effects of metformin?"
- "How to perform CPR"
        """
        return help_text
    
    def _handle_time(self, command: str = "") -> str:
        """Return the current time."""
        current_time = time.strftime("%I:%M %p")
        return f"The current time is {current_time}."
    
    def _handle_date(self, command: str = "") -> str:
        """Return the current date."""
        current_date = time.strftime("%A, %B %d, %Y")
        return f"Today is {current_date}."
    
    def _handle_clear(self, command: str = "") -> str:
        """Clear the console."""
        os.system('cls' if os.name == 'nt' else 'clear')
        return "Console cleared."
    
    def _handle_exit(self, command: str = "") -> str:
        """Handle exit commands."""
        try:
            # Stop any ongoing speech
            self.speaker.stop()
            # Speak the goodbye message
            self.speaker.speak("Goodbye! Take care of your health!", wait=True)
            # Give some time for the speech to complete
            time.sleep(0.5)
        except Exception as e:
            print(f"Error during exit: {e}")
        finally:
            # Ensure the program exits cleanly
            os._exit(0)


def parse_arguments():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description='Health Voice Interface')
    parser.add_argument('--text', action='store_true', help='Run in text-only mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    return parser.parse_args()

def main():
    """Main function to run the health voice interface."""
    args = parse_arguments()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('health_assistant.log')
        ]
    )
    
    logger.info("Starting Health Voice Interface")
    
    try:
        # Initialize the voice interface
        voice_interface = HealthVoiceInterface(text_mode=args.text)
        
        # Start the interface
        voice_interface.start(text_mode=args.text)
        
    except Exception as e:
        error_msg = f"Fatal error: {e}"
        logger.critical(error_msg, exc_info=True)
        print(f"\nA critical error occurred: {e}")
        print("Please check the log file for more details.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
