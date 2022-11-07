import os


class Mode:

    _is_master: bool = bool(int(os.environ['IS_MASTER']))
    _debug: bool = bool(int(os.environ['DEBUG']))
    _on_pi: bool = bool(int(os.environ['ON_PI']))

    print(os.environ['ON_PI'])

    @classmethod
    def is_master(cls) -> bool:
        return cls._is_master

    @classmethod
    def on_pi(cls) -> bool:
        return cls._on_pi

    @classmethod
    def debug(cls) -> bool:
        return cls._debug

    @classmethod
    def get_prefix(cls) -> str:
        return "master" if cls._is_master else 'device'
