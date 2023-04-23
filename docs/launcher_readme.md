# Solar Monitor Launcher
This launcher is a static html page that contains a big link to the Grafana dashboard, a button to enable/disable full screen, and links to the Prometheus dashboard and raw feed for debugging. The main grafana dashboard has a button that links back to this page, allowing you to exit fullscreen mode without any keyboard inputs.

This is beneficial if you have an older/slower Pi that is running the grafana dashboard on an LCD touch screen, and it hangs if you try to load grafana directly. It also provides an easy way to exit fullscreen mode without keyboard input or 'right clicking' on the touch-screen.

## Python HTTP.Server
Set up a simple file server to run the launcher html.

1. Create the solar-monitor-launcher.service file in /etc/systemd/system/solar-monitor-launcher.service
```
sudo nano /etc/systemd/system/solar-monitor-launcher.service
```
Paste the following and save. Change the User and the file paths to your username and the correct filepaths.
```
[Unit]
Description=Solar Monitor Launcher
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/solar-battery-bt-monitor/launcher
ExecStart=/usr/bin/python3 -m http.server 7800
Restart=on-abort

[Install]
WantedBy=multi-user.target
```
2. Start up the solar-monitor-launcher service
```
sudo systemctl daemon-reload
sudo systemctl start solar-monitor-launcher
sudo systemctl status solar-monitor-launcher
sudo systemctl enable solar-monitor-launcher
```

## Set up Chromium
1. Copy the link to the launcher:
```
http://solar-monitor:7800/
```
2. Open Chromium.
3. Go into Chromium settings -> Appearance -> Show Home Button.
4. Set the home button to the launcher url.
5. Go into Chromium settings -> On start-up -> Open a specific page... -> Add a new page
6. Paste the launcher url.
7. Reboot and test. If it still hangs on the blank white screen when loading chromium, link to the file in the repo directly:
```
file:///home/pi/solar-battery-bt-monitor/launcher/index.html
```
