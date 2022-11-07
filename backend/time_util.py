import shlex
import subprocess
import time
from datetime import datetime

from backend.config import Config
from backend.logger import logger

TIME_ORIGIN: datetime = datetime(1970, 1, 1)
TIME_RESOLUTION: float = Config.get_constant('time_resolution')


def get_system_time() -> str:
    return datetime.now().replace(tzinfo=None).isoformat()


def set_system_time(t: str):
    logger.debug(f"Set system time to {t}")
    subprocess.call(shlex.split("timedatectl set-ntp false"))
    subprocess.call(shlex.split(f"sudo date -s '{t}'"))


def timestamp_now() -> float:
    return (datetime.now() - TIME_ORIGIN).total_seconds()


def string_to_datetime(t: str) -> datetime:
    return datetime.fromisoformat(t)


def datetime_to_string(dt: datetime) -> str:
    return dt.replace(tzinfo=None).isoformat()


def datetime_to_timestamp(dt: str) -> float:
    return (dt - TIME_ORIGIN).total_seconds()


def datetime_reached(dt: datetime) -> bool:
    return datetime.now() >= dt


def sleep(seconds: float):
    time.sleep(seconds)
