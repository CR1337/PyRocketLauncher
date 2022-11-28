import logging
import os
from datetime import datetime
from typing import Dict, List

from backend.instance import Instance


class Logger:

    START: str = ">>>"
    SEP: str = ":::"

    _logger: logging.Logger

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)

        filename = (
            f"logs/{Instance.get_prefix()}-"
            f"{str(datetime.now()).replace(' ', '-').replace(':', '-')}"
            ".log"
        )

        stream_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(filename)

        stream_handler.setLevel(logging.WARNING)
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            f'{self.START}%(asctime)s{self.SEP}%(levelname)s'
            f'{self.SEP}%(threadName)s'
            f'{self.SEP}%(filename)s{self.SEP}%(lineno)d{self.SEP}%(message)s',
            datefmt='%Y-%m-%d %H.%M.%S'
        )

        stream_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        self._logger.addHandler(stream_handler)
        self._logger.addHandler(file_handler)

    def debug(self, message: str):
        self._logger.debug(message)

    def info(self, message: str):
        self._logger.info(message)

    def exception(self, message: str):
        self._logger.exception(message)

    @staticmethod
    def get_log_files() -> List[str]:
        return [
            filename for filename
            in os.listdir("logs")
            if filename.endswith(".log")
        ]

    @staticmethod
    def get_log_file_content(name: str) -> str:
        with open(f"logs/{name}", 'r', encoding='utf-8') as file:
            return file.read()

    @classmethod
    def get_log_structured_file_content(
        cls, name: str
    ) -> List[Dict[str, str]]:
        content = cls.get_log_file_content(name).replace("\n", "")
        structured_content = []
        for line in content.split(cls.START)[1:]:
            time, level, thread, file, lineno, message = line.split(cls.SEP)
            structured_content.append({
                'time': time,
                'level': level,
                'thread': thread,
                'file': file,
                'line': lineno,
                'message': message
            })
        return structured_content

    @staticmethod
    def logfile_exists(name: str) -> bool:
        return os.path.exists(os.path.join("logs", name))


logger = Logger()
