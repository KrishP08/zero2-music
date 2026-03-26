# Zero2 Music Player — Hardware Fixes for Pi Zero 2 W

If you are seeing errors or the screen is blank on Raspberry Pi OS Bookworm, follow these steps.

## 1. Install CAVA (Music Visualizer)

CAVA needs to be installed on the system for the bars to show up:

```bash
sudo apt update
sudo apt install cava
```

## 2. Audio & Display Permissions

Make sure your user (`krish`) is in the `video`, `audio`, and `gpio` groups:

```bash
sudo usermod -a -G video,audio,gpio krish
# Log out and log back in for this to take effect!
```

## 3. Fix "Unknown Error 524" (ALSA)

If you get audio errors, it's often because ALSA is busy. We have updated the code to force `SDL_AUDIODRIVER=alsa`, but if it still fails, try:

```bash
# Check if anything is using the sound card
fuser -v /dev/snd/*
# If you see processes, stop them.
```

## 4. Fix Black Screen on TFT (/dev/fb1)

If the display is black but `main.py` is running, ensure your `fbtft` overlay is correct in `/boot/firmware/config.txt`.

Example for ILI9341:
```ini
dtparam=spi=on
dtoverlay=fbtft,ili9341,speed=32000000,rotate=90,gpios=dc:24,reset:25
```

Then run the player with:
```bash
SDL_VIDEODRIVER=fbcon SDL_FBDEV=/dev/fb1 python3 main.py
```

## 5. Correct Pinout Reference (GamePad)

The code has been updated to use **Pin 24 (DC)** and **Pin 25 (Reset)** to match standard `fbtft` configs.

**Buttons (Internal Pull-Up):**
- **D-Pad Up**: GPIO 17
- **D-Pad Down**: GPIO 27
- **D-Pad Left**: GPIO 22
- **D-Pad Right**: GPIO 23
- **A**: GPIO 4
- **B**: GPIO 3
- **X**: GPIO 2
- **Y**: GPIO 18
- **L**: GPIO 5
- **R**: GPIO 6
- **START**: GPIO 20
- **SELECT**: GPIO 21

## 6. Dependencies for Bookworm

We now use `gpiozero` and `lgpio`. If `pip install` fails, install them via apt:
```bash
sudo apt install python3-gpiozero python3-lgpio
```
