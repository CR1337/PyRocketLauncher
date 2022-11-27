# PyRocketLauncher

## Description
This software was designed for a custom built fireworks ignition system. The corresponding hardware is based on a Raspberry Pi together with one or more [TLC59116](https://github.com/CR1337/PyRocketLauncher/blob/dev/doc/tlc59116.pdf) to control a driver stage that drives eletric igniters. The Raspberry Pi communicates with the TLC59116 via an I²C interface. This communication is controlled by this software. In addition this software provides a browser based frontend for easy user intercation with the system.

## Installation
1. Download  the [rl-install script](https://raw.githubusercontent.com/CR1337/PyRocketLauncher/main/bin/rl-install) by running `wget https://raw.githubusercontent.com/CR1337/PyRocketLauncher/main/bin/rl-install`
2. Set execution permission by running `chmod +x rl-install`
3. Execute the `rl-install` script as root.
4. Run `sudo rl setup`.
5. Configure your device by interacting with the config wizard.
6. Your device is now fully functional.
7. Check further options by running `sudo rl help`.
