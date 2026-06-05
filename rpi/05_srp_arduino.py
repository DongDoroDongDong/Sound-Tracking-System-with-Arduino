import usb.core
import usb.util
import serial
import serial.tools.list_ports
import time
import struct

# ==========================================
# 1. Connect to Arduino (turret motor).
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
# 2. Direct USB connection to ReSpeaker v2.0 (XMOS XVF-3000).
# ==========================================
dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
if dev is None:
    print("ReSpeaker not found. Check the USB connection.")
    exit()
print("XMOS hardware control link connected.")

print("\n=========================================")
print("[Hardware-accelerated turret] Started.")
print("Audio processing is delegated to the hardware.")
print("=========================================\n")

last_shoot_time = 0
COOLDOWN_SEC = 1.5   # Cooldown time to protect the motor.

try:
    while True:
        try:
            # 1. Read VAD (voice activity detection) state.
            # Request code (wValue): 0xE0, parameter ID (wIndex): 19, length: 8 bytes.
            vad_raw = dev.ctrl_transfer(0xC0, 0, 0xE0, 19, 8)
            
            # Interpret the C struct (8 bytes) as two Python integers (<ii), then read the first value.
            vad = struct.unpack('<ii', vad_raw.tobytes())[0]
            
            # Aim only when voice is detected (vad == 1) and the cooldown has passed.
            if vad == 1 and (time.time() - last_shoot_time > COOLDOWN_SEC):
                
                # 2. Read DOA (sound direction angle).
                # Request code (wValue): 0xC0, parameter ID (wIndex): 21, length: 8 bytes.
                doa_raw = dev.ctrl_transfer(0xC0, 0, 0xC0, 21, 8)
                angle = struct.unpack('<ii', doa_raw.tobytes())[0]
                
                # Convert 0-359 degrees to -180-180 degrees for Arduino motor control if needed.
                if angle > 180:
                    angle -= 360.0
                    
                print(f"Hardware VAD target detected. Direction: {angle:>6.1f} deg | Aiming motor now.")
                
                # 3. Send angle to Arduino.
                if arduino and arduino.is_open:
                    arduino.write(f"{angle:.1f}\n".encode('utf-8'))
                    
                last_shoot_time = time.time()
                
        except usb.core.USBError as e:
            # Ignore brief communication dropouts.
            print(f"USB communication delay: {e}")
            
        time.sleep(0.05) # Prevent a hot infinite loop (wait 0.05 seconds).

except KeyboardInterrupt:
    print("\n[System] Turret stopped.")
    if arduino and arduino.is_open:
        arduino.close()
