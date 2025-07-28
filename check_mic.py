import sounddevice as sd
import numpy as np
import time

def print_devices():
    print("\n=== Available Audio Input Devices ===")
    devices = sd.query_devices()
    input_devices = []
    
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            input_devices.append(i)
            print(f"{i}: {dev['name']}")
            print(f"   - Input channels: {dev['max_input_channels']}")
            print(f"   - Default sample rate: {dev['default_samplerate']} Hz")
    
    if not input_devices:
        print("No input devices found!")
        return None
    
    return input_devices

def test_microphone(device_id=None, duration=5, sample_rate=44100):
    print("\n🎤 Testing microphone...")
    print(f"   - Duration: {duration} seconds")
    print(f"   - Sample rate: {sample_rate} Hz")
    print("   - Speak into the microphone to see the audio levels")
    print("   - Press Ctrl+C to stop early\n")
    
    try:
        def callback(indata, frames, time, status):
            if status:
                print(f"Audio status: {status}")
            
            # Calculate RMS volume
            rms = np.sqrt(np.mean(np.square(indata)))
            
            # Simple VU meter (0-50 scale)
            level = min(int(rms * 100), 50)
            print("\r[" + "|" * level + " " * (50 - level) + "]", end="", flush=True)
        
        with sd.InputStream(device=device_id, channels=1, samplerate=sample_rate,
                          callback=callback, blocksize=1024):
            print("Listening...")
            sd.sleep(int(duration * 1000))
            
    except Exception as e:
        print(f"\nError: {e}")
        return False
    
    print("\n\n✅ Test complete!")
    return True

if __name__ == "__main__":
    print("=== Microphone Test ===\n")
    
    # List available devices
    input_devices = print_devices()
    
    if not input_devices:
        print("No input devices found. Exiting...")
        sys.exit(1)
    
    # Try to find a Realtek device
    devices = sd.query_devices()
    realtek_devices = [i for i in input_devices 
                      if 'realtek' in devices[i]['name'].lower()]
    
    if realtek_devices:
        device_id = realtek_devices[0]
        print(f"\n🔊 Using Realtek device: {devices[device_id]['name']}")
    else:
        device_id = input_devices[0]
        print(f"\nℹ️  Using default input device: {devices[device_id]['name']}")
    
    # Run the test
    try:
        test_microphone(device_id=device_id)
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
