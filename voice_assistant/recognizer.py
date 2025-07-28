# recognizer.py
import queue
import time
import logging
import sounddevice as sd
import numpy as np
import json
from vosk import Model, KaldiRecognizer

# Configure logging
logger = logging.getLogger(__name__)

class VoiceRecognizer:
    def __init__(self, model_path="voice_assistant/models/vosk-model-en-us-0.42-gigaspeech", 
                 samplerate=44100, min_confidence=0.3, min_speech_length=0.3):
        """Initialize the VoiceRecognizer with improved settings.
        
        Args:
            model_path: Path to the Vosk model
            samplerate: Audio sample rate in Hz (default: 44100 for better quality)
            min_confidence: Minimum confidence threshold (0.0 to 1.0)
            min_speech_length: Minimum speech length in seconds
        """
        self.q = queue.Queue()
        self.model = Model(model_path)
        self.samplerate = 44100  # Force 44.1kHz for better compatibility
        self.min_confidence = min_confidence
        self.min_speech_length = min_speech_length
        
        # Configure audio device
        try:
            # Try to find the best available input device
            devices = sd.query_devices()
            input_devices = [i for i, dev in enumerate(devices) 
                           if dev['max_input_channels'] > 0]
            
            if not input_devices:
                raise ValueError("No input devices found!")
                
            # Try to find a Realtek device first
            realtek_devices = [i for i in input_devices 
                             if 'realtek' in devices[i]['name'].lower()]
            
            if realtek_devices:
                sd.default.device = realtek_devices[0]
            else:
                sd.default.device = input_devices[0]  # Use first available
                
            print(f"\n🔊 Selected audio device: {devices[sd.default.device]['name']}")
            print(f"   - Sample rate: {self.samplerate} Hz")
            print(f"   - Channels: {devices[sd.default.device]['max_input_channels']}")
            
        except Exception as e:
            print(f"\n⚠️  Error configuring audio device: {e}")
            print("Falling back to default audio device")
        
        # Initialize recognizer with the selected sample rate
        self.recognizer = KaldiRecognizer(self.model, self.samplerate)
        self.recognizer.SetWords(True)  # Enable word-level timestamps
        
        # Audio processing settings - adjusted for very quiet microphones
        self.silence_threshold = 0.0001  # Drastically lowered threshold for quiet microphones
        self.silence_duration = 2.0      # Increased to allow for natural pauses
        
        # Debug flag
        self.debug = True  # Set to True to enable debug prints
        
        # Set the default input device explicitly
        try:
            # Try to find the Realtek microphone array
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if 'microphone' in dev['name'].lower() and 'realtek' in dev['name'].lower():
                    sd.default.device = i
                    print(f"\n✅ Selected audio input: {dev['name']} (Device {i})")
                    break
            else:
                # Fall back to default input device if Realtek not found
                print("\n⚠️  Realtek microphone not found, using default input device")
                print("Available input devices:")
                for i, dev in enumerate(devices):
                    if dev['max_input_channels'] > 0:
                        print(f"  {i}: {dev['name']} (Inputs: {dev['max_input_channels']})")
        except Exception as e:
            print(f"\n⚠️  Error setting audio device: {e}")
            print("Falling back to default audio device")
        
        # Common commands mapping with possible variations
        self.command_mapping = {
            'help': ['help', 'hell', 'hellp', 'hep', 'halp'],
            'exit': ['exit', 'quit', 'excel', 'excite'],
            'hello': ['hello', 'hi', 'hey', 'hi there', 'hello there'],
            'time': ['time', 'what time is it', 'current time'],
            'date': ['date', 'what is today', 'what day is it']
        }
        
    def _is_silent(self, audio_data):
        """Check if audio data is below the silence threshold."""
        if not audio_data.any():
            if self.debug:
                print("  [DEBUG] No audio data received")
            return True
            
        rms = np.sqrt(np.mean(np.square(audio_data)))
        
        if self.debug:
            print(f"  [DEBUG] Audio RMS level: {rms:.8f} (threshold: {self.silence_threshold:.8f})")
            
        return rms < self.silence_threshold
    
    def _get_confidence(self, result):
        """Extract confidence score from recognition result."""
        if 'result' not in result or not result['result']:
            return 0.0
        # Calculate average confidence of all words in the result
        confidences = [word.get('conf', 0) for word in result['result']]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def _callback(self, indata, frames, time, status):
        """Callback for audio input stream."""
        if status:
            logger.debug(f"SoundDevice Status: {status}")
        self.q.put(bytes(indata))

    def listen(self, timeout=10):
        """Listen for speech input with improved noise handling.
        
        Args:
            timeout: Maximum time to listen in seconds
            
        Returns:
            str: Recognized text or empty string if no valid speech detected
        """
        print("\n🔊 Voice Recognition Active")
        print("   - Speak clearly into the microphone")
        print(f"   - Silence threshold: {self.silence_threshold:.6f}")
        print("   - Try saying: 'hello', 'help', or 'exit'\n")
        
        logger.info("Listening... (Speak within %d seconds)", timeout)
        start_time = time.time()
        last_audio_time = start_time
        audio_buffer = []
        
        # Get current input device info
        try:
            current_device = sd.query_devices(sd.default.device[0])
            print(f"Using audio input: {current_device['name']}")
            print(f"  - Sample rate: {current_device['default_samplerate']} Hz")
            print(f"  - Channels: {current_device['max_input_channels']}")
            print(f"  - Silence threshold: {self.silence_threshold:.6f}")
        except Exception as e:
            print(f"⚠️  Could not get audio device info: {e}")
            
        print("\nListening... Speak now!\n")
        
        try:
            with sd.RawInputStream(
                samplerate=self.samplerate,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=self._callback
            ):
                while (time.time() - start_time) < timeout:
                    try:
                        # Process audio data
                        data = self.q.get_nowait()
                        if not data:
                            continue
                            
                        # Convert to numpy array for silence detection
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        audio_buffer.append(audio_data)
                        
                        # Process with Vosk
                        if self.recognizer.AcceptWaveform(data):
                            result = json.loads(self.recognizer.Result())
                            text = result.get('text', '').strip()
                            confidence = self._get_confidence(result)
                            
                            if text and confidence >= self.min_confidence:
                                word_count = len(text.split())
                                text_lower = text.lower()
                                
                                if self.debug:
                                    print(f"\n[DEBUG] Recognized: '{text}'")
                                    print(f"[DEBUG] Confidence: {confidence:.2f}")
                                    print(f"[DEBUG] Word count: {word_count}")
                                
                                # Check for command variations
                                for command, variations in self.command_mapping.items():
                                    if any(variation in text_lower for variation in variations):
                                        logger.info("Recognized command '%s' from '%s' (confidence: %.2f)",
                                                  command, text, confidence)
                                        return command
                                
                                # If no command matched but we have text, return it
                                return text_lower
                            
                        # Check for silence
                        if self._is_silent(audio_data):
                            if (time.time() - last_audio_time) > self.silence_duration:
                                # Process any remaining audio
                                if audio_buffer:
                                    result = json.loads(self.recognizer.FinalResult())
                                    text = result.get('text', '').strip()
                                    if text:
                                        confidence = self._get_confidence(result)
                                        word_count = len(text.split())
                                        common_commands = ['help', 'exit', 'quit', 'hello', 'hi', 'time', 'date']
                                        is_common_command = any(cmd in text.lower() for cmd in common_commands)
                                        
                                        if confidence >= self.min_confidence and (is_common_command or word_count >= 1):
                                            logger.info("Final recognized: %s (confidence: %.2f, words: %d)", 
                                                      text, confidence, word_count)
                                            return text
                                break
                        else:
                            last_audio_time = time.time()
                            
                    except queue.Empty:
                        # No audio data available yet
                        time.sleep(0.1)
                        continue
                    except Exception as e:
                        logger.error("Error processing audio: %s", str(e))
                        break
                
                # Process any remaining audio
                if audio_buffer:
                    result = json.loads(self.recognizer.FinalResult())
                    text = result.get('text', '').strip()
                    if text:
                        confidence = self._get_confidence(result)
                        if confidence >= self.min_confidence:
                            logger.info("Final recognized: %s", text)
                            return text
                            
        except Exception as e:
            logger.error("Error in listen: %s", str(e), exc_info=True)
            
        logger.debug("No valid speech detected")
        return ""
