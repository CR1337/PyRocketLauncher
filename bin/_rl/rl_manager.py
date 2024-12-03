import os
import shutil
import signal
import sys
import time

from _rl.command import Command
from _rl.config import AutoConfig, Config, ConfigWizard
from _rl.constants import ExitCodes, Paths
from _rl.cronjob import Cronjob
from _rl.format_validator import FormatValidator
from _rl.inout import Ask, Output
from _rl.status import Status


class RlManager:

    @classmethod
    def setup(cls):
        if Status.is_running():
            cls.stop()
        AutoConfig.run()
        ConfigWizard.run()
        if not Status.is_cronjob_registered():
            Cronjob.register()
        cls._change_directory_permissions()
        Output.info("This system should now be fully functional.")
        Output.info("For further options run: 'sudo rl help'")

    @staticmethod
    def run(no_wait: bool = False):
        if Status.is_running():
            Output.critical("System is already running!")
        if Config.get_device():
            Output.info("Starting device...")
            command = Command(
                [sys.executable, Paths.RL_RUN]
            )
            command.run_background()
        if Config.get_master():
            Output.info("Starting master...")
            command = Command(
                [sys.executable, Paths.RL_RUN, '--master']
            )
            command.run_background()
        if no_wait:
            return
        Output.info("Waiting for server running...")
        while not Status.is_running():
            time.sleep(1)

    @staticmethod
    def stop():
        if not Status.is_running():
            Output.critical("System is not running!")
        Output.info("Stopping system...")
        command = Command(f"pkill -{int(signal.SIGTERM)} -f {Paths.RL_RUN}")
        if command.get_returncode() != -int(signal.SIGTERM):
            Output.error("Error stopping device!")

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
        commands = [
            Command(cmd) for cmd in [
                f"git -C {Paths.HOME} pull",
                "apt update",
                'apt -y install $(grep -vE "^\\s*#" '
                f'{Paths.APT_REQUIREMENTS}  | tr "\\n" " ")',
                f"python3 -m pip install -r {Paths.PIP_REQUIREMENTS}"
            ]
        ]
        for command in commands:
            if command.get_returncode() != ExitCodes.SUCCESS:
                Output.unexpected_error()
        if was_running:
            cls.run()

    @staticmethod
    def _reenable_wifi_on_pi_zero_w():
        with open(Paths.MODEL, 'r', encoding='ascii') as file:
            if "Zero W" not in file.read():
                return
        Output.info("Enabling onboard WiFi on Pi Zero W (reboot needed)...")
        with open(Paths.CONFIG_TXT, 'r', encoding='ascii') as file:
            lines = file.readlines()
        lines = [
            line for line in lines
            if "dtoverlay=disable-wifi" not in line
        ]
        with open(Paths.CONFIG_TXT, 'w', encoding='ascii') as file:
            file.writelines(lines)

    @staticmethod
    def _change_directory_permissions():
        Output.info("Changing directory permissions...")
        command = Command(f"chmod -R 777 {Paths.PARENT}")
        if command.get_returncode() != ExitCodes.SUCCESS:
            Output.unexpected_error()

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
        Output.info("Removing bin directory from SECURE_PATH...")
        os.remove(Paths.SUDOERS_RL)
        cls._reenable_wifi_on_pi_zero_w()
        Output.info("Removing udev rules...")
        AutoConfig.remove_udev_rules()
        Output.info("Copying install script to parent directory...")
        shutil.copy(Paths.RL_INSTALL, Paths.PARENT)
        Output.info("Removing all files...")
        shutil.rmtree(Paths.HOME)

    @classmethod
    def emergency(cls):
        program_filename = input("Program filename> ")
        program_filename = os.path.join(Paths.HOME, program_filename)
        if not os.path.exists(program_filename):
            Output.critical(f"File {program_filename} does not exist!")

        schedule_time = input("Schedule time> ")
        if not FormatValidator.validate_time(schedule_time):
            Output.critical(
                f"Invalid time: {schedule_time}! "
                "Format should be: HH:MM:SS"
            )

        command = Command(
            f"python3 {Paths.RL_EMERGENCY} "
            f"{program_filename} {schedule_time}"
        )
        command.run()
