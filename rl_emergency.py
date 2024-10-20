import json
import sys
from datetime import datetime, timedelta

import backend.time_util as tu
from backend.led_controller import LedController
from backend.program import Program
from backend.schedule import Schedule


def get_schedule_time() -> str:
    time_arg = sys.argv[2]
    time_now = datetime.now()

    today = time_now
    year, month, day = today.year, today.month, today.day
    iso_time_str_today = f"{year}-{month:02}-{day:02}T{time_arg}"

    tomorrow = today + timedelta(days=1)
    year, month, day = tomorrow.year, tomorrow.month, tomorrow.day
    iso_time_str_tomorrow = f"{year}-{month:02}-{day:02}T{time_arg}"

    time_today = tu.string_to_datetime(iso_time_str_today)
    return (
        iso_time_str_today
        if time_today > time_now
        else iso_time_str_tomorrow
    )


def get_program():
    with open(sys.argv[1], 'r', encoding='utf-8') as file:
        return Program.from_json(
            "emergency_program", json_data=json.load(file)
        )


def report(program: Program, scheduled_time: str):
    print(f"Filename: {sys.argv[1]}")
    print(program)
    print()
    print(f"Running program at: {scheduled_time}")


def main():
    led_controller = LedController()
    led_controller.load_preset('idle')
    program = get_program()
    schedule_time = get_schedule_time()
    schedule = Schedule(schedule_time, lambda: program.run(lambda: None))
    schedule.start()
    report(program, schedule_time)
    try:
        schedule.join()
        program.join()
    except Exception:
        print("Unexpected exception!")
    except KeyboardInterrupt:
        schedule.cancel()
        if program.is_running:
            program.stop()
        print("Stopped.")
    else:
        print("Done.")
    finally:
        led_controller.off()


if __name__ == "__main__":
    main()
