# gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, threading, os, json, hashlib

# ─── Style Constants ───────────────────────────────────────────────────────────
BG = "#282C34"
FG = "#ABB2BF"
ACC = "#61AFEF"
BTN = "#98C379"
FONT = ("Segoe UI", 10)
FONT_B = ("Segoe UI", 11, "bold")

TRACKER_DEFAULT_IP   = "127.0.0.1"
TRACKER_DEFAULT_PORT = "5000"

# ─── Helpers ────────────────────────────────────────────────────────────────────
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ─── Main GUI ───────────────────────────────────────────────────────────────────
class MiniTorrentGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MiniTorrent")
        self.configure(bg=BG)
        self.geometry("600x350")
        self._build()

    def _build(self):
        # Title
        tk.Label(self, text="MiniTorrent", font=("Segoe UI", 18, "bold"),
                 bg=BG, fg=ACC).pack(pady=8)

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        # ─ Left: File → .mts ───────────────────
        left = tk.LabelFrame(frame, text="1) Create .mts", font=FONT_B,
                             bg=BG, fg=ACC, padx=10, pady=10)
        left.pack(side="left", fill="both", expand=True, padx=5)

        self.src_var = tk.StringVar()
        tk.Entry(left, textvariable=self.src_var, width=30, font=FONT).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(left, text="Browse File", bg=BTN, fg=BG, font=FONT,
                  command=self._browse_file).grid(row=0, column=1, padx=5)
        tk.Label(left, text="Tracker IP:", bg=BG, fg=FG, font=FONT).grid(row=1, column=0, sticky="w", pady=3)
        self.tr_ip = tk.StringVar(value=TRACKER_DEFAULT_IP)
        tk.Entry(left, textvariable=self.tr_ip, width=15, font=FONT).grid(row=1, column=1, pady=3)
        tk.Label(left, text="Tracker Port:", bg=BG, fg=FG, font=FONT).grid(row=2, column=0, sticky="w", pady=3)
        self.tr_pt = tk.StringVar(value=TRACKER_DEFAULT_PORT)
        tk.Entry(left, textvariable=self.tr_pt, width=15, font=FONT).grid(row=2, column=1, pady=3)
        tk.Button(left, text="Create .mts", bg=BTN, fg=BG, font=FONT_B,
                  command=self._create_mts).grid(row=3, column=0, columnspan=2, pady=8)

        # ─ Center: Seed ───────────────────────
        mid = tk.LabelFrame(frame, text="2) Seed .mts", font=FONT_B,
                             bg=BG, fg=ACC, padx=10, pady=10)
        mid.pack(side="left", fill="both", expand=True, padx=5)

        self.seed_var = tk.StringVar()
        tk.Entry(mid, textvariable=self.seed_var, width=30, font=FONT).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(mid, text="Browse .mts", bg=BTN, fg=BG, font=FONT,
                  command=lambda: self._browse_mts(self.seed_var)).grid(row=0, column=1, padx=5)
        tk.Label(mid, text="Your Port:", bg=BG, fg=FG, font=FONT).grid(row=1, column=0, sticky="w", pady=3)
        self.seed_pt = tk.StringVar(value="6000")
        tk.Entry(mid, textvariable=self.seed_pt, width=15, font=FONT).grid(row=1, column=1, pady=3)
        tk.Button(mid, text="Start Seeder", bg=BTN, fg=BG, font=FONT_B,
                  command=self._start_seeder).grid(row=2, column=0, columnspan=2, pady=8)

        # ─ Right: Download ────────────────────
        right = tk.LabelFrame(frame, text="3) Download", font=FONT_B,
                              bg=BG, fg=ACC, padx=10, pady=10)
        right.pack(side="left", fill="both", expand=True, padx=5)

        self.dl_name = tk.StringVar()
        tk.Entry(right, textvariable=self.dl_name, width=30, font=FONT).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(right, text="Your Port:", bg=BG, fg=FG, font=FONT).grid(row=1, column=0, sticky="w", pady=3)
        self.dl_pt = tk.StringVar(value="7000")
        tk.Entry(right, textvariable=self.dl_pt, width=15, font=FONT).grid(row=1, column=1, pady=3)
        tk.Button(right, text="Download File", bg=BTN, fg=BG, font=FONT_B,
                  command=self._download_file).grid(row=2, column=0, columnspan=2, pady=8)

        # ─ Bottom: Log ─────────────────────────
        self.log = tk.Text(self, height=6, bg="#1E222A", fg=FG, font=("Consolas", 10))
        self.log.pack(fill="both", expand=False, padx=10, pady=(0,10))
        self.log.insert("end", "Ready.\n")
        self.log.configure(state="disabled")

    # ─── Callbacks ───────────────────────────────────────────────────────────────
    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _browse_file(self):
        path = filedialog.askopenfilename(title="Select any file")
        if path:
            self.src_var.set(path)
            self._log(f"Selected file → {path}")

    def _browse_mts(self, var):
        path = filedialog.askopenfilename(title="Select .mts file", filetypes=[("MTS","*.mts")])
        if path:
            var.set(path)
            self._log(f"Loaded metadata → {path}")

    def _create_mts(self):
        src = self.src_var.get().strip()
        ip  = self.tr_ip.get().strip()
        pt  = self.tr_pt.get().strip()
        if not src or not os.path.exists(src):
            messagebox.showerror("Error","Please select a valid file.")
            return
        # build metadata
        fname = os.path.basename(src)
        sha   = sha256_file(src)
        meta = {"filename": fname, "size": os.path.getsize(src),
                "sha256": sha, "tracker": f"{ip}:{pt}"}
        mts_path = src + ".mts"
        with open(mts_path, "w") as f:
            json.dump(meta, f, indent=2)
        self._log(f"Created .mts → {mts_path}")
        messagebox.showinfo("Success", f".mts file created:\n{mts_path}")

    def _start_seeder(self):
        mts = self.seed_var.get().strip()
        pt  = self.seed_pt.get().strip()
        if not mts or not os.path.exists(mts):
            messagebox.showerror("Error","Please select a valid .mts file.")
            return
        cmd = ["python","client.py", mts, TRACKER_DEFAULT_IP, pt]
        self._log("Seeding: " + " ".join(cmd))
        threading.Thread(target=lambda: subprocess.run(cmd), daemon=True).start()

    def _download_file(self):
        name = self.dl_name.get().strip()
        pt   = self.dl_pt.get().strip()
        if not name:
            messagebox.showerror("Error","Enter the base filename (e.g., report.pdf).")
            return
        cmd = ["python","client.py", name, TRACKER_DEFAULT_IP, pt]
        self._log("Downloading: " + " ".join(cmd))
        threading.Thread(target=lambda: subprocess.run(cmd), daemon=True).start()

# ─── Launch ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = MiniTorrentGUI()
    app.mainloop()
