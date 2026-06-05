import numpy as np
import pyaudio
import pyroomacoustics as pra
import serial
import serial.tools.list_ports
import time

# ==========================================
# 1. Auto-connect to Arduino (motor).
# ==========================================
def find_arduino():
    for port in serial.tools.list_ports.comports():
        if 'Arduino' in port.description or 'ACM' in port.device or 'USB' in port.device:
            return port.device
    return None

arduino_port = find_arduino()
if arduino_port:
    arduino = serial.Serial(arduino_port, 9600, timeout=1)
    print(f"[System] Arduino connected: {arduino_port}")
    time.sleep(2)
else:
    print("[Warning] Arduino not found.")
    exit()

# ==========================================
# 2. Set up absolute microphone array coordinates (clockwise physical mapping).
# ==========================================
# Calculate the 45-degree diagonal component for a circular array with a 35 mm (0.035 m) radius (about 0.0247 m).
val = 0.035 * np.sqrt(2) / 2  

# Actual hardware channel order: [Ch1(top-right), Ch2(bottom-right), Ch3(bottom-left), Ch4(top-left)].
R = np.array([
    # Ch1(top-right)  Ch2(bottom-right)  Ch3(bottom-left)  Ch4(top-left)
    [   val,     -val,    -val,     val ], # X coordinates (robot front +, rear -)
    [   val,      val,    -val,    -val ]  # Y coordinates (robot right +, left -)
])

FS = 16000      
CHUNK = 1024    
NFFT = 256      
CHANNELS = 6    

# Direction-of-arrival detector (SRP-PHAT).
doa = pra.doa.srp.SRP(L=R, fs=FS, nfft=NFFT, c=343.0, num_deg=360)

# ==========================================
# 3. Open audio stream.
# ==========================================
p = pyaudio.PyAudio()
try:
    stream = p.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=FS,
        input=True,
        frames_per_buffer=CHUNK
    )
    print("6-channel audio stream opened.")
except Exception as e:
    print(f"Failed to open audio stream: {e}")
    exit()

print("\n=========================================")
print("[Final build] SRP-PHAT turret with CNC polarity inversion compensation started.")
print("Front: 0 deg | Right: positive direction | Left: negative direction")
print("=========================================\n")

last_shoot_time = 0  
COOLDOWN_SEC = 1.5   

try:
    while True:
        raw_data = stream.read(CHUNK, exception_on_overflow=False)
        
        # 1. Cooldown (motor protection).
        if time.time() - last_shoot_time < COOLDOWN_SEC:
            continue
            
        # 2. Split and normalize raw 6-channel data.
        audio_data = np.frombuffer(raw_data, dtype=np.int16).reshape(-1, CHANNELS).T
        audio_float = audio_data.astype(np.float32) / 32768.0
        
        # 3. Extract microphone channels only (Ch1-Ch4).
        pure_mics = audio_float[1:5] 
        
        # 4. Noise filtering threshold.
        volume = np.max(np.abs(pure_mics))
        if volume > 0.01:
            start_time = time.time()

            # 5. Transform the raw signal to the frequency domain and align dimensions [channel, frequency, time].
            X = pra.transform.stft.analysis(pure_mics.T, NFFT, NFFT // 2)
            X = X.transpose([2, 1, 0]) 
            
            # 6. Run mathematical inference.
            doa.locate_sources(X)
            
            # 7. Send only when a reliable direction signal exists (empty-value guard).
            if len(doa.azimuth_recon) > 0:
                
                angle = doa.azimuth_recon[0] * 180 / np.pi
                
                # Flatten across the circular boundary to the -180 to +180 range.
                while angle > 180.0:
                    angle -= 360.0
                while angle <= -180.0:
                    angle += 360.0
                    
                # Clip to the hardware stepper motor limit (-179.5 to 179.5).
                angle = np.clip(angle, -179.5, 179.5)
                
                # CNC motor polarity inversion (reverse direction): force a software inversion.
                angle = -angle
                    
                elapsed = (time.time() - start_time) * 1000
                print(f"Real-time aiming angle: {angle:>6.1f} deg (inference: {elapsed:.1f} ms) | Command sent.")
                
                try:
                    arduino.write(f"{angle:.1f}\n".encode('utf-8'))
                except Exception as e:
                    print("Serial communication error:", e)
                    
                last_shoot_time = time.time()
                
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n[System] Process stopped safely.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    if arduino and arduino.is_open:
        arduino.close()
