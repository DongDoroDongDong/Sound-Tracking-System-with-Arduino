import pyaudio
import socket

# PC (laptop) IP address.
PC_IP = '192.168.10.44'
PORT = 5005

# Audio recording settings.
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 3  # Record for a 3-second test.

p = pyaudio.PyAudio()

print("[Raspberry Pi] Microphone initialized.")
print(f"Starting a {RECORD_SECONDS}-second recording. Speak into the microphone.")

# 1. Start recording from the microphone.
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

frames = []
for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    frames.append(stream.read(CHUNK, exception_on_overflow=False))

stream.stop_stream()
stream.close()
p.terminate()

print("Recording complete. Sending to PC...")

# Combine captured frames into one bytes object.
audio_data = b''.join(frames)

# 2. Send to PC over TCP.
try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((PC_IP, PORT))
        sock.sendall(audio_data)
    print("Audio sent to PC.")
except Exception as e:
    print(f"Transfer failed: {e}")
    print("Make sure the receiver script is running on the PC.")
