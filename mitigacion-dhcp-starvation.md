# Mitigación DHCP Starvation Attack

## Aviso de uso responsable

Este documento fue desarrollado únicamente con fines educativos, académicos y de laboratorio controlado.

Las configuraciones presentadas deben aplicarse solamente en entornos propios o autorizados, como GNS3, EVE-NG, PNETLab o laboratorios internos de pruebas.

---

## Descripción de la mitigación

El ataque **DHCP Starvation** consiste en consumir las direcciones disponibles de un servidor DHCP mediante múltiples solicitudes generadas con direcciones MAC falsas.

Cuando el ataque es exitoso, el servidor DHCP asigna direcciones IP a clientes inexistentes. Como consecuencia, los clientes legítimos pueden quedarse sin dirección IP disponible y perder conectividad en la red.

Para mitigar este ataque se aplican controles de seguridad en el switch, principalmente:

* DHCP Snooping
* DHCP Snooping Rate Limit
* Port Security

En este laboratorio, el switch IOSvL2 se encarga de controlar el tráfico DHCP y limitar el abuso desde el puerto donde está conectada la máquina atacante.

---

## Topología del laboratorio

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

## Direccionamiento IP

| Dispositivo | Rol                     | Interfaz | Dirección IP  | Descripción                   |
| ----------- | ----------------------- | -------- | ------------- | ----------------------------- |
| R-1         | Gateway / DHCP legítimo | Fa0/0    | 20.25.8.45/24 | Servidor DHCP autorizado      |
| Kali        | Atacante                | eth0     | 20.25.8.46/24 | Máquina que ejecuta el ataque |
| VPC         | Cliente legítimo        | eth0     | DHCP          | Equipo víctima de la prueba   |
| SW-1        | Switch                  | Gi0/0    | N/A           | Puerto hacia R-1              |
| SW-1        | Switch                  | Gi0/1    | N/A           | Puerto hacia Kali             |
| SW-1        | Switch                  | Gi0/2    | N/A           | Puerto hacia VPC              |

---

## Objetivo de la mitigación

El objetivo de la mitigación es impedir que un atacante conectado a un puerto de acceso pueda consumir de forma masiva el pool DHCP del servidor legítimo.

La defensa busca lograr lo siguiente:

* Permitir que R-1 actúe como servidor DHCP legítimo.
* Bloquear servidores DHCP falsos en puertos no confiables.
* Limitar la cantidad de paquetes DHCP permitidos desde el puerto del atacante.
* Evitar que un solo puerto genere muchas direcciones MAC falsas.
* Mantener disponible el servicio DHCP para clientes legítimos.

---

## Concepto de DHCP Snooping

**DHCP Snooping** es una función de seguridad de capa 2 que permite al switch diferenciar entre puertos confiables y no confiables.

Un puerto confiable puede enviar respuestas de servidor DHCP, como:

```text
DHCP Offer
DHCP ACK
DHCP NAK
```

Un puerto no confiable puede enviar solicitudes normales de cliente, como:

```text
DHCP Discover
DHCP Request
```

Pero no puede actuar como servidor DHCP.

En esta topología, el único puerto confiable debe ser el puerto conectado al router R-1, porque R-1 es el servidor DHCP legítimo.

```text
Gi0/0 = Puerto confiable hacia R-1
Gi0/1 = Puerto no confiable hacia Kali
Gi0/2 = Puerto no confiable hacia VPC
```

---

## Configuración de DHCP Snooping

En SW-1:

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

---

## Explicación de la configuración

### Activar DHCP Snooping globalmente

```cisco
ip dhcp snooping
```

Activa la función DHCP Snooping en el switch.

### Activar DHCP Snooping en la VLAN 1

```cisco
ip dhcp snooping vlan 1
```

Aplica DHCP Snooping sobre la VLAN usada por la topología.

### Desactivar Option 82

```cisco
no ip dhcp snooping information option
```

Evita que el switch agregue información adicional DHCP que algunos routers o laboratorios virtuales pueden no procesar correctamente.

### Marcar el puerto hacia R-1 como confiable

```cisco
interface gigabitEthernet0/0
ip dhcp snooping trust
```

Permite que R-1 envíe respuestas DHCP legítimas.

### Limitar el puerto hacia Kali

```cisco
interface gigabitEthernet0/1
ip dhcp snooping limit rate 5
```

Limita la cantidad de paquetes DHCP permitidos por segundo desde el puerto de Kali.

Si Kali genera demasiados paquetes DHCP, el switch puede colocar el puerto en estado `err-disable`.

### Limitar el puerto hacia la VPC

```cisco
interface gigabitEthernet0/2
ip dhcp snooping limit rate 5
```

Protege también el puerto de usuario, manteniendo una política uniforme sobre puertos no confiables.

---

## Verificación de DHCP Snooping

Después de aplicar la configuración, verificar el estado de DHCP Snooping:

```cisco
show ip dhcp snooping
```

También se puede revisar la tabla de bindings DHCP aprendidos:

```cisco
show ip dhcp snooping binding
```

Verificar el estado de las interfaces:

```cisco
show interfaces status
```

Verificar si algún puerto cayó en `err-disable`:

```cisco
show errdisable recovery
```

---

## Evidencia esperada con DHCP Snooping Rate Limit

Al ejecutar nuevamente el ataque DHCP Starvation desde Kali, el switch debe detectar que el puerto `Gi0/1` está superando el límite de paquetes DHCP permitido.

Ejemplo de salida esperada:

```text
%DHCP_SNOOPING-4-DHCP_SNOOPING_ERRDISABLE_WARNING: DHCP Snooping received 5 DHCP packets on interface Gi0/1
%DHCP_SNOOPING-4-DHCP_SNOOPING_RATE_LIMIT_EXCEEDED: The interface Gi0/1 is receiving more than the threshold set
%PM-4-ERR_DISABLE: dhcp-rate-limit error detected on Gi0/1, putting Gi0/1 in err-disable state
```

Esto confirma que DHCP Snooping detectó exceso de tráfico DHCP desde Kali y bloqueó el puerto atacante.

---

## Levantar el puerto después del bloqueo

Si el puerto de Kali cae en `err-disable`, primero se debe detener el ataque en Kali:

```bash
sudo pkill -f dhcp-starvation
```

Luego, en SW-1:

```cisco
configure terminal
interface gigabitEthernet0/1
shutdown
no shutdown
exit
end
```

Verificar que el puerto volvió a subir:

```cisco
show interfaces status
```

---

## Recuperación automática del puerto

Opcionalmente, se puede configurar recuperación automática para puertos bloqueados por DHCP Rate Limit.

```cisco
configure terminal
errdisable recovery cause dhcp-rate-limit
errdisable recovery interval 30
end
write memory
```

Con esta configuración, si el puerto cae por exceso de paquetes DHCP, el switch intentará recuperarlo automáticamente después de 30 segundos.

Verificar la recuperación automática:

```cisco
show errdisable recovery
```

---

## Mitigación adicional con Port Security

Aunque DHCP Snooping con Rate Limit puede detener el ataque, una defensa adicional muy efectiva es **Port Security**.

DHCP Starvation normalmente genera múltiples direcciones MAC falsas desde un mismo puerto. Port Security permite limitar cuántas MAC pueden aparecer en ese puerto.

En el puerto de Kali:

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

Con esta configuración, el switch permite solo una dirección MAC en el puerto de Kali.

Si Kali intenta generar múltiples MAC falsas, el puerto entra en violación de seguridad y se apaga.

---

## Evidencia esperada con Port Security

Al ejecutar el ataque con Port Security activo, el switch puede mostrar:

```text
%PM-4-ERR_DISABLE: psecure-violation error detected on Gi0/1, putting Gi0/1 in err-disable state
%PORT_SECURITY-2-PSECURE_VIOLATION: Security violation occurred, caused by MAC address 02e8.79d2.d520 on port GigabitEthernet0/1.
```

Esto confirma que Port Security detectó múltiples MAC falsas desde el puerto de Kali.

---

## Verificación de Port Security

```cisco
show port-security
show port-security interface gigabitEthernet0/1
show port-security address
show interfaces status
```

---

## Levantar puerto después de Port Security

Primero detener el ataque en Kali:

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

## Quitar Port Security para probar solo DHCP Snooping

Si se desea probar únicamente DHCP Snooping con Rate Limit, se puede retirar Port Security del puerto de Kali.

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

Verificar que Port Security ya no esté activo:

```cisco
show port-security interface gigabitEthernet0/1
```

Verificar que DHCP Snooping siga activo:

```cisco
show ip dhcp snooping
```

---

## Limpieza del DHCP en R-1

Después de realizar pruebas de ataque, se recomienda limpiar bindings y conflictos DHCP en R-1.

```cisco
enable
clear ip dhcp binding *
clear ip dhcp conflict *
clear arp-cache
```

Verificar:

```cisco
show ip dhcp binding
show ip dhcp conflict
```

Si el servicio DHCP queda ocupado, se puede reiniciar de forma controlada:

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

## Prueba antes de la mitigación

Antes de aplicar la mitigación, el ataque puede generar múltiples leases falsos en R-1.

En Kali:

```bash
sudo python3 dhcp-starvation.py
```

En R-1:

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

En la VPC:

```text
dhcp
show ip
```

La VPC puede fallar al solicitar IP si el pool fue consumido o el servicio DHCP quedó afectado.

---

## Prueba después de la mitigación

Después de aplicar DHCP Snooping con Rate Limit, se ejecuta nuevamente el ataque.

Resultado esperado:

* El switch detecta exceso de paquetes DHCP en `Gi0/1`.
* El puerto de Kali cae por `dhcp-rate-limit`.
* El ataque se detiene desde la capa 2.
* R-1 deja de recibir solicitudes DHCP masivas desde Kali.
* La red queda protegida contra el consumo masivo del pool DHCP.

Con Port Security activo, el resultado esperado es:

* El switch detecta múltiples MAC falsas desde `Gi0/1`.
* El puerto cae por `psecure-violation`.
* El ataque queda bloqueado antes de consumir el pool DHCP.

---

## Comandos útiles de verificación

### En SW-1

```cisco
terminal length 0
show ip interface brief
show interfaces status
show ip dhcp snooping
show ip dhcp snooping binding
show errdisable recovery
show port-security
show port-security interface gigabitEthernet0/1
show port-security address
```

### En R-1

```cisco
terminal length 0
show ip interface brief
show ip dhcp binding
show ip dhcp conflict
show running-config
```

### En Kali

```bash
ip -br addr
sudo tcpdump -eni eth0 "udp port 67 or udp port 68"
sudo python3 dhcp-starvation.py
```

### En VPC

```text
dhcp
show ip
```

---

## Troubleshooting

### El switch no reconoce `interface e0`, `e1` o `e2`

En IOSvL2, las interfaces suelen llamarse:

```text
GigabitEthernet0/0
GigabitEthernet0/1
GigabitEthernet0/2
```

Verificar interfaces:

```cisco
show ip interface brief
```

Usar el nombre completo de la interfaz:

```cisco
interface gigabitEthernet0/1
```

---

### La VPC no recibe DHCP después de limpiar

Verificar que R-1 tenga DHCP activo:

```cisco
show running-config
```

Limpiar bindings y conflictos:

```cisco
clear ip dhcp binding *
clear ip dhcp conflict *
clear arp-cache
```

En la VPC:

```text
dhcp
show ip
```

---

### El puerto Gi0/1 está en err-disable

Verificar:

```cisco
show interfaces status
```

Detener el ataque en Kali:

```bash
sudo pkill -f dhcp-starvation
```

Levantar el puerto:

```cisco
configure terminal
interface gigabitEthernet0/1
shutdown
no shutdown
exit
end
```

---

### DHCP Snooping bloquea demasiado rápido

Si el laboratorio necesita mostrar más tráfico antes de bloquear el puerto, aumentar el límite:

```cisco
configure terminal
interface gigabitEthernet0/1
ip dhcp snooping limit rate 15
exit
end
```

Para una protección más estricta, mantener:

```cisco
ip dhcp snooping limit rate 5
```

---

## Recomendaciones finales

Para una red real o un laboratorio más completo, se recomienda:

* Activar DHCP Snooping en las VLANs de usuarios.
* Marcar como trusted únicamente los puertos hacia servidores DHCP legítimos.
* Aplicar Rate Limit en puertos de usuarios.
* Usar Port Security en puertos de acceso.
* Monitorear eventos de `dhcp-rate-limit`.
* Documentar qué puertos son confiables.
* Evitar conectar servidores DHCP no autorizados.
* Mantener una política clara de seguridad de capa 2.

---

## Conclusión

El ataque DHCP Starvation puede afectar gravemente la disponibilidad de una red local al consumir las direcciones IP disponibles del servidor DHCP legítimo.

La mitigación efectiva se logra aplicando controles de capa 2 en el switch. En este laboratorio, **DHCP Snooping con Rate Limit** permitió detectar y bloquear el exceso de paquetes DHCP provenientes del puerto de Kali. Además, **Port Security** demostró ser una defensa adicional eficaz al bloquear múltiples direcciones MAC falsas generadas desde el mismo puerto.

Estas medidas reducen significativamente el impacto del ataque y ayudan a proteger el servicio DHCP para que los clientes legítimos puedan seguir obteniendo configuración de red de forma segura.

---

## Autor

**Michael Robles / iClexi**
Laboratorio de Seguridad de Redes
Proyecto académico de mitigación DHCP Starvation
