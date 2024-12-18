import subprocess
import json
from typing import List


class Network:

    hardcoded_ips: List[str] 
    HARDCODED_IPS_FILENAME: str = "config/hard_ips.json"
    with open(HARDCODED_IPS_FILENAME, 'r', encoding='utf-8') as file:
        hardcoded_ips = json.load(file)

    @classmethod
    def gateway_ip(cls) -> str:
        output = subprocess.check_output(
            "/sbin/ip route|awk '/default/ { print $3 }'",
            shell=True,
            stderr=subprocess.DEVNULL
        ).decode(encoding='ascii')
        return output.strip()

    @classmethod
    def local_ip_prefix(cls) -> str:
        return ".".join(cls.gateway_ip().split(".")[:3]) + "."

    @classmethod
    def local_ips(cls) -> List[str]:
        lines = subprocess.check_output(
            f"nmap -sP {cls.local_ip_prefix()}*",
            shell=True,
            stderr=subprocess.DEVNULL
        ).decode(encoding='ascii').split("\n")
        ip_lines = [
            line for line in lines
            if line.startswith("Nmap scan report for")
        ]
        ips = cls.hardcoded_ips + [
            line.split("(")[-1][:-1]
            if line.endswith(")")
            else line.split(" ")[-1]
            for line in ip_lines
        ]
        ips = list(set(ips))
        gateway_ip = cls.gateway_ip()
        return [
            ip for ip in ips
            if ip != gateway_ip
        ]
