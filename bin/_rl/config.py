import json
import os
import shutil
import socket
from datetime import datetime
from typing import Any, Callable, Dict
import subprocess

from _rl.command import Command
from _rl.constants import Paths, ExitCodes
from _rl.format_validator import FormatValidator
from _rl.inout import Ask, Output
from _rl.network import Network
from smbus2 import SMBus


class AutoConfig:

    I2C_BUS_ADDRESS: int = 1
    BASE_CHIP_ADDRESS: int = 0x60

    @staticmethod
    def _determine_device_id() -> str:
        return socket.gethostname()

    @classmethod
    def _determine_chip_amount(cls) -> int:
        bus = SMBus(cls.I2C_BUS_ADDRESS)
        for idx in range(8):
            try:
                bus.read_byte_data(cls.BASE_CHIP_ADDRESS + idx, 0x00)
            except OSError:
                return idx

    @staticmethod
    def _determine_debug() -> bool:
        return False

    @staticmethod
    def _determine_master() -> bool:
        return Config.get_device_id().lower() in ['master', 'main']

    @staticmethod
    def _determine_device() -> bool:
        return True
    
    @staticmethod
    def _create_udev_rule(filename: str, vendor_id: str, product_id: str):
        with open(filename, 'w') as file:
            file.write(
                f'SUBSYSTEM=="usb", ATTRS{{idVendor}}=="{vendor_id}", '
                f'ATTRS{{idProduct}}=="{product_id}", MODE="0666"'
            )

    @staticmethod
    def _extract_vendor_and_product_id(device: str) -> tuple[str, str]:
        chunks = device.split(' ')
        vendor_id , product_id = chunks[5].split(':')
        return vendor_id, product_id

    @classmethod
    def _create_udev_rules(cls):
        process = subprocess.Popen(
            "lsusb",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, _ = process.communicate()
        if process.returncode != ExitCodes.SUCCESS:
            Output.critical("Error reading usb devices!")
            return
        devices = stdout.decode('utf-8').split('\n')
        devices_found = 0
        for device in devices:
            if "Helios Laser DAC" in device:
                vendor_id, product_id = cls._extract_vendor_and_product_id(device)
                cls._create_udev_rule(
                    Paths.HELIOS_RULE,
                    vendor_id,
                    product_id
                )
                devices_found += 1
            elif "FT232 Serial" in device:
                vendor_id, product_id = cls._extract_vendor_and_product_id(device)
                cls._create_udev_rule(
                    Paths.FT232_RULE,
                    vendor_id,
                    product_id
                )
                devices_found += 1
            if devices_found == 2:
                break
        os.system("udevadm control --reload-rules")
        os.system("udevadm trigger")

    @classmethod
    def remove_udev_rules(cls):
        if os.path.exists(Paths.HELIOS_RULE):
            os.remove(Paths.HELIOS_RULE)
        if os.path.exists(Paths.FT232_RULE):
            os.remove(Paths.FT232_RULE)
        os.system("udevadm control --reload-rules")
        os.system("udevadm trigger")

    @staticmethod
    def _create_config_files():
        for filename, default_filename in zip(
            [
                Paths.CONSTANTS,
                Paths.CONFIG,
                Paths.RUN_CONFIG
            ],
            [
                Paths.DEFAULT_CONSTANTS,
                Paths.DEFAULT_CONFIG,
                Paths.DEFAULT_RUN_CONFIG
            ]
        ):
            if not os.path.exists(filename):
                shutil.copy(default_filename, Paths.CONFIG_PATH)

    @staticmethod
    def _compile_audio_library():
        process = subprocess.Popen(
            ["make"],
            cwd=Paths.AUDIOLIB,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        _, stderr = process.communicate()
        if process.returncode != ExitCodes.SUCCESS:
            Output.critical(
                f"Error compiling audio library:\n{stderr.decode('utf-8')}"
            )

    @classmethod
    def run(cls):
        Output.info("Creting udev rules for usb devices...")
        cls._create_udev_rules()

        Output.info("Creating config files...")
        cls._create_config_files()

        Output.info("Performing automatic configuration...")

        device_id = cls._determine_device_id()
        Output.info(f"Auto-setting device_id to '{device_id}'")
        Config.set_device_id(device_id)

        chip_amount = cls._determine_chip_amount()
        Output.info(f"Auto-setting chip amount to '{chip_amount}'")
        Config.set_chip_amount(chip_amount)

        debug = cls._determine_debug()
        Output.info(f"Auto-setting debug to '{debug}'")
        Config.set_debug(debug)

        master = cls._determine_master()
        Output.info(f"Auto-setting master to '{master}'")
        Config.set_master(master)

        device = cls._determine_device()
        Output.info(f"Auto-setting device to '{device}'")
        Config.set_device(device)

        Output.info("Compiling audio library.")
        cls._compile_audio_library()


class Config:

    @staticmethod
    def _get(key: str, filename: str) -> Any:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)[key]

    @staticmethod
    def _set(key: str, value: Any, filename: str):
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        data[key] = value
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file)

    @classmethod
    def _get_config(cls, key: str) -> Any:
        return cls._get(key, Paths.CONFIG)

    @classmethod
    def _set_config(cls, key: str, value: Any):
        cls._set(key, value, Paths.CONFIG)

    @classmethod
    def _get_run_config(cls, key: str) -> Any:
        return cls._get(key, Paths.RUN_CONFIG)

    @classmethod
    def _set_run_config(cls, key: str, value: Any):
        cls._set(key, value, Paths.RUN_CONFIG)

    @classmethod
    def get_device_id(cls) -> str:
        return cls._get_config('device_id')

    @classmethod
    def set_device_id(cls, value: str):
        cls._set_config('device_id', str(value))

    @classmethod
    def get_chip_amount(cls) -> int:
        return cls._get_config('chip_amount')

    @classmethod
    def set_chip_amount(cls, value: int):
        cls._set_config('chip_amount', int(value))

    @classmethod
    def get_debug(cls) -> bool:
        return cls._get_config('debug')

    @classmethod
    def set_debug(cls, value: bool):
        cls._set_config('debug', bool(value))

    @classmethod
    def get_master(cls) -> bool:
        return cls._get_run_config('master')

    @classmethod
    def set_master(cls, value: bool):
        cls._set_run_config('master', bool(value))

    @classmethod
    def get_device(cls) -> bool:
        return cls._get_run_config('device')

    @classmethod
    def set_device(cls, value: bool):
        cls._set_run_config('device', bool(value))

    @classmethod
    def get_timezone(cls) -> str:
        command = Command("cat /etc/timezone")
        return command.get_output().strip()

    @classmethod
    def set_timezone(cls, value: str):
        command = Command(f"timedatectl set-timezone {value}")
        if command.get_returncode() != ExitCodes.SUCCESS:
            Output.critical("Error setting timezone!")

    @classmethod
    def get_system_time(cls) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def set_system_time(cls, value: str) -> str:
        time_string = str(value).strip()
        command = Command(f"timedatectl set-time '{time_string}'")
        if command.get_returncode() != ExitCodes.SUCCESS:
            Output.critical(
                f"Invalid time format: {time_string}\n"
                "Format has to be 'YYYY-MM-DD HH:MM:SS'"
            )
        Output.info(f"Set time to {time_string}.")

    @classmethod
    def get_static_ip_byte(cls) -> int:
        return Network.get_static_ip_byte()

    @classmethod
    def set_static_ip_byte(cls, value: str):
        value = int(value)
        if value == -1:
            Network.unset_static_ip()
        else:
            Network.set_static_ip(value)

    @classmethod
    def validate_value(cls, key: str, value: Any) -> bool:
        if cls.TYPES[key] == str:
            if key == 'timezone':
                return FormatValidator.validate_timezone(value)
            elif key == 'system_time':
                return FormatValidator.validate_datetime(value)
            else:
                return True
        elif key == 'chip_amount':
            return FormatValidator.validate_int(value, 1, 8)
        elif key == 'static_ip_byte':
            return FormatValidator.validate_int(value, -1, 254)
        elif cls.TYPES[key] == bool:
            return FormatValidator.validate_bool(value)

    ASK_METHODS: Dict[str, Callable] = {
        'device_id': Ask.string,
        'chip_amount': Ask.integer,
        'debug': Ask.boolean,
        'master': Ask.boolean,
        'device': Ask.boolean,
        'timezone': Ask.timezone,
        'system_time': Ask.datetime,
        'static_ip_byte': Ask.integer
    }

    TYPES: Dict[str, type] = {
        'device_id': str,
        'chip_amount': int,
        'debug': bool,
        'master': bool,
        'device': bool,
        'timezone': str,
        'system_time': str,
        'static_ip_byte': int
    }


Config.SET_METHODS: Dict[str, Callable] = {
    'device_id': Config.set_device_id,
    'chip_amount': Config.set_chip_amount,
    'debug': Config.set_debug,
    'master': Config.set_master,
    'device': Config.set_device,
    'timezone': Config.set_timezone,
    'system_time': Config.set_system_time,
    'static_ip_byte': Config.set_static_ip_byte
}


Config.GET_METHODS: Dict[str, Callable] = {
    'device_id': Config.get_device_id,
    'chip_amount': Config.get_chip_amount,
    'debug': Config.get_debug,
    'master': Config.get_master,
    'device': Config.get_device,
    'timezone': Config.get_timezone,
    'system_time': Config.get_system_time,
    'static_ip_byte': Config.get_static_ip_byte
}


class ConfigWizard:

    KEY_COUNT: int = len(Config.ASK_METHODS.keys())

    @classmethod
    def _print_main_menu(cls):
        print()
        print("This is the current configuration.")
        print("Type a number to change an entry.")
        print()
        for idx, key in enumerate(Config.ASK_METHODS.keys()):
            print(f"[{idx}] {key}: {Config.GET_METHODS[key]()}")
        print()
        print(f"[{cls.KEY_COUNT}] DONE")

    @classmethod
    def _mainloop(cls):
        while True:
            cls._print_main_menu()
            selection = Ask.integer("> ", 0, cls.KEY_COUNT)
            if selection is None:
                break
            if selection == cls.KEY_COUNT:
                break
            key = list(Config.ASK_METHODS.keys())[selection]

            ask_for_bool = (Config.ASK_METHODS[key] == Ask.boolean)
            ask_for_chip_amount = (key == 'chip_amount')
            ask_for_static_ip_byte = (key == 'static_ip_byte')

            value = Config.ASK_METHODS[key](
                f"Enter the new value for {key} "
                f"{'(yn)' if ask_for_bool else ''}"
                f"{'(1-8)' if ask_for_chip_amount else ''}"
                f"{'(-1-254)' if ask_for_static_ip_byte else ''}"
                "> ",
                *([1, 8] if ask_for_chip_amount else []),
                *([-1, 254] if ask_for_static_ip_byte else [])
            )
            if value is None:
                break

            Config.SET_METHODS[key](value)

    @classmethod
    def run(cls):
        Output.info("Starting PyRocketLauncher Config Wizard...")
        cls._mainloop()
