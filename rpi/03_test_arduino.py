import serial
import serial.tools.list_ports
import socket
import time

# ==========================================
# 1. Auto-connect to Arduino.
# ==========================================
def find_arduino():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'Arduino' in port.description or 'ACM' in port.device or 'USB' in port.device:
            return port.device
    return None

arduino_port = find_arduino()
if arduino_port:
    arduino = serial.Serial(arduino_port, 9600, timeout=1)
    print(f"[Raspberry Pi] Arduino connected ({arduino_port})")
    time.sleep(2) # Wait for the Arduino board to stabilize.
else:
    print("[Warning] Arduino not found. Check the USB cable.")
    exit()

# ==========================================
# 2. Socket server setup (wait for commands).
# ==========================================
HOST = '0.0.0.0'
PORT = 5006 # Dedicated command port.

print(f"[Raspberry Pi] Port {PORT} open. Waiting for fire commands from PC...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(1)

    try:
        while True:
            # Wait until the PC connects.
            conn, addr = server_sock.accept()
            with conn:
                # Read text (angle) sent by the PC.
                data = conn.recv(1024).decode('utf-8').strip()
                if data:
                    print(f"[Command received] Target angle '{data} deg' -> sending to Arduino.")
                    # Append a newline so the Arduino can parse the command.
                    arduino.write(f"{data}\n".encode('utf-8'))
    except KeyboardInterrupt:
        print("\n[Raspberry Pi] Test stopped.")

if 'arduino' in globals() and arduino.is_open:
    arduino.close()
