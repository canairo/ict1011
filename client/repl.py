#!/usr/bin/env python3
import json
import socket
import sys

SERVER_IP = "127.0.0.1"
SERVER_PORT = 9999
CLIENT_PORT = 9998   # ephemeral client port (change if needed)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", CLIENT_PORT))
sock.settimeout(1.0)   # non-blocking receive

print(f"[REPL] UDP JSON client")
print(f"[REPL] Server: {SERVER_IP}:{SERVER_PORT}")
print(f"[REPL] Type JSON and press enter. Ctrl+C to quit.\n")

while True:
    try:
        line = input("> ").strip()
        if not line:
            continue

        # Validate JSON
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"[ERR] Invalid JSON: {e}")
            continue

        # Send packet
        sock.sendto(line.encode("utf-8"), (SERVER_IP, SERVER_PORT))
        print("[SENT]")

        # Try to receive response(s)
        responses = 0
        while True:
            try:
                data, addr = sock.recvfrom(2048)
                print(f"[RECV from {addr[0]}:{addr[1]}] {data.decode('utf-8')}")
                responses += 1
            except socket.timeout:
                break
        
        if responses == 0:
            print("[NO RESPONSE]")

    except KeyboardInterrupt:
        print("\n[EXIT]")
        sys.exit()

