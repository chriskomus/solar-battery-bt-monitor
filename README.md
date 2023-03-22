# Solar Panel and Battery Bluetooth Monitor

## For Monitoring Renogy BT-1 Devices

Python app to read data from Renogy solar Charge Controllers using the [BT-1](https://www.renogy.com/bt-1-bluetooth-module-new-version/) bluetooth adapter. Tested with a **Rover 40A Charge Controller** and **Adventurer 30A Charge Controller**. May also work with Renogy **Wanderer** series charge controllers.  My setup uses a **Raspberry Pi Compute Module 4 with the Compute Module 4 IO Board**. It might also work with other  "SRNE like" devices like Rich Solar, PowMr, WEIZE etc.

This setup uses prometheus for logging data and leverages grafana to create a real-time dashboard for monitoring the performance of your system.



# Setup

## Getting Started

1. Set up a Raspberry Pi with wifi/bluetooth that can be powered by usb. For this project I am using a Raspberry Pi Compute Module 4 with the Compute Module 4 IO Board. I'm powering it using a 5v USB to Barrel Jack, so that I can power it off the front of the Renogy Solar Charge Controller. YMMV on how well that works depending on your charge controller and Pi power consumption.
2. [See the hardware instructions specific to that build.](hardware_setup.md)
3. Enable SSH, VNC, and Hostname:
    ```
    sudo raspi-config
    ```
   - Interface Options -> Enable SSH
   - Interface Options -> Enable VNC
   - System Options -> Hostname
      - Set a familiar name that you can then reference on your local network (i.e. solar-monitor)
      - Once this is set up, you can reference your device with a url like http://solar-monitor.local instead of its IP address
4. Update the system software:
    ```
    sudo apt-get update
    sudo apt-get upgrade
    ```

## Install Project

1. Install this project on your Raspberry Pi - https://github.com/chriskomus/solar-battery-bt-monitor.git
    ```
    cd ~/
    git clone https://github.com/chriskomus/solar-battery-bt-monitor.git
    cd solar-battery-bt-monitor
    cp solar-battery-bt-monitor.ini.dist solar-battery-bt-monitor.ini
    ```


## Install Prometheus

1. Check the [prometheus website](https://prometheus.io/download/) for the latest version of their application.  The URL below may link to older versions.
    ```
    cd ~/
    wget https://github.com/prometheus/prometheus/releases/download/v2.42.0/prometheus-2.42.0.linux-armv7.tar.gz
    tar xfz prometheus-2.42.0.linux-armv7.tar.gz
    rm prometheus-2.42.0.linux-armv7.tar.gz
    mv prometheus-2.42.0.linux-armv7/ prometheus/
    ```
2. Copy the file in this project (`prometheus\prometheus.yml`) into the prometheus install folder (`~/prometheus/prometheus.yml`), overwriting the existing file:
   ```
   cp ~/solar-battery-bt-monitor/prometheus/prometheus.yml ~/prometheus/prometheus.yml
   ```

3. Create the prometheus.service file in /etc/systemd/system/prometheus.service
   ```
   sudo nano /etc/systemd/system/prometheus.service
   ```
   Paste the following and save. Change the User and the file paths to your username and the correct filepaths.
   ```
   [Unit]
   Description=Prometheus Server
   Documentation=https://prometheus.io/docs/introduction/overview/
   After=network-online.target

   [Service]
   User=pi
   Restart=on-failure

   #Change this line if Prometheus is somewhere different
   ExecStart=/home/pi/prometheus/prometheus \
   --config.file=/home/pi/prometheus/prometheus.yml \
   --storage.tsdb.path=/home/pi/prometheus/data

   [Install]
   WantedBy=multi-user.target
   ```
4. Setup the Prometheus Service
    ```
    sudo systemctl daemon-reload
    sudo systemctl start prometheus
    sudo systemctl status prometheus
    sudo systemctl enable prometheus
    ```

5. Verify Prometheus is running (modify the address below with the IP address of your Raspberry Pi)
   - http://192.168.0.XXX:9090 or http://solar-monitor.local:9090 if you set up the hostname

## Install Grafana

1. Check the [Grafana web site](https://grafana.com/grafana/download) for the latest version of their application.  The URL below may link to older versions.
   ```
   cd ~/
   wget https://dl.grafana.com/enterprise/release/grafana-enterprise-9.3.6.linux-armv7.tar.gz
   tar -zxvf grafana-enterprise-9.3.6.linux-armv7.tar.gz
   rm grafana-enterprise-9.3.6.linux-armv7.tar.gz
   mv grafana-9.3.6/ grafana/
   ```
2. Create the grafana.service file in /etc/systemd/system/grafana.service
   ```
   sudo nano /etc/systemd/system/grafana.service
   ```
   Paste the following and save. Change the User and the file paths to your username and the correct filepaths.
   ```
   [Unit]
   Description=Grafana Server
   After=network.target

   [Service]
   Type=simple
   User=pi
   ExecStart=/home/pi/grafana/bin/grafana-server
   WorkingDirectory=/home/pi/grafana/
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```
3. Set Up the Grafana Service
    ```
    sudo systemctl daemon-reload
    sudo systemctl start grafana
    sudo systemctl status grafana
    sudo systemctl enable grafana
    ```
4. After grafana is installed, go to http://192.168.0.36:3000 or http://solar-monitor.local:3000/
   - Default log in is username: admin, password: admin
   - You'll be prompted to create a unique password for your installation

## Setup Project

1. Install the GATT library
    ```
    pip install gatt
    ```
2. Install the prometheus-client library
    ```
    pip install prometheus-client
    ```
3. Install libscrc. I had to build libscrc because it's not installable with pip3
    ```
    git clone https://github.com/hex-in/libscrc
    cd libscrc/
    python3 setup.py build
    sudo python3 setup.py install
    ```
4. Now you'll need to edit the solar-battery-bt-monitor.ini with the specifics of your setup. You need to get the MAC address of your particular BT-1 device.
   - You can use a BLE scanner app like:
      - [BLE Scanner (Apple App Store)](https://apps.apple.com/us/app/ble-scanner-4-0/id1221763603)
      - [BLE Scanner (Google Play)](https://play.google.com/store/apps/details?id=com.macdom.ble.blescanner)
   - OR you can use:
   ```
   sudo bluetoothctl
   scan on
   ```
5. Look for devics with alias `BT-TH-XXXX..`.  If the device doesn't show up in the scanner, make sure you force quit any of the Renogy apps that might be connected to your BT-1. If you are using BLE Scanner, connect to the BT-TH device and get the MAC address from the bytes in the Advertisement Data section: {length = 6, bytes = 0x806fb0000000}

6. Edit solar-battery-bt-monitor.ini file with the device name and MAC address.
7. It's time to test it out:
    ```
    cd ~/solar-battery-bt-monitor
    python3 solar-battery-bt-monitor.py
    ```
8. The script will attempt to connect to your BT-1.  Often times, the bluetooth libraries will immediately disconnect. This script is set up by default to reconnect if that happens. Usually after a handful of reconnect attempts, the application will connect and you'll see the values output on the console.

9. The script by default logs the data read from the controller to prometheus. If prometheus is running on your pi, you should be able to go to the URL http://192.168.0.XXX:5000 or http://solar-monitor.local:5000 and see some output that looks something like the following (you'll likely see a bunch of additional parameters).
    ```
    # HELP solarshed_battery_percentage Battery %
    # TYPE solarshed_battery_percentage gauge
    solarshed_battery_percentage 100.0
    # HELP solarshed_battery_volts Battery Voltage
    # TYPE solarshed_battery_volts gauge
    solarshed_battery_volts 13.600000000000001
    # HELP solarshed_battery_current Battery Current
    # TYPE solarshed_battery_current gauge
    solarshed_battery_current 5.5
    # HELP solarshed_controller_temperature_celsius Controller Temperature
    # TYPE solarshed_controller_temperature_celsius gauge
    solarshed_controller_temperature_celsius 32.0
    # HELP solarshed_battery_temperature_celsius Battery Temperature
    # TYPE solarshed_battery_temperature_celsius gauge
    solarshed_battery_temperature_celsius 25.0
    # HELP solarshed_load_volts Load Voltage
    # TYPE solarshed_load_volts gauge
    solarshed_load_volts 13.600000000000001
    # HELP solarshed_load_amperes Load Current
    # TYPE solarshed_load_amperes gauge
    solarshed_load_amperes 0.15
    # HELP solarshed_load_power_watts Load Power
    # TYPE solarshed_load_power_watts gauge
    solarshed_load_power_watts 2.0
    ...
    ```

## Run The Script Automatically

There are a few methods to run the script at startup. Either as a service or adding to ~/.config/autostart/solar-battery-bt-monitor.desktop.

I'd suggest trying Service method first, and using Option B as a fallback. There are other options as well, but don't add to .bashrc or rc.local.

### Option A: As a Service

This is the best and simplest method for running headless.

1. Create the solar-bt-service.service file in /etc/systemd/system/solar-battery-bt-monitor.service
```
sudo nano /etc/systemd/system/solar-battery-bt-monitor.service
```
Paste the following and save. Change the User and the file paths to your username and the correct filepaths.
```
[Unit]
Description=Solar Bluetooth Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/solar-battery-bt-monitor
ExecStart=/usr/bin/python3 /home/pi/solar-battery-bt-monitor/solar-battery-bt-monitor.py
RestartSec=13
Restart=always

[Install]
WantedBy=multi-user.target
```
2. Start up the solar-battery-bt-monitor service
```
sudo systemctl daemon-reload
sudo systemctl start solar-battery-bt-monitor
sudo systemctl status solar-battery-bt-monitor
sudo systemctl enable solar-battery-bt-monitor
```

### Option B: Add to ~/.config/autostart/solar-battery-bt-monitor.desktop

1. Edit ~/.config/autostart/solar-battery-bt-monitor.desktop, make sure to use correct username in directory
   ```
   mkdir /home/pi/.config/autostart
   nano /home/pi/.config/autostart/solar-battery-bt-monitor.desktop
   ```
2. Add to the file:
   ```
   [Desktop Entry]
   Name=solar-battery-bt-monitor
   Exec=/home/pi/solar-battery-bt-monitor/start.sh
   ```
3. Enable GUI Autologin:
    ```
    sudo raspi-config
    ```
   - System Options -> Boot / Auto Login -> Desktop Autologin
4. Make script executable:
   ```
   cd ~/solar-battery-bt-monitor
   sudo chmod +x start.sh
   ```

## Configure Grafana

1. Now that you're logging data to prometheus, we need to set up grafana to use this data source to display an awesome dashboard!
2. Go to your grafana install at http://192.168.0.XXX:3000 or http://solar-monitor.local:3000 and log in.
3. Set up the grafana data source coming from prometheus
4. From the navigation bar running down the left side of the window, select:
   - Configuration (gear icon) -> Data Sources
   - Select Prometheus
   - Give the data source a good name (solar-monitor)
   - Under the HTTP section, set the URL to http://192.168.0.XXX:9090 or http://solar-monitor.local:9090
   - Scroll to the bottom and select Save & Test
5. From the Create menu (Dashboard -> + icon on left navigation panel), choose Import and import the example dashboard json file included in the grafana folder in this project

# Troubleshooting

## BT Issues

Some BT dongles work better than others. It's probably best to use a Pi with integrated BT, but I ran into issues with that too. I have had success with this [Broadcom based BT Dongle](https://www.amazon.ca/gp/product/B007Q45EF4/).




Try this:
```
sudo hciconfig hci0 down; sudo systemctl restart bluetooth
```

Unload and reload btusb kernel:
```
sudo rmmod btusb
sudo modprobe btusb
```
Power off and on with bluetoothctl. If successful you should see results after running `scan on`
```
sudo bluetoothctl
power off
power on
scan on
```
Restart the solar-battery-bt-monitor service and check the status:
```
sudo systemctl daemon-reload
sudo service solar-battery-bt-monitor restart
sudo service solar-battery-bt-monitor status
```
If that doesn't work, try to restart the bluetooth service:
```
sudo service bluetooth restart
sudo service bluetooth status
```


## solar-battery-bt-monitor Service Issues

In case you run into issues running as a Service and want to stop and disable it:
```
sudo systemctl stop solar-battery-bt-monitor
sudo systemctl disable solar-battery-bt-monitor
```
Run the script instead
```
python3 ~/solar-battery-bt-monitor/solar-battery-bt-monitor.py
```

# Credits

This project is based off of [snichol67's solar-battery-bt-monitor](https://github.com/snichol67/solar-battery-bt-monitor), and contains elements of the following projects:
- [snichol67/solar-battery-bt-monitor](https://github.com/snichol67/solar-battery-bt-monitor)
- [Olen/solar-monitor](https://github.com/Olen/solar-monitor)
- [cyrils/renogy-bt1](https://github.com/cyrils/renogy-bt1)
- [corbinbs/solarshed](https://github.com/corbinbs/solarshed)
- [Rover 20A/40A Charge Controller—MODBUS Protocol](https://docs.google.com/document/d/1OSW3gluYNK8d_gSz4Bk89LMQ4ZrzjQY6/edit)
