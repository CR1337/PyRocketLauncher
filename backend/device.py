from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Tuple

import requests

from backend.config import Config
from backend.network import Network
from backend.logger import logger


class Device:

    # IP_PREFIX: str = ".".join(Instance.gateway_ip().split(".")[:3]) + "."
    REQUEST_TIMEOUT: int = Config.get_constant('request_timeout')
    # FIRST_IP_LAST_BYTE: int = 1
    # LAST_IP_LAST_BYTE: int = 254
    DEVICE_PORT: int = 5000

    _ip_address: str
    _device_id: str
    _initial_state: Dict[str, Any]

    @classmethod
    def _search_for_device(cls, ip_address) -> Tuple[str, str]:
        # ip_address = cls.IP_PREFIX + str(index)
        try:
            response = requests.get(
                f"http://{ip_address}:{cls.DEVICE_PORT}/discover",
                timeout=cls.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            device_id = response.json()['device_id']
            return (ip_address, device_id)
        except Exception:
            return None

    @classmethod
    def find_all(cls) -> List['Device']:
        ip_addresses = Network.local_ips()
        with ThreadPoolExecutor(
            max_workers=len(ip_addresses),
            thread_name_prefix="find_all_devices"
        ) as executor:
            futures = []

            for ip_address in ip_addresses:
                futures.append(
                    executor.submit(cls._search_for_device, ip_address)
                )

            devices = set()
            for f in futures:
                if f.result() is not None:
                    devices.add(f.result())

        result = []
        device_ids_found = set()
        for ip_address, device_id in devices:
            if device_id not in device_ids_found:
                device_ids_found.add(device_id)
                result.append(Device(ip_address, device_id))
        return result

    def __init__(self, ip_address: str, device_id: str):
        self._ip_address = ip_address
        self._device_id = device_id
        self._initial_state = self._get("state")

    def __hash__(self) -> int:
        return hash(self._device_id)

    def __eq__(self, other: 'Device') -> bool:
        return self._device_id == other.device_id

    def _request(
        self, method: str, url: str, data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        logger.debug(
            f"{method.capitalize()} request to {self._device_id}/{url}"
        )
        address = f"http://{self._ip_address}:{self.DEVICE_PORT}/{url}"
        try:
            if method == 'post':
                response = requests.post(
                    address,
                    json=data,
                    timeout=self.REQUEST_TIMEOUT
                )
            elif method == 'get':
                response = requests.get(
                    address,
                    timeout=self.REQUEST_TIMEOUT
                )
            elif method == 'delete':
                response = requests.delete(
                    address,
                    json=data,
                    timeout=self.REQUEST_TIMEOUT
                )
            return response.json()
        except requests.exceptions.Timeout:
            logger.exception(
                f"Timeout while {method.capitalize()} "
                f"request to {self._device_id}/{url}"
            )
            return {'error': 'timeout'}, None
        except requests.exceptions.RequestException:
            logger.exception(
                f"Exception while {method.capitalize()} "
                f"request to {self._device_id}/{url}"
            )
            return {'error': 'request'}, None

    def _post(
        self, url: str, data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        return self._request('post', url, data)

    def _get(self, url: str) -> Tuple[Dict[str, Any], int]:
        return self._request('get', url, None)

    def _delete(
        self, url: str, data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        return self._request('delete', url, data)

    def load_program(self, name: str, event_list: List) -> Dict[str, Any]:
        logger.debug(f"{self._device_id}: load program {name}")
        return self._post("program", {'name': name, 'event_list': event_list})

    def unload_program(self):
        logger.debug(f"{self._device_id}: unload program")
        return self._delete("program", {})

    def schedule_program(self, time: str):
        logger.debug(f"{self._device_id}: schedule program for {time}")
        return self._post(
            "program/control", {'action': 'schedule', 'time': time}
        )

    def unschedule_program(self):
        logger.debug(f"{self._device_id}: unschedule program")
        return self._post("program/control", {'action': 'unschedule'})

    def run_program(self):
        logger.debug(f"{self._device_id}: run program")
        return self._post("program/control", {'action': 'run'})

    def pause_program(self):
        logger.debug(f"{self._device_id}: pause program")
        return self._post("program/control", {'action': 'pause'})

    def continue_program(self):
        logger.debug(f"{self._device_id}: continue program")
        return self._post("program/control", {'action': 'continue'})

    def stop_program(self):
        logger.debug(f"{self._device_id}: stop program")
        return self._post("program/control", {'action': 'stop'})

    def run_testloop(self):
        logger.debug(f"{self._device_id}: run testloop")
        return self._post("testloop", {})

    def fire(self, letter: str, number: int):
        logger.debug(f"{self._device_id}: fire {letter}{number}")
        return self._post("fire", {'letter': letter, 'number': number})

    def get_system_time(self) -> str:
        logger.debug(f"{self._device_id}: get system time")
        return self._get("system-time")

    def set_hardware_lock(self, is_locked: bool):
        if is_locked:
            logger.debug(f"{self._device_id}: lock hardware")
        else:
            logger.debug(f"{self._device_id}: unlock hardware")
        return self._post("lock", {'is_locked': is_locked})

    def get_state(self) -> Dict[str, Any]:
        state = self._initial_state
        state['ip_address'] = self._ip_address
        return state

    def update(self):
        logger.debug(f"{self._device_id}: update")
        return self._post("update", {})

    @property
    def device_id(self) -> str:
        return self._device_id
