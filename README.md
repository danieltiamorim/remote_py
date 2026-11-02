# remote_py
Get Codes of Remote Controls (InfraRed) using Python

## Installation
    sudo apt update
    sudo apt install -y python3-serial python3-evdev
    sudo modprobe uinput
    sudo chmod 666 /dev/ttyUSB0 /dev/uinput
## Run 
    python3 ~/roku_pc.py

## File Map
    mapa_aoc_roku.json

This model runs the Control *AOC + Roku TV*, maybe you using AI you can adapt to your remote control model.

## Esquema de Montagem
    Pino no CP2102 (USB) -> Pino no YS-IRTM (IR) = Função
    +5V -> 5V           = Alimentação principal de 5V DC vinda da USB
    GND -> GND          = Terra comum (Referência 0V)
    TXD (ou TXO) -> RXD = Dados enviados do PC para o módulo IR
    RXD (ou RXI) -> TXD = Códigos IR decodificados enviados para o PC
    
    DTR e 3V3 ~  (Não conectados) = Usados apenas para gravar Arduinos/ESP
