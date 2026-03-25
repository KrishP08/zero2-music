# Zero2 Music Player — Installation Guide

## Prerequisites

- **Hardware**: Raspberry Pi Zero 2 W
- **OS**: Raspberry Pi OS Bookworm (Lite or Desktop)
- **Display**: SPI TFT (320×240) via fbTFT kernel overlay
- **Buttons**: 14 GPIO buttons (gamepad layout)

---

## 1. System Packages

```bash
sudo apt update && sudo apt install -y \
    python3 python3-venv python3-pip python3-dev \
    libsdl2-dev libsdl2-mixer-dev libsdl2-image-dev libsdl2-ttf-dev \
    libjpeg-dev libpng-dev libfreetype6-dev \
    git alsa-utils
```

---

## 2. fbTFT Display Setup

If you're using an SPI TFT display (ILI9341/ST7789), make sure it's enabled via device-tree overlay.

Edit `/boot/firmware/config.txt` (Bookworm) or `/boot/config.txt` (older):

```ini
# Example for ILI9341 320x240
dtoverlay=fbtft,ili9341,speed=32000000,rotate=90,gpios=dc:24,reset:25
dtparam=spi=on
```

After editing, reboot:

```bash
sudo reboot
```

Verify the display appears as `/dev/fb1`:

```bash
ls /dev/fb*
# Should show /dev/fb0 (HDMI) and /dev/fb1 (TFT)
```

---

## 3. Clone & Setup

```bash
cd ~
git clone <your-repo-url> "zero2 music"
cd "zero2 music"

python3 -m venv .venv
source .venv/bin/activate       # bash/zsh
# source .venv/bin/activate.fish  # fish shell

pip install -r requirements.txt
```

---

## 4. GPIO Wiring Reference

### Buttons

| Button    | GPIO | Physical Pin | Function            |
|-----------|------|--------------|---------------------|
| D-Pad UP  | 17   | 11           | Navigate up         |
| D-Pad DOWN| 27   | 13           | Navigate down       |
| D-Pad LEFT| 22   | 15           | Previous / Left     |
| D-Pad RIGHT| 23  | 16           | Next / Right        |
| A         | 4    | 7            | Select / Confirm    |
| B         | 3    | 5            | Back / Cancel       |
| X         | 2    | 3            | Play / Pause        |
| Y         | 18   | 12           | (Reserved)          |
| L         | 5    | 29           | Volume Down         |
| R         | 6    | 31           | Volume Up           |
| L2        | 12   | 32           | (Reserved)          |
| R2        | 16   | 36           | (Reserved)          |
| START     | 20   | 38           | Play / Pause (alt)  |
| SELECT    | 21   | 40           | Back (alt)          |

### Display (do NOT use these GPIOs for buttons)

| Function   | GPIO | Physical Pin |
|------------|------|--------------|
| SPI CS     | 8    | 24           |
| SPI MOSI   | 10   | 19           |
| SPI MISO   | 9    | 21           |
| SPI CLK    | 11   | 23           |
| Display DC | 24   | 18           |
| Display RST| 25   | 22           |

All buttons wire: **GPIO pin → button → GND**.  
Internal pull-up resistors are enabled in software — no external resistors needed.

---

## 5. Add Music

Place audio files in `~/Music`:

```bash
mkdir -p ~/Music
# Copy .mp3, .flac, .wav, .ogg, .m4a, .aac files into ~/Music
```

---

## 6. Run

```bash
cd ~/zero2\ music
source .venv/bin/activate
python main.py
```

---

## 7. Auto-Start on Boot (systemd)

Create a service file:

```bash
sudo tee /etc/systemd/system/zero2music.service << 'EOF'
[Unit]
Description=Zero2 Music Player
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/zero2 music
Environment="SDL_FBDEV=/dev/fb1"
Environment="SDL_VIDEODRIVER=fbcon"
ExecStart=/home/pi/zero2 music/.venv/bin/python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable zero2music
sudo systemctl start zero2music
```

Check status:

```bash
sudo systemctl status zero2music
journalctl -u zero2music -f   # live logs
```

---

## 8. Troubleshooting

| Problem | Fix |
|---------|-----|
| `No module named RPi.GPIO` | `pip install RPi.GPIO` |
| Display shows nothing | Check `/dev/fb1` exists, check `config.txt` overlay |
| Buttons not responding | Verify wiring (GPIO → button → GND), check `gpio readall` |
| No audio output | `alsamixer` — unmute and set volume, check headphone jack |
| Player crashes on start | Check `python main.py 2>&1` for traceback |
