# Set Up A Raspberry Pi for monitoring Renogy BT-1 devices.

## Hardware

Any capable Raspberry Pi setup should work, as long as it has bluetooth. I'm using the following because that's what I had/was available at the time. I'd recommend something more compact with integrated wifi and bt. But in this economy, you gotta deal with what is available!

### Raspberry Pi
- Raspberry Pi Compute Module 4, 8GB Lite - CM4008000
- Raspberry Pi Compute Module CM4IO Board
- 64gb microSD card
- USB to DC Barrel Jack Power Cable 5.5 x 2.1 mm 5V
- BrosTrend AC650 Dual Band WiFi
- Bluetooth CSR 4.0 Dongle Plug & Play

### Renogy Solar Equipment
- Renogy Adventurer Solar Charge Controller
- Renogy BT-1 Bluetooth Module
- 2x 100 watt solar panels
- 12v 100ah lead acid deep cycle battery

## Setup

1. Download Raspberry Pi OS: https://www.raspberrypi.com/software/
2. Install onto SD Card.
3. Using the USB to DC Barrel Jack Power Cable for power, start up Raspberry Pi. This is the bare min power, but the idea is to have it run off the usb port on the front of the Adventurer.
4. Plug in a monitor, keyboard/mouse, and ethernet.
5. Install the WiFi driver: https://cdn.shopify.com/s/files/1/0270/1023/6487/files/AC1L_AC3L_AC5L_Linux_Manual_BrosTrend_WiFi_Adapter_v8.pdf?v=1671154201
6. Enable SSH and VNC:
    ```
   sudo raspi-config
    ```
   - Interface Options -> Enable SSH
   - Interface Options -> Enable VNC
   - System Options -> Hostname
7. Reboot and sign in to VNC.
8. At this point the Pi should be accessible via VNC. Unplug the ethernet, keyboard, and mouse, after confirming remote access.
9. Plug in the BT dongle. It should be plug and play.
10. Update the system:
    ```
    sudo apt-get update
    sudo apt-get upgrade
    ```
11. The Raspberry Pi should be ready for use.