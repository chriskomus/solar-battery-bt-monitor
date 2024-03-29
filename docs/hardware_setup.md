# Set Up A Raspberry Pi for monitoring Renogy BT-1 devices.

## Hardware

Any capable Raspberry Pi setup should work, as long as it has bluetooth. I'm using the following because that's what I had available at the time. I'd recommend something more compact with integrated wifi and bt. But in this economy, you gotta deal with what is available!

### Raspberry Pi
- Raspberry Pi Compute Module 4, 8GB Lite - CM4008000
- Raspberry Pi Compute Module CM4IO Board
- 64gb microSD card
- 12V DC 5.5mm x 2.1mm Barrel Jack Power Cable
- BrosTrend AC650 Dual Band WiFi [installation guide](https://cdn.shopify.com/s/files/1/0270/1023/6487/files/AC1L_AC3L_AC5L_Linux_Manual_BrosTrend_WiFi_Adapter_v8.pdf?v=1671154201)
- Kinivo BTD400 Bluetooth Low Energy USB Adapter [installation guide](https://community.kinivo.com/t/how-to-raspberry-pi-setup/173)
- RTC Real Time Clock, DS3231 Clock Memory Module [installation guide](https://thepihut.com/blogs/raspberry-pi-tutorials/17209332-adding-a-real-time-clock-to-your-raspberry-pi)
- 7inch HDMI LCD (H) Display (with case), 1024x600, IPS [installation guide](https://www.waveshare.com/wiki/7inch_HDMI_LCD_(H)_(with_case))

### Renogy Solar Charge Controller and Panels
- Renogy Adventurer Solar Charge Controller
- Renogy BT-1 Bluetooth Module
- 2x 100 watt solar panels

### Battery Monitor
- Junctek Battery Monitor KH140F [user manual](http://68.168.132.244/KG-F_EN_manual.pdf)

### Battery
- PowerQueen 12.8v 100ah LifePo4 battery

# Raspberry Pi Setup

## Powering the Pi

Insufficient power will cause low voltage warnings and lots of problems. I wanted to power it off the front USB port on the Renogy Solar Charge Controller but I kept getting low voltage warnings, so I ended up using a 12v DC barrel jack (**IMPORTANT:** The Raspberry Pi CM4 Board accepts 12v DC, most other Pis only accept 5v) and powering right from the 12v DC source.

YMMV on how well powering off the solar charge controller's usb works depending on controller and power cable. The best solution is to use officially supported power supplies that supply 5.1v.

## Getting Started

1. Download Raspberry Pi OS: https://www.raspberrypi.com/software/
2. Install onto SD Card. Install with wifi/ssh settings specified before installing, or use a monitor/keyboard/mouse/ethernet to get started.
5. Install the WiFi driver: https://cdn.shopify.com/s/files/1/0270/1023/6487/files/AC1L_AC3L_AC5L_Linux_Manual_BrosTrend_WiFi_Adapter_v8.pdf?v=1671154201
6. Enable SSH, VNC, and Hostname:
    ```
    sudo raspi-config
    ```
   - Interface Options -> Enable SSH
   - Interface Options -> Enable VNC
   - System Options -> Hostname
      - Set hostname to solar-monitor
      - Once this is set up, you can reference your device with a url like http://solar-monitor.local instead of its IP address
7. Update the system software:
    ```
    sudo apt-get update
    sudo apt-get upgrade
    ```
8. Reboot.
    ```
    sudo shutdown -r now
    ```

## SSH Setup

### Part 1
1. At this point the Pi should be accessible via VNC/SSH/etc:
```
ssh username@solar-monitor.local
```
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

### Part 2 - Setting up VSCode
8. More info on setting up key based auth: https://code.visualstudio.com/docs/remote/troubleshooting#_configuring-key-based-authentication
9. More info on setting up vscode: https://code.visualstudio.com/docs/remote/ssh

### Part 3 - Add Key to Github
10. Create new SSH Key
```
cd ~/.ssh
ssh-keygen -t rsa -C "youremail@address.com"
```
11. Accept the default options.
12. Copy the contents of the file
```
sudo nano ~/.ssh/id_rsa.pub
```
13. Goto https://github.com/settings/keys and create new SSH key
14. You should get a success message if everything worked:
```
ssh -T git@github.com
```

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
sudo nano /boot/config.txt
```
3. Add the following to the end of the file and save:
#### Raspberry Pi 4:
```
hdmi_group:1=2
hdmi_mode:1=87
hdmi_cvt:1 1024 600 60 6 0 0 0
```

#### Raspberry Pi 3:
```
hdmi_force_hotplug=1
config_hdmi_boost=10
hdmi_group=2
hdmi_mode=87
hdmi_cvt 1024 600 60 6 0 0 0
```
4. Reboot:
```
sudo shutdown -r now
```
5. Plug in HDMI and USB cable.

## RTC Setup

This is only required if the Pi won't have internet access. The Pi gets the current datetime from the internet when it boots up, if there's no internet, the time will be incorrect and the logged data will be inaccurate.

1. Edit the /boot/config.txt file:
```bash
sudo nano /boot/config.txt
```
2. Add the following to the end of the file and save:
```bash
dtparam=i2c_arm=on
```
3. Shutdown:
```bash
sudo shutdown -h now
```
4. Install the RTC on Pins 1 thru 5.
5. Start up the Pi and run this command to check that it is installed, You should see ID #68:
```bash
sudo i2cdetect -y 1
```
6. The RTC module must be loaded by the kernel by running:
```bash
sudo modprobe rtc-ds1307
```
7. Now you need to be running as the super user; type in:
```bash
sudo bash
```
8. Setup new device:
```bash
echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device
```
9. Exit bash:
```bash
exit
```
10. Check the time on the RTC, if its the first time being used it should show Jan 1 2000:
```bash
sudo hwclock -r
```
11. Set the current datetime:
```bash
sudo date -s '2023-05-31 20:20:20 PM'
```
12. Write the time to the RTC:
```bash
sudo hwclock -w
```
13. Verify that the time has been written:
```bash
sudo hwclock -r
```
14. Add the RTC kernel module to the file `/etc/modules` so it is loaded when the Raspberry Pi boots.
```bash
sudo nano /etc/modules
```
15. Add to the end of the file:
```bash
rtc-ds1307
```
16. add the DS1307 device creation at boot by editing `/etc/rc.local`
```bash
sudo nano /etc/rc.local
```
17. Add just before the `exit 0` line at the end of the file:
```bash
echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device
sudo hwclock -s
date
```
18. Save and reboot. The time should be cvorrect even without internet.