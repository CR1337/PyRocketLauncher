import logging
import os
from datetime import datetime
from typing import Dict, List

from backend.instance import Instance

START: str = ">>>"
SEP: str = ":::"


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
    '>>>%(asctime)s:::%(levelname)s:::%(threadName)s'
    ':::%(filename)s:::%(lineno)d:::%(message)s',
    datefmt='%Y-%m-%d %H.%M.%S'
)

stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)


def get_log_files() -> List[str]:
    return [
        filename for filename
        in os.listdir("logs")
        if filename.endswith(".log")
    ]


def get_log_file_content(name: str) -> str:
    with open(f"logs/{name}", 'r', encoding='utf-8') as file:
        return file.read()


def get_log_structured_file_content(name: str) -> List[Dict[str, str]]:
    content = get_log_file_content(name).replace("\n", "")
    structured_content = []
    for line in content.split(START)[1:]:
        time, level, thread, file, lineno, message = line.split(SEP)
        structured_content.append({
            'time': time,
            'level': level,
            'thread': thread,
            'file': file,
            'line': lineno,
            'message': message
        })
    return structured_content


def logfile_exists(name: str) -> bool:
    return os.path.exists(os.path.join("logs", name))
