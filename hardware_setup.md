# Set Up A Raspberry Pi for monitoring Renogy BT-1 devices.

## Hardware

Any capable Raspberry Pi setup should work, as long as it has bluetooth. I'm using the following because that's what I had available at the time. I'd recommend something more compact with integrated wifi and bt. But in this economy, you gotta deal with what is available!

### Raspberry Pi
- Raspberry Pi Compute Module 4, 8GB Lite - CM4008000
- Raspberry Pi Compute Module CM4IO Board
- 64gb microSD card
- USB to DC Barrel Jack Power Cable 5.5 x 2.1 mm 5V
- BrosTrend AC650 Dual Band WiFi [installation guide](https://cdn.shopify.com/s/files/1/0270/1023/6487/files/AC1L_AC3L_AC5L_Linux_Manual_BrosTrend_WiFi_Adapter_v8.pdf?v=1671154201)
- Kinivo BTD400 Bluetooth Low Energy USB Adapter [installation guide](https://community.kinivo.com/t/how-to-raspberry-pi-setup/173)
- 7inch HDMI LCD (H) Display (with case), 1024x600, IPS [installation guide](https://www.waveshare.com/wiki/7inch_HDMI_LCD_(H)_(with_case))

### Renogy Solar Equipment
- Renogy Adventurer Solar Charge Controller
- Renogy BT-1 Bluetooth Module
- 2x 100 watt solar panels

### Battery Monitor
- Junctek Battery Monitor KH140F [user manual](http://68.168.132.244/KG-F_EN_manual.pdf)

### Battery
- 12v 100ah lead acid deep cycle battery

## Raspberry Pi Setup

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
      - Set a familiar name that you can then reference on your local network (i.e. solar-monitor)
      - Once this is set up, you can reference your device with a url like http://solar-monitor.local instead of its IP address-
7. Reboot.

## SSH Setup

1. At this point the Pi should be accessible via VNC/SSH/etc. Unplug the ethernet, keyboard, and mouse, after confirming remote access.
2. First check if you already have an SSH key on your local machine (not the Pi).
3. This is typically located at ```~/.ssh/id_ed25519.pub``` on macOS / Linux, and the .ssh directory in your user profile folder on Windows (for example ```C:\Users\your-user\.ssh\id_ed25519.pub```).
4. If you don't have a key, run this on your local machine: ```ssh-keygen -t rsa -b 4096```
5. Connect to Pi via Mac (don't forget to update ssh username and hostname). Open Terminal and type:
   ```
   export USER_AT_HOST="username@solar-monitor"
   export PUBKEYPATH="$HOME/.ssh/id_ed25519.pub"
   ssh-copy-id -i "$PUBKEYPATH" "$USER_AT_HOST"
   ```
6. Connect to Pi via PC (don't forget to update ssh username and hostname). Open Powershell and type:
   ```powershell
   $USER_AT_HOST="username@solar-monitor"
   $PUBKEYPATH="$HOME\.ssh\id_ed25519.pub"
   $pubKey=(Get-Content "$PUBKEYPATH" | Out-String); ssh "$USER_AT_HOST" "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '${pubKey}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
   ```
7. Now test the connection: ```ssh username@solar-monitor.local```. If it worked you shouldn't need a password.
8. More info on setting up key based auth: https://code.visualstudio.com/docs/remote/troubleshooting#_configuring-key-based-authentication
9. More info on setting up vscode: https://code.visualstudio.com/docs/remote/ssh

## BT Setup

1. Plug in the BT dongle.
2. Install:
```
sudo apt-get install --no-install-recommends bluetooth
sudo apt-get install --no-install-recommends bluez-utils
sudo apt-get install --no-install-recommends blueman
sudo apt-get install --no-install-recommends bluez
```
3. If you need audio support:
```
sudo apt-get install pulseaudio pavucontrol pulseaudio-module-bluetooth
```
4. Open /etc/systemd/system/bluetooth.target.wants/bluetooth.service:
```
sudo nano /etc/systemd/system/bluetooth.target.wants/bluetooth.service
```
5. Change:
```
ExecStart=/usr/lib/bluetooth/bluetoothd
```
To:
```
ExecStart=/usr/lib/bluetooth/bluetoothd --noplugin=sap
```
6. Reload the systemd:
```
sudo systemctl daemon-reload
```
7. Restart the bluetooth:
```
sudo service bluetooth restart
```
8. Get the bluetooth status:
```
sudo service bluetooth status
```
You should see something like this:
   ```
   ● bluetooth.service - Bluetooth service
     Loaded: loaded (/lib/systemd/system/bluetooth.service; enabled; vendor preset: enabled)
     Active: active (running) since Tue 2023-02-28 11:54:33 CST; 50s ago
       Docs: man:bluetoothd(8)
   Main PID: 16463 (bluetoothd)
     Status: "Running"
      Tasks: 1 (limit: 4915)
        CPU: 194ms
     CGroup: /system.slice/bluetooth.service
             └─16463 /usr/libexec/bluetooth/bluetoothd --noplugin=sap

Feb 28 11:54:33 solar-monitor systemd[1]: Stopped Bluetooth service.
Feb 28 11:54:33 solar-monitor systemd[1]: bluetooth.service: Consumed 10.381s CPU time.
Feb 28 11:54:33 solar-monitor systemd[1]: Starting Bluetooth service...
Feb 28 11:54:33 solar-monitor systemd[1]: Started Bluetooth service.
Feb 28 11:54:33 solar-monitor bluetoothd[16463]: Bluetooth daemon 5.55
Feb 28 11:54:33 solar-monitor bluetoothd[16463]: Starting SDP server
Feb 28 11:54:33 solar-monitor bluetoothd[16463]: Excluding (cli) sap
Feb 28 11:54:33 solar-monitor bluetoothd[16463]: Bluetooth management interface 1.21 initialized
Feb 28 11:54:33 solar-monitor bluetoothd[16463]: Endpoint registered: sender=:1.104 path=/MediaEndpoint/A2DPSink/sbc
Feb 28 11:54:33 solar-monitor bluetoothd[16463]: Endpoint registered: sender=:1.104 path=/MediaEndpoint/A2DPSource/sbc
   ```
9. Test BT dongle is able to discover. Devices should start displaying if everything went well.
```
sudo bluetoothctl
scan on
```
10. The Raspberry Pi should be ready for use.

## LCD Setup

1. Follow the [installation instructions](https://www.waveshare.com/wiki/7inch_HDMI_LCD_(H)_(with_case)) but please note there is an error in the text that is to be added to config.txt
2. Edit the /boot/config.txt file:
```
cd /boot
sudo nano config.txt
```
3. Add the following to the end of the file and save:
```
hdmi_force_hotplug=1
config_hdmi_boost=10
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 6 0 0 0
```
4. Reboot:
```
sudo shutdown -r now
```
5. Plug in HDMI and USB cable.