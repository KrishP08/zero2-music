#!/bin/bash
# Zero2 Music Player — launcher for systemd
cd "/home/krish/zero2 music"
export SDL_AUDIODRIVER=pulseaudio
export SDL_VIDEODRIVER=dummy
export SDL_NOMOUSE=1
exec "/home/krish/zero2 music/.venv/bin/python" main.py
