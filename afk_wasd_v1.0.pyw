import tkinter as tk
import threading
import time
import random
import pyautogui

pyautogui.FAILSAFE = False

KEYS = ["w", "a", "s", "d"]
DEFAULT_MIN_INTERVAL = 30.0
DEFAULT_MAX_INTERVAL = 50.0
KEY_HOLD_RANGE = (0.08, 0.18)
POLL_SECONDS = 0.1

class RoundedButton(tk.Canvas):
    """A canvas-based button with rounded corners."""
    def __init__(self, parent, text, command, width=180, height=52,
                 radius=16, bg_color="#00ff88", fg_color="#0d0d0d",
                 hover_color="#00cc6a", font=("Courier New", 12, "bold"), **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg="#0d0d0d", highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.fg_color = fg_color
        self.radius = radius
        self.w = width
        self.h = height
        self.font = font
        self._text = text
        self._draw(bg_color)
        self.bind("<Enter>", lambda e: self._draw(hover_color))
        self.bind("<Leave>", lambda e: self._draw(self.bg_color))
        self.bind("<Button-1>", lambda e: self.command())

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90,  extent=90,  style="pieslice", **kw)
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0,   extent=90,  style="pieslice", **kw)
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90,  style="pieslice", **kw)
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90,  style="pieslice", **kw)
        self.create_rectangle(x1+r, y1, x2-r, y2, **kw)
        self.create_rectangle(x1, y1+r, x2, y2-r, **kw)

    def _draw(self, color):
        self.delete("all")
        self._round_rect(0, 0, self.w, self.h, self.radius,
                         fill=color, outline=color)
        self.create_text(self.w//2, self.h//2, text=self._text,
                         fill=self.fg_color, font=self.font)

    def set_text(self, text):
        self._text = text
        self._draw(self.bg_color)

    def set_colors(self, bg_color, hover_color, fg_color):
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.fg_color = fg_color
        self._draw(bg_color)


class AFKFarmer:
    def __init__(self, root):
        self.root = root
        self.root.title("AFK WASD Farmer")
        self.root.geometry("360x460")
        self.root.resizable(False, False)
        self.root.configure(bg="#0d0d0d")

        self.running = False
        self.key_index = 0
        self.press_count = 0
        self.thread = None
        self.start_time = None
        self.interval_min = DEFAULT_MIN_INTERVAL
        self.interval_max = DEFAULT_MAX_INTERVAL

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        bg = "#0d0d0d"
        card = "#161616"
        accent = "#00ff88"
        muted = "#444444"
        text = "#e0e0e0"
        subtle = "#888888"

        # Title
        tk.Label(self.root, text="WASD AFK FARMER", font=("Courier New", 13, "bold"),
                 fg=accent, bg=bg).pack(pady=(22, 2))
        tk.Label(self.root, text="for XP grinding",
                 font=("Courier New", 8), fg=subtle, bg=bg).pack(pady=(0, 16))

        # Timing config frame
        config_frame = tk.Frame(self.root, bg=card, bd=0, relief="flat")
        config_frame.pack(fill="x", padx=24, pady=(0, 14))

        tk.Label(config_frame, text="INTERVAL (seconds)",
                 font=("Courier New", 8, "bold"), fg=subtle, bg=card).grid(
                 row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 4))

        tk.Label(config_frame, text="MIN", font=("Courier New", 8), fg=subtle, bg=card).grid(
            row=1, column=0, sticky="w", padx=14)
        self.min_var = tk.StringVar(value=str(int(DEFAULT_MIN_INTERVAL)))
        min_entry = tk.Entry(config_frame, textvariable=self.min_var, width=6,
                             font=("Courier New", 11), fg=accent, bg="#1e1e1e",
                             insertbackground=accent, bd=0, relief="flat")
        min_entry.grid(row=2, column=0, padx=14, pady=(2, 12), sticky="w")

        tk.Label(config_frame, text="MAX", font=("Courier New", 8), fg=subtle, bg=card).grid(
            row=1, column=1, sticky="w", padx=14)
        self.max_var = tk.StringVar(value=str(int(DEFAULT_MAX_INTERVAL)))
        max_entry = tk.Entry(config_frame, textvariable=self.max_var, width=6,
                             font=("Courier New", 11), fg=accent, bg="#1e1e1e",
                             insertbackground=accent, bd=0, relief="flat")
        max_entry.grid(row=2, column=1, padx=14, pady=(2, 12), sticky="w")

        # WASD display
        wasd_frame = tk.Frame(self.root, bg=bg)
        wasd_frame.pack(pady=(0, 14))

        self.key_labels = {}
        for i, k in enumerate(KEYS):
            lbl = tk.Label(wasd_frame, text=k.upper(), width=3,
                           font=("Courier New", 16, "bold"),
                           fg=muted, bg=card, relief="flat", bd=0)
            lbl.grid(row=0, column=i, padx=5, pady=6, ipadx=6, ipady=6)
            self.key_labels[k] = lbl

        # Status
        self.status_var = tk.StringVar(value="IDLE")
        tk.Label(self.root, textvariable=self.status_var,
                 font=("Courier New", 9), fg=subtle, bg=bg).pack(pady=(0, 4))

        # Next key / countdown
        self.next_var = tk.StringVar(value="—")
        tk.Label(self.root, textvariable=self.next_var,
                 font=("Courier New", 10, "bold"), fg=text, bg=bg).pack(pady=(0, 2))

        # Press count
        self.count_var = tk.StringVar(value="presses: 0")
        tk.Label(self.root, textvariable=self.count_var,
                 font=("Courier New", 8), fg=subtle, bg=bg).pack(pady=(0, 2))

        # Elapsed timer
        self.timer_var = tk.StringVar(value="elapsed: 00:00:00")
        tk.Label(self.root, textvariable=self.timer_var,
                 font=("Courier New", 8), fg="#555555", bg=bg).pack(pady=(0, 12))

        # Rounded Start/Stop button
        self.btn = RoundedButton(self.root, text="START", command=self.toggle,
                                 width=180, height=52, radius=16,
                                 bg_color=accent, hover_color="#00cc6a", fg_color="#0d0d0d")
        self.btn.pack(pady=(0, 6))

        tk.Label(self.root, text="switch to game window after clicking start",
                 font=("Courier New", 7), fg="#333333", bg=bg).pack()

        # Watermark
        tk.Label(self.root, text="Built by Nori",
                 font=("Courier New", 7), fg="#222222", bg=bg).pack(side="bottom", pady=(0, 6))

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        interval = self._read_interval()
        if interval is None:
            return

        self.interval_min, self.interval_max = interval
        self.running = True
        self.key_index = 0
        self.press_count = 0
        self.start_time = time.time()
        self.btn.set_text("STOP")
        self.btn.set_colors("#ff4455", "#cc2233", "#ffffff")
        self.status_var.set("RUNNING — switch to game window now")
        self.count_var.set("presses: 0")
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        self._tick_timer()

    def stop(self):
        self.running = False
        self.btn.set_text("START")
        self.btn.set_colors("#00ff88", "#00cc6a", "#0d0d0d")
        self.status_var.set("STOPPED")
        self.next_var.set("—")
        for lbl in self.key_labels.values():
            lbl.config(fg="#444444")

    def on_close(self):
        self.running = False
        self.root.destroy()

    def _schedule_ui(self, callback, *args):
        try:
            self.root.after(0, callback, *args)
        except tk.TclError:
            self.running = False

    def _read_interval(self):
        try:
            mn = float(self.min_var.get())
            mx = float(self.max_var.get())
        except ValueError:
            self.status_var.set("invalid input")
            return None

        if mn <= 0 or mx <= mn:
            self.status_var.set("bad interval values")
            return None

        return mn, mx

    def _tick_timer(self):
        if self.running and self.start_time is not None:
            elapsed = int(time.time() - self.start_time)
            h = elapsed // 3600
            m = (elapsed % 3600) // 60
            s = elapsed % 60
            self.timer_var.set(f"elapsed: {h:02d}:{m:02d}:{s:02d}")
            self.root.after(1000, self._tick_timer)

    def _loop(self):
        while self.running:
            wait = random.uniform(self.interval_min, self.interval_max)

            key = KEYS[self.key_index % 4]

            start_time = time.time()
            while self.running:
                elapsed = time.time() - start_time
                remaining = wait - elapsed
                if remaining <= 0:
                    break
                self._schedule_ui(self.next_var.set,
                                  f"next: [{key.upper()}]  in {remaining:.1f}s")
                time.sleep(POLL_SECONDS)

            if not self.running:
                break

            self._schedule_ui(self._flash_key, key)

            try:
                pyautogui.keyDown(key)
                time.sleep(random.uniform(*KEY_HOLD_RANGE))
            finally:
                pyautogui.keyUp(key)

            self.key_index += 1
            self.press_count += 1
            self._schedule_ui(self.count_var.set, f"presses: {self.press_count}")

    def _flash_key(self, key):
        accent = "#00ff88"
        muted = "#444444"
        for k, lbl in self.key_labels.items():
            lbl.config(fg=accent if k == key else muted)
        try:
            self.root.after(300, lambda: self.key_labels[key].config(fg=muted))
        except tk.TclError:
            self.running = False


if __name__ == "__main__":
    root = tk.Tk()
    app = AFKFarmer(root)
    root.mainloop()
