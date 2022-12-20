import subprocess

from _rl.constants import Paths


class Command:

    _command: str

    def __init__(self, command: str):
        self._command = command

    def run(self, show_output: bool = True):
        subprocess.run(
            self._command,
            shell=True,
            stdout=(None if show_output else subprocess.DEVNULL),
            stderr=(None if show_output else subprocess.DEVNULL)
        )

    def run_background(self):
        subprocess.Popen(
            self._command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=Paths.HOME
        )

    def get_output(self) -> str:
        return subprocess.check_output(
            self._command,
            shell=True,
            stderr=subprocess.DEVNULL
        ).decode(encoding='ascii')

    def get_returncode(self, show_output: bool = True) -> int:
        process = subprocess.Popen(
            self._command,
            shell=True,
            stdout=(None if show_output else subprocess.DEVNULL),
            stderr=(None if show_output else subprocess.DEVNULL)
        )
        process.wait()
        return process.returncode
