# remote_py
Get Codes of Remote Controls (InfraRed) using Python

##Installation
    sudo apt update
    sudo apt install -y python3-serial python3-evdev
    sudo modprobe uinput
    sudo chmod 666 /dev/ttyUSB0 /dev/uinput
##Run 
    python3 ~/roku_pc.py

##File Map
    mapa_aoc_roku.json

This model runs the Control *AOC + Roku TV*, maybe you using AI you can adapt to your remote control model.
