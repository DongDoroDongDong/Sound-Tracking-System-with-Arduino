import socket

# Destination Raspberry Pi IP and port
RPI_IP = '192.168.10.59'
PORT = 5006

print("=========================================")
print("[PC Control Tower] Turret Remote Control Program")
print(f"Connection Target (Raspberry Pi): {RPI_IP}:{PORT}")
print("=========================================")

while True:
    angle = input("\nEnter rotation angle (e.g., 45, -90 / quit: q): ")
    
    if angle.lower() == 'q':
        print("Exiting the remote control program.")
        break
        
    try:
        # Validate if the input is an integer
        int(angle)
        
        # Briefly connect to the Raspberry Pi server, send data, and close
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((RPI_IP, PORT))
            sock.sendall(angle.encode('utf-8'))
            
        print(f"Successfully transmitted '{angle} degrees' command to Raspberry Pi!")
        
    except ValueError:
        print("Error: Only integer numbers are allowed. (e.g., 90, -30)")
    except Exception as e:
        print(f"Transmission failed: {e}")
        print("Make sure the Python code on the Raspberry Pi is running.")