# script_lang.py
import time
import subprocess

def run_script(path):
    with open(path) as f:
        for line in f:
            cmd = line.strip()
            if cmd.startswith("CONNECT TRACKER"):
                print("Tracker connected.")
            elif cmd.startswith("SHARE"):
                filename = cmd.split()[1]
                subprocess.run(["python", "client.py", filename, "127.0.0.1"])
            elif cmd.startswith("DOWNLOAD"):
                filename = cmd.split()[1]
                subprocess.run(["python", "client.py", filename, "127.0.0.1"])
            elif cmd.startswith("WAIT"):
                time.sleep(int(cmd.split()[1]))
            elif cmd.startswith("LOG"):
                print(" ".join(cmd.split()[1:]))
            elif cmd.startswith("EXIT"):
                print("Script finished.")
                break
"# Minor refactor" 
"# Added input validation" 
