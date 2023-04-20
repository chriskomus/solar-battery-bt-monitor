# Solar Panel and Battery Bluetooth Monitor

All-in-one DIY solar charge controller and battery monitoring solution!

This guide is for Renogy BT-1 compatible charge controllers and the Junctek KH140F bluetooth battery monitor.

Real-time dashboard for monitoring the performance of your system on a touch-screen LCD using Grafana and Prometheus for data logging.

## Monitoring Renogy BT-1 Devices

**BT-1 Compatible Charge Controllers**: This python script reads data from Renogy solar Charge Controllers using the [BT-1](https://www.renogy.com/bt-1-bluetooth-module-new-version/) bluetooth adapter. Tested with a **Rover 40A Charge Controller** and **Adventurer 30A Charge Controller**. May also work with Renogy **Wanderer** series charge controllers. It might also work with other  "SRNE like" devices like Rich Solar, PowMr, WEIZE etc.

**Junctek KH140F Bluetooth Battery Monitor**: This python script reads data from the Junctek KH140F battery monitor.

My setup uses a **Raspberry Pi Compute Module 4 with the Compute Module 4 IO Board**. [See the hardware instructions specific to that build.](hardware_setup.md)



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

1. Add the APT key used to authenticate packages.
   ```
   wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
   ```
2. Add the Grafana APT repository
   ```
   echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
   ```
3. Install Grafana.
   ```
   sudo apt-get update
   sudo apt-get install -y grafana
   ```
3. Enable and start the Grafana server
    ```
    sudo /bin/systemctl enable grafana-server
    sudo /bin/systemctl start grafana-server
    ```
4. After grafana is installed, go to http://192.168.0.36:3000 or http://solar-monitor.local:3000/
   - Default log in is username: admin, password: admin
   - You'll be prompted to create a unique password for your installation

5. More info on installing Grafana on a Raspberry Pi [here](https://grafana.com/tutorials/install-grafana-on-raspberry-pi/).

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
    cd ~/
    git clone https://github.com/hex-in/libscrc
    cd libscrc/
    python3 setup.py build
    sudo python3 setup.py install
    ```
4. Now you'll need to edit the solar-battery-bt-monitor.ini with the specifics of your setup. You need to get the MAC address of your particular BT-1 device.
   ```
   sudo bluetoothctl
   scan on
   ```
5. Look for devics with alias `BT-TH-XXXX..`.  If the device doesn't show up in the scanner, make sure you force quit any of the Renogy apps that might be connected to your BT-1.
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

## Setup Complete!
Yay! At this point setup should be complete. Go to http://192.168.0.XXX:3000 or http://solar-monitor.local:3000 and you should start seeing at minimum a battery charge % and a battery voltage. Additional information should also display if the battery monitor is working and the solar panels are supplying power.

## Optional: Grafana on Touch Screen LCD
This is an optional step if you have a touch screen LCD. [See the hardware instructions on setting up the touch-screen LCD.](hardware_setup.md)

1. Edit the grafana config file:
```
sudo nano /etc/grafana/config.ini
```
2. Look for the section starting with [auth.anonymous] and change to the following values (don't forget to remove the ; at the beginning of the line):
```
[auth.anonymous]
# enable anonymous access
enabled = true

# specify organization name that should be used for unauthenticated users
org_name = SolarBluetoothMonitor

# specify role for unauthenticated users
org_role = Viewer

# mask the Grafana version number for unauthenticated users
hide_version = true
```
3. In a browser go to http://192.168.0.XXX:3000 or http://solar-monitor.local:3000
4. From the navigation bar running down the left side of the window, select Server admin (shield icon) -> Organizations:
   - Click on the organizations
   - Update the Organization name in Grafana to `SolarBluetoothMonitor` or whatever you chose in step 2.
5. From the navigation bar, select Dashboards -> Browse:
   - Click on Solar Bluetooth Monitor
   - Click on the star to make it the default.
6. From the navigation bar, select Configuration -> Preferences.
   - Set the Home dashboard for the organisation
   - Set the Org name to to match the name above
7. If you completed the above steps on the Raspberry Pi, log out of grafana.
8. On the Raspberry Pi, ensure you are logged out of grafana dashboard, then go to http://192.168.0.XXX:3000 or http://solar-monitor.local:3000
9. You should now see the dashboard without having logged in.
10. Bookmark the dashboard with the settings you'd like to see as a default.
11. Go into Chromium settings -> Appearance -> Show Home Button.
12. Set the home button to the grafana url that you bookmarked.
13. Go into Chromium settings -> On start-up -> Open a specific page... -> Add a new page
14. Paste the grafana url.
15. Open a terminal and type this to get to the configuration setting:
```
cd .config
sudo mkdir -p lxsession/LXDE-pi
sudo nano lxsession/LXDE-pi/autostart
```
16. Paste this into nano and save:
```
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
#@xscreensaver -no-splash
point-rpi
@chromium-browser --start-fullscreen --start-maximized
```
17. Optional: Install virtual keyboard for the touchscreen.
```
sudo apt install onboard
```
18. Reboot.
```
sudo shutdown -r now
```
19. The grafana dashboard should load after the reset. F11 to toggle fullscreen.

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

## Touchscreen issues

The hardware guide is designed for Raspberry Pi CM4, which has 2 HDMI ports. Use the following settings instead if using a Pi 3.
```
hdmi_group=2
hdmi_mode=87
hdmi_cvt 1024 600 60 6 0 0 0
```

# New Features

- Upgraded Grafana:
   - New Time Series replaced deprecated line charts
   - Added 24hr offset historical overlay on some graphs
   - Converted to Celcius
   - More colours for safe temperature ranges
   - Colour coded gauges and charts for both lifepo4 and lead acid
- Added Celcius and Fehrenheit

# Credits

This project is based off of [snichol67's solar-battery-bt-monitor](https://github.com/snichol67/solar-battery-bt-monitor), and contains elements of the following projects:
- [snichol67/solar-battery-bt-monitor](https://github.com/snichol67/solar-battery-bt-monitor)
- [Olen/solar-monitor](https://github.com/Olen/solar-monitor)
- [cyrils/renogy-bt1](https://github.com/cyrils/renogy-bt1)
- [BarkinSpider/SolarShed](https://github.com/BarkinSpider/SolarShed)
- [corbinbs/solarshed](https://github.com/corbinbs/solarshed)
- [Rover 20A/40A Charge Controller—MODBUS Protocol](https://docs.google.com/document/d/1OSW3gluYNK8d_gSz4Bk89LMQ4ZrzjQY6/edit)
