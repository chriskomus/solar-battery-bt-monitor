# Solar Panel and Battery Bluetooth Monitor

## For Monitoring Renogy BT-1 Devices

Read data from Renogy charge controllers that use BT-1, and display it using grafana.  

### Setup

#### Hardware Setup

Use any modern Raspberry Pi device. For this project I am using a Raspberry Pi Compute Module 4 with the Compute Module 4 IO Board. I'm powering it using a 5v USB to Barrel Jack, so that I can power it off the front of the Renogy Solar Charge Controller. YMMV on how well that works depending on your charge controller and Pi power consumption. You will occasionally get low power warnings when the monitor is plugged in.

[See the instructions specific to that build.](hardware_setup.md)

#### Promethius




### FAQ

### Credits

This project is largely based off of Scott Nichol's implementation of the Python based solar-monitor scripts, which are based off of other earlier implementations:
- [snichol67/solar-bt-monitor](https://github.com/snichol67/solar-bt-monitor)
- [Olen/solar-monitor](https://github.com/Olen/solar-monitor)
- [cyrils/renogy-bt1](https://github.com/cyrils/renogy-bt1)
- [corbinbs/solarshed](https://github.com/corbinbs/solarshed)
- [Rover 20A/40A Charge Controller—MODBUS Protocol](https://docs.google.com/document/d/1OSW3gluYNK8d_gSz4Bk89LMQ4ZrzjQY6/edit)
