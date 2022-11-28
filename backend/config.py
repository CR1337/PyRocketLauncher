import json
from typing import Any, Dict

from backend.logger import logger
from backend.rl_exception import RlException


class Config:

    class ConfigKeyError(RlException):
        pass

    CONFIG_FILENAME: str = "config/config.json"
    CONSTANTS_FILENAME: str = "config/constants.json"

    _config_data: Dict[str, Any]
    _constants_data: Dict[str, Any]

    with open(CONFIG_FILENAME, 'r', encoding='utf-8') as file:
        _config_data = json.load(file)

    with open(CONSTANTS_FILENAME, 'r', encoding='utf-8') as file:
        _constants_data = json.load(file)

    @classmethod
    def _raise_for_key(
        cls, key: str, dictionary: Dict[str, Any], display_name: str
    ):
        if key not in dictionary.keys():
            raise cls.ConfigKeyError(
                f"{display_name} key '{key}' does not exist"
            )

    @classmethod
    def _get(cls, key: str, dictionary: Dict[str, Any], display_name: str):
        cls._raise_for_key(key, dictionary, display_name)
        return dictionary[key]

    @classmethod
    def _set(
        cls, key: str, value: Any, dictionary: Dict[str, Any],
        display_name: str, filename: str
    ):
        logger.info(f"Set '{key}' to '{value}'")
        cls._raise_for_key(key, dictionary, display_name)
        dictionary[key] = value
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(dictionary, file, indent=4)

    @classmethod
    def get_value(cls, key: str) -> Any:
        return cls._get(key, cls._config_data, "Config")

    @classmethod
    def get_constant(cls, key: str) -> Any:
        return cls._get(key, cls._constants_data, "Constants")

    @classmethod
    def set_value(cls, key: str, value: Any):
        cls._set(key, value, cls._config_data, "Config", cls.CONFIG_FILENAME)

    @classmethod
    def set_constant(cls, key: str, value: Any):
        cls._set(
            key, value, cls._constants_data,
            "Constants", cls.CONSTANTS_FILENAME
        )

    @classmethod
    def get_state(cls):
        return {
            'config': cls._config_data,
            'constants': cls._constants_data
        }

    @classmethod
    def update_state(cls, data: Dict[str, Any]):
        logger.debug("Update state")
        for key, value in data['config'].items():
            cls.set_value(key, value)
        for key, value in data['constants'].items():
            cls.set_constant(key, value)
