import serial
import time
import json
import os
import sys
import subprocess
from evdev import UInput, ecodes as e

PORTA = '/dev/ttyUSB0'
BAUD = 9600
ARQUIVO_MAPA = os.path.expanduser('~/mapa_aoc_roku.json')

BOTOES_AOC = [
    # Volume e Áudio
    ("vol_mais", "Volume +", [e.KEY_VOLUMEUP]),
    ("vol_menos", "Volume -", [e.KEY_VOLUMEDOWN]),
    ("mudo", "Mudo (Mute)", [e.KEY_MUTE]),

    # Navegação Principal e Menu
    ("home", "Botão Home (Casinha - Abre painel do Ubuntu)", [e.KEY_LEFTMETA]),
    ("voltar", "Seta Voltar (Volta página no navegador/sistema)", [e.KEY_LEFTALT, e.KEY_LEFT]),
    ("exit", "Botão Exit (Fecha a janela atual - Alt+F4)", [e.KEY_LEFTALT, e.KEY_F4]),
    ("guide", "Botão Guide (Alterna janelas com Alt+Tab)", [e.KEY_LEFTALT, e.KEY_TAB]),
    ("asterisco", "Botão * Asterisco (Ativa/Desativa Legendas 'C')", [e.KEY_C]),

    # Canais
    ("ch_mais", "Canal + (Page Up / Subir página)", [e.KEY_PAGEUP]),
    ("ch_menos", "Canal - (Page Down / Descer página)", [e.KEY_PAGEDOWN]),

    # Setas Direcionais e OK
    ("cima", "Seta Cima", [e.KEY_UP]),
    ("baixo", "Seta Baixo", [e.KEY_DOWN]),
    ("esquerda", "Seta Esquerda (Voltar 5s no vídeo)", [e.KEY_LEFT]),
    ("direita", "Seta Direita (Avançar 5s no vídeo)", [e.KEY_RIGHT]),
    ("ok", "Botão OK (Enter / Play-Pause)", [e.KEY_ENTER]),

    # Controle de Mídia (Play/Pause, Avançar >> e Retroceder <<)
    ("play_pause", "Botão Play / Pause", [e.KEY_PLAYPAUSE]),
    ("avancar_midia", "Botão Avançar Mídia (>>)", [e.KEY_NEXTSONG]),
    ("retroceder_midia", "Botão Retroceder Mídia (<<)", [e.KEY_PREVIOUSSONG]),

    # Teclado Numérico (0 a 9) e Ponto (.)
    ("num_1", "Número 1", [e.KEY_1]),
    ("num_2", "Número 2", [e.KEY_2]),
    ("num_3", "Número 3", [e.KEY_3]),
    ("num_4", "Número 4", [e.KEY_4]),
    ("num_5", "Número 5", [e.KEY_5]),
    ("num_6", "Número 6", [e.KEY_6]),
    ("num_7", "Número 7", [e.KEY_7]),
    ("num_8", "Número 8", [e.KEY_8]),
    ("num_9", "Número 9", [e.KEY_9]),
    ("num_0", "Número 0", [e.KEY_0]),
    ("ponto", "Botão Ponto (.)", [e.KEY_DOT]),

    # Botões de Streaming e Aplicativos
    ("youtube", "Botão YouTube", ["xdg-open", "https://www.youtube.com"]),
    ("netflix", "Botão Netflix", ["xdg-open", "https://www.netflix.com"]),
    ("disney", "Botão Disney+", ["xdg-open", "https://www.disneyplus.com"]),
    ("appletv", "Botão Apple TV", ["xdg-open", "https://tv.apple.com"]),
    ("prime", "Botão Prime Video", ["xdg-open", "https://www.primevideo.com"]),
    ("verde_spotify", "Botão Verde (Abrir Spotify App)", [
        "sh", "-c", "spotify || /snap/bin/spotify || flatpak run com.spotify.Client"
    ]),
]

# Códigos fixos capturados no seu terminal para não precisar mapear de novo:
CODIGOS_FIXOS = {
    "eac711": "youtube",
    "eac755": "avancar_midia",
    "eac734": "retroceder_midia",
    "eac707": "exit",
    "eac74a": "ponto",
}

DICIONARIO_ACOES = {id_btn: (nome, acao) for id_btn, nome, acao in BOTOES_AOC}

def ler_pacote_ir(ser):
    primeiro = ser.read(1)
    if not primeiro:
        return None
    time.sleep(0.02)
    resto = ser.read(2)
    if len(resto) == 2:
        return (primeiro + resto).hex().lower()
    ser.reset_input_buffer()
    return None

def mapear_botoes(ser, mapa, apenas_novos=True):
    ja_mapeados = set(mapa.values())
    lista_para_mapear = [
        (id_btn, nome) for id_btn, nome, _ in BOTOES_AOC
        if not apenas_novos or id_btn not in ja_mapeados
    ]

    if not lista_para_mapear:
        return mapa

    print("\n=== MAPEAMENTO DE BOTÕES DO CONTROLE AOC ===")
    for id_btn, nome in lista_para_mapear:
        ser.reset_input_buffer()
        print(f"--> Aperte agora no controle: [{nome}] ... ", end="", flush=True)
        try:
            while True:
                codigo = ler_pacote_ir(ser)
                if codigo:
                    mapa[codigo] = id_btn
                    print(f"OK! (Código gravado: {codigo})")
                    time.sleep(0.6)
                    ser.reset_input_buffer()
                    break
        except KeyboardInterrupt:
            print("Pulado.")
            time.sleep(0.3)

    with open(ARQUIVO_MAPA, 'w') as f:
        json.dump(mapa, f, indent=2)
    return mapa

def disparar_teclas(ui, teclas):
    for t in teclas:
        ui.write(e.EV_KEY, t, 1)
    ui.syn()
    time.sleep(0.03)
    for t in reversed(teclas):
        ui.write(e.EV_KEY, t, 0)
    ui.syn()

def executar_acao(ui, acao):
    if acao and isinstance(acao[0], int):
        disparar_teclas(ui, acao)
    elif acao and isinstance(acao[0], str):
        subprocess.Popen(
            acao,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

def main():
    try:
        ser = serial.Serial(PORTA, BAUD, timeout=0.05)
    except Exception as err:
        print(f"Erro ao abrir {PORTA}: {err}")
        return

    mapa = {}
    if os.path.exists(ARQUIVO_MAPA):
        try:
            with open(ARQUIVO_MAPA, 'r') as f:
                mapa = json.load(f)
        except Exception:
            mapa = {}

    # Injeta automaticamente os 4 códigos eac7.. no seu arquivo JSON
    atualizou = False
    for cod, acao_id in CODIGOS_FIXOS.items():
        if mapa.get(cod) != acao_id:
            mapa[cod] = acao_id
            atualizou = True

    if atualizou:
        with open(ARQUIVO_MAPA, 'w') as f:
            json.dump(mapa, f, indent=2)
        print("Códigos eac755, eac734, eac707 e eac74a adicionados ao mapa!")

    if "--mapear-tudo" in sys.argv:
        mapa = mapear_botoes(ser, {}, apenas_novos=False)
    else:
        mapa = mapear_botoes(ser, mapa, apenas_novos=True)

    todas_teclas = set()
    for _, _, acao in BOTOES_AOC:
        if acao and isinstance(acao[0], int):
            todas_teclas.update(acao)

    ui = UInput({e.EV_KEY: list(todas_teclas)}, name="Controle-AOC-Roku-USB")
    print("Controle AOC Roku 100% ativo no Ubuntu 26!")

    ultimo_tempo = 0
    ser.reset_input_buffer()

    while True:
        codigo = ler_pacote_ir(ser)
        if codigo:
            agora = time.time()
            if agora - ultimo_tempo > 0.25:
                ultimo_tempo = agora
                if codigo in mapa:
                    id_btn = mapa[codigo]
                    if id_btn in DICIONARIO_ACOES:
                        nome, acao = DICIONARIO_ACOES[id_btn]
                        print(f"[Ação] {nome} ({codigo})")
                        executar_acao(ui, acao)
                else:
                    print(f"[Não mapeado] Código recebido: {codigo}")

if __name__ == "__main__":
    main()