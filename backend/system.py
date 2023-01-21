import signal
import subprocess
from threading import Thread

import backend.time_util as tu
from backend.instance import Instance
from backend.logger import logger


class System:
    class ShutdownError(Exception):
        pass

    class ExternalTermination(Exception):
        pass

    update_needed: bool

    @classmethod
    def shutdown(cls):
        logger.info("Shutdown system")
        process = subprocess.Popen("halt", shell=True)
        process.wait()
        if process.returncode != 0:
            raise cls.ShutdownError()

    @classmethod
    def reboot(cls):
        logger.info("Reboot system")
        process = subprocess.Popen("reboot", shell=True)
        process.wait()
        if process.returncode != 0:
            raise cls.ShutdownError()

    @classmethod
    def run_ntp_service(cls):
        logger.info("Start NTP service")
        subprocess.Popen("service ntp start", shell=True)

    @classmethod
    def update(cls):
        def thread_handler():
            tu.sleep(1)
            subprocess.Popen("rl update", shell=True)
        logger.info("Installing updates")
        thread = Thread(target=thread_handler)
        thread.name = "update"
        thread.start()

    @staticmethod
    def _update_needed() -> bool:
        logger.debug("Checking for updates")
        if not Instance.on_pi():
            return False
        output = subprocess.check_output(
            "rl status get update",
            shell=True
        ).decode(encoding='ascii')
        status = output.split()[-1]
        if status == 'ahead':
            logger.warning("This branch is ahead!")
            return False
        elif status == 'diverged':
            logger.warning("This branch is diverged!")
            return False
        elif status == 'behind':
            logger.info("This branch is behind.")
            return True
        elif status == 'up_to_date':
            logger.debug("This branch in up to date.")
            return False
        elif status == 'no_internet':
            logger.info("Cannot check for updates. No Internet.")
            return False

    @classmethod
    def sigterm_handler(cls, *args):
        raise cls.ExternalTermination("SIGTERM received")


try:
    System.update_needed = System._update_needed()
except Exception:
    logger.exception("Error in update check!")
signal.signal(signal.SIGTERM, System.sigterm_handler)
