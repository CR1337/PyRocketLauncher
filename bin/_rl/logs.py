import os
from typing import Dict, List

from _rl.constants import Paths, TerminalColors
from _rl.inout import Ask, Output


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
        filenames = [
            os.path.join(os.path.abspath(Paths.LOGS), fn)
            for fn in os.listdir(Paths.LOGS)
        ]
        log_filenames = [fn for fn in filenames if fn.endswith(".log")]
        if not len(log_filenames):
            Output.critical("There are no logfiles.")
        return log_filenames

    @classmethod
    def get_latest_log_filename(cls, mode: str) -> str:
        log_filenames = [
            fn for fn in sorted(cls.get_log_filenames())
            if mode in fn.split(os.path.sep)[-1]
        ]
        return log_filenames[-1]

    @classmethod
    def clear_logs(cls):
        if not Ask.boolean(
            "Are you sure you want to delete all logfiles? (yn)> "
        ):
            Output.success("Logfile deletion was cancelled.")
        Output.info("Deleting all logfiles...")
        for filename in cls.get_log_filenames():
            os.remove(os.path.join(Paths.LOGS, filename))

    @classmethod
    def print_latest_raw(cls):
        latest_log_filename = cls.get_latest_log_filename()
        with open(
            os.path.join(Paths.LOGS, latest_log_filename), 'r',
            encoding='utf-8'
        ) as file:
            print(file.read())

    @classmethod
    def print_latest_pretty(cls):
        latest_log_filename = cls.get_latest_log_filename()
        with open(
            os.path.join(Paths.LOGS, latest_log_filename), 'r',
            encoding='utf-8'
        ) as file:
            lines = file.readlines()
        for line in lines:
            level = line.split(cls.SEP)[1]
            color_code = cls.LEVEL_COLORS.get(
                level, TerminalColors.DEFAULT
            )
            print(f"{color_code}{line}{TerminalColors.RESET}")
