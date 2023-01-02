import subprocess

from backend.logger import logger


class System:

    class ShutdownError(Exception):
        pass

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
