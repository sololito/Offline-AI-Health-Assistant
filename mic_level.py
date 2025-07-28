import sounddevice as sd
import numpy as np
import time
import sys

def print_devices():
    print("\n=== Input Devices ===")
    devices = sd.query_devices()
    input_devices = []
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            input_devices.append((i, dev))
            print(f"{i}: {dev['name']}")
            print(f"   - Input channels: {dev['max_input_channels']}")
            print(f"   - Default sample rate: {dev['default_samplerate']} Hz")
    print("===================\n")
    return input_devices

def test_microphone(device_id, duration=5):
    print(f"\nTesting microphone: {sd.query_devices(device_id)['name']}")
    print("Speak into the microphone...")
    print("Press Ctrl+C to stop early\n")
    
    try:
        # Record a small chunk of audio
        def callback(indata, frames, time, status):
            if status:
                print(f"Audio status: {status}")
            
            # Calculate volume
            volume = np.abs(indata).mean()
            
            # Simple VU meter (0-100 scale)
            level = min(int(volume * 1000), 100)
            bar = "█" * (level // 2)
            print(f"\rLevel: {volume:.6f} |{bar:<50}| {level}%", end="", flush=True)
        
        with sd.InputStream(device=device_id, samplerate=44100, channels=1,
                          callback=callback, blocksize=1024):
            print("Listening...")
            sd.sleep(int(duration * 1000))
            
    except Exception as e:
        print(f"\nError: {e}")
        return False
    
    print("\n\n✅ Test complete!")
    return True

if __name__ == "__main__":
    print("=== Microphone Level Test ===\n")
    
    # List available devices
    input_devices = print_devices()
    
    if not input_devices:
        print("No input devices found!")
        sys.exit(1)
    
    # Try to find a Realtek device
    realtek_devices = [i for i, dev in input_devices 
                      if 'realtek' in dev['name'].lower()]
    
    if realtek_devices:
        device_id = realtek_devices[0]
        print(f"\n🔊 Using Realtek device: {sd.query_devices(device_id)['name']}")
    else:
        device_id = input_devices[0][0]
        print(f"\nℹ️  Using default input device: {sd.query_devices(device_id)['name']}")
    
    # Run the test
    try:
        test_microphone(device_id)
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
