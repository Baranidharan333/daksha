import os
import subprocess
import sys

def main():
    PASSWORD = os.environ.get("VCAN_SUDO_PASSWORD")
    BITRATE = os.environ.get("CAN_BITRATE", "1000000")

    if PASSWORD is None:
        print("Error: VCAN_SUDO_PASSWORD environment variable not set.")
        sys.exit(1)

    def sudo(cmd):
        subprocess.run(
            ["sudo", "-S"] + cmd,
            input=PASSWORD + "\n",
            text=True,
            check=True,
        )

    for can in ("can0", "can1"):
        try:
            sudo(["ip", "link", "set", can, "down"])
        except subprocess.CalledProcessError:
            pass

        sudo(["ip", "link", "set", can, "type", "can", "bitrate", BITRATE])
        sudo(["ip", "link", "set", can, "up"])

    print("CAN interfaces are up.")


if __name__ == "__main__":
    main()