import subprocess
import sys
import os
import ctypes
import re
import msvcrt


# --- Elevation ----------------------------------------------------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def elevate():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join([f'"{a}"' for a in sys.argv]), None, 1
    )
    sys.exit()


# --- UI Helpers ---------------------------------------------------------------


def clear():
    os.system("cls")


def print_header():
    print("\n  +==========================================+")
    print("  |        usbipd  ->  WSL  Attacher         |")
    print("  +==========================================+\n")


def show_menu(title, items):
    """Arrow-key driven menu. Returns selected index, or None on Q."""
    selected = 0

    while True:
        clear()
        print_header()
        print(f"  {title}\n")
        print("  [UP/DOWN] Navigate   [ENTER] Select   [Q] Quit\n")

        for i, item in enumerate(items):
            if i == selected:
                print(f"  >>> {item}")
            else:
                print(f"      {item}")

        print()
        key = msvcrt.getch()

        if key == b"\xe0":
            key2 = msvcrt.getch()
            if key2 == b"H":  # up arrow
                selected = (selected - 1) % len(items)
            elif key2 == b"P":  # down arrow
                selected = (selected + 1) % len(items)
        elif key == b"\r":  # enter
            return selected
        elif key in (b"q", b"Q"):
            return None


# --- USB Device Handling ------------------------------------------------------


def fetch_devices():
    """Run usbipd list and return a list of (busid, label) tuples for all devices."""
    result = subprocess.run(["usbipd", "list"], capture_output=True, text=True)
    devices = []
    for line in result.stdout.splitlines():
        match = re.match(r"^\s*(\d+-\d+)\s+(.*)", line)
        if match:
            busid = match.group(1).strip()
            desc = match.group(2).strip()
            devices.append((busid, f"{busid}   {desc}"))
    return devices


def fetch_attached_devices():
    """Return only devices currently attached to WSL."""
    result = subprocess.run(["usbipd", "list"], capture_output=True, text=True)
    devices = []
    for line in result.stdout.splitlines():
        match = re.match(r"^\s*(\d+-\d+)\s+(.*)", line)
        if match:
            busid = match.group(1).strip()
            desc = match.group(2).strip()
            # usbipd marks attached devices with "Attached" in the state column
            if re.search(r"\bAttached\b", desc, re.IGNORECASE):
                devices.append((busid, f"{busid}   {desc}"))
    return devices


def bind_device(busid):
    """Run usbipd bind for the given busid."""
    print(f"\n  [1/2] Binding...  (usbipd bind --busid {busid})\n")
    r = subprocess.run(["usbipd", "bind", "--busid", busid], text=True)
    if r.returncode != 0:
        print("  Warning: bind returned non-zero (may already be bound, continuing...)")


def attach_device(busid):
    """Run usbipd attach --wsl for the given busid. Returns True on success."""
    print(f"\n  [2/2] Attaching to WSL...  (usbipd attach --busid {busid} --wsl)\n")
    r = subprocess.run(["usbipd", "attach", "--busid", busid, "--wsl"], text=True)
    return r.returncode == 0


def detach_device(busid):
    """Run usbipd detach for the given busid. Returns True on success."""
    print(f"\n  Detaching...  (usbipd detach --busid {busid})\n")
    r = subprocess.run(["usbipd", "detach", "--busid", busid], text=True)
    return r.returncode == 0


def detach_selection_menu():
    """Show only attached devices and detach the chosen one."""
    while True:
        clear()
        print_header()
        print("  Fetching attached devices...\n")
        devices = fetch_attached_devices()

        if not devices:
            print("  No devices are currently attached to WSL.\n")
            input("  Press Enter to return to the main menu...")
            return

        labels = [d[1] for d in devices]
        labels += ["--- Refresh list ---", "--- Back to main menu ---"]

        choice = show_menu("Select a device to detach from WSL:", labels)

        # Q or Back
        if choice is None or choice == len(labels) - 1:
            return

        # Refresh
        if choice == len(labels) - 2:
            continue

        # Device selected
        busid = devices[choice][0]
        label = devices[choice][1]

        clear()
        print_header()
        print(f"  Selected: {label}\n")

        success = detach_device(busid)

        print()
        print(
            "  Device detached successfully!"
            if success
            else "  Detach failed. Check the output above."
        )
        print()
        input("  Press Enter to return to the main menu...")
        return


def bind_attach_selection_menu():
    """Show device list with Refresh and Back options. Performs bind+attach."""
    while True:
        clear()
        print_header()
        print("  Fetching USB device list...\n")
        devices = fetch_devices()

        if not devices:
            print("  No USB devices found. Is usbipd installed and running?\n")
            input("  Press Enter to return to the main menu...")
            return

        labels = [d[1] for d in devices]
        labels += ["--- Refresh list ---", "--- Back to main menu ---"]

        choice = show_menu("Select a USB device to attach:", labels)

        # Q or Back
        if choice is None or choice == len(labels) - 1:
            return

        # Refresh
        if choice == len(labels) - 2:
            continue

        # Device selected
        busid = devices[choice][0]
        label = devices[choice][1]

        clear()
        print_header()
        print(f"  Selected: {label}\n")

        bind_device(busid)
        success = attach_device(busid)

        print()
        print(
            "  Device attached successfully!"
            if success
            else "  Attach failed. Check the output above."
        )
        print()
        input("  Press Enter to return to the main menu...")
        return


# --- Main Menu ----------------------------------------------------------------


def main_menu():
    options = [
        "Attach a USB device to WSL",
        "Detach a USB device from WSL",
        "Exit",
    ]

    while True:
        choice = show_menu("Main Menu", options)

        if choice is None or choice == 2:
            clear()
            print_header()
            print("  Goodbye!\n")
            sys.exit(0)

        elif choice == 0:
            bind_attach_selection_menu()

        elif choice == 1:
            detach_selection_menu()


# --- Entry Point --------------------------------------------------------------

if __name__ == "__main__":
    if not is_admin():
        elevate()
    main_menu()
