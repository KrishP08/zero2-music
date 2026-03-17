import os
import threading
import subprocess

class CavaVisualizer:
    """Reads CAVA output from a FIFO pipe to build a live audio spectrum array."""
    def __init__(self, bars=32):
        self.bars = bars
        self.values = [0.0] * bars
        self.fifo_path = "/tmp/cava.fifo"
        self._running = False
        self._thread = None
        self._process = None

    def start(self):
        if self._running:
            return
            
        self._running = True
        
        # Ensure FIFO exists
        if not os.path.exists(self.fifo_path):
            try:
                os.mkfifo(self.fifo_path)
            except OSError:
                pass
                
        # Write config if needed
        config_dir = os.path.expanduser("~/.config/cava")
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "config_zero2")
        
        with open(config_path, "w") as f:
            f.write(f'''[general]
bars = {self.bars}
framerate = 60

[input]
method = pulse

[output]
method = raw
raw_target = {self.fifo_path}
data_format = ascii
ascii_max_range = 100
bar_delimiter = 59
''')

        # Start cava process
        try:
            self._process = subprocess.Popen(
                ["cava", "-p", config_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"Failed to start CAVA: {e}")
            self._running = False
            return
            
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        # Open FIFO
        try:
            with open(self.fifo_path, "r") as fifo:
                while self._running:
                    line = fifo.readline()
                    if not line:
                        break # EOF or closed
                        
                    line = line.strip()
                    if not line:
                        continue
                        
                    parts = [p for p in line.split(";") if p]
                    if len(parts) >= self.bars:
                        try:
                            # Parse integers 0-100 and normalize to 0.0-1.0
                            self.values = [max(0.0, min(1.0, int(v) / 100.0)) for v in parts[:self.bars]]
                        except ValueError:
                            pass
        except Exception as e:
            print(f"CAVA read loop error: {e}")
            
    def stop(self):
        self._running = False
        if self._process:
            self._process.terminate()
            self._process = None
            
    def get_levels(self):
        return self.values
