MODEL: str = "/sys/firmware/devicetree/base/model"

try:
    with open(MODEL, 'r', encoding='ascii') as file:
        if "Zero W" not in file:
            raise ValueError()
except (FileNotFoundError, ValueError):
    exit(1)
