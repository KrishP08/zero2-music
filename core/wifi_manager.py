"""
WiFi Manager — wraps nmcli for network scanning and connection.
Gracefully degrades when NetworkManager is unavailable.
"""

import subprocess
import threading
import re


class WiFiNetwork:
    """Represents a discovered WiFi network."""

    def __init__(self, ssid, signal=0, security="", connected=False, saved=False):
        self.ssid = ssid
        self.signal = signal      # 0–100
        self.security = security  # e.g. "WPA2", "Open"
        self.connected = connected
        self.saved = saved

    @property
    def signal_bars(self):
        """Return a visual signal strength indicator."""
        if self.signal >= 75:
            return "▂▄▆█"
        elif self.signal >= 50:
            return "▂▄▆ "
        elif self.signal >= 25:
            return "▂▄  "
        return "▂   "

    @property
    def status_text(self):
        if self.connected:
            return "Connected"
        elif self.saved:
            return "Saved"
        return self.security or ""

    def __repr__(self):
        return f"<WiFi {self.ssid} signal={self.signal} conn={self.connected}>"


class WiFiManager:
    """Manages WiFi via nmcli (NetworkManager CLI)."""

    def __init__(self):
        self._available = self._check_available()
        self._networks = []
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
    def networks(self):
        return list(self._networks)

    def _check_available(self):
        """Check if nmcli is installed and WiFi hardware exists."""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "TYPE,STATE", "device"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode != 0:
                return False
            return "wifi" in result.stdout.lower()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def toggle_power(self):
        """Toggle WiFi on/off."""
        if not self._available:
            return
        self._enabled = not self._enabled
        state = "on" if self._enabled else "off"
        self._run_cmd(["nmcli", "radio", "wifi", state])
        if not self._enabled:
            self._networks.clear()

    def start_scan(self):
        """Start async WiFi scan."""
        if not self._available or not self._enabled or self._scanning:
            return
        self._scanning = True
        self._scan_thread = threading.Thread(
            target=self._scan_worker, daemon=True
        )
        self._scan_thread.start()

    def _scan_worker(self):
        """Background scan thread."""
        try:
            # Trigger a fresh scan
            self._run_cmd(["nmcli", "device", "wifi", "rescan"], timeout=10)
            # Fetch results
            self._refresh_networks()
        except Exception as e:
            print(f"[WiFi] Scan error: {e}")
        finally:
            self._scanning = False

    def _refresh_networks(self):
        """Parse nmcli wifi list output."""
        networks = []
        current = self.get_current_network()
        saved = self._get_saved_ssids()

        try:
            result = self._run_cmd([
                "nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,ACTIVE",
                "device", "wifi", "list"
            ])
            if result and result.stdout:
                seen = set()
                for line in result.stdout.strip().split("\n"):
                    parts = line.split(":")
                    if len(parts) >= 4:
                        ssid = parts[0].strip()
                        if not ssid or ssid in seen:
                            continue
                        seen.add(ssid)
                        try:
                            signal = int(parts[1])
                        except ValueError:
                            signal = 0
                        security = parts[2] if parts[2] else "Open"
                        is_active = parts[3].strip().lower() == "yes"
                        networks.append(WiFiNetwork(
                            ssid=ssid,
                            signal=signal,
                            security=security,
                            connected=is_active,
                            saved=(ssid in saved),
                        ))
        except Exception as e:
            print(f"[WiFi] Parse error: {e}")

        # Sort: connected first, then saved, then by signal
        networks.sort(key=lambda n: (
            not n.connected, not n.saved, -n.signal
        ))
        self._networks = networks

    def get_current_network(self):
        """Get the SSID of the currently connected WiFi network."""
        try:
            result = self._run_cmd([
                "nmcli", "-t", "-f", "NAME,TYPE,DEVICE",
                "connection", "show", "--active"
            ])
            if result and result.stdout:
                for line in result.stdout.strip().split("\n"):
                    parts = line.split(":")
                    if len(parts) >= 2 and "wireless" in line.lower():
                        return parts[0]
        except Exception:
            pass
        return None

    def _get_saved_ssids(self):
        """Get set of saved WiFi connection names."""
        ssids = set()
        try:
            result = self._run_cmd([
                "nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"
            ])
            if result and result.stdout:
                for line in result.stdout.strip().split("\n"):
                    parts = line.split(":")
                    if len(parts) >= 2 and "wireless" in parts[1].lower():
                        ssids.add(parts[0])
        except Exception:
            pass
        return ssids

    def connect(self, ssid):
        """Connect to a saved WiFi network."""
        if not self._available:
            return False
        try:
            result = self._run_cmd(
                ["nmcli", "connection", "up", ssid], timeout=15
            )
            success = result is not None and result.returncode == 0
            if success:
                self._refresh_networks()
            return success
        except Exception:
            return False

    def disconnect(self):
        """Disconnect from current WiFi network."""
        if not self._available:
            return False
        current = self.get_current_network()
        if not current:
            return True
        try:
            result = self._run_cmd(
                ["nmcli", "connection", "down", current], timeout=5
            )
            self._refresh_networks()
            return result is not None and result.returncode == 0
        except Exception:
            return False

    def get_ip_address(self):
        """Get current IP address."""
        try:
            result = self._run_cmd([
                "nmcli", "-t", "-f", "IP4.ADDRESS", "device", "show"
            ])
            if result and result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if "IP4.ADDRESS" in line:
                        parts = line.split(":")
                        if len(parts) >= 2 and parts[1].strip():
                            return parts[1].strip().split("/")[0]
        except Exception:
            pass
        return "N/A"

    def _run_cmd(self, cmd, timeout=5):
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"[WiFi] Command failed: {' '.join(cmd)} — {e}")
            return None

    def cleanup(self):
        """Cleanup resources."""
        self._scanning = False
