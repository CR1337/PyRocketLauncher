import os


class Paths:

    SELF: str = "/" + os.path.join(
        *os.path.realpath(__file__).split(os.path.sep)[:-2], "rl"
    )

    PARENT: str = "/" + os.path.join(*(SELF.split(os.path.sep)[:-3]))
    HOME: str = "/" + os.path.join(*(SELF.split(os.path.sep)[:-2]))
    CONFIG_PATH: str = os.path.join(HOME, "config")
    BIN: str = os.path.join(HOME, "bin")
    LOGS: str = os.path.join(HOME, "logs")
    HELP: str = os.path.join(HOME, "doc/rl_help")

    RL_RUN: str = os.path.join(HOME, "rl_run.py")
    RL_EMERGENCY: str = os.path.join(HOME, "rl_emergency.py")

    HELP_RL: str = os.path.join(HELP, "rl.txt")
    HELP_RL_CONFIG: str = os.path.join(HELP, "rl_config.txt")
    HELP_RL_STATUS: str = os.path.join(HELP, "rl_status.txt")
    HELP_RL_CRONJOB: str = os.path.join(HELP, "rl_cronjob.txt")
    HELP_RL_LOGS: str = os.path.join(HELP, "rl_logs.txt")

    RL_INSTALL: str = os.path.join(BIN, "rl-install")

    CONFIG: str = os.path.join(CONFIG_PATH, "config.json")
    RUN_CONFIG: str = os.path.join(CONFIG_PATH, "run_config.json")

    MODEL: str = "/sys/firmware/devicetree/base/model"
    I2C: str = "/dev/i2c-1"
    SUDOERS_RL: str = "/etc/sudoers.d/rl"
    CRONJOB: str = "/etc/cron.d/rl"
    CONFIG_TXT: str = "/boot/config.txt"

    RESOLV_CONF: str = "/etc/resolv.conf"

    DHCPCD_CONF: str = "/etc/dhcpcd.conf"


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


class ExitCodes:

    SUCCESS: int = 0


class UserIds:

    ROOT: int = 0
