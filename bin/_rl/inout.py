import sys
from difflib import SequenceMatcher

from _rl.constants import ExitCodes, TerminalColors
from _rl.format_validator import FormatValidator


class Ask:

    @staticmethod
    def string(prompt: str) -> str:
        try:
            return input(prompt)
        except KeyboardInterrupt:
            print()
            return None

    @classmethod
    def boolean(cls, prompt: str) -> bool:
        while True:
            answer = cls.string(prompt).lower()
            if answer is None:
                return None
            if len(answer) == 1 and answer in "yn":
                return answer == 'y'

    @classmethod
    def integer(
        cls, prompt: str, min_value: int = None, max_value: int = None
    ) -> int:
        while True:
            answer = cls.string(prompt)
            if answer is None:
                return None
            try:
                number = int(answer)
            except ValueError:
                pass
            else:
                if min_value is not None:
                    if number < min_value:
                        continue
                if max_value is not None:
                    if number > max_value:
                        continue
                return number

    @classmethod
    def timezone(cls, prompt: str) -> str:
        timezones = FormatValidator.get_all_timezones()
        lower_timezones = [
            tz.lower()
            for tz in timezones
        ]
        while True:
            answer = cls.string(prompt)
            if answer is None:
                return None
            if answer.lower() in lower_timezones:
                index = lower_timezones.index(answer.lower())
                return timezones[index]

            def sort_key(item: str) -> float:
                return SequenceMatcher(None, answer, item).ratio()

            sorted_timezones = sorted(timezones, key=sort_key, reverse=True)

            print()
            print("Did you mean...?")
            print("Type a number.")
            for idx, timezone in enumerate(sorted_timezones[:10]):
                print(f"[{idx}] {timezone}")

            selection = Ask.integer("> ", 0, 9)
            if selection is None:
                return None

            return sorted_timezones[selection]

    @classmethod
    def datetime(cls, prompt: str) -> str:
        while True:
            answer = cls.string(prompt)
            if answer is None:
                return None
            if FormatValidator.validate_datetime(answer):
                return answer


class Output:

    @staticmethod
    def info(message: str):
        print(f"{TerminalColors.CYAN}INFO> {message}{TerminalColors.RESET}")

    @staticmethod
    def important(message: str):
        print(
            f"{TerminalColors.MAGENTA}IMPORTANT> "
            f"{message}{TerminalColors.RESET}"
        )

    @staticmethod
    def error(message: str):
        print(
            f"{TerminalColors.RED}ERROR> {message}{TerminalColors.RESET}",
            file=sys.stderr
        )

    @classmethod
    def critical(cls, message: str):
        cls.error(message)
        exit(1)

    @staticmethod
    def success(message: str):
        print(
            f"{TerminalColors.GREEN}SUCCESS> {message}{TerminalColors.RESET}"
        )
        exit(ExitCodes.SUCCESS)

    @classmethod
    def wrong_usage(cls):
        cls.error("Wrong arguments! Run 'sudo rl help' for help.")

    @staticmethod
    def print_file(filename: str):
        with open(filename, 'r', encoding='utf-8') as file:
            print(file.read())
        exit(ExitCodes.SUCCESS)

    @classmethod
    def unexpected_error(cls):
        cls.critical("Unexpected error!")
