import os


class Environment:

    @classmethod
    def is_master(cls) -> bool:
        return bool(int(os.environ['IS_MASTER']))

    @classmethod
    def on_pi(cls) -> bool:
        return bool(int(os.environ['ON_PI']))

    @classmethod
    def debug(cls) -> bool:
        return bool(int(os.environ['DEBUG']))

    @classmethod
    def gateway_ip(cls) -> str:
        return os.environ['GATEWAY_IP']

    @classmethod
    def server_port(cls) -> int:
        return int(os.environ['SERVER_PORT'])

    @classmethod
    def get_prefix(cls) -> str:
        return "master" if cls._is_master else 'device'
