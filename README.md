# Solar Panel and Battery Bluetooth Monitor with Dashboard

All-in-one DIY solar charge controller and battery monitoring dashboard solution!

This guide is for Renogy BT-1 compatible charge controllers and the Junctek KG-F Series bluetooth battery monitor, monitored by a Raspberry Pi.

A real-time dashboard for monitoring the performance of your system uses a touch-screen LCD displaying a Grafana dashboard with Prometheus for data logging from a Python script.

## Monitoring Renogy BT-1 Devices with Junctek KH140F Battery Monitor

**[BT-1 Compatible Charge Controllers](https://www.renogy.com/bt-1-bluetooth-module-new-version/)**: A python script reads data from Renogy solar Charge Controllers via its BT-1 bluetooth adapter. Tested with a **Rover 40A Charge Controller** and **Adventurer 30A Charge Controller**. May also work with Renogy **Wanderer** series charge controllers.

**[Junctek KG-F Series KH140F Bluetooth Battery Monitor](https://www.aliexpress.com/item/1005005293243736.html)**: The python script reads data from the Junctek KH140F battery monitor.

My setup utilizes two Raspberry Pis:
- Server: **Raspberry Pi Compute Module 4 with the Compute Module 4 IO Board**. [See the hardware instructions specific to that build.](docs/hardware_setup.md) Handles the heavy lifting: running the python script, prometheus and grafana services.
- Touchscren Dashboard: **Raspberry Pi 3 A+** [See 2nd Pi Instructions](docs/second_pi_setup.md) Runs Chromium in full screen mode displaying the Grafana dashboard.

For simplicity, the [readme](README.md) and [hardware setup](docs/hardware_setup.md) is written for using one Raspberry Pi. [See the 2nd Pi readme guide for setting up two Pis.](docs/second_pi_setup.md)

# Setup

## Getting Started

1. Set up a Raspberry Pi with wifi/bluetooth. [See the hardware instructions specific to my build.](docs/hardware_setup.md) Or set up two Raspberry Pis: one for running python/prometheus/grafana server and the other as a LCD touch-screen dashboard. [See 2nd Pi Instructions](docs/second_pi_setup.md)

## Install Project

1. Install this project on your Raspberry Pi - https://github.com/chriskomus/solar-battery-bt-monitor.git
    ```
    cd ~/
    git clone git@github.com:chriskomus/solar-battery-bt-monitor.git
    ```
2. Copy the ini file
    ```
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
4. Install Custom Plugins:
   ```
   sudo grafana-cli plugins install petrslavotinek-carpetplot-panel
   sudo grafana-cli plugins install speakyourcode-button-panel
   ```
5. Enable and start the Grafana server
    ```
    sudo /bin/systemctl enable grafana-server
    sudo /bin/systemctl start grafana-server
    ```
6. After grafana is installed, go to http://192.168.0.36:3000 or http://solar-monitor.local:3000/
   - Default log in is username: admin, password: admin
   - You'll be prompted to create a unique password for your installation

7. More info on installing Grafana on a Raspberry Pi [here](https://grafana.com/tutorials/install-grafana-on-raspberry-pi/).

## Setup Project

### Install Packages
1. Install the GATT library
    ```
    pip install gatt
    sudo apt-get install python3-dbus
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

### Configure your BT Devices
4. Now you'll need to edit the solar-battery-bt-monitor.ini with the specifics of your setup. You need to get the MAC address of your particular Renogy BT-1 device and Junctek KG-F Series device.
   ```
   sudo bluetoothctl
   scan on
   ```

#### Renogy BT-1
5. Look for devices with alias `BT-TH-XXXX..` and note the device name and mac address. If the device doesn't show up in the scanner, make sure you force quit any of the Renogy apps that might be connected to your BT-1.

#### Junctek KG-F Series KH140F
6. Look for devices with alias `BTGXXX` and note the device name and mac address. **Note** there is no documention online regarding the BT device name for this device. So I'm taking a guess that other KG-F Series devices have a similar alias. Download the official Juncket app, and tap "Search" and it should bring up the device name. Tap connect to confirm it's correct, then be sure to disconnect before proceeding.

#### Edit solar-battery-bt-monitor.ini
7. If you are using BT-1 data, set `renogy_enable` to True.
8. If you are using KG-F Series data, set `junctek_enable` to True.
6. Edit solar-battery-bt-monitor.ini file with the device name and MAC address for both devices.

### Fire it up!
7. It's time to test it out:
    ```
    cd ~/solar-battery-bt-monitor
    python3 solar-battery-bt-monitor.py
    ```
8. The script will attempt to connect to your BT-1 and KG-F Series device.  Often times, the bluetooth libraries will immediately disconnect. This script is set up by default to reconnect if that happens. Usually after a handful of reconnect attempts, the application will connect and you'll see the values output on the console.

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

## Run The Script Automatically as a Service

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
5. From the Create menu (Dashboard -> + icon on left navigation panel), choose Import and import the dashboard json files included in the grafana folder in this project. There are multiple files for different views on the LCD. Set `solar-battery-bt-monitor.json` to be the default dashboard. **If hostname is not solar-monitor**, find and replace `http://solar-monitor.local` with whatever the host name is for all the grafana dashboard json files.

## Setup Complete
Yay! At this point setup should be complete. Go to http://192.168.0.XXX:3000 or http://solar-monitor.local:3000 and you should start seeing at minimum a battery charge % and a battery voltage. Additional information should also display if the battery monitor is working and the solar panels are supplying power.

# Set Up Touch Screen LCD (Optional)
This is an optional step if you have a touch screen LCD. Complete the [hardware setup instructions first](docs/hardware_setup.md#lcd-setup), if you haven't already.

### Part 1 - Enable Grafana anonymous auth
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
8. On the Raspberry Pi that will be running the LCD, ensure you are logged out of grafana dashboard, then go to http://192.168.0.XXX:3000 or http://solar-monitor.local:3000
9. You should now see the dashboard without having logged in!

### Part 2 - Launch Chromium at startup
10. Open a terminal and type this to get to the configuration setting:
```
cd .config
sudo mkdir -p lxsession/LXDE-pi
sudo nano lxsession/LXDE-pi/autostart
```
11. Paste this into nano and save:
```
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
#@xscreensaver -no-splash
point-rpi
@chromium-browser --start-fullscreen --start-maximized
```
12. Optional: Install virtual keyboard for the touchscreen.
```
sudo apt install onboard
```
13. Go to Main Menu -> Preferences -> Raspberry Pi Configuration -> Display
14. Disable Screen-Blanking.
15. If you'd like Grafana to launch after booting continue with the following steps. If you prefer an html launcher instead, [read the launcher guide](docs/launcher_readme.md) and skip to step 21 in this section.

### Part 3 - Set up Bookmarks and Home Button
16. Bookmark the dashboard with the settings you'd like to see as a default.
17. Go into Chromium settings -> Appearance -> Show Home Button.
18. Set the home button to the grafana url that you bookmarked.
19. Go into Chromium settings -> On start-up -> Open a specific page... -> Add a new page
20. Paste the grafana url.

### Part 4 - Reboot and test
21. Use the shutdown script or reboot:
```
sudo shutdown -r now
```
22. The grafana dashboard should load after the reset. F11 to toggle fullscreen.


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

## Low Voltage Warnings
Powering the Pi off the front USB port on the charge controller can result in low voltage warnings. The best solution is to use an official Raspberry Pi power supply. In a 12v system this means running an inverter 24/7. Alternatively, find some magical combo of USB cables and 12v power where the number of voltage warnings is reduced or eliminated.


## Chromium Blank White Screen After Booting
If the Pi gets stuck on a white screen after launching Chromium in full screen after booting, you may have to use the [launcher](docs/launcher_readme.md) instead. Instead of automatically loading Grafana after booting, it will instead load a static html page with a link to Grafana. It also has a button to enable and disable full screen.

## Increase Swap Size
1. If the Kiosk Pi is running really slow, increase the swap size. First stop swapfile:
```
sudo dphys-swapfile swapoff
```
2. Modify swapfile config
```
sudo nano /etc/dphys-swapfile
```
3. Change `CONF_SWAPSIZE=100` to `CONF_SWAPSIZE=1024`
4. Restart swapfile
```
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

# Reverse Engineering A BT Device

If you want to learn more about the process of reverse engineering a BT device using just the device and a Raspberry Pi, check out my guide here:
[BLE Sniffer Walkthrough for Junctek BT Battery Monitor](https://github.com/chriskomus/ble-sniffer-walkthrough)

# Credits

Big thanks to [snichol67's solar-bt-monitor](https://github.com/snichol67/solar-bt-monitor) for his implementation using grafana and prometheus, and [Olen's solar-monitor](https://github.com/Olen/solar-monitor) which stands as the foundation of this project, and contains the Junctek plugin that I wrote and then adapted for this project.

This project contains elements of the following:
- [snichol67/solar-bt-monitor](https://github.com/snichol67/solar-bt-monitor)
- [Olen/solar-monitor](https://github.com/Olen/solar-monitor)
- [cyrils/renogy-bt1](https://github.com/cyrils/renogy-bt1)
- [BarkinSpider/SolarShed](https://github.com/BarkinSpider/SolarShed)
- [corbinbs/solarshed](https://github.com/corbinbs/solarshed)
- [Rover 20A/40A Charge Controller—MODBUS Protocol](https://docs.google.com/document/d/1OSW3gluYNK8d_gSz4Bk89LMQ4ZrzjQY6/edit)
