import os
from typing import Callable, Dict

import requests
from _rl.command import Command
from _rl.config import Config
from _rl.constants import Paths
from _rl.cronjob import Cronjob
from _rl.dns import Dns
from _rl.network import Network


class Status:

    @staticmethod
    def _check_localhost(port: int) -> bool:
        try:
            response = requests.get(f"http://localhost:{port}/", timeout=3)
            response.raise_for_status()
        except Exception:
            return False
        else:
            return True

    @classmethod
    def is_running(cls) -> bool:
        command = Command("pgrep -af python")
        running_py_scripts = command.get_output()
        if Paths.RL_RUN not in running_py_scripts:
            return False
        if Config.get_master():
            if not cls._check_localhost(80):
                return False
        if Config.get_device():
            if not cls._check_localhost(5000):
                return False
        return True

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

    @staticmethod
    def dns() -> bool:
        return Dns.is_installed()


Status.GET_METHODS: Dict[str, Callable] = {
    'running': Status.is_running,
    'cronjob': Status.is_cronjob_registered,
    'pi': Status.is_on_pi,
    'gateway_ip': Status.get_gateway_ip,
    'dns': Status.dns
}
