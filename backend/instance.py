import os
import subprocess
import sys


class Instance:

    MODEL_PATH: str = "/sys/firmware/devicetree/base/model"

    _is_master: bool
    try:
        _is_master = sys.argv[1] == '--master'
    except IndexError:
        _is_master = False

    @classmethod
    def is_master(cls) -> bool:
        return cls._is_master

    @classmethod
    def on_pi(cls) -> bool:
        if not os.path.exists(cls.MODEL_PATH):
            return False
        try:
            with open(
                cls.MODEL_PATH,
                'r', encoding='ascii'
            ) as file:
                return "pi" in file.read().lower()
        except FileNotFoundError:
            return False

    @classmethod
    def gateway_ip(cls) -> str:
        output = subprocess.check_output(
            "/sbin/ip route|awk '/default/ { print $3 }'",
            shell=True,
            stderr=subprocess.DEVNULL
        ).decode(encoding='ascii')
        return output.strip()

    @classmethod
    def get_server_port(cls) -> int:
        return 8080 if cls._is_master else 5000

    @classmethod
    def get_prefix(cls) -> str:
        return "master" if cls._is_master else "device"
