from typing import List

from _rl.command import Command
from _rl.constants import Paths
from _rl.format_validator import FormatValidator
from _rl.inout import Ask, Output
from _rl.network import Network


class DnsWizard():

    _needs_restart: bool = False

    @classmethod
    def _add_entry_wizard(cls):
        domain = Ask.string("Domain> ")
        if domain is None:
            return
        ip = Ask.string("Address> ")
        if ip is None:
            return
        if not FormatValidator.validate_ipv4(ip):
            Output.error("Ivalid ip!")
            return
        Dns.add_entry(domain, ip)
        cls._needs_restart = True
        Output.info("dns entry added.")

    @classmethod
    def _remove_entry_wizard(cls):
        print()
        print("Select an entries to remove:")
        print()
        entries = Dns.get_entries()
        if len(entries) == 0:
            print("no entries to remove")
            return
        selection = Ask.integer("> ", 0, len(entries))
        if selection is None:
            return
        if selection == len(entries):
            return
        domain, ip = entries[selection][0], entries[selection][1]
        Dns.remove_entry(domain, ip)
        cls._needs_restart = True
        Output.info(f"dns entry {domain} -> {ip} removed.")

    @classmethod
    def _print_main_menu(cls):
        print()
        print("[0] List entries")
        print("[1] Add entry")
        print("[2] Remove entry")
        print()
        print("[3] DONE")

    @classmethod
    def _mainloop(cls):
        while True:
            cls._print_main_menu()
            selection = Ask.integer("> ", 0, 4)
            if selection is None:
                break
            if selection == 3:
                break

            if selection == 0:
                Dns.print_entries()
            elif selection == 1:
                cls._add_entry_wizard()
            elif selection == 2:
                cls._remove_entry_wizard()
        if cls._needs_restart:
            Dns.restart()

    @classmethod
    def run(cls):
        if not Dns.is_installed():
            Output.critical("dns is not installed!")
        cls._needs_restart = False
        cls._mainloop()


class Dns:

    @classmethod
    def print_entries(cls):
        print()
        print("DNS entries:")
        print()
        entries = Dns.get_entries()
        if len(entries) == 0:
            print("no entries")
        else:
            for entry in entries:
                print(f"{entry[0]} -> {entry[1]}")

    @staticmethod
    def restart():
        Output.info("Restarting dns service...")
        command = Command("systemctl restart dnsmasq")
        if command.get_returncode() != 0:
            Output.unexpected_error()

    @classmethod
    def add_entry(cls, domain: str, ip: str):
        Output.info(f"Adding dns entry {domain} -> {ip}...")
        with open(Paths.DNSMASQ_CONF, 'a', encoding='ascii') as file:
            file.writelines([
                f"address=/{domain}/{ip}"
            ])

    @classmethod
    def remove_entry(cls, domain: str, ip: str):
        Output.info(f"Removing dns entry {domain} -> {ip}...")
        with open(Paths.DNSMASQ_CONF, 'r', encoding='ascii') as file:
            lines = file.readlines()
        keep_lines = []
        for line in lines:
            if domain in line and ip in line:
                continue
            keep_lines.append(line)
        with open(Paths.DNSMASQ_CONF, 'w', encoding='ascii') as file:
            file.writelines(keep_lines)

    @staticmethod
    def get_entries() -> List[List[str]]:
        entries = []
        with open(Paths.DNSMASQ_CONF, 'r', encoding='ascii') as file:
            lines = file.readlines()
        for line in lines:
            if line.startswith("address"):
                entry = line.split("=")[-1]
                _, domain, address = entry.split("/")
                entries.append([domain, address])
        return entries

    @classmethod
    def install(cls):
        Output.info("Installing dns...")
        if cls.is_installed():
            Output.critical("dns is already installed!")
        Output.info("Installing dns...")
        command = Command("apt -y install dnsmasq")
        if command.get_returncode() != 0:
            Output.unexpected_error()

        with open(Paths.DNSMASQ_CONF, 'w', encoding='ascii') as file:
            file.writelines([
                "listen-address=127.0.0.1\n",
                f"listen-address={Network.get_ip()}"
            ])

        with open(Paths.RESOLV_CONF, 'w', encoding='ascii') as file:
            file.writelines([
                "nameserver 127.0.0.1\n",
                f"nameserver {Network.get_gateway_ip()}"
            ])

        cls.restart()

    @classmethod
    def uninstall(cls):
        Output.info("Uninstalling dns...")
        if not cls.is_installed():
            Output.critical("dns is not installed!")
        Output.info("Disabling dns service...")
        command = Command("systemctl disable dnsmasq")
        if command.get_returncode() != 0:
            Output.unexpected_error()
        Output.info("Uninstalling dns...")
        command = Command("apt -y purge dnsmasq")
        if command.get_returncode() != 0:
            Output.unexpected_error()

        with open(Paths.RESOLV_CONF, 'w', encoding='ascii') as file:
            file.writelines([
                "nameserver 127.0.0.1"
            ])

    @staticmethod
    def is_installed() -> bool:
        command = Command("dpkg -l dnsmasq")
        if command.get_returncode(show_output=False) != 0:
            return False
        lines = command.get_output().split("\n")
        dnsmasq_line = None
        for line in lines:
            if 'dnsmasq' in line:
                dnsmasq_line = line
                break
        else:
            return False
        parts = [p for p in dnsmasq_line.split() if len(p) > 0]
        index = parts.index('dnsmasq')
        return parts[index + 1] != '<none>'
