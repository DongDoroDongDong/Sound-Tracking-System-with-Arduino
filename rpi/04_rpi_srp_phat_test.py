import pyaudio
import numpy as np
import pyroomacoustics as pra
import time

# ==========================================
# 1. Settings (SRP-PHAT and sliding window).
# ==========================================
FS = 16000
NFFT = 256
BUFFER_SEC = 4  # Total audio length for AI input (4 seconds).
SHIFT_SEC = 1   # Length refreshed each pass (1 second).

# Four-microphone array coordinates.
R = np.array([
    [ 0.045, -0.045, -0.045,  0.045], 
    [ 0.045,  0.045, -0.045, -0.045]  
])

# Calculate buffer sizes (1 second = 16,000 frames).
buffer_size = FS * BUFFER_SEC
shift_size = FS * SHIFT_SEC

# Create an empty 4-second mono buffer for AI input.
ai_audio_buffer = np.zeros(buffer_size, dtype=np.float32)

# Direction-of-arrival detector.
doa = pra.doa.srp.SRP(L=R, fs=FS, nfft=NFFT, c=343.0, num_deg=360)

# ==========================================
# 2. Open audio stream (4 channels, read 1 second at a time).
# ==========================================
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=4,          # Always use 4 channels for SRP-PHAT.
    rate=FS,
    input=True,
    frames_per_buffer=shift_size # Read exactly 1 second at a time.
)

print("\n[System] Hybrid inference loop started (angle detection + 4-second AI buffer)")
print("Filling the initial 4-second buffer. Please wait...\n")

try:
    # Initial warm-up (fill the first 4 seconds).
    for _ in range(BUFFER_SEC):
        raw_data = stream.read(shift_size, exception_on_overflow=False)
        audio_data = np.frombuffer(raw_data, dtype=np.int16).reshape(-1, 4).T
        audio_float = audio_data.astype(np.float32) / 32768.0
        
        # Copy microphone 0 audio into the 4-second buffer.
        ai_audio_buffer = np.roll(ai_audio_buffer, -shift_size)
        ai_audio_buffer[-shift_size:] = audio_float[0]

    print("Buffer ready. Starting real-time inference.\n")

    # ==========================================
    # 3. Real-time integration loop (runs once per second).
    # ==========================================
    while True:
        start_time = time.time()

        # 1. Read exactly 1 second of 4-channel audio from the microphone array.
        raw_data = stream.read(shift_size, exception_on_overflow=False)
        audio_data = np.frombuffer(raw_data, dtype=np.int16).reshape(-1, 4).T
        audio_float = audio_data.astype(np.float32) / 32768.0

        # 2. [Track 1] SRP-PHAT angle detection.
        # Use all 4 channels to estimate direction.
        X = pra.transform.stft.analysis(audio_float.T, NFFT, NFFT // 2)
        X = X.transpose([2, 1, 0]) 
        doa.locate_sources(X)
        angle = doa.azimuth_recon[0] * 180 / np.pi
        if angle > 180: angle -= 360.0

        # 3. [Track 2] Update sliding window for AI input.
        # Refresh the 4-second buffer with microphone 0 from the 4 channels.
        ai_audio_buffer = np.roll(ai_audio_buffer, -shift_size)
        ai_audio_buffer[-shift_size:] = audio_float[0]

        elapsed = (time.time() - start_time) * 1000 
        volume = np.max(np.abs(audio_float))

        # 4. Print results only when sound is detected.
        if volume > 0.05:
            print(f"Sound direction: {angle:>6.1f} deg | Latest 4-second AI buffer ready | Latency: {elapsed:.2f} ms")
            
            # --------------------------------------------------
            # Add wireless socket communication here if needed.
            # sock.sendall(f"{angle:>8.1f}".encode('utf-8')) # Send angle.
            # sock.sendall(ai_audio_buffer.tobytes())        # Send 4 seconds of audio.
            # --------------------------------------------------

except KeyboardInterrupt:
    print("\n[System] Shutting down.")
    stream.stop_stream()
    stream.close()
    p.terminate()
