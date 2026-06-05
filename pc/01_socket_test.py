import socket

# Accept connections from any network interface.
HOST = '0.0.0.0'
PORT = 5005

print("[PC] Starting the communication test server...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Bind the socket to the host and port
    s.bind((HOST, PORT))
    # Enter listening state
    s.listen(1)
    print(f"[PC] Listening on port {PORT} and waiting for the Raspberry Pi...")
    
    # The code pauses here until the Raspberry Pi connects.
    conn, addr = s.accept()
    
    with conn:
        print(f"[PC] Connection successful! Connected Raspberry Pi IP: {addr[0]}")
        
        # Read up to 1024 bytes of data.
        data = conn.recv(1024)
        print(f"[PC] Message received from Raspberry Pi: {data.decode('utf-8')}")

print("[PC] Test completed successfully. Closing the socket securely.")