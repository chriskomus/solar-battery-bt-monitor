# Solar Monitor Launcher
This launcher is a static html page that contains a big link to the Grafana dashboard, and a button to enable/disable full screen. The main grafana dashboard has a button that links to this page, allowing you to exit fullscreen mode without any keyboard inputs.

This is beneficial if you have an older/slower Pi that is running the grafana dashboard on an LCD touch screen. It also provides an easy way to exit fullscreen mode without keyboard input or 'right clicking' on the touch-screen.

1. If setting up on 2 Pis, ensure that this repo is also on the Kiosk Pi. [Project installation instructions.](../README.md#install-project)
1. Copy the link to the launcher, it should be something like:
```
file:///home/username/solar-battery-bt-monitor/launcher/launcher.html
```
2. Open Chromium.
3. Go into Chromium settings -> Appearance -> Show Home Button.
4. Set the home button to the launcher url.
5. Go into Chromium settings -> On start-up -> Open a specific page... -> Add a new page
6. Paste the launcher url.