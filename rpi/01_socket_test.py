import socket

# Destination PC IP address and port.
PC_IP = '192.168.10.44'
PORT = 5005

print("[Raspberry Pi] Connecting to PC server over Wi-Fi...")

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Request a connection to the PC.
        s.connect((PC_IP, PORT))
        print("[Raspberry Pi] Connected to PC server.")
        
        # Text message to send, encoded as bytes.
        msg = "Hello PC! I am Raspberry Pi 3B."
        s.sendall(msg.encode('utf-8'))
        print("[Raspberry Pi] Test text sent.")
        
except Exception as e:
    print(f"[Raspberry Pi] Connection failed: {e}")
    print("Check the Windows firewall and make sure both devices are on the same Wi-Fi network.")
