"""
Bluetooth Manager — wraps bluetoothctl for device scanning, pairing, and connection.
Gracefully degrades when bluetooth is unavailable.
"""

import subprocess
import threading
import re
import time


class BluetoothDevice:
    """Represents a discovered or paired Bluetooth device."""

    def __init__(self, mac, name, paired=False, connected=False, rssi=None):
        self.mac = mac
        self.name = name or "Unknown Device"
        self.paired = paired
        self.connected = connected
        self.rssi = rssi

    @property
    def status_text(self):
        if self.connected:
            return "Connected"
        elif self.paired:
            return "Paired"
        return ""

    def __repr__(self):
        return f"<BT {self.name} [{self.mac}] paired={self.paired} conn={self.connected}>"


class BluetoothManager:
    """Manages Bluetooth via bluetoothctl subprocess calls."""

    def __init__(self):
        self._available = self._check_available()
        self._devices = []
        self._scanning = False
        self._enabled = self._available
        self._scan_thread = None

    @property
    def available(self):
        return self._available

    @property
    def enabled(self):
        return self._enabled

    @property
    def scanning(self):
        return self._scanning

    @property
    def devices(self):
        return list(self._devices)

    def _check_available(self):
        """Check if bluetoothctl is installed and a controller exists."""
        try:
            result = subprocess.run(
                ["bluetoothctl", "show"],
                capture_output=True, text=True, timeout=3
            )
            return result.returncode == 0 and "Controller" in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def toggle_power(self):
        """Toggle Bluetooth on/off."""
        if not self._available:
            return
        self._enabled = not self._enabled
        state = "on" if self._enabled else "off"
        self._run_cmd(["bluetoothctl", "power", state])
        if not self._enabled:
            self._scanning = False
            self._devices.clear()

    def start_scan(self, duration=8):
        """Start async device scan."""
        if not self._available or not self._enabled or self._scanning:
            return
        self._scanning = True
        self._scan_thread = threading.Thread(
            target=self._scan_worker, args=(duration,), daemon=True
        )
        self._scan_thread.start()

    def _scan_worker(self, duration):
        """Background scan thread using non-interactive bluetoothctl."""
        try:
            # Use --timeout flag which makes bluetoothctl exit after scanning
            proc = subprocess.Popen(
                ["bluetoothctl", "--timeout", str(duration), "scan", "on"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
            )
            try:
                proc.wait(timeout=duration + 5)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception as e:
            print(f"[BT] Scan error: {e}")
        finally:
            self._refresh_devices()
            self._scanning = False

    def _refresh_devices(self):
        """Refresh device list from bluetoothctl."""
        devices = []
        try:
            result = self._run_cmd(["bluetoothctl", "devices"])
            if result and result.stdout:
                for line in result.stdout.strip().split("\n"):
                    match = re.match(r"Device\s+([0-9A-F:]{17})\s+(.+)", line)
                    if match:
                        mac = match.group(1)
                        name = match.group(2)
                        paired = self._is_paired(mac)
                        connected = self._is_connected(mac)
                        devices.append(BluetoothDevice(mac, name, paired, connected))
        except Exception as e:
            print(f"[BT] Refresh error: {e}")
        self._devices = devices

    def get_paired_devices(self):
        """Get list of paired devices."""
        devices = []
        try:
            result = self._run_cmd(["bluetoothctl", "devices", "Paired"])
            if result and result.stdout:
                for line in result.stdout.strip().split("\n"):
                    match = re.match(r"Device\s+([0-9A-F:]{17})\s+(.+)", line)
                    if match:
                        mac = match.group(1)
                        name = match.group(2)
                        connected = self._is_connected(mac)
                        devices.append(BluetoothDevice(mac, name, True, connected))
        except Exception:
            pass
        return devices

    def pair(self, mac):
        """Pair with a device."""
        if not self._available:
            return False
        result = self._bt_cmd_stepped([
            f"trust {mac}",
            f"pair {mac}",
        ], step_delay=2, timeout=20)
        return "Pairing successful" in result or "already" in result.lower()

    def connect(self, mac):
        """Connect to a paired device."""
        if not self._available:
            return False
        result = self._bt_cmd_stepped([
            f"connect {mac}",
        ], step_delay=2, timeout=15)
        success = "Connection successful" in result
        if success:
            self._refresh_devices()
        return success

    def pair_and_connect(self, mac):
        """Trust, pair, and connect in a single bluetoothctl session."""
        if not self._available:
            return False

        commands = [f"trust {mac}"]

        if not self._is_paired(mac):
            commands.append(f"pair {mac}")

        commands.append(f"connect {mac}")

        result = self._bt_cmd_stepped(commands, step_delay=3, timeout=30)
        print(f"[BT] pair_and_connect output: {result[-200:]}")
        success = "Connection successful" in result
        if success:
            self._refresh_devices()
        return success

    def _bt_cmd_stepped(self, commands, step_delay=2, timeout=20):
        """
        Run a sequence of bluetoothctl commands in a single session,
        with delays between each command.
        """
        import time as _time

        proc = subprocess.Popen(
            ["bluetoothctl"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            # Send each command with a delay
            for cmd in commands:
                proc.stdin.write(cmd + "\n")
                proc.stdin.flush()
                _time.sleep(step_delay)

            # Send quit and collect output
            proc.stdin.write("quit\n")
            proc.stdin.flush()
            stdout, _ = proc.communicate(timeout=timeout)
            return stdout or ""
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, _ = proc.communicate()
            return stdout or ""
        except Exception as e:
            print(f"[BT] Command error: {e}")
            try:
                proc.kill()
            except Exception:
                pass
            return ""

    def disconnect(self, mac):
        """Disconnect from a device."""
        if not self._available:
            return False
        result = self._bt_cmd_stepped([f"disconnect {mac}"], step_delay=2, timeout=10)
        success = "Successful disconnected" in result or "not connected" in result.lower()
        self._refresh_devices()
        return success

    def _is_paired(self, mac):
        try:
            result = self._run_cmd(["bluetoothctl", "info", mac])
            if result and result.stdout:
                return "Paired: yes" in result.stdout
        except Exception:
            pass
        return False

    def _is_connected(self, mac):
        try:
            result = self._run_cmd(["bluetoothctl", "info", mac])
            if result and result.stdout:
                return "Connected: yes" in result.stdout
        except Exception:
            pass
        return False

    def _run_cmd(self, cmd, timeout=5):
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"[BT] Command failed: {' '.join(cmd)} — {e}")
            return None

    def cleanup(self):
        """Stop scanning if active."""
        if self._scanning:
            self._run_cmd(["bluetoothctl", "scan", "off"], timeout=2)
            self._scanning = False
