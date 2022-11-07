import json
from typing import Any, Dict

from backend.logger import logger


class Config:
    CONFIG_FILENAME: str = f"config/config.json"
    CONSTANTS_FILENAME: str = f"config/constants.json"

    _config_data: Dict[str, Any]
    _constants_data: Dict[str, Any]

    with open(CONFIG_FILENAME, 'r', encoding='utf-8') as file:
        _config_data = json.load(file)

    with open(CONSTANTS_FILENAME, 'r', encoding='utf-8') as file:
        _constants_data = json.load(file)

    @classmethod
    def get_value(cls, key: str) -> Any:
        if key not in cls._config_data.keys():
            raise KeyError(f"Config key '{key}' does not exist")
        return cls._config_data[key]

    @classmethod
    def get_constant(cls, key: str) -> Any:
        if key not in cls._constants_data.keys():
            raise KeyError(f"Constants key '{key}' does not exist")
        return cls._constants_data[key]

    @classmethod
    def set_value(cls, key: str, value: Any):
        logger.info(f"Set '{key}' to '{value}'")
        if key not in cls._config_data.keys():
            raise KeyError(f"Config key '{key}' does not exist")
        cls._config_data[key] = value
        with open(cls.CONFIG_FILENAME, 'w', encoding='utf-8') as file:
            json.dump(cls._config_data, file, indent=4)

    @classmethod
    def set_constant(cls, key: str, value: Any):
        logger.info(f"Set '{key}' to '{value}'")
        if key not in cls._constants_data.keys():
            raise KeyError(f"Constants key '{key}' does not exist")
        cls._constants_data[key] = value
        with open(cls.CONSTANTS_FILENAME, 'w', encoding='utf-8') as file:
            json.dump(cls._constants_data, file, indent=4)

    @classmethod
    def get_state(cls):
        return {
            'config': cls._config_data,
            'constants': cls._constants_data
        }

    @classmethod
    def update_state(cls, data: Dict[str, Any]):
        logger.info("Update state")
        for key, value in data['config'].items():
            cls.set_value(key, value)
        for key, value in data['constants'].items():
            cls.set_constant(key, value)
