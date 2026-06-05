import pyaudio

p = pyaudio.PyAudio()

print("=========================================")
print("Connected microphone devices and channel counts")
print("=========================================\n")

for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    channels = dev['maxInputChannels']
    
    # Print only microphone/input devices.
    if channels > 0:
        print(f"Device [ {i} ]: {dev['name']}")
        print(f"  Max input channels: {channels}\n")

p.terminate()
