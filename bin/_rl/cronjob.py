import os

from _rl.constants import Paths
from _rl.inout import Output


class Cronjob:

    @classmethod
    def register(cls):
        Output.info("Registering cronjob...")
        if cls.is_registered():
            Output.critical("A cronjob was already registered!")
        with open(Paths.CRONJOB, 'w', encoding='ascii') as file:
            file.write(f"@reboot root {Paths.SELF} run_no_wait\n")
        os.chmod(Paths.CRONJOB, int('600', 8))

    @classmethod
    def deregister(cls):
        Output.info("Deregistering cronjob...")
        if not cls.is_registered():
            Output.critical("There is no cronjob registered!")
        os.remove(Paths.CRONJOB)

    @staticmethod
    def is_registered() -> bool:
        return os.path.exists(Paths.CRONJOB)
