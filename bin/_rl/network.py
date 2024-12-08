import os

from _rl.command import Command
from _rl.constants import Paths
from _rl.inout import Output


class Network:

    INTERFACE_LINE: str = "interface wlan0"

    @staticmethod
    def get_gateway_ip() -> str:
        command = Command("/sbin/ip route|awk '/default/ { print $3 }'")
        return command.get_output().strip()

    @classmethod
    def get_ip(cls) -> str:
        command = Command("hostname --all-ip-addresses")
        ips = command.get_output().strip()
        ips = ips.split(" ")

        for ip in ips:
            if ip.startswith(cls._get_gateway_ip_begin()):
                return ip

        Output.critical("Could not determine own ip!")

    @classmethod
    def _get_gateway_ip_begin(cls) -> str:
        return ".".join(cls.get_gateway_ip().split(".")[0:3])

    @classmethod
    def _is_interface_line(cls, line: str) -> bool:
        return not line.startswith("#") and cls.INTERFACE_LINE in line

    @classmethod
    def set_static_ip(cls, last_byte: int):
        if cls.is_ip_static():
            cls.unset_static_ip()
        ip_begin = cls._get_gateway_ip_begin()
        content = (
            f"{cls.INTERFACE_LINE}\n"
            f"static routers={ip_begin}.1\n"
            f"static domain_name_servers={ip_begin}.1\n"
            f"static ip_address={ip_begin}.{last_byte}\n"
        )
        with open(Paths.DHCPCD_CONF, 'a', encoding='ascii') as file:
            file.write(content)

    @classmethod
    def unset_static_ip(cls):
        with open(Paths.DHCPCD_CONF, 'r', encoding='ascii') as file:
            lines = file.readlines()
        keep_lines = []
        counter = -1
        for line in lines:
            if cls._is_interface_line(line):
                counter = 0
            if counter >= 0:
                counter += 1
            if counter < 0 or counter > 4:
                keep_lines.append(line)
        with open(Paths.DHCPCD_CONF, 'w', encoding='ascii') as file:
            file.writelines(keep_lines)

    @classmethod
    def get_static_ip_byte(cls) -> int:
        if not cls.is_ip_static():
            return -1
        with open(Paths.DHCPCD_CONF, 'r', encoding='ascii') as file:
            lines = file.readlines()
        ip_line = None
        for idx, line in enumerate(lines):
            if cls._is_interface_line(line):
                ip_line = lines[idx + 3]
                break
        else:
            return -1
        return int(ip_line.strip().split(".")[-1])

    @classmethod
    def is_ip_static(cls) -> bool:
        if not os.path.exists(Paths.DHCPCD_CONF):
            return False
        with open(Paths.DHCPCD_CONF, 'r', encoding='ascii') as file:
            lines = file.readlines()
        for line in lines:
            if cls._is_interface_line(line):
                return True
        return False
