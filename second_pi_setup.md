# Two Pis Are Better Than One

## Set Up A 2nd Raspberry Pi with LCD Touch-Screen and Grafana Dashboard

The [readme](README.md) and [hardware setup](hardware_setup.md) is written for using one Raspberry Pi, but it might be beneficial to have one higher powered **Server Pi** for running Python/Prometheus/Grafana server, and a lower powered **Kiosk Pi** running the LCD touch-screen and grafana dashboard in full screen mode.

In this configuration the logging server does all the work and should remain powered at all times, whereas the 2nd Pi only needs to be powered up when in use (when you want a dashboard display).

## Configure Two Pi's

1. Set up the main **server Pi** by following the instructions in the [readme](README.md) and [hardware setup](hardware_setup.md).

2. Repeat the following sections for the **kiosk Pi**:
  - [Hardware Setup: Raspberry Pi Setup](hardware_setup.md#raspberry-pi-setup) - Use a different hostname from the server Pi.
  - [Hardware Setup: SSH Setup](hardware_setup.md#ssh-setup)
  - [Hardware Setup: LCD Setup](hardware_setup.md#lcd-setup)
  - [Readme: Grafana on Touch Screen](README.md#part-2---launch-chromium-at-startup) - Start at Part 2
  - [Readme: Install Project](README.md#install-project) - Step 1 only
  - [Optional: Launcher Setup](launcher/readme.md)
  - [Optional: Increase Swap Size](README.md#freezing-and-hanging-on-pis-with-limited-ram)
