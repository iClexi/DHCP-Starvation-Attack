# DHCP Starvation Attack – Guía How-to

## Información del proyecto

- **Autor:** Michael David Robles Fermín
- **Matrícula:** 2025-0845
- **Asignatura:** Seguridad de Redes
- **Repositorio:** https://github.com/iClexi/DHCP-Starvation-Attack
- **Video:** https://youtu.be/_hAUU0W4hLw?si=vcRpOVleFQxaPitr
- **Documentación técnica profesional:** `docs/documentacion-tecnica-profesional.docx`

## Aviso de uso responsable

Este proyecto fue desarrollado únicamente con fines educativos, académicos y de laboratorio controlado. Las pruebas deben ejecutarse solamente en entornos propios o autorizados.

## Objetivo del laboratorio

Demostrar cómo un atacante puede agotar el pool de direcciones IP de un servidor DHCP legítimo mediante el envío masivo de solicitudes DHCP usando múltiples direcciones MAC falsas. Luego se aplica una contramedida basada en **DHCP Snooping**, **rate limit** y **Port Security** para bloquear el ataque y restaurar el servicio legítimo.

## Topología de laboratorio

![Topología del laboratorio](images/topology.png)

## Flujo del laboratorio

### 1. Ejecución del ataque

Se ejecuta el script desde Kali Linux:

```bash
sudo python3 dhcp-starvation.py
```

![Ejecución del script](images/script_execution.png)

### 2. Evidencia de agotamiento del pool DHCP

Mientras el ataque está activo, el router R-1 muestra múltiples asignaciones DHCP dinámicas falsas:

```cisco
show ip dhcp binding
```

![Pool DHCP lleno en R-1](images/dhcp_binding_full_r1.png)

### 3. Impacto en la víctima

La VPC intenta solicitar una dirección IP por DHCP, pero falla porque el pool quedó agotado:

```text
dhcp
```

![Fallo de DHCP en VPC1](images/pc1_dhcp_failed.png)

### 4. Aplicación de la contramedida

En el switch SW-1 se habilita DHCP Snooping de forma global y en la VLAN 1. Además, se configura el puerto hacia Kali como no confiable, se limita la tasa de mensajes DHCP y se habilita Port Security.

![Configuración de la contramedida](images/mitigation_switch.png)

### 5. Limpieza de bindings en el router

Para restaurar el servicio, se limpian los bindings y conflictos DHCP, además de la caché ARP:

```cisco
clear ip dhcp binding *
clear ip dhcp conflict *
clear arp-cache
```

![Limpieza en R-1](images/cleanup_r1.png)

### 6. Reintento del ataque después de la mitigación

Cuando se vuelve a ejecutar el ataque, el script ya no recibe ofertas DHCP, lo que indica que la protección está funcionando.

![Ataque sin OFFER](images/script_no_offer_after_mitigation.png)

### 7. Verificación final del servicio

Finalmente, la VPC vuelve a obtener una dirección IP legítima del router R-1:

![DHCP funcional en VPC1](images/pc1_dhcp_success_after_mitigation.png)

## Contramedida aplicada

La defensa utilizada en este laboratorio combina:

- **DHCP Snooping**: valida qué puertos pueden enviar respuestas DHCP.
- **ip dhcp snooping limit rate**: limita la velocidad de solicitudes DHCP en puertos no confiables.
- **Port Security**: evita que el atacante utilice múltiples direcciones MAC falsas desde un mismo puerto.

## Enlaces directos

- **Repositorio:** https://github.com/iClexi/DHCP-Starvation-Attack
- **Video:** https://youtu.be/_hAUU0W4hLw?si=vcRpOVleFQxaPitr
- **Documentación técnica profesional:** `docs/documentacion-tecnica-profesional.docx`
