# tracker.py
"""
MiniTorrent Tracker

Stores:
- file_hash → metadata (JSON)
- file_hash → list of peers ([{ip,port}])
"""

import socket, threading, json

shared_files = {}   # sha256_hash → [peers]
meta_info    = {}   # sha256_hash → metadata dict

def client_handler(conn, addr):
    try:
        data = conn.recv(8192).decode()
        req  = json.loads(data)
        action = req.get("action")

        if action == "register":
            sha  = req["sha256"]
            peer = {"ip": req["ip"], "port": req["port"]}
            # Store metadata once
            meta = req.get("meta")
            if meta:
                meta_info[sha] = meta

            # Register peer
            shared_files.setdefault(sha, [])
            if peer not in shared_files[sha]:
                shared_files[sha].append(peer)
            conn.send(b"Registered")

        elif action == "get_peers":
            sha  = req["sha256"]
            peer = {"ip": req["ip"], "port": req["port"]}
            peers = [
                p for p in shared_files.get(sha, [])
                if not (p["ip"] == peer["ip"] and p["port"] == peer["port"])
            ]
            conn.send(json.dumps(peers).encode())

        elif action == "list_meta":
            # Return list of all metadata dicts
            conn.send(json.dumps(list(meta_info.values())).encode())

    except Exception as e:
        print("Tracker error:", e)
    finally:
        conn.close()

def start_tracker(host="0.0.0.0", port=5000):
    print(f"Tracker running on {host}:{port}")
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind((host, port))
    srv.listen()
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=client_handler, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_tracker()
