"""
Voice Assistant Package

This package contains the core components for the voice assistant functionality,
including speech recognition, text-to-speech, and command handling.
"""

# Import key components to make them available at the package level
from .recognizer import VoiceRecognizer
from .speaker import VoiceSpeaker
from .commands import CommandHandler

__all__ = ['VoiceRecognizer', 'VoiceSpeaker', 'CommandHandler']
