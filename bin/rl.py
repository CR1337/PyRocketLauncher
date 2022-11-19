#!/bin/python3

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Callable, Dict, List


class Paths:

    SELF: str = os.path.realpath(__file__)

    PARENT: str = "/" + os.path.join(*(SELF.split(os.path.sep)[:-3]))
    HOME: str = "/" + os.path.join(*(SELF.split(os.path.sep)[:-2]))
    CONFIG_PATH: str = os.path.join(HOME, "config")
    BIN: str = os.path.join(HOME, "bin")
    LOGS: str = os.path.join(HOME, "logs")
    HELP: str = os.path.join(HOME, "doc/help")

    HELP_RL: str = os.path.join(HELP, "rl.txt")
    HELP_RL_CONFIG: str = os.path.join(HELP, "rl_config.txt")
    HELP_RL_STATUS: str = os.path.join(HELP, "rl_status.txt")
    HELP_RL_CRONJOB: str = os.path.join(HELP, "rl_cronjob.txt")
    HELP_RL_LOGS: str = os.path.join(HELP, "rl_logs.txt")

    # HELP_TXT: str = os.path.join(BIN, "rl_help.txt")
    RL_INSTALL: str = os.path.join(BIN, "rl-install")

    CONFIG: str = os.path.join(CONFIG_PATH, "config.json")
    RUN_CONFIG: str = os.path.join(CONFIG_PATH, "run_config.jon")

    MODEL: str = "/sys/firmware/devicetree/base/model"
    I2C: str = "/dev/i2c-1"
    BASHRC: str = "/root/.bashrc"


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
    def print_file(filename: str):
        with open(filename, 'r', encoding='utf-8') as file:
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


class FormatValidator:

    @staticmethod
    def get_all_timezones(cls):
        command = Command("timedatectl list-timezones")
        timezones = [
            tz.strip()
            for tz in command.get_output().split("\n")
        ]
        return timezones

    @classmethod
    def validate_timezone(cls, value: str) -> bool:
        return value in cls.get_all_timezones()

    @staticmethod
    def validate_datetime(value: str) -> bool:
        try:
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def validate_bool(value: str) -> bool:
        return value in ['0', '1']

    @staticmethod
    def validate_int(value: str, max_value: int, min_value: int) -> bool:
        try:
            value = int(value)
        except ValueError:
            return False
        else:
            if value > max_value:
                return False
            if value < min_value:
                return False
            return True


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
        timezones = FormatValidator.get_all_timezones()
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
            if FormatValidator.validate_datetime(answer):
                return answer


class Network:

    @staticmethod
    def get_gateway_ip() -> str:
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
    def is_registered() -> bool:
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
        cls._set_config('device_id', str(value))

    @classmethod
    def get_chip_amount(cls) -> int:
        return cls._get_config('chip_amount')

    @classmethod
    def set_chip_amount(cls, value: int):
        cls._set_config('chip_amount', int(value))

    @classmethod
    def get_debug(cls) -> bool:
        return cls._get_run_config('debug')

    @classmethod
    def set_debug(cls, value: bool):
        cls._set_run_config('debug', bool(value))

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
        return cls._get_run_config('timezone')

    @classmethod
    def set_timezone(cls, value: str):
        cls._set_run_config('timezone', str(value))

    @classmethod
    def get_system_time(cls) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def set_system_time(cls, value: str) -> str:
        time_string = str(value).strip()
        command = Command(f"timedatectl set-time '{time_string}'")
        if command.get_returncode() != 0:
            Output.error(
                f"Invalid time format: {time_string}\n"
                "Format has to be 'YYYY-MM-DD HH:MM:SS'"
            )
        Output.info(f"Set time to {time_string}.")

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
            FormatValidator.validate_int(value, 1, 26)
        elif cls.TYPES[key] == bool:
            return FormatValidator.validate_bool(value)

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

    TYPES: Dict[str, type] = {
        'device_id': str,
        'chip_amount': int,
        'debug': bool,
        'master': bool,
        'device': bool,
        'timezone': str,
        'system_time': str
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

            ask_for_bool = (Config.ASK_METHODS[key] == Ask.boolean)
            ask_for_chip_amount = (key == 'chip_amount')
            value = Config.ASK_METHODS[key](
                f"Enter the new value for {key} "
                f"{'(yn)' if ask_for_bool else ''}"
                f"{'(1-26)' if ask_for_chip_amount else ''}"
                "> ",
                *([1, 26] if ask_for_chip_amount else [])
            )
            if value is None:
                break

            Config.SET_METHODS[key](value)

    @classmethod
    def run(cls):
        Output.info("Starting PyRocketLauncher Config Wizard...")
        cls._mainloop()
        Output.info("Config Wizard exited.")


class Logs:

    SEP: str = ":::"

    LEVEL_COLORS: Dict[str, str] = {
        'DEBUG': TerminalColors.LIGHT_GRAY,
        'INFO': TerminalColors.CYAN,
        'WARNING': TerminalColors.DARK_YELLOW,
        'ERROR': TerminalColors.DARK_RED,
        'CRITICAL': TerminalColors.RED
    }

    @staticmethod
    def get_log_filenames() -> List[str]:
        filenames = os.listdir(Paths.LOGS)
        log_filenames = [fn for fn in filenames if fn.endswith(".log")]
        if len(log_filenames) == 0:
            Output.error("There are no logfiles.")
        return log_filenames

    @classmethod
    def get_latest_log_filename(cls) -> str:
        return sorted(cls.get_log_filenames())[-1]

    @classmethod
    def clear_logs(cls):
        if not Ask.boolean("Are you sure you want to delete all logfiles? (yn)> "):
            Output.success("Logfile deletion was cancelled.")
        Output.info("Deleting all logfiles...")
        for filename in cls.get_log_filenames():
            os.remove(os.path.join(Paths.LOGS, filename))

    @classmethod
    def print_latest_raw(cls):
        latest_log_filename = cls.get_latest_log_filename()
        with open(os.path.join(Paths.LOGS, latest_log_filename), 'r', encoding='utf-8') as file:
            print(file.read())

    @classmethod
    def print_latest_pretty(cls):
        latest_log_filename = cls.get_latest_log_filename()
        with open(os.path.join(Paths.LOGS, latest_log_filename), 'r', encoding='utf-8') as file:
            lines = file.readlines()
        for line in lines:
            level = line.split(cls.SEP)[1]
            color_code = cls.LEVEL_COLORS.get(
                level, TerminalColors.DEFAULT
            )
            print(f"{color_code}{line}{TerminalColors.RESET}")


class Status:

    @staticmethod
    def _is_container_running(container_id: str) -> bool:
        try:
            command = Command(f"docker container inspect -f '{{{{.State.Status}}}}' {container_id}")
            result = command.get_output()
        except subprocess.CalledProcessError:
            return False
        else:
            if 'running' in result:
                return True
        return False

    @classmethod
    def is_running(cls) -> bool:
        return any([
            (
                Config.get_device()
                and cls._is_container_running(Ids.DEVICE_CONTAINER)
            ),
            (
                Config.get_master()
                and cls._is_container_running(Ids.MASTER_CONTAINER)
            )
        ])

    @staticmethod
    def is_cronjob_registered() -> bool:
        return Cronjob.is_registered()

    @staticmethod
    def is_on_pi() -> bool:
        if not os.path.exists(Paths.MODEL):
            return False
        try:
            with open(
                Paths.MODEL,
                'r', encoding='ascii'
            ) as file:
                return "pi" in file.read().lower()
        except FileNotFoundError:
            return False

    @staticmethod
    def get_gateway_ip() -> str:
        return Network.get_gateway_ip()

    GET_METHODS: Dict[str, Callable] = {
        'running': is_running,
        'cronjob': is_cronjob_registered,
        'pi': is_on_pi,
        'gateway_ip': get_gateway_ip
    }


class RlManager:

    @classmethod
    def setup(cls):
        if Status.is_running():
            cls.stop()
        ConfigWizard.run()
        cls.build()
        if not Status.is_cronjob_registered():
            Cronjob.register()
        cls.run()
        Output.info("This system should now be fully functional.")
        Output.info("For further options run: 'rl help'")

    @classmethod
    def build(cls):
        was_running = False
        if Status.is_running():
            was_running = True
            cls.stop()
        Output.info("Building docker image...")
        command = Command(f"docker build --tag {Ids.IMAGE} {Paths.HOME}")
        if command.get_returncode() != 0:
            Output.unexpected_error()
        if was_running:
            cls.run()

    @staticmethod
    def run():
        if Status.is_running():
            Output.error("System is already running!")
        debug_str = str(int(Config.get_debug()))
        on_pi_str = str(int(Status.is_on_pi()))
        if Config.get_device():
            Output.info("Starting device...")
            command = Command(
                f"docker run "
                f"--rm "
                f"--detach "
                f"--env IS_MASTER=0 "
                f"--env FLASK_DEBUG={debug_str} "
                f"--env GATEWAY_IP={Network.get_gateway_ip()} "
                f"--env ON_PI={on_pi_str} "
                f"--env TZ={Config.get_timezone()}"
                f"--env SERVER_PORT=5001 "
                f"-p 5001:5001"
                f"--name {Ids.DEVICE_CONTAINER}"
                f"--volume {Paths.I2C}:{Paths.I2C}"
                f"--volume {Paths.LOGS}:/rl/logs "
                f"--volume {Paths.CONFIG_PATH}:/rl/config "
                f"{Ids.IMAGE}"
            )
            if command.get_returncode() != 0:
                Output.unexpected_error()
        if Config.get_master():
            Output.info("Starting master...")
            command = Command(
                f"docker run "
                f"--rm "
                f"--detach "
                f"--env IS_MASTER=1 "
                f"--env FLASK_DEBUG={debug_str} "
                f"--env GATEWAY_IP={Network.get_gateway_ip()} "
                f"--env ON_PI={on_pi_str} "
                f"--env TZ={Config.get_timezone()} "
                f"--env SERVER_PORT=5000 "
                f"-p 80:5000 "
                f"--name {Ids.MASTER_CONTAINER} "
                f"--volume {Paths.LOGS}:/rl/logs "
                f"--volume {Paths.CONFIG_PATH}:/rl/config "
                f"{Ids.IMAGE}"
            )
            if command.get_returncode() != 0:
                Output.unexpected_error()

    @staticmethod
    def stop():
        if not Status.is_running():
            Output.error("System is not running!")
        Output.info("Stopping system...")
        if Config.get_device():
            Output.info("Stopping device...")
            command = Command(f"docker stop {Ids.DEVICE_CONTAINER}")
            if command.get_returncode() != 0:
                Output.info("Error stopping device! Maybe it was already stopped?")
        if Config.get_master():
            Output.info("Stopping master...")
            command = Command(f"docker stop {Ids.MASTER_CONTAINER}")
            if command.get_returncode() != 0:
                Output.info("Error stopping master. Maybe is was already stopped?")

    @classmethod
    def restart(cls):
        Output.info("Restarting system...")
        cls.stop()
        cls.run()

    @classmethod
    def update(cls):
        Output.info("Updating System...")
        was_running = False
        if Status.is_running():
            was_running = True
            cls.stop()
        command = Command(f"git -C {Paths.HOME} pull")
        if command.get_returncode() != 0:
            Output.unexpected_error()
        cls.build()
        if was_running:
            cls.run()

    @classmethod
    def uninstall(cls):
        Output.info("Starting deinstallation process...")
        Output.important("Are you sure you want to uninstall?")
        if not Ask.boolean("Are you sure you want to uninstall? (yn)> "):
            Output.success("Deinstallation process was cancelled.")
        keyword = 'uninstall'
        answer = Ask.string(f"Type '{keyword}' if you are really sure> ")
        if answer != keyword:
            Output.success("Deinstallation process was cancelled.")
        if Status.is_running():
            cls.stop()
        if Cronjob.is_registered():
            Cronjob.deregister()
        try:
            Output("Removing bin directory from PATH...")
            sys.path.remove(Paths.BIN)
        except ValueError:
            Output.info("bin directory not found in PATH.")
        Output.info(f"Removing PATH configuration from {Paths.BASHRC}")
        with open(Paths.BASHRC, 'r') as file:
            lines = file.readlines()
        with open(Paths.BASHRC, 'w') as file:
            for line in lines:
                if Paths.BIN not in line.strip("\n"):
                    file.write(line)
        Output.info("Copying install script to parent directory...")
        shutil.copy(Paths.RL_INSTALL, Paths.PARENT)
        Output.info("Removing all files...")
        shutil.rmtree(Paths.HOME)


class UserInterface:

    @classmethod
    def _check_for_no_further_arguments(cls, args: List[str], name: str):
        if len(args) != 1:
            Output.error(f"'rl {name}' takes no further arguments!\nRun 'rl help'.")

    @classmethod
    def _check_for_further_arguments(cls, args: List[str], count: int, name: str):
        if len(args) != count + 1:
            Output.error(f"'rl {name}' takes {count} further argument{'s' if count > 1 else ''}!\nRun 'rl help'.")

    @classmethod
    def run(cls, args: List[str]):
        if len(args) < 1:
            Output.error("Invalid number of arguments!\nRun 'rl help'.")

        if args[0] in ['setup', 'build', 'run', 'stop', 'restart', 'update', 'uninstall', 'help']:
            cls._check_for_no_further_arguments(args, args[0])
            if args[0] == 'setup':
                RlManager.setup()
                Output.success("Setup done.")
            elif args[0] == 'build':
                RlManager.build()
                Output.success("Building done.")
            elif args[0] == 'run':
                RlManager.run()
                Output.success("System is now running.")
            elif args[0] == 'stop':
                RlManager.stop()
                Output.success("System was stopped.")
            elif args[0] == 'restart':
                RlManager.setup()
                Output.success("System was restarted.")
            elif args[0] == 'update':
                RlManager.setup()
                Output.success("Update done.")
            elif args[0] == 'uninstall':
                RlManager.uninstall()
                Output.success("Deinstallation done.")
            elif args[0] == 'help':
                Output.print_file(Paths.HELP_RL)

        elif args[0] == 'config':
            cls._config(args[1:])
        elif args[0] == 'status':
            cls._status(args[1:])
        elif args[0] == 'cronjob':
            cls._cronjob(args[1:])
        elif args[0] == 'logs':
            cls._logs(args[1:])
        else:
            Output.error("Unknown command!\nRun 'rl help'.")

    @classmethod
    def _config(cls, args: List[str]):
        if len(args) < 1:
            Output.error("Invalid number of arguments!\nRun 'rl config help'.")

        if args[0] in ['list', 'wizard', 'help']:
            cls._check_for_no_further_arguments(args, f"config {args[0]}")
            if args[0] == 'list':
                for key in Config.GET_METHODS.keys():
                    print(f"{key}:\t{Config.GET_METHODS[key]()}")
            elif args[0] == 'wizard':
                ConfigWizard.run()
                Output.success("Exited wizard.")
            elif args[0] == 'help':
                Output.print_file(Paths.HELP_RL_CONFIG)

        elif args[0] == 'set':
            cls._check_for_further_arguments(args, 2, f"config {args[0]}")
            key, value = args[1], args[2]
            if key not in Config.SET_METHODS.keys():
                Output.error(f"Invalid key: {key}!\nRun 'rl config help'.")
            if not Config.validate_value(key, value):
                Output.error(f"Invalid value: {value}\nRun 'rl config help'.")
            Config.SET_METHODS[key](value)
            Output.success(f"Set {key} to {value}.")

        elif args[0] == 'get':
            cls._check_for_further_arguments(args, 1, f"config {args[0]}")
            key = args[1]
            if key not in Config.SET_METHODS.keys():
                Output.error(f"Invalid key: {key}!\nRun 'rl config help'.")
            print(f"{key}:\t{Config.GET_METHODS[key]()}")

        else:
            Output.error("Unknown command!\nRun 'rl config help'.")

    @classmethod
    def _status(cls, args: List[str]):
        if len(args) < 1:
            Output.error("Invalid number of arguments!\nRun 'rl status help'.")

        if args[0] in ['list', 'help']:
            if args[0] == 'list':
                for key in Status.GET_METHODS.keys():
                    print(f"{key}:\t{Status.GET_METHODS[key]()}")
            elif args[0] == 'help':
                Output.print_file(Paths.HELP_RL_STATUS)

        elif args[0] == 'get':
            cls._check_for_further_arguments(args, 1, f"status {args[0]}")
            key = args[1]
            if key not in Status.SET_METHODS.keys():
                Output.error(f"Invalid key: {key}!\nRun 'rl status help'.")
            print(f"{key}:\t{Status.GET_METHODS[key]()}")

        else:
            Output.error("Unknown command!\nRun 'rl status help'.")

    @classmethod
    def _cronjob(cls, args: List[str]):
        if len(args) < 1:
            Output.error("Invalid number of arguments!\nRun 'rl cronjob help'.")

        if args[0] in ['register', 'deregister', 'status', 'help']:
            if args[0] == 'register':
                Cronjob.register()
                Output.success("Cronjob registered.")
            elif args[0] == 'deregister':
                Cronjob.deregister()
                Output.success("Cronjob deregistered.")
            elif args[0] == 'status':
                print(f"cronjob:\t{Cronjob.is_registered()}")
            elif args[0] == 'help':
                Output.print_file(Paths.HELP_RL_CRONJOB)

        else:
            Output.error("Unknown command!\nRun 'rl cronjob help'.")

    @classmethod
    def _logs(cls, args: List[str]):
        if len(args) < 1:
            Output.error("Invalid number of arguments!\nRun 'rl logs help'.")

        if args[0] in ['list', 'latest', 'clear', 'help']:
            if args[0] == 'list':
                for filename in Logs.get_log_filenames():
                    print(filename)
            elif args[0] == 'latest':
                print(Logs.get_latest_log_filename())
            elif args[0] == 'clear':
                Logs.clear_logs()
                Output.success("All logfiles were deleted.")
            elif args[0] == 'help':
                Output.print_file(Paths.HELP_RL_LOGS)

        else:
            Output.error("Unknown command!\nRun 'rl logs help'.")


if __name__ == "__main__":
    UserInterface.run(sys.argv[1:])
