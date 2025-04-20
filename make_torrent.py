# make_torrent.py
import hashlib
import json
import os
import sys

def sha256_file(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def generate_torrent(file_path, tracker_ip="127.0.0.1", tracker_port=5000):
    if not os.path.exists(file_path):
        print("File not found.")
        return

    file_info = {
        "filename": os.path.basename(file_path),
        "size": os.path.getsize(file_path),
        "sha256": sha256_file(file_path),
        "tracker": f"{tracker_ip}:{tracker_port}"
    }

    torrent_file = file_path + ".mts"
    with open(torrent_file, 'w') as f:
        json.dump(file_info, f, indent=4)
    print(f"Torrent file generated: {torrent_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_torrent.py <file_path> [tracker_ip] [tracker_port]")
    else:
        generate_torrent(*sys.argv[1:])
