import os
from typing import List

from _rl.config import Config, ConfigWizard
from _rl.constants import Paths, UserIds
from _rl.cronjob import Cronjob
from _rl.inout import Output
from _rl.logs import Logs
from _rl.rl_manager import RlManager
from _rl.status import Status


class UserInterface:

    @classmethod
    def _check_for_no_further_arguments(
        cls, args: List[str], subcommand_name: str
    ):
        if len(args) != 1:
            Output.critical(
                f"'rl {subcommand_name}{' ' if subcommand_name else ''}"
                f"{args[0]}' takes no further arguments!\nRun 'sudo rl"
                f"{' ' if subcommand_name else ''}{subcommand_name} help'."
            )

    @classmethod
    def _check_for_further_arguments(
        cls, args: List[str], count: int, subcommand_name: str
    ):
        if len(args) != count + 1:
            Output.critical(
                f"'rl {subcommand_name}{' ' if subcommand_name else ''}"
                f"{args[0]}' takes {count} further "
                f"argument{'s' if count > 1 else ''}!\nRun 'sudo rl"
                f"{' ' if subcommand_name else ''}{subcommand_name} help'."
            )

    @staticmethod
    def _require_root():
        if os.geteuid() != UserIds.ROOT:
            Output.critical("Please run as root!")

    @classmethod
    def run(cls, args: List[str]):
        if len(args) < 1:
            Output.critical(
                "Invalid number of arguments!\nRun 'sudo rl help'."
            )

        if args[0] in [
            'setup', 'run', 'run_no_wait', 'stop', 'restart',
            'update', 'uninstall', 'emergency', 'help'
        ]:
            cls._check_for_no_further_arguments(args, "")
            if args[0] == 'setup':
                cls._require_root()
                RlManager.setup()
                Output.success("Setup done.")
            elif args[0] == 'run':
                RlManager.run()
                Output.success("System is now running.")
            elif args[0] == 'run_no_wait':
                RlManager.run(no_wait=True)
            elif args[0] == 'stop':
                RlManager.stop()
                Output.success("System was stopped.")
            elif args[0] == 'restart':
                RlManager.restart()
                Output.success("System was restarted.")
            elif args[0] == 'update':
                cls._require_root()
                RlManager.update()
                Output.success("Update done.")
            elif args[0] == 'uninstall':
                cls._require_root()
                RlManager.uninstall()
                Output.success("Deinstallation done.")
            elif args[0] == 'emergency':
                RlManager.emergency()
                Output.success("Emergency run done.")
            elif args[0] == 'help':
                Output.print_file(Paths.HELP_RL)

        elif args[0] == 'config':
            cls._config(args[1:])
        elif args[0] == 'status':
            cls._status(args[1:])
        elif args[0] == 'cronjob':
            cls._require_root()
            cls._cronjob(args[1:])
        elif args[0] == 'logs':
            cls._logs(args[1:])
        else:
            Output.critical("Unknown command!\nRun 'sudo rl help'.")

    @classmethod
    def _config(cls, args: List[str]):
        if len(args) < 1:
            Output.critical(
                "Invalid number of arguments!\nRun 'sudo rl config help'."
            )

        if args[0] in ['list', 'wizard', 'help']:
            cls._check_for_no_further_arguments(args, "config")
            if args[0] == 'list':
                max_key_len = max([len(k) for k in Config.GET_METHODS.keys()])
                for key in Config.GET_METHODS.keys():
                    printed_key = f"{key}:{' ' * (max_key_len - len(key))}"
                    print(f"{printed_key}\t{Config.GET_METHODS[key]()}")
            elif args[0] == 'wizard':
                ConfigWizard.run()
                Output.success("Exited wizard.")
            elif args[0] == 'help':
                Output.print_file(Paths.HELP_RL_CONFIG)

        elif args[0] == 'set':
            cls._check_for_further_arguments(args, 2, "config")
            key, value = args[1], args[2]
            if key not in Config.SET_METHODS.keys():
                Output.critical(
                    f"Invalid key: {key}!\nRun 'sudo rl config help'."
                )
            if not Config.validate_value(key, value):
                Output.critical(
                    f"Invalid value: {value}\nRun 'sudo rl config help'."
                )
            Config.SET_METHODS[key](value)
            Output.success(f"Set {key} to {value}.")

        elif args[0] == 'get':
            cls._check_for_further_arguments(args, 1, "config")
            key = args[1]
            if key not in Config.SET_METHODS.keys():
                Output.critical(
                    f"Invalid key: {key}!\nRun 'sudo rl config help'."
                )
            value = Config.GET_METHODS[key]()
            print(f"{key}:\t{value}")

        else:
            Output.critical("Unknown command!\nRun 'sudo rl config help'.")

    @classmethod
    def _status(cls, args: List[str]):
        if len(args) < 1:
            Output.critical(
                "Invalid number of arguments!\nRun 'sudo rl status help'."
            )

        if args[0] in ['list', 'help']:
            if args[0] == 'list':
                max_key_len = max([len(k) for k in Status.GET_METHODS.keys()])
                for key in Status.GET_METHODS.keys():
                    printed_key = f"{key}:{' ' * (max_key_len - len(key))}"
                    print(f"{printed_key}\t{Status.GET_METHODS[key]()}")
            elif args[0] == 'help':
                Output.print_file(Paths.HELP_RL_STATUS)

        elif args[0] == 'get':
            cls._check_for_further_arguments(args, 1, "status")
            key = args[1]
            if key not in Status.GET_METHODS.keys():
                Output.critical(
                    f"Invalid key: {key}!\nRun 'sudo rl status help'."
                )
            print(f"{key}:\t{Status.GET_METHODS[key]()}")

        else:
            Output.critical("Unknown command!\nRun 'sudo rl status help'.")

    @classmethod
    def _cronjob(cls, args: List[str]):
        if len(args) < 1:
            Output.critical(
                "Invalid number of arguments!\nRun 'sudo rl cronjob help'."
            )

        if args[0] in ['register', 'deregister', 'status', 'help']:
            if args[0] == 'register':
                Cronjob.register()
                Output.success("Cronjob registered.")
            elif args[0] == 'deregister':
                Cronjob.deregister()
                Output.success("Cronjob deregistered.")
            elif args[0] == 'status':
                print(f"cronjob:\t{Cronjob.is_registered()}")
            elif args[0] == 'help':
                Output.print_file(Paths.HELP_RL_CRONJOB)

        else:
            Output.critical("Unknown command!\nRun 'sudo rl cronjob help'.")

    @classmethod
    def _logs(cls, args: List[str]):
        if len(args) < 1:
            Output.critical(
                "Invalid number of arguments!\nRun 'sudo rl logs help'."
            )

        if args[0] in ['list', 'latest', 'clear', 'help']:
            if args[0] == 'list':
                for filename in Logs.get_log_filenames():
                    print(filename)
            elif args[0] == 'latest':
                cls._check_for_further_arguments(args, 1, "logs")
                mode = args[1]
                if mode not in ['master', 'device']:
                    Output.critical(f"Unexpected argument: {mode}")
                print(Logs.get_latest_log_filename(mode))
            elif args[0] == 'clear':
                Logs.clear_logs()
                Output.success("All logfiles were deleted.")
            elif args[0] == 'help':
                Output.print_file(Paths.HELP_RL_LOGS)

        else:
            Output.critical("Unknown command!\nRun 'sudo rl logs help'.")
