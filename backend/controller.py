from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any, Dict, List

import backend.time_util as tu
from backend.address import Address
from backend.command import Command
from backend.config import Config
from backend.device import Device
from backend.hardware import Hardware
from backend.instance import Instance
from backend.led_controller import LedController
from backend.logger import logger
from backend.program import Program
from backend.rl_exception import RlException
from backend.schedule import Schedule
from backend.state_machine import State, StateMachine
from backend.system import System
from backend.zipfile_handler import ZipfileHandler


def lock(func):
    def wrapper(*args, **kwargs):
        Controller.controller_lock.acquire(blocking=True)
        logger.debug("Controller locked")
        result = func(*args, **kwargs)
        Controller.controller_lock.release()
        logger.debug("Controller unlocked")
        return result
    return wrapper


def raise_for_state_transition(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except StateMachine.InvalidTransitionError as e:
            raise DeviceController.InvalidTransitionError(e.message)
    return wrapper


class DeviceController:

    class InvalidTransitionError(RlException):
        pass

    class ProgramIsLoadedError(RlException):
        pass

    _state_machine: StateMachine = StateMachine()

    NOT_LOADED: State = _state_machine.add_state('not_loaded', is_initial=True)
    LOADED: State = _state_machine.add_state('loaded')
    SCHEDULED: State = _state_machine.add_state('scheduled')
    RUNNING: State = _state_machine.add_state('running')
    PAUSED: State = _state_machine.add_state('paused')

    LOCAL_PROGRAM_PATH: str = "programs/local_program.zip"

    _program: Program = None
    _schedule: Schedule = None
    controller_lock: Lock = Lock()

    @classmethod
    def _load_program(cls, program: Program):
        cls._program = program
        LedController.instance().load_preset('loaded')
        logger.debug(f"Program {program.name} loaded")

    @classmethod
    def _unload_program(cls):
        if cls._schedule is not None:
            cls._unschedule_program()
        cls._program = None
        LedController.instance().load_preset('idle')
        logger.debug("Program unloaded")

    @classmethod
    def _run_program(cls):
        cls._program.run(callback=cls._program_finished)
        logger.debug("Programm running")

    @classmethod
    def _schedule_program(cls, time: str):
        cls._schedule = Schedule(time, cls.run_program)
        cls._schedule.start()
        logger.debug(f"Program scheduled for {time}")

    @classmethod
    def _unschedule_program(cls):
        cls._schedule.cancel()
        cls._schedule = None
        logger.debug("Program unscheduled")

    @classmethod
    def _pause_program(cls):
        cls._program.pause()
        logger.debug("Program paused")

    @classmethod
    def _continue_program(cls):
        cls._program.continue_()
        logger.debug("Program continued")

    @classmethod
    def _stop_program(cls):
        cls._program.stop()
        logger.debug("Program stopped")

    @classmethod
    def _program_finished(cls):
        cls._unload_program()
        cls._state_machine.reset()
        logger.info("Program finished")

    @classmethod
    def load_local_program(cls):
        name = "Local Program"
        with open(cls.LOCAL_PROGRAM_PATH, 'rb') as file:
            data = file.read()
        cls.load_program(name, data, is_zip=True)

    @classmethod
    @lock
    @raise_for_state_transition
    def load_program(cls, name: str, data: Any, is_zip: bool):
        logger.info(f"Load program {name}")
        if is_zip:
            program = Program.from_zip(name, data)
        else:
            program = Program.from_json(name, data)
        cls._state_machine.transition(cls.LOADED, program)

    @classmethod
    @lock
    @raise_for_state_transition
    def unload_program(cls):
        logger.info("Unload program")
        cls._state_machine.transition(cls.NOT_LOADED)

    @classmethod
    @lock
    @raise_for_state_transition
    def schedule_program(cls, time: str):
        logger.info(f"Schedule program for {time}")
        cls._state_machine.transition(cls.SCHEDULED, time)

    @classmethod
    @lock
    @raise_for_state_transition
    def unschedule_program(cls):
        logger.info("Unschedule program")
        cls._state_machine.transition(cls.LOADED)

    @classmethod
    @lock
    @raise_for_state_transition
    def run_program(cls):
        logger.info("Run program")
        cls._state_machine.transition(cls.RUNNING)

    @classmethod
    @lock
    @raise_for_state_transition
    def pause_program(cls):
        logger.info("Pause program")
        cls._state_machine.transition(cls.PAUSED)

    @classmethod
    @lock
    @raise_for_state_transition
    def continue_program(cls):
        logger.info("Continue program")
        cls._state_machine.transition(cls.RUNNING)

    @classmethod
    @lock
    @raise_for_state_transition
    def stop_program(cls):
        logger.info("Stop program")
        cls._state_machine.transition(cls.NOT_LOADED)

    @classmethod
    @lock
    @raise_for_state_transition
    def run_testloop(cls):
        logger.info("Run testloop")
        program = Program.testloop_program()
        cls._state_machine.transition(cls.LOADED, program)
        cls._state_machine.transition(cls.RUNNING)

    @classmethod
    @lock
    def fire(cls, letter: str, number: int):
        logger.info(f"Fire {letter}{number}")
        if Hardware.is_locked():
            raise Hardware.HardwareLockedError(
                f"Cannot light {letter}{number}. "
                "Hardware is locked!"
            )
        address = Address(
            Config.get_value('device_id'),
            letter,
            number
        )
        if cls._state_machine.state == cls.NOT_LOADED:
            command = Command(address, 0, f"manual_fire_command_{address}")
            command.light()
        else:
            raise cls.ProgramIsLoadedError(
                "Can only fire when not program is loaded"
            )

    @classmethod
    def update(cls):
        logger.info("Updating")
        if System.update_needed:
            System.update()
        else:
            logger.info("No update needed")

    @classmethod
    def get_system_time(cls) -> str:
        return tu.get_system_time()

    @classmethod
    def get_state(cls) -> Dict[str, Any]:
        return {
            'controller': {
                'state': cls._state_machine.state.name,
                'system_time': cls.get_system_time()
            },
            'hardware': Hardware.get_state(),
            'config': Config.get_state(),
            'schedule': (
                None if cls._schedule is None
                else cls._schedule.get_state()
            ),
            'program': (
                None if cls._program is None
                else cls._program.get_state()
            ),
            'update_needed': System.update_needed,
            'is_remote': False
        }


DeviceController._state_machine.add_transition(
    DeviceController.NOT_LOADED,
    DeviceController.LOADED,
    DeviceController._load_program
)
DeviceController._state_machine.add_transition(
    DeviceController.LOADED,
    DeviceController.NOT_LOADED,
    DeviceController._unload_program
)
DeviceController._state_machine.add_transition(
    DeviceController.SCHEDULED,
    DeviceController.NOT_LOADED,
    DeviceController._unload_program
)
DeviceController._state_machine.add_transition(
    DeviceController.LOADED,
    DeviceController.RUNNING,
    DeviceController._run_program
)
DeviceController._state_machine.add_transition(
    DeviceController.LOADED,
    DeviceController.SCHEDULED,
    DeviceController._schedule_program
)
DeviceController._state_machine.add_transition(
    DeviceController.SCHEDULED,
    DeviceController.LOADED,
    DeviceController._unschedule_program
)
DeviceController._state_machine.add_transition(
    DeviceController.SCHEDULED,
    DeviceController.RUNNING,
    DeviceController._run_program
)
DeviceController._state_machine.add_transition(
    DeviceController.RUNNING,
    DeviceController.PAUSED,
    DeviceController._pause_program
)
DeviceController._state_machine.add_transition(
    DeviceController.RUNNING,
    DeviceController.NOT_LOADED,
    DeviceController._stop_program
)
DeviceController._state_machine.add_transition(
    DeviceController.PAUSED,
    DeviceController.RUNNING,
    DeviceController._continue_program
)
DeviceController._state_machine.add_transition(
    DeviceController.PAUSED,
    DeviceController.NOT_LOADED,
    DeviceController._stop_program
)


class MasterController:

    _devices: Dict[str, Device] = dict()
    controller_lock: Lock = Lock()

    @classmethod
    def search_devices(cls) -> List[str]:
        logger.info("Search devices")
        found_devices = Device.find_all()
        logger.info(f"Found devices: {[d.device_id for d in found_devices]}")
        new_devices = []

        next_device = False
        for found_device in found_devices:
            for device_id in cls._devices.keys():
                if found_device.device_id == device_id:
                    next_device = True
                    break
            if next_device:
                next_device = False
                continue

            cls._devices[found_device.device_id] = found_device
            new_devices.append(found_device)

        logger.info(f"New devices: {[d.device_id for d in new_devices]}")
        return {
            device_id: device.get_state()
            for device_id, device
            in cls._devices.items()
        }

    @classmethod
    def _call_device_method(
        cls, method_name: str, *args, **kwargs
    ) -> Dict[str, Dict]:
        if not len(cls._devices):
            return {}
        with ThreadPoolExecutor(
            max_workers=len(cls._devices),
            thread_name_prefix=f"call_device_{method_name}"
        ) as executor:
            futures = {
                device_id: executor.submit(
                    getattr(device, method_name),
                    *args, **kwargs
                )
                for device_id, device in cls._devices.items()
            }
            return {
                device_id: f.result()
                for device_id, f in futures.items()
            }
        
    @classmethod
    @lock
    def load_local_program(cls):
        name = "Local Program"
        with open(DeviceController.LOCAL_PROGRAM_PATH, 'rb') as file:
            data = file.read()
        zipfile_handler = ZipfileHandler(data)
        return cls._call_device_method("load_local_program", name, zipfile_handler)

    @classmethod
    @lock
    def load_program(cls, name: str, data: Any, is_zip: bool):
        logger.info(f"Load program {name}")
        if is_zip:
            zipfile_handler = ZipfileHandler(data)
            return cls._call_device_method("load_zip_program", name, zipfile_handler)
        else:
            Program.raise_on_json(data)
            return cls._call_device_method("load_program", name, data)

    @classmethod
    @lock
    def unload_program(cls):
        logger.info("Unload program")
        return cls._call_device_method("unload_program")

    @classmethod
    @lock
    def schedule_program(cls, time: str):
        logger.info(f"Schedule program for {time}")
        return cls._call_device_method("schedule_program", time)

    @classmethod
    @lock
    def unschedule_program(cls):
        logger.info("Unschedule program")
        return cls._call_device_method("unschedule_program")

    @classmethod
    @lock
    def run_program(cls):
        logger.info("Run program")
        return cls._call_device_method("run_program")

    @classmethod
    @lock
    def pause_program(cls):
        logger.info("Pause program")
        return cls._call_device_method("pause_program")

    @classmethod
    @lock
    def continue_program(cls):
        logger.info("Continue program")
        return cls._call_device_method("continue_program")

    @classmethod
    @lock
    def stop_program(cls):
        logger.info("Stop program")
        return cls._call_device_method("stop_program")

    @classmethod
    @lock
    def run_testloop(cls):
        logger.info("Run testloop")
        return cls._call_device_method("run_testloop")

    @classmethod
    @lock
    def fire(cls, device_id: str, letter: str, number: int):
        logger.info(f"Fire {device_id}::{letter}{number}")
        return cls._devices[device_id].fire(letter, number)

    @classmethod
    def get_system_time(cls) -> str:
        return tu.get_system_time()

    @classmethod
    @lock
    def set_hardware_lock(cls, is_locked: bool):
        if is_locked:
            logger.info("Lock hardware")
        else:
            logger.info("Unlock program")
        return cls._call_device_method("set_hardware_lock", is_locked)

    @classmethod
    def deregister(cls, device_id: str):
        logger.info(f"Deregister {device_id}")
        del cls._devices[device_id]

    @classmethod
    def deregister_all(cls):
        logger.info("Deregister all")
        cls._devices = dict()

    @classmethod
    def update(cls):
        logger.info("Update all")
        return cls._call_device_method("update")

    @classmethod
    def get_state(cls) -> Dict:
        return {
            'system_time': cls.get_system_time(),
            'device_ids': list(cls._devices.keys())
        }

    @classmethod
    def get_devices(cls) -> Dict:
        return {
            device_id: device.get_state()
            for device_id, device in cls._devices.items()
        }


Controller = MasterController if Instance.is_master() else DeviceController
