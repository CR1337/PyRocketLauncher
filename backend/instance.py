import argparse
import os
import subprocess


class Instance:

    class ShutdownError(Exception):
        pass

    MODEL_PATH: str = "/sys/firmware/devicetree/base/model"

    _is_master: bool

    parser = argparse.ArgumentParser()
    parser.add_argument('--master', action='store_true')
    args = parser.parse_args()
    _is_master = bool(args.master)

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
        return 80 if cls._is_master else 5000

    @classmethod
    def get_prefix(cls) -> str:
        return "master" if cls._is_master else "device"

    @classmethod
    def shutdown(cls):
        process = subprocess.Popen("halt", shell=True)
        process.wait()
        if process.returncode != 0:
            raise cls.ShutdownError()

    @classmethod
    def reboot(cls):
        process = subprocess.Popen("reboot", shell=True)
        process.wait()
        if process.returncode != 0:
            raise cls.ShutdownError()
