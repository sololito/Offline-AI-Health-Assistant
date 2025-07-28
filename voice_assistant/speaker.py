"""
Voice synthesis module for the Offline AI Health Assistant.
Handles text-to-speech conversion with proper formatting and error handling.
"""

import re
import time
import pyttsx3
import threading
from typing import Optional, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)

class VoiceSpeaker:
    """Handles text-to-speech conversion with proper formatting and error handling."""
    
    def __init__(self, rate: int = 180, volume: float = 1.0, voice_preference: str = 'female'):
        """Initialize the voice engine with improved settings.
        
        Args:
            rate: Speech rate in words per minute (default: 180)
            volume: Volume level from 0.0 to 1.0 (default: 1.0)
            voice_preference: Preferred voice gender ('male' or 'female')
        """
        self.engine = None
        self.rate = rate
        self.volume = volume
        self.voice_preference = voice_preference.lower()
        self._speech_lock = threading.Lock()
        self._stop_speaking = False
        self._event_loop_running = False
        self._initialize_engine()
        
        # Start the event loop in a separate thread
        self._start_event_loop()
        
    def _initialize_engine(self) -> None:
        """Initialize the TTS engine with proper error handling."""
        try:
            self.engine = pyttsx3.init(driverName='sapi5')  # Force SAPI5 on Windows
            if not self.engine:
                raise RuntimeError("Failed to initialize pyttsx3 engine")
                
            self._configure_voice()
            logger.info("Speech engine initialized successfully")
            
            # Set default voice properties
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
        except Exception as e:
            logger.error(f"Failed to initialize speech engine: {e}", exc_info=True)
            self.engine = None
    
    def _configure_voice(self) -> None:
        """Configure voice settings for optimal speech quality."""
        if not self.engine:
            return
            
        try:
            # Get available voices
            voices = self.engine.getProperty('voices')
            if not voices:
                logger.warning("No voices found. Using default voice.")
                return
            
            # Log all available voices for debugging
            logger.info(f"Available voices ({len(voices)}):")
            for i, voice in enumerate(voices):
                logger.info(f"  {i+1}. ID: {voice.id}")
                logger.info(f"     Name: {voice.name}")
                logger.info(f"     Languages: {voice.languages}")
            
            # Try to find preferred voice
            preferred_voices = [
                'zira', 'david',  # Common Windows voices
                'hazel', 'george', 'eva', 'peter',  # Common names
                'english', 'us', 'uk', 'en',  # Language identifiers
                'female' if self.voice_preference == 'female' else 'male'
            ]
            
            # Find the best matching voice
            best_voice = None
            best_score = -1
            
            for voice in voices:
                voice_name = voice.name.lower()
                voice_id = voice.id.lower()
                
                # Skip voices that don't match our preference
                if (self.voice_preference == 'female' and 
                    not any(term in voice_name + ' ' + voice_id for term in ['female', 'woman', 'lady'])):
                    continue
                if (self.voice_preference == 'male' and 
                    not any(term in voice_name + ' ' + voice_id for term in ['male', 'man', 'gentleman'])):
                    continue
                
                # Score based on preferred terms
                score = sum(1 for term in preferred_voices if term in voice_name + ' ' + voice_id)
                
                # Prefer voices with language tags
                if hasattr(voice, 'languages') and voice.languages:
                    score += 2
                
                if score > best_score or (score == best_score and best_voice is None):
                    best_score = score
                    best_voice = voice
            
            if best_voice:
                self.engine.setProperty('voice', best_voice.id)
                logger.info(f"Selected voice: {best_voice.name} (ID: {best_voice.id})")
            else:
                # Fall back to first available voice
                best_voice = voices[0]
                self.engine.setProperty('voice', best_voice.id)
                logger.warning(f"No matching voice found, using first available: {best_voice.name}")
                
        except Exception as e:
            logger.error(f"Error configuring voice: {e}", exc_info=True)
            # Try to continue with default voice if possible
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text to improve speech quality.
        
        Args:
            text: Input text to preprocess
            
        Returns:
            str: Preprocessed text
        """
        if not text:
            return ""
            
        # Convert to string if needed
        text = str(text)
        
        # Common replacements for better speech
        replacements = {
            # Fix common phrases with spaces between letters
            r'\bh\s+e\s+a\s+l\s+t\s+h\s+a\s+s\s+s\s+i\s+s\s+t\s+a\s+n\s+t\b': 'health assistant',
            r'\bh\s*e\s*l\s*l\s*o\b': 'hello',
            r'\bh\s*i\b': 'hi',
            r'\bh\s*e\s*y\b': 'hey',
            r'\bh\s*o\s*w\s*a\s*r\s*e\s*y\s*o\s*u\b': 'how are you',
            r'\bw\s*h\s*a\s*t\s+i\s*s\s+y\s*o\s*u\s*r\s+n\s*a\s*m\s+e\b': 'what is your name',
            
            # Common abbreviations
            r'\bmg\b': 'milligrams',
            r'\bml\b': 'milliliters',
            r'\bmmhg\b': 'millimeters of mercury',
            r'\bbpm\b': 'beats per minute',
            r'\bhr\b': 'heart rate',
            r'\bbp\b': 'blood pressure',
            r'\brr\b': 'respiratory rate',
            r'\btemp\b': 'temperature',
            r'\bo2\b': 'oxygen',
            r'\bspo2\b': 'oxygen saturation',
            
            # Normalize whitespace and punctuation
            r'\s+': ' ',
            r'\s*([.,!?;:])\s*': r'\1 ',
            r'\.{2,}': '.',
            
            # Fix common word separators
            r'(?<=\w)\.(?=\w)': ' ',
            r'(?<=\w)\s+(?=\w)': ' ',
        }
        
        # Apply replacements
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Capitalize first letter and ensure proper spacing after punctuation
        text = text.strip()
        if text:
            text = text[0].upper() + text[1:]
            text = re.sub(r'([.!?]\s*)([a-z])', lambda m: m.group(1) + ' ' + m.group(2).upper(), text)
        
        return text
    
    def _start_event_loop(self) -> None:
        """Start the event loop in a separate thread if not already running."""
        if not self.engine or self._event_loop_running:
            return
            
        def run_loop():
            try:
                self._event_loop_running = True
                self.engine.startLoop(False)
                while self._event_loop_running:
                    self.engine.iterate()
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in TTS event loop: {e}")
            finally:
                self._event_loop_running = False
        
        # Start the event loop in a daemon thread
        threading.Thread(target=run_loop, daemon=True).start()
        time.sleep(0.5)  # Give it time to start
    
    def stop(self) -> None:
        """Stop any ongoing speech and clean up resources."""
        self._stop_speaking = True
        self._event_loop_running = False
        if self.engine:
            try:
                self.engine.stop()
                if hasattr(self.engine, 'endLoop'):
                    self.engine.endLoop()
            except Exception as e:
                logger.error(f"Error stopping TTS engine: {e}")
    
    def speak(self, text: str, wait: bool = False) -> None:
        """Convert text to speech with proper error handling.
        
        Args:
            text: Text to be spoken
            wait: If True, blocks until speech is complete
        """
        logger.info(f"Speak called with text: {text[:100]}{'...' if len(text) > 100 else ''}")
        
        if not text or not text.strip():
            logger.warning("Empty text provided for speech")
            return
            
        if not self.engine:
            logger.warning("No TTS engine available")
            self._initialize_engine()
            if not self.engine:
                logger.error("Failed to initialize TTS engine")
                return
        
        try:
            # Preprocess text
            text = self._preprocess_text(text)
            logger.info(f"Speaking (after preprocessing): {text[:100]}{'...' if len(text) > 100 else ''}")
            
            # Ensure event loop is running
            if not self._event_loop_running:
                logger.info("Starting event loop for TTS")
                self._start_event_loop()
            
            # Use a lock to prevent overlapping speech
            with self._speech_lock:
                self._stop_speaking = False
                
                # Stop any ongoing speech
                logger.debug("Stopping any ongoing speech")
                try:
                    self.engine.stop()
                except Exception as e:
                    logger.warning(f"Error stopping speech: {e}")
                
                # Queue the text to be spoken
                logger.debug(f"Queueing text for speech: {text[:50]}...")
                self.engine.say(text)
                
                if wait:
                    logger.debug("Running blocking speech")
                    try:
                        # Only runAndWait if we're not already in an event loop
                        if not self._event_loop_running:
                            self.engine.runAndWait()
                        else:
                            # If event loop is already running, just let it process the queue
                            self.engine.iterate()
                        logger.debug("Speech completed successfully")
                    except Exception as e:
                        if 'run loop already started' in str(e).lower():
                            logger.debug("Event loop already running, continuing...")
                            self.engine.iterate()
                        else:
                            logger.error(f"Error in speech synthesis: {e}", exc_info=True)
                else:
                    logger.debug("Speech queued, running in background")
                
        except RuntimeError as e:
            error_msg = str(e).lower()
            if 'run loop already started' in error_msg:
                logger.debug("TTS event loop already running (expected)")
            else:
                logger.error(f"Runtime error in speech synthesis: {e}", exc_info=True)
                try:
                    self._initialize_engine()
                except Exception as init_e:
                    logger.error(f"Failed to reinitialize TTS engine: {init_e}")
        except Exception as e:
            logger.error(f"Unexpected error in speech synthesis: {e}", exc_info=True)
            try:
                self._initialize_engine()
            except Exception as init_e:
                logger.error(f"Failed to reinitialize TTS engine: {init_e}")
            
    def _speak_audio_response(self, text: str, wait: bool = False) -> None:
        """Alias for speak method for compatibility."""
        self.speak(text, wait)
    
    def __del__(self):
        """Clean up resources."""
        self.stop()
        self.engine = None
