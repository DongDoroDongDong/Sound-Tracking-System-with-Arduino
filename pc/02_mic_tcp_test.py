import socket
import wave

HOST = '0.0.0.0'
PORT = 5005

# Audio recording settings (16kHz, Mono, 16-bit)
CHANNELS = 1
RATE = 16000

print("[PC] Audio receiving server started. Waiting for Raspberry Pi to transmit...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(1)
    
    conn, addr = server_sock.accept()
    with conn:
        print(f"\n[PC] Raspberry Pi connected! IP: {addr[0]}")
        
        # Receive data in chunks until the connection is closed
        audio_frames = []
        while True:
            packet = conn.recv(4096)
            if not packet:
                break
            audio_frames.append(packet)
            
        raw_audio = b''.join(audio_frames)
        print(f"[PC] Audio reception complete! (Size: {len(raw_audio)} bytes)")
        
        # Save the received data as a WAV file
        wav_filename = "test_record.wav"
        with wave.open(wav_filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(RATE)
            wf.writeframes(raw_audio)
            
        print(f"[PC] Saved successfully as '{wav_filename}'. Play the file to check the audio!")