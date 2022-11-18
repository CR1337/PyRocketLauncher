#!/bin/python3

import json
import os
import shutil
import subprocess
from datetime import datetime
import sys
import re
from difflib import SequenceMatcher
from typing import Callable, Dict, List, Any


class Paths:

    SELF: str = os.path.realpath(__file__)

    PARENT: str = "/" + os.path.join(*(SELF.split(os.path.sep)[:-3]))
    HOME: str = "/" + os.path.join(*(SELF.split(os.path.sep)[:-2]))
    CONFIG_PATH: str = os.path.join(HOME, "config")
    BIN: str = os.path.join(HOME, "bin")
    LOGS: str = os.path.join(HOME, "logs")

    HELP_TXT: str = os.path.join(BIN, "rl_help.txt")
    RL_INSTALL: str = os.path.join(BIN, "rl-install")

    CONFIG: str = os.path.join(CONFIG_PATH, "config.json")
    RUN_CONFIG: str = os.path.join(CONFIG_PATH, "run_config.jon")


class Ids:

    IMAGE: str = "rl_image"
    DEVICE_CONTAINER: str = 'rl_device_container'
    MASTER_CONTAINER: str = 'rl_master_container'


class TerminalColors:

    DEFAULT: str = "\033[39m"
    BLACK: str = "\033[30m"
    DARK_RED: str = "\033[31m"
    DARK_GREEN: str = "\033[32m"
    DARK_YELLOW: str = "(Orange-ish"
    DARK_BLUE: str = "\033[34m"
    DARK_MAGENTA: str = "\033[35m"
    DARK_CYAN: str = "\033[36m"
    LIGHT_GRAY: str = "\033[37m"
    DARK_GRAY: str = "\033[90m"
    RED: str = "\033[91m"
    GREEN: str = "\033[92m"
    ORANGE: str = "\033[93m"
    BLUE: str = "\033[94m"
    MAGENTA: str = "\033[95m"
    CYAN: str = "\033[96m"
    WHITE: str = "\033[97m"
    RESET: str = '\033[0m'


class Output:

    @staticmethod
    def info(message: str):
        print(f"{TerminalColors.CYAN}INFO> {message}{TerminalColors.RESET}")

    @staticmethod
    def important(message: str):
        print(f"{TerminalColors.MAGENTA}IMPORTANT> {message}{TerminalColors.RESET}")

    @staticmethod
    def error(message: str):
        print(f"{TerminalColors.RED}ERROR> {message}{TerminalColors.RESET}", file=sys.stderr)
        exit(1)

    @staticmethod
    def success(message: str):
        print(f"{TerminalColors.GREEN}SUCCESS> {message}{TerminalColors.RESET}")
        exit(0)

    @classmethod
    def wrong_usage(cls):
        cls.error("Wrong arguments! Run 'rl help' for help.")

    @staticmethod
    def print_help():
        with open(
            os.path.join(Paths.BIN, "rl_help.txt"),
            'r', encoding='utf-8'
        ) as file:
            print(file.read())
        exit(0)

    @classmethod
    def unexpected_error(cls):
        cls.error("Unexpected error!")


class Command:

    _command: str

    def __init__(self, command: str):
        self._command = command

    def run(self, show_output: bool = True):
        subprocess.run(
            self._command,
            shell=True,
            stdout=(None if show_output else subprocess.DEVNULL),
            stderr=(None if show_output else subprocess.DEVNULL)
        )

    def get_output(self) -> str:
        return subprocess.check_output(
            self._command,
            shell=True,
            stderr=subprocess.DEVNULL
        ).decode(encoding='ascii')

    def get_returncode(self, show_output: bool = True) -> int:
        process = subprocess.Popen(
            self._command,
            shell=True,
            stdout=(None if show_output else subprocess.DEVNULL),
            stderr=(None if show_output else subprocess.DEVNULL)
        )
        process.wait()
        return process.returncode


class Ask:

    @staticmethod
    def string(prompt: str) -> str:
        try:
            return input(prompt)
        except KeyboardInterrupt:
            return None

    @classmethod
    def boolean(cls, prompt: str) -> bool:
        while True:
            answer = cls.string(prompt).lower()
            if answer is None:
                return None
            if len(answer) == 1 and answer in "yn":
                return answer == 'y'

    @classmethod
    def integer(cls, prompt: str, min_value: int = None, max_value: int = None) -> int:
        while True:
            answer = cls.string(prompt)
            if answer is None:
                return None
            try:
                number = int(answer)
            except ValueError:
                pass
            else:
                if min_value is not None:
                    if number < min_value:
                        continue
                if max_value is not None:
                    if number > max_value:
                        continue
                return number

    @classmethod
    def timezone(cls, prompt: str) -> str:
        command = Command("timedatectl list-timezones")
        timezones = [
            tz.strip()
            for tz in command.get_output().split("\n")
        ]
        lower_timezones = [
            tz.lower()
            for tz in timezones
        ]
        while True:
            answer = cls.string(prompt)
            if answer is None:
                return None
            if answer.lower() in lower_timezones:
                index = lower_timezones.index(answer.lower())
                return timezones[index]

            def sort_key(item: str) -> float:
                return SequenceMatcher(None, answer, item).ratio()

            sorted_timezones = sorted(timezones, sort_key, reverse=True)

            print()
            print("Did you mean...?")
            print("Type a number.")
            for idx, timezone in enumerate(sorted_timezones[:10]):
                print(f"[{idx}] {timezone}")

            selection = Ask.integer("> ", 0, 9)
            if selection is None:
                return None

            return sorted_timezones[selection]

    @classmethod
    def datetime(cls, prompt: str) -> str:
        while True:
            answer = cls.string(prompt)
            if answer is None:
                return None
            try:
                datetime.strptime(answer, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
            else:
                return answer


class Network:

    @staticmethod
    def get_gateway_ip():
        command = Command("/sbin/ip route|awk '/default/ { print $3 }'")
        return command.get_output().strip()


class Cronjob:

    @classmethod
    def register(cls):
        Output.info("Registering cronjob...")
        if cls.is_registered():
            Output.error("A cronjob was already registered!")
        command = Command(f'crontab -l ; echo "@reboot {Paths.SELF} run" | crontab -')
        if command.get_returncode() != 0:
            Output.unexpected_error()

    @classmethod
    def deregister(cls):
        Output.info("Deregistering cronjob...")
        if not cls.is_registered():
            Output.error("There is no cronjob registered!")
        command = Command(f"crontab -l | grep -v '{Paths.SELF} run' | crontab -")
        if command.get_returncode() != 0:
            Output.unexpected_error()

    @staticmethod
    def is_registered():
        command = Command(f'crontab -l | grep -q "@reboot {Paths.SELF} run"')
        return command.get_returncode() == 0


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
            json.dump(data, filename)

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
        cls._set_config('device_id', value)

    @classmethod
    def get_chip_amount(cls) -> int:
        return cls._get_config('chip_amount')

    @classmethod
    def set_chip_amount(cls, value: int):
        cls._set_config('chip_amount', value)

    @classmethod
    def get_debug(cls) -> bool:
        return cls._get_run_config('debug')

    @classmethod
    def set_debug(cls, value: bool):
        cls._set_run_config('debug', value)

    @classmethod
    def get_master(cls) -> bool:
        return cls._get_run_config('master')

    @classmethod
    def set_master(cls, value: bool):
        cls._set_run_config('master', value)

    @classmethod
    def get_device(cls) -> bool:
        return cls._get_run_config('device')

    @classmethod
    def set_device(cls, value: bool):
        cls._set_run_config('device', value)

    @classmethod
    def get_timezone(cls) -> str:
        return cls._get_run_config('timezone')

    @classmethod
    def set_timezone(cls, value: str):
        cls._set_run_config('timezone', value)

    @classmethod
    def get_system_time(cls) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def set_system_time(cls, value: str) -> str:
        time_string = value.strip()
        command = Command(f"timedatectl set-time '{time_string}'")
        if command.get_returncode() != 0:
            Output.error(
                f"Invalid time format: {time_string}\n"
                "Format has to be 'YYYY-MM-DD HH:MM:SS'"
            )
        Output.info(f"Set time to {time_string}.")

    ASK_METHODS: Dict[str, Callable] = {
        'device_id': Ask.string,
        'chip_amount': Ask.integer,
        'debug': Ask.boolean,
        'master': Ask.boolean,
        'device': Ask.boolean,
        'timezone': Ask.timezone,
        'system_time': Ask.datetime
    }

    SET_METHODS: Dict[str, Callable] = {
        'device_id': set_device_id,
        'chip_amount': set_chip_amount,
        'debug': set_debug,
        'master': set_master,
        'device': set_device,
        'timezone': set_timezone,
        'system_time': set_system_time
    }

    GET_METHODS: Dict[str, Callable] = {
        'device_id': set_device_id,
        'chip_amount': set_chip_amount,
        'debug': set_debug,
        'master': set_master,
        'device': set_device,
        'timezone': set_timezone,
        'system_time': set_system_time
    }


class ConfigWizard:

    KEY_COUNT = len(Config.ASK_METHODS.keys())

    @classmethod
    def _print_main_menu(cls):
        print()
        print("This is the current configuration.")
        print("Type a number to change an entry.")
        print()
        for idx, key in enumerate(Config.ASK_METHODS.keys()):
            print(f"[{idx}] {key}: {Config.GET_METHODS[key]()}")
        print()
        print(f"[{cls.KEY_COUNT}] EXIT")

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
            if key is None:
                break

            ask_for_bool = (Config.ASK_METHODS[key] == Ask.boolean)
            ask_for_chip_amount = (key == 'chip_amount')
            value = Config.ASK_METHODS[key](
                f"Enter the new value for {key} "
                f"{'(yn)' if ask_for_bool else ''}"
                f"{'(1-26)' if ask_for_chip_amount else ''}"
                "> ",
                *([1, 26] if ask_for_chip_amount else [])
            )

            Config.SET_METHODS[key](value)

    @classmethod
    def run(cls):
        Output.info("Starting PyRocketLauncher Config Wizard...")
        cls._mainloop()
        Output.info("Config Wizard exited.")


class Logs:
    ...


class Status:
    # runnig, cronjob, onpi, gateway_ip
    ...