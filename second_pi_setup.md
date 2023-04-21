# Two Pis Are Better Than One

## Set Up A 2nd Raspberry Pi with LCD Touch-Screen and Grafana Dashboard

The [readme](README.md) and [hardware setup](hardware_setup.md) is written for using one Raspberry Pi, but it might be beneficial to have one higher powered **Server Pi** for running Python/Prometheus/Grafana server, and a lower powered **Kiosk Pi** running the LCD touch-screen and grafana dashboard in full screen mode.

In this configuration the logging server does all the work and should remain powered at all times, whereas the 2nd Pi only needs to be powered up when in use (when you want a dashboard display).

## Configure Two Pi's

To set up the main **server Pi**, follow the instructions in the [readme](README.md) and [hardware setup](hardware_setup.md), however the following sections should instead be done on the **kiosk Pi**:

[Hardware Setup: Raspberry Pi Setup](hardware_setup.md#raspberry-pi-setup) - Use a different hostname from the server Pi.

[Hardware Setup: SSH Setup](hardware_setup.md#raspberry-pi-setup)

[Hardware Setup: LCD Setup](hardware_setup.md#raspberry-pi-setup)

### Optional: Install Full Screen Button for Chromium
1. Goto https://chrome.google.com/webstore/detail/full-screen-button/

### Optional: Increase Swap Size
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

[Readme: Grafana on Touch Screen](README.md#optional-grafana-on-touch-screen-lcd) - Start at #8