# DHCP Starvation Attack Lab

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-red)
![Lab](https://img.shields.io/badge/Environment-GNS3%20%7C%20IOSvL2-orange)
![Attack](https://img.shields.io/badge/Attack-DHCP%20Starvation-purple)
![Mitigation](https://img.shields.io/badge/Mitigation-DHCP%20Snooping-darkgreen)
![Status](https://img.shields.io/badge/Use-Controlled%20Lab-yellow)
![Security](https://img.shields.io/badge/Topic-Network%20Security-purple)

## Aviso de uso responsable

Este proyecto fue desarrollado únicamente con fines educativos, académicos y de laboratorio controlado.

El script debe ejecutarse solamente en redes propias, laboratorios autorizados o entornos virtuales como GNS3, EVE-NG, PNETLab o ambientes internos de prueba.

No debe utilizarse en redes públicas, empresariales o de terceros sin autorización explícita.

---

## Archivos del repositorio

| Archivo                                                            | Descripción                                                                                                  |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| [`dhcp-starvation.py`](./dhcp-starvation.py)                       | Script principal utilizado para ejecutar el ataque DHCP Starvation desde Kali Linux.                         |
| [`mitigacion-dhcp-starvation.md`](./mitigacion-dhcp-starvation.md) | Documento técnico con la mitigación contra DHCP Starvation usando DHCP Snooping, Rate Limit y Port Security. |
| [`README.md`](./README.md)                                         | Documentación principal del laboratorio, uso del script, evidencia esperada, mitigación y flujo recomendado. |

---

## Descripción

Este laboratorio demuestra un ataque **DHCP Starvation**, donde una máquina atacante conectada a una red local envía múltiples solicitudes DHCP utilizando direcciones MAC falsas.

El objetivo del ataque es consumir las direcciones disponibles del pool DHCP legítimo. Cuando el servidor DHCP entrega sus direcciones a clientes falsos, los clientes reales ya no pueden obtener una dirección IP válida.

En este escenario, Kali Linux genera clientes DHCP falsificados y solicita direcciones al router R-1, que funciona como servidor DHCP legítimo. Después del ataque, la VPC víctima intenta solicitar una IP, pero el servicio DHCP ya no puede responderle correctamente debido al consumo del pool o a la protección activada en el switch.

---

## Base del direccionamiento IP

El direccionamiento IP del laboratorio fue definido tomando como base la matrícula:

```text
20250845
```

Separando la matrícula en octetos, se obtuvo la dirección base:

```text
20.25.8.45
```

A partir de esta dirección se creó la red del laboratorio:

```text
20.25.8.0/24
```

---

## Objetivo del laboratorio

Demostrar cómo un atacante conectado a la misma red local puede consumir el pool DHCP legítimo mediante múltiples solicitudes generadas con direcciones MAC falsas.

---

## Objetivo del script

El script [`dhcp-starvation.py`](./dhcp-starvation.py) permite:

* Seleccionar la interfaz conectada a la red víctima.
* Generar múltiples direcciones MAC falsas.
* Enviar mensajes DHCP Discover.
* Recibir DHCP Offer desde el servidor legítimo.
* Enviar DHCP Request para reservar direcciones.
* Registrar en consola las IPs obtenidas por clientes falsos.
* Evidenciar que el pool DHCP puede quedar agotado o afectado.
* Facilitar la demostración de mitigaciones como DHCP Snooping y Port Security.

---

## Topología utilizada

```text
                   +----------------+
                   |      R-1       |
                   | 20.25.8.45     |
                   | DHCP legítimo  |
                   | Fa0/0          |
                   +-------+--------+
                           |
                           |
                    Gi0/0  |
                   +-------+--------+
                   |     SW-1       |
                   |    IOSvL2      |
                   +---+--------+---+
                       |        |
                 Gi0/1 |        | Gi0/2
                       |        |
              +--------+        +--------+
              |                          |
        +-----+-----+              +-----+-----+
        |   Kali    |              |    VPC    |
        |20.25.8.46 |              |   DHCP    |
        +-----------+              +-----------+
```

---

## Direccionamiento IP del laboratorio

| Dispositivo | Rol                     | Interfaz | Dirección IP  | Descripción                       |
| ----------- | ----------------------- | -------- | ------------- | --------------------------------- |
| R-1         | Gateway / DHCP legítimo | Fa0/0    | 20.25.8.45/24 | Router principal de la red        |
| Kali        | Atacante                | eth0     | 20.25.8.46/24 | Máquina que ejecuta el ataque     |
| VPC         | Víctima                 | eth0     | DHCP          | Cliente que solicita dirección IP |
| SW-1        | Switch                  | Gi0/0    | N/A           | Conexión hacia R-1                |
| SW-1        | Switch                  | Gi0/1    | N/A           | Conexión hacia Kali               |
| SW-1        | Switch                  | Gi0/2    | N/A           | Conexión hacia la VPC             |

---

## Configuración DHCP legítima en R-1

R-1 funciona como servidor DHCP legítimo para la red `20.25.8.0/24`.

En este laboratorio se excluyen únicamente las IPs usadas de forma fija:

```text
20.25.8.45 = R-1
20.25.8.46 = Kali
```

Configuración recomendada en R-1:

```cisco
enable
configure terminal

service dhcp

interface fastEthernet0/0
description LAN_20250845
ip address 20.25.8.45 255.255.255.0
no shutdown
exit

no ip dhcp pool LAN_20250845
no ip dhcp pool LAN-ATAQUES

no ip dhcp excluded-address 20.25.8.1 20.25.8.46
no ip dhcp excluded-address 20.25.8.45 20.25.8.46
no ip dhcp excluded-address 20.25.8.48 20.25.8.254
no ip dhcp excluded-address 20.25.8.61 20.25.8.254

ip dhcp excluded-address 20.25.8.45 20.25.8.46

ip dhcp pool LAN_20250845
network 20.25.8.0 255.255.255.0
default-router 20.25.8.45
dns-server 8.8.8.8
lease 0 1
exit

ip dhcp ping packets 0

end
write memory
```

---

## Limpiar la tabla DHCP en R-1

Antes de repetir pruebas, se recomienda limpiar los bindings, conflictos y caché ARP:

```cisco
enable
clear ip dhcp binding *
clear ip dhcp conflict *
clear arp-cache
```

Verificación:

```cisco
show ip dhcp binding
show ip dhcp conflict
```

Si el proceso DHCP queda ocupado o la tabla no se libera correctamente, se puede reiniciar el servicio DHCP:

```cisco
configure terminal
no service dhcp
end
```

Esperar unos segundos y volver a activarlo:

```cisco
configure terminal
service dhcp
ip dhcp ping packets 0
end
write memory
```

---

## Configuración IP de Kali

Kali debe tener IP fija dentro de la red del laboratorio.

Si la interfaz del laboratorio es `eth0`:

```bash
sudo ip addr flush dev eth0
sudo ip addr add 20.25.8.46/24 dev eth0
sudo ip link set eth0 up
sudo ip route replace default via 20.25.8.45
```

Si la interfaz usada es otra, reemplazar `eth0` por la interfaz correcta.

Verificar interfaces:

```bash
ip -br addr
```

Probar conectividad con R-1:

```bash
ping -c 4 20.25.8.45
```

---

## Prueba del DHCP legítimo

Antes del ataque, la VPC debe poder obtener IP desde R-1.

En la VPC:

```text
dhcp
show ip
```

Resultado esperado:

```text
IP/MASK     : 20.25.8.x/24
GATEWAY     : 20.25.8.45
DNS         : 8.8.8.8
DHCP SERVER : 20.25.8.45
```

Esto confirma que el servicio DHCP legítimo está funcionando antes del ataque.

---

## Requisitos

### Sistema atacante

* Kali Linux
* Python 3
* Scapy instalado
* Permisos de superusuario
* Conectividad directa de capa 2 con el servidor DHCP
* Interfaz conectada al switch del laboratorio

### Dispositivos de red

* Router Cisco funcionando como servidor DHCP
* Switch Cisco IOSvL2
* Cliente DHCP en la misma red local
* Laboratorio en GNS3, EVE-NG, PNETLab o entorno equivalente

---

## Verificar Scapy

Antes de ejecutar el script, validar que Scapy esté disponible:

```bash
python3 -c "import scapy; print('Scapy instalado')"
```

Si Scapy no está instalado y Kali tiene internet:

```bash
sudo apt update
sudo apt install -y python3-scapy
```

---

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/iClexi/DHCP-Starvation-Attack.git
cd DHCP-Starvation-Attack
```

Dar permisos de ejecución:

```bash
chmod +x dhcp-starvation.py
```

Verificar sintaxis:

```bash
python3 -m py_compile dhcp-starvation.py
```

---

## Uso básico

Ejecutar el script:

```bash
sudo python3 dhcp-starvation.py
```

El script solicitará los valores necesarios de forma interactiva:

```text
Interfaz conectada al switch
Cantidad de clientes falsos
Pausa entre intentos
Tiempo máximo para esperar DHCP OFFER
Tiempo máximo para esperar DHCP ACK
Prefijo de hostname falso
```

Ejemplo recomendado para este laboratorio:

```text
Interfaz: eth0
Cantidad de clientes falsos: 300
Pausa entre intentos: 0.03
Tiempo máximo para esperar OFFER: 2
Tiempo máximo para esperar ACK: 1
Hostname falso: LAB-CLIENT
```

---

## Uso recomendado para demostración

Para una demostración estable en IOSvL2 y R-1:

```text
Cantidad de clientes falsos: 300
Pausa entre intentos: 0.03
Timeout OFFER: 2
Timeout ACK: 1
```

Para una prueba más agresiva:

```text
Cantidad de clientes falsos: 400
Pausa entre intentos: 0.01
Timeout OFFER: 2
Timeout ACK: 1
```

---

## Funcionamiento técnico

El ataque se basa en el proceso DHCP conocido como DORA:

```text
Discover -> Offer -> Request -> Acknowledge
```

El script genera múltiples clientes falsos con diferentes direcciones MAC. Cada cliente falso intenta completar el proceso DHCP con el servidor legítimo.

### Paso 1: DHCP Discover

Kali envía una solicitud DHCP como si fuera un cliente nuevo:

```text
DHCP Discover
MAC falsa: 02:xx:xx:xx:xx:xx
Hostname: LAB-CLIENT-n
```

### Paso 2: DHCP Offer

R-1 responde ofreciendo una IP disponible del pool:

```text
DHCP Offer
Servidor DHCP: 20.25.8.45
IP ofrecida: 20.25.8.x
```

### Paso 3: DHCP Request

El cliente falso solicita formalmente la IP ofrecida:

```text
DHCP Request
IP solicitada: 20.25.8.x
```

### Paso 4: DHCP ACK

R-1 confirma la concesión:

```text
DHCP ACK
Lease asignado a la MAC falsa
```

Al repetirse este proceso muchas veces, el pool DHCP puede quedar consumido por clientes inexistentes.

---

## Evidencia esperada del ataque

En Kali se debe observar una salida similar a:

```text
[1] ACK 20.25.8.1 mac=02:df:75:7c:7f:b6
[2] ACK 20.25.8.2 mac=02:fa:68:29:85:2a
[3] ACK 20.25.8.3 mac=02:4d:76:99:f3:5b
```

En R-1 se deben observar múltiples bindings DHCP con MACs falsas:

```cisco
show ip dhcp binding
```

Resultado esperado:

```text
IP address       Client-ID/              Lease expiration        Type
20.25.8.1        0102.df75.7c7f.b6       Automatic
20.25.8.2        0102.fa68.2985.2a       Automatic
20.25.8.3        0102.4d76.99f3.5b       Automatic
```

En la VPC, después del ataque, al intentar renovar DHCP puede aparecer:

```text
PC1> dhcp
DDD
Can't find dhcp server
```

Esto demuestra que el cliente legítimo no pudo obtener dirección IP correctamente después del consumo del pool o la saturación del proceso DHCP.

---

## Captura con tcpdump

En Kali se puede capturar el proceso DHCP:

```bash
sudo tcpdump -ni eth0 -vvv "udp port 67 or udp port 68"
```

Para ver también las direcciones MAC de capa 2:

```bash
sudo tcpdump -eni eth0 -vvv "udp port 67 or udp port 68"
```

Se espera observar mensajes como:

```text
DHCP Discover
DHCP Offer
DHCP Request
DHCP ACK
```

También pueden observarse hostnames generados por el script:

```text
LAB-CLIENT-1
LAB-CLIENT-2
LAB-CLIENT-3
```

---

## Comandos de validación

### En R-1

```cisco
show ip dhcp binding
show ip dhcp conflict
show running-config
```

### En la VPC

```text
dhcp
show ip
```

### En Kali

```bash
ip -br addr
sudo tcpdump -eni eth0 "udp port 67 or udp port 68"
```

---

## Mitigación

La mitigación recomendada contra DHCP Starvation es aplicar controles de capa 2 en el switch:

* DHCP Snooping
* DHCP Snooping Rate Limit
* Port Security

En este laboratorio se validaron dos mecanismos:

```text
DHCP Snooping Rate Limit
Port Security
```

---

## Mitigación con DHCP Snooping

DHCP Snooping permite identificar qué puertos pueden actuar como servidores DHCP confiables.

En esta topología:

```text
Gi0/0 -> R-1 / DHCP legítimo
Gi0/1 -> Kali / atacante
Gi0/2 -> VPC / cliente
```

La configuración recomendada en SW-1 es:

```cisco
enable
configure terminal

ip dhcp snooping
ip dhcp snooping vlan 1
no ip dhcp snooping information option

interface gigabitEthernet0/0
description HACIA-R1-DHCP-LEGITIMO
ip dhcp snooping trust
exit

interface gigabitEthernet0/1
description HACIA-KALI-ATACANTE
ip dhcp snooping limit rate 5
exit

interface gigabitEthernet0/2
description HACIA-PC1-VPC
ip dhcp snooping limit rate 5
exit

end
write memory
```

Los puertos no marcados como `trust` son no confiables por defecto. Por eso, Kali y la VPC permanecen como puertos no confiables.

### Funcionamiento de DHCP Snooping

DHCP Snooping permite que los clientes envíen mensajes normales como:

```text
DHCP Discover
DHCP Request
```

Pero bloquea respuestas de servidor DHCP no autorizadas desde puertos no confiables, como:

```text
DHCP Offer
DHCP ACK
DHCP NAK
```

Además, con `ip dhcp snooping limit rate 5`, el switch limita la cantidad de paquetes DHCP permitidos por segundo en el puerto del atacante.

---

## Evidencia de DHCP Snooping funcionando

Después de ejecutar nuevamente el ataque, el switch puede mostrar:

```text
%DHCP_SNOOPING-4-DHCP_SNOOPING_ERRDISABLE_WARNING: DHCP Snooping received 5 DHCP packets on interface Gi0/1
%DHCP_SNOOPING-4-DHCP_SNOOPING_RATE_LIMIT_EXCEEDED: The interface Gi0/1 is receiving more than the threshold set
%PM-4-ERR_DISABLE: dhcp-rate-limit error detected on Gi0/1, putting Gi0/1 in err-disable state
```

Esto demuestra que el switch detectó exceso de tráfico DHCP desde Kali y colocó la interfaz `Gi0/1` en estado `err-disable`.

Comandos de verificación:

```cisco
show ip dhcp snooping
show ip dhcp snooping binding
show interfaces status
show errdisable recovery
```

---

## Levantar el puerto después de DHCP Rate Limit

Primero detener el ataque en Kali:

```bash
sudo pkill -f dhcp-starvation
```

Luego levantar el puerto en el switch:

```cisco
configure terminal
interface gigabitEthernet0/1
shutdown
no shutdown
exit
end
```

Opcionalmente, se puede configurar recuperación automática:

```cisco
configure terminal
errdisable recovery cause dhcp-rate-limit
errdisable recovery interval 30
end
```

---

## Mitigación adicional con Port Security

Port Security evita que desde un mismo puerto aparezcan muchas direcciones MAC diferentes.

Esto es útil porque el ataque DHCP Starvation genera múltiples MAC falsas desde Kali.

Configuración en el puerto de Kali:

```cisco
enable
configure terminal

interface gigabitEthernet0/1
switchport mode access
switchport port-security
switchport port-security maximum 1
switchport port-security violation shutdown
switchport port-security mac-address sticky
exit

end
write memory
```

Configuración opcional en el puerto de la VPC:

```cisco
configure terminal

interface gigabitEthernet0/2
switchport mode access
switchport port-security
switchport port-security maximum 1
switchport port-security violation restrict
switchport port-security mac-address sticky
exit

end
write memory
```

---

## Evidencia de Port Security funcionando

Al ejecutar el ataque con Port Security activo, el switch puede mostrar:

```text
%PM-4-ERR_DISABLE: psecure-violation error detected on Gi0/1, putting Gi0/1 in err-disable state
%PORT_SECURITY-2-PSECURE_VIOLATION: Security violation occurred, caused by MAC address 02e8.79d2.d520 on port GigabitEthernet0/1.
```

Esto confirma que el switch detectó múltiples MAC falsas provenientes del puerto de Kali y bloqueó la interfaz.

Comandos de verificación:

```cisco
show interfaces status
show port-security
show port-security interface gigabitEthernet0/1
show port-security address
```

---

## Quitar Port Security para probar solo DHCP Snooping

Si se desea dejar solamente DHCP Snooping activo, se puede retirar Port Security del puerto de Kali:

```cisco
enable
configure terminal

interface gigabitEthernet0/1
no switchport port-security
shutdown
no shutdown
exit

end
write memory
```

Si también se desea quitarlo del puerto de la VPC:

```cisco
configure terminal

interface gigabitEthernet0/2
no switchport port-security
shutdown
no shutdown
exit

end
write memory
```

Verificar:

```cisco
show port-security interface gigabitEthernet0/1
show ip dhcp snooping
```

---

## Verificación de la mitigación

Después de aplicar DHCP Snooping con Rate Limit o Port Security, ejecutar nuevamente el script desde Kali.

Resultado esperado:

* El puerto de Kali puede entrar en `err-disable`.
* El switch bloquea o limita el exceso de tráfico DHCP.
* La VPC puede seguir recibiendo DHCP legítimo desde R-1 después de limpiar el ataque.
* El router deja de entregar direcciones a clientes falsificados.
* El ataque queda mitigado desde la capa 2.

---

## Flujo recomendado para el video

1. Mostrar la topología en GNS3.
2. Mostrar nombre, matrícula, fecha y hora.
3. Mostrar direccionamiento IP del laboratorio.
4. Mostrar configuración DHCP legítima de R-1.
5. Confirmar que la VPC recibe DHCP desde R-1.
6. Mostrar tabla DHCP limpia en R-1.
7. Ejecutar `dhcp-starvation.py` desde Kali.
8. Mostrar en Kali las IPs obtenidas por clientes falsos.
9. Mostrar `show ip dhcp binding` en R-1 con múltiples leases falsos.
10. Intentar renovar DHCP en la VPC y mostrar el fallo.
11. Limpiar bindings y conflictos en R-1.
12. Aplicar DHCP Snooping en SW-1.
13. Ejecutar nuevamente el ataque.
14. Mostrar que `Gi0/1` cae por `dhcp-rate-limit`.
15. Levantar el puerto.
16. Aplicar Port Security como defensa adicional.
17. Ejecutar nuevamente el ataque.
18. Mostrar que `Gi0/1` cae por `psecure-violation`.
19. Cerrar con una conclusión técnica.

---

## Comandos útiles para grabación

### En R-1

```cisco
terminal length 0
show ip interface brief
show ip dhcp binding
show ip dhcp conflict
show running-config
clear ip dhcp binding *
clear ip dhcp conflict *
clear arp-cache
```

### En SW-1

```cisco
terminal length 0
show ip interface brief
show interfaces status
show ip dhcp snooping
show ip dhcp snooping binding
show port-security
show port-security interface gigabitEthernet0/1
show errdisable recovery
```

### En Kali

```bash
ip -br addr
sudo python3 dhcp-starvation.py
sudo tcpdump -eni eth0 "udp port 67 or udp port 68"
```

### En VPC

```text
dhcp
show ip
```

---

## Troubleshooting

### El script muestra `Sin OFFER`

Posibles causas:

* El router no tiene DHCP configurado.
* La interfaz incorrecta fue seleccionada en Kali.
* Kali no está en la misma red de capa 2.
* El DHCP del router tiene conflictos.
* El pool DHCP está mal configurado.
* El puerto de Kali está apagado por `err-disable`.

Validar conectividad:

```bash
ping -c 4 20.25.8.45
```

Capturar tráfico DHCP:

```bash
sudo tcpdump -eni eth0 "udp port 67 or udp port 68"
```

Verificar en R-1:

```cisco
show ip dhcp binding
show ip dhcp conflict
```

---

### La VPC no recibe DHCP antes del ataque

Si la VPC no recibe DHCP antes del ataque, el problema no está en el script. Primero se debe validar el servidor DHCP legítimo.

En R-1:

```cisco
show ip interface brief
show ip dhcp binding
show ip dhcp conflict
show running-config
```

En la VPC:

```text
dhcp
show ip
```

---

### El router marca conflictos DHCP

Si R-1 muestra mensajes como:

```text
DHCP address conflict
```

Limpiar conflictos:

```cisco
clear ip dhcp conflict *
clear arp-cache
```

También se puede desactivar el ping previo del DHCP para el laboratorio:

```cisco
configure terminal
ip dhcp ping packets 0
end
```

---

### El puerto Gi0/1 cae en err-disable

Si el puerto de Kali cae por DHCP Snooping o Port Security, detener primero el ataque:

```bash
sudo pkill -f dhcp-starvation
```

Luego levantar el puerto:

```cisco
configure terminal
interface gigabitEthernet0/1
shutdown
no shutdown
exit
end
```

---

### El switch no reconoce `interface e0`, `e1` o `e2`

En IOSvL2, las interfaces suelen llamarse:

```text
GigabitEthernet0/0
GigabitEthernet0/1
GigabitEthernet0/2
```

Verificar con:

```cisco
show ip interface brief
```

Luego usar el nombre completo de la interfaz:

```cisco
interface gigabitEthernet0/1
```

---

## Estructura recomendada del repositorio

```text
DHCP-Starvation-Attack/
├── README.md
├── dhcp-starvation.py
├── mitigacion-dhcp-starvation.md
├── captures/
│   ├── dhcp-before.png
│   ├── starvation-running.png
│   ├── dhcp-bindings-filled.png
│   ├── vpc-dhcp-fail.png
│   ├── snooping-rate-limit.png
│   ├── port-security-violation.png
│   └── mitigation-result.png
├── docs/
│   └── technical-report.md
└── video/
    └── youtube-link.txt
```

---

## Evidencias recomendadas

| Evidencia                     | Descripción                                           |
| ----------------------------- | ----------------------------------------------------- |
| `dhcp-before.png`             | VPC recibiendo DHCP legítimo desde R-1                |
| `starvation-running.png`      | Kali ejecutando el script y generando clientes falsos |
| `dhcp-bindings-filled.png`    | R-1 mostrando múltiples bindings DHCP falsificados    |
| `vpc-dhcp-fail.png`           | VPC fallando al solicitar DHCP después del ataque     |
| `snooping-rate-limit.png`     | Switch bloqueando Gi0/1 por `dhcp-rate-limit`         |
| `port-security-violation.png` | Switch bloqueando Gi0/1 por `psecure-violation`       |
| `mitigation-result.png`       | Verificación de que la mitigación controla el ataque  |

---

## Topics sugeridos para GitHub

```text
dhcp
dhcp-starvation
dhcp-snooping
kali-linux
python
scapy
gns3
iosvl2
network-security
cybersecurity
packet-crafting
lab
ethical-hacking
switch-security
port-security
```

---

## Conclusión

Este laboratorio demuestra cómo un atacante puede abusar del funcionamiento normal de DHCP para consumir direcciones IP disponibles en un servidor legítimo.

El ataque fue validado al observar múltiples leases DHCP asignados a MACs falsas y al comprobar que un cliente legítimo podía presentar fallos al intentar obtener dirección IP después del ataque.

La mitigación efectiva se aplicó desde el switch mediante **DHCP Snooping**, marcando como confiable únicamente el puerto conectado al servidor DHCP legítimo y limitando la cantidad de paquetes DHCP permitidos desde puertos no confiables. Además, se demostró el uso de **Port Security** para bloquear la generación masiva de direcciones MAC falsas desde el puerto del atacante.

En conjunto, DHCP Snooping, Rate Limit y Port Security permiten reducir significativamente el impacto de ataques DHCP Starvation en redes conmutadas.

Para más detalles, revisar el documento de mitigación:

* [`mitigacion-dhcp-starvation.md`](./mitigacion-dhcp-starvation.md)

---

## Autor

**Michael Robles / iClexi**
Laboratorio de Seguridad de Redes
Proyecto académico de ataque y mitigación DHCP Starvation
