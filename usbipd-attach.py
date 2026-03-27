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


def busid_to_drive_letters(busid):
    """
    Use WMI via PowerShell to find drive letters mounted from the USB device
    identified by busid (e.g. '2-3').
    Returns a list of drive letters like ['E:', 'F:'], or [] if none found.
    """
    # busid format is Port-Hub, e.g. "3-4". We match by USB port/hub in WMI.
    # Strategy: walk Win32_DiskDrive -> Win32_DiskDriveToDiskPartition ->
    #           Win32_LogicalDiskToPartition to get drive letters, then filter
    #           by the PNPDeviceID which contains the USB port address.
    ps_script = (
        r"""
$busid = '"""
        + busid
        + r"""'
# Convert busid "Port-Hub" to the address format Windows uses: "Port&Hub_X"
# usbipd busid "3-4" corresponds to USB\\VID_...&PID_...\\... with location "Port_#000X.Hub_#000Y"
# We match loosely by checking if the disk's PNPDeviceID contains the port numbers.
$port, $hub = $busid -split '-'
$portPad = $port.PadLeft(4, '0')
$hubPad  = $hub.PadLeft(4, '0')
$pattern = "Port_#$portPad.Hub_#$hubPad"

$drives = @()
Get-WmiObject Win32_DiskDrive | Where-Object { $_.PNPDeviceID -match 'USBSTOR' } | ForEach-Object {
    $disk = $_
    $loc = (Get-WmiObject -Query "SELECT * FROM Win32_PnPEntity WHERE DeviceID='$($disk.PNPDeviceID)'" -ErrorAction SilentlyContinue).LocationInformation
    if (-not $loc) {
        # Try parent device location via registry path heuristic
        $loc = $disk.PNPDeviceID
    }
    if ($disk.PNPDeviceID -like "*$portPad*" -or $loc -like "*$pattern*") {
        $disk | Get-WmiObject -Query "ASSOCIATORS OF {Win32_DiskDrive.DeviceID='$($disk.DeviceID)'} WHERE AssocClass=Win32_DiskDriveToDiskPartition" -ErrorAction SilentlyContinue | ForEach-Object {
            $part = $_
            Get-WmiObject -Query "ASSOCIATORS OF {Win32_DiskPartition.DeviceID='$($part.DeviceID)'} WHERE AssocClass=Win32_LogicalDiskToPartition" -ErrorAction SilentlyContinue | ForEach-Object {
                $drives += $_.DeviceID
            }
        }
    }
}
$drives | Sort-Object -Unique
"""
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True,
        text=True,
    )
    letters = [
        l.strip()
        for l in result.stdout.splitlines()
        if re.match(r"^[A-Z]:$", l.strip())
    ]
    return letters


def eject_drive(letter):
    """
    Eject/unmount a Windows drive letter using PowerShell + Shell.Application.
    Returns True on success.
    """
    ps_script = f"""
$shell = New-Object -ComObject Shell.Application
$folder = $shell.Namespace(17)  # ssfDRIVES
$item = $folder.ParseName('{letter}')
if ($item) {{
    $item.InvokeVerb('Eject')
    Start-Sleep -Milliseconds 800
    Write-Output 'OK'
}} else {{
    Write-Output 'NOT_FOUND'
}}
"""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True,
        text=True,
    )
    return "OK" in result.stdout


def unmount_usb_volumes(busid):
    """
    Attempt to auto-detect and eject all volumes mounted from the given busid.
    Falls back gracefully if nothing is found.
    Returns list of ejected drive letters.
    """
    print(f"  Detecting mounted volumes for busid {busid}...")
    letters = busid_to_drive_letters(busid)

    if not letters:
        # Fallback: show all removable drives and let user pick or skip
        ps_script = """
Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DriveType -eq 2 } | Select-Object -ExpandProperty DeviceID
"""
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
        )
        removable = [
            l.strip()
            for l in result.stdout.splitlines()
            if re.match(r"^[A-Z]:$", l.strip())
        ]

        if not removable:
            print("  No removable drives detected. Skipping unmount.")
            return []

        print(
            f"\n  Could not auto-match busid to a drive. Removable drives found: {', '.join(removable)}"
        )
        items = removable + ["--- Skip unmount ---"]
        choice = show_menu("Select the drive to eject before attaching:", items)

        if choice is None or choice == len(items) - 1:
            print("  Skipping unmount.")
            return []

        letters = [removable[choice]]

    ejected = []
    for letter in letters:
        print(f"  Ejecting {letter} ...", end=" ")
        ok = eject_drive(letter)
        if ok:
            print("OK")
            ejected.append(letter)
        else:
            print("failed (drive may already be unmounted, continuing...)")

    return ejected


def bind_device(busid):
    """Run usbipd bind for the given busid."""
    print(f"\n  [2/3] Binding...  (usbipd bind --busid {busid})\n")
    r = subprocess.run(["usbipd", "bind", "--busid", busid], text=True)
    if r.returncode != 0:
        print("  Warning: bind returned non-zero (may already be bound, continuing...)")


def attach_device(busid):
    """Run usbipd attach --wsl for the given busid. Returns True on success."""
    print(f"\n  [3/3] Attaching to WSL...  (usbipd attach --busid {busid} --wsl)\n")
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

        print("  [1/3] Unmounting Windows volumes...\n")
        unmount_usb_volumes(busid)

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
