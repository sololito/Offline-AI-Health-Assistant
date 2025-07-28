@echo off
echo Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo Installing PyAudio (this might require Visual C++ Build Tools)...
pip install pipwin
pipwin install pyaudio

echo Installing NLTK data...
python -c "import nltk; nltk.download('punkt')"

echo Installation complete! You can now run the voice assistant with: python run_voice_assistant.py
pause
