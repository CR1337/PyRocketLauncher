from datetime import datetime

from _rl.command import Command


class FormatValidator:

    @staticmethod
    def get_all_timezones():
        command = Command("timedatectl list-timezones")
        timezones = [
            tz.strip()
            for tz in command.get_output().split("\n")
        ]
        return timezones

    @classmethod
    def validate_timezone(cls, value: str) -> bool:
        return value in cls.get_all_timezones()

    @staticmethod
    def validate_datetime(value: str) -> bool:
        try:
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def validate_time(value: str) -> bool:
        if len(value) != len("00:00:00"):
            return False
        values = value.split(":")
        if len(values) != 3:
            return False
        try:
            hours, minutes, seconds = [
                int(v) for v in values
            ]
        except ValueError:
            return False
        if not (0 <= hours <= 23):
            return False
        if not (0 <= minutes <= 59):
            return False
        if not (0 <= seconds <= 59):
            return False
        return True

    @staticmethod
    def validate_bool(value: str) -> bool:
        return value in ['0', '1']

    @staticmethod
    def validate_int(value: str, min_value: int, max_value: int) -> bool:
        try:
            value = int(value)
        except ValueError:
            return False
        else:
            if value > max_value:
                return False
            if value < min_value:
                return False
            return True

    @staticmethod
    def validate_ipv4(value: str) -> bool:
        if value.count(".") != 3:
            return False
        numbers = value.split(".")
        for number in numbers:
            try:
                number = int(number)
            except ValueError:
                return False
            if number < 0 or number > 255:
                return False
        return True
