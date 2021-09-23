#!/usr/bin/env python3
import os
import sys
import time
import telnetlib


# TODO: ver si es necesario manejar errores:
# Al recibir desconexion remota:
# OFError: telnet connection closed
# Al no existir el host
# OSError: [Errno 113] No route to host
# al no ser un moxa:
# ConnectionRefusedError: [Errno 111] Connection refused
def send_selection(tn: telnetlib.Telnet, key=None, expect_message=None):
    output = tn.read_until(b"Key in your selection: " if not expect_message else expect_message.encode('ascii'), timeout=2)
    tn.write((str(key).encode('ascii') if key else b'') + b'\r\n')
    return output


def press_key_to_continue(tn: telnetlib.Telnet):
    return send_selection(tn, expect_message="Press any key to continue...")


def read_info(moxa_ip):
    output = b""
    tn = telnetlib.Telnet(moxa_ip)
    output += send_selection(tn, 'q') #   (q) Quit
    output += tn.read_until(b"q", timeout=1)
    tn.close()
    time.sleep(1)
    return output


def parse_info(raw_info):
    raw_info = raw_info if isinstance(raw_info, str) else raw_info.decode('ascii')
    _, raw_info, _ = raw_info.split('-'*77)
    return { line.split(':')[0].strip() : line.split(':', maxsplit=1)[1].strip()
        for line in raw_info.strip().split('\r\n')}


def dump_settings(moxa_ip):
    output = b""
    tn = telnetlib.Telnet(moxa_ip)
    output += send_selection(tn, 'v') #   (v) View settings
    for _ in range(9): # has 9 sections of settings
        output += press_key_to_continue(tn)
    output += send_selection(tn, 'q') #   (q) Quit
    output += tn.read_until(b"q", timeout=1)
    tn.close()
    time.sleep(1)
    return output


def save_settings(moxa_ip, tipo, settings):
    counter = 0
    prefix = os.path.basename(__file__).replace('.py', '')
    file_name = f"{prefix}_{tipo}_{counter}_{moxa_ip}.txt"
    while os.path.exists(file_name):
        counter += 1
        file_name = f"{prefix}_{tipo}_{counter}_{moxa_ip}.txt"

    with open(file_name, 'wb') as fp:
        if isinstance(settings, str):
            fp.write(settings.encode('ascii'))
        else:
            fp.write(settings)


def apply_settings(moxa_ip, model='NPort 5150'):
    tn = telnetlib.Telnet(moxa_ip)
    output = b""
    # print(tn.read_all().decode('ascii'))
    output += send_selection(tn, '3') #   (3) Serial settings
    output += send_selection(tn, '1') #   (1) Port 1
    output += send_selection(tn, '2') #   (2) Baud rate
    if model=='NPort 5150':
        output += send_selection(tn, 'c') #   (c) 9600
    if model=='NPort 5110':
        output += send_selection(tn, 'a') #   (a) 9600
    output += send_selection(tn, '3') #   (3) Data bits
    output += send_selection(tn, '2') #   (2) 7
    output += send_selection(tn, '5') #   (5) Parity
    output += send_selection(tn, '1') #   (1) Odd
    output += send_selection(tn, 'm') #   (m) Back to main menu
    output += send_selection(tn, '4') #   (4) Operating settings
    output += send_selection(tn, '1') #   (1) Port 1
    output += send_selection(tn, '1') #   (1) Operating mode (Real COM Mode)
    output += send_selection(tn, '1') #   (1) TCP Server Mode
    # --------------------------------
    output += send_selection(tn, '4') #   (4) Max connection
    output += tn.read_until(b"ANY", timeout=1) # Read default Value
    BACKSPACE = '\b'
    output += send_selection(tn, BACKSPACE + '2', expect_message="Max connection(1-4): ") #   Max connection(1-4): 2
    output += press_key_to_continue(tn)
    # --------------------------------
    output += send_selection(tn, '5') #   (5) Ignore jammed IP
    output += tn.read_until(b"ANY", timeout=1) # Lee prompt ""
    output += send_selection(tn, 'y', expect_message="Key in your selection: ") #   Key in your selection: 2
    output += press_key_to_continue(tn)
    # --------------------------------
    output += send_selection(tn, 'm') #   (m) Back to main menu    # saliendo de "Port 1")
    # output += send_selection(tn, 'm') #   (m) Back to main menu    # saliendo de "Operating settings")
    output += send_selection(tn, 's') #   (s) Save/Restart
    output += send_selection(tn, 'y') #   (y) Yes                  # pregunta Save change?
    output += tn.read_until(b"y", timeout=1)
    tn.close()
    time.sleep(1)
    return output


def main():
    if len(sys.argv) == 1:
        print("Indicar la IP del moxa como parametro.")
        return
    moxa_ip = sys.argv[1]
    # Leo info:
    info_moxa = parse_info(read_info(moxa_ip))
    print("Informacion del Moxa en '" + moxa_ip + "': " + str(info_moxa))
    
    # Leo configuracion actual:
    settings = dump_settings(moxa_ip)
    # print(settings.decode('ascii'))
    save_settings(moxa_ip, 'antes', settings)
    print("Guardada configuracion anterior de '" + moxa_ip + "'.")
    
    # Aplico receta de configuracion:
    log_steps = apply_settings(moxa_ip, model=info_moxa['Model name'])
    # print(log_steps.decode('ascii'))
    save_settings(moxa_ip, 'configurando', log_steps)
    print("Configurado '" + moxa_ip + "'. Esperando a que reinicie...")
    time.sleep(10)

    # Leo configuracion posterior:
    save_settings(moxa_ip, 'despues', dump_settings(moxa_ip))
    print("Guardada configuracion posterior de '" + moxa_ip + "'.")


if __name__ == '__main__':
    main()
