# PyRocketLauncher

## Description
This software was designed for a custom built fireworks ignition system. The corresponding hardware is based on a Raspberry Pi together with one or more [TLC59116](https://github.com/CR1337/PyRocketLauncher/raw/dev/doc/tlc59116.pdf) to control a driver stage that drives eletric igniters. The Raspberry Pi communicates with the TLC59116 via an I²C interface. This communication is controlled by this software. In addition this software provides a browser based frontend for easy user intercation with the system.

When this software does not run on an Raspberry Pi it simulates the behaviour of the the underlying hardware. It should therefore be able to be installed on any Linux system and provide a mock up of the complete system with its appropriate hardware.

## Installation
1. Download  the [rl-install script](https://raw.githubusercontent.com/CR1337/PyRocketLauncher/dev/bin/rl-install).
2. Execute the `rl-install` script.
3. Run `sudo rl setup`
4. Configure your device by interacting with the config wizard.
5. Save your configuration.
6. Your device is now fully functional.
