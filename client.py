import socket, json, threading, os, sys, time

# Default ports / dirs
DEFAULT_SERVE_PORT = 6000
TRACKER_HOST = "127.0.0.1"
TRACKER_PORT = 5000
SHARED_DIR = "shared"
DOWNLOAD_DIR = "downloaded"

# ─── Utility: fetch metadata list from tracker ────────────────────────────────
def fetch_all_metadata():
    msg = {"action": "list_meta"}
    with socket.socket() as s:
        s.connect((TRACKER_HOST, TRACKER_PORT))
        s.send(json.dumps(msg).encode())
        data = s.recv(8192).decode()
    return json.loads(data)  # list of metadata dicts

# ─── 1) Load .mts metadata ─────────────────────────────────────────────────────
def load_metadata(mts_path):
    with open(mts_path, 'r') as f:
        return json.load(f)

# ─── 2) Tracker Communication ─────────────────────────────────────────────────
def register_with_tracker(meta, self_ip, self_port):
    msg = {
        "action": "register",
        "sha256": meta["sha256"],
        "ip":     self_ip,
        "port":   self_port,
        "meta":   meta        # send full metadata for others
    }
    with socket.socket() as s:
        s.connect((TRACKER_HOST, TRACKER_PORT))
        s.send(json.dumps(msg).encode())
        print(f"[Tracker] {s.recv(1024).decode()}")

def get_peers_from_tracker(meta, self_ip, self_port):
    msg = {
        "action": "get_peers",
        "sha256": meta["sha256"],
        "ip":     self_ip,
        "port":   self_port
    }
    with socket.socket() as s:
        s.connect((TRACKER_HOST, TRACKER_PORT))
        s.send(json.dumps(msg).encode())
        peers = json.loads(s.recv(4096).decode())
    print(f"[Tracker] Peers for {meta['filename']}: {peers}")
    return peers

# ─── 3) File Serving (Seeder) ──────────────────────────────────────────────────
def serve_file_server(filename, port):
    filepath = os.path.join(SHARED_DIR, filename)

    def handler():
        sock = socket.socket()
        sock.bind(('127.0.0.1', port))
        sock.listen()
        print(f"[Seeder] Serving '{filename}' on port {port}...")

        while True:
            conn, addr = sock.accept()
            request = conn.recv(1024).decode().strip()
            print(f"[Seeder] {addr} requested '{request}'")
            # Serve either the data file or the .mts
            if request == filename or request == filename + ".mts":
                path = filepath if request == filename else filepath + ".mts"
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        while chunk := f.read(8192):
                            conn.sendall(chunk)
                    print(f"[Seeder] Sent '{request}' to {addr}")
                else:
                    print(f"[Seeder] File not found: {path}")
            else:
                print(f"[Seeder] Invalid request: '{request}'")
            conn.close()

    threading.Thread(target=handler, daemon=True).start()

# ─── 4) File Downloading (Leecher) ─────────────────────────────────────────────
def download_from_peer(peer, name, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, name)

    try:
        sock = socket.socket()
        sock.connect((peer["ip"], peer["port"]))
        sock.send(name.encode())
        with open(dest, 'wb') as f:
            while chunk := sock.recv(8192):
                if not chunk: break
                f.write(chunk)
        sock.close()
        print(f"[Leecher] Downloaded '{name}' → {dest}")
        return True
    except Exception as e:
        print(f"[Leecher] Error downloading '{name}' from {peer}: {e}")
        return False

# ─── 5) Main Logic ─────────────────────────────────────────────────────────────
def client_main(arg, self_ip, self_port):
    # 1) If arg is not an existing .mts, fetch metadata from tracker
    if arg.endswith(".mts") and os.path.exists(arg):
        mts_path = arg
    else:
        # assume arg is base filename
        fname = arg
        # fetch all metadata, find for filename
        metas = fetch_all_metadata()
        meta = next((m for m in metas if m["filename"] == fname), None)
        if not meta:
            print(f"[Error] No metadata for '{fname}' on tracker.")
            return
        mts_path = os.path.join(SHARED_DIR, fname + ".mts")
        # save it
        with open(mts_path, 'w') as f:
            json.dump(meta, f, indent=2)
        print(f"[Auto] Saved metadata → {mts_path}")

    # 2) Load metadata
    meta = load_metadata(mts_path)
    filename = meta["filename"]

    # 3) Start seeder thread (serves both .pdf and .mts)
    serve_file_server(filename, port=self_port)

    # 4) Register with tracker
    register_with_tracker(meta, self_ip, self_port)

    # 5) Discover peers & download data file
    peers = get_peers_from_tracker(meta, self_ip, self_port)
    for peer in peers:
        if peer["ip"] == self_ip and peer["port"] == self_port:
            continue
        print(f"[Leecher] Attempting download from {peer['ip']}:{peer['port']}...")
        if download_from_peer(peer, filename, DOWNLOAD_DIR):
            break
    else:
        print("[Leecher] No peers found serving data file.")

    # Keep the seeder thread alive
    while True:
        time.sleep(1)

# ─── 6) Entry Point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python client.py <filename|.mts> <your_ip> <your_port>")
        sys.exit(1)

    arg     = sys.argv[1]
    ip_addr = sys.argv[2]
    port    = int(sys.argv[3])
    client_main(arg, ip_addr, port)
