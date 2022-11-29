import os

if os.geteuid() != 0:
    print("Please run as root!")
    exit(1)

MODEL: str = "/sys/firmware/devicetree/base/model"
CONFIG_TXT: str = "/boot/config.txt"

try:
    with open(MODEL, 'r', encoding='ascii') as file:
        if "Zero W" not in file.read():
            raise ValueError()
except (FileNotFoundError, ValueError):
    exit(1)

with open(CONFIG_TXT, 'r', encoding='ascii') as file:
    in_lines = file.readlines()

out_lines = []
for line in in_lines:
    out_lines.append(line)
    if "/boot/overlays/README" in line:
        out_lines.append("dtoverlay=disable-wifi")

with open(CONFIG_TXT, 'w', encoding='ascii') as file:
    file.writelines(out_lines)
