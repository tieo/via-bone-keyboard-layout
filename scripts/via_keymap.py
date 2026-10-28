#!/usr/bin/env python3
"""Read and write a VIA keyboard's keymap over USB, without a configurator.

  via_keymap.py diff  <keymap.json>         keys where the keyboard differs from the file
  via_keymap.py apply <keymap.json> [-n]    write those keys, then read them back
  via_keymap.py get   <layer> <row> <col>   one key's keycode
  via_keymap.py set   <layer> <row> <col> <keycode>

<keymap.json> is a Keychron Launcher export as in keymaps/: per layer a list
of {row, col, val}, val the QMK 16-bit keycode. Only the keymap is compared
and written; the knob section stays as the keyboard has it.

The keyboard talks VIA on its raw HID interface (usage page 0xFF60, usage
0x61): 32-byte reports, one command per report, answered by one report. Keys
written with the dynamic keymap command land in the keyboard's EEPROM, so
they survive a replug the same as a Launcher import. --vid and --pid pick the
keyboard; the default vendor 0x3434 is Keychron, and with no --pid the only
VIA keyboard of that vendor is used.

Standard library only. Windows goes through hid.dll and setupapi; Linux
through /dev/hidraw*, which needs the udev rule from the README for a
non-root user.
"""
import argparse
import json
import sys

REPORT = 32
TIMEOUT_MS = 1000

ID_GET_PROTOCOL_VERSION = 0x01
ID_GET_KEYCODE = 0x04
ID_SET_KEYCODE = 0x05
ID_GET_LAYER_COUNT = 0x11
ID_UNHANDLED = 0xFF


class ViaError(Exception):
    pass


def _windows_devices(vid, pid):
    import ctypes
    from ctypes import wintypes as W

    hid = ctypes.WinDLL("hid")
    setupapi = ctypes.WinDLL("setupapi")
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class GUID(ctypes.Structure):
        _fields_ = [("a", W.DWORD), ("b", W.WORD), ("c", W.WORD), ("d", ctypes.c_ubyte * 8)]

    class IFDATA(ctypes.Structure):
        _fields_ = [("cbSize", W.DWORD), ("guid", GUID), ("flags", W.DWORD), ("res", ctypes.c_void_p)]

    class CAPS(ctypes.Structure):
        _fields_ = [("Usage", W.USHORT), ("UsagePage", W.USHORT), ("InLen", W.USHORT),
                    ("OutLen", W.USHORT), ("FeatLen", W.USHORT), ("rest", W.USHORT * 17)]

    class OVERLAPPED(ctypes.Structure):
        _fields_ = [("Internal", ctypes.c_void_p), ("InternalHigh", ctypes.c_void_p),
                    ("Offset", W.DWORD), ("OffsetHigh", W.DWORD), ("hEvent", W.HANDLE)]

    setupapi.SetupDiGetClassDevsW.restype = ctypes.c_void_p
    setupapi.SetupDiGetClassDevsW.argtypes = [ctypes.POINTER(GUID), W.LPCWSTR, W.HWND, W.DWORD]
    setupapi.SetupDiEnumDeviceInterfaces.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(GUID), W.DWORD, ctypes.POINTER(IFDATA)]
    setupapi.SetupDiGetDeviceInterfaceDetailW.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(IFDATA), ctypes.c_void_p, W.DWORD,
        ctypes.POINTER(W.DWORD), ctypes.c_void_p]
    setupapi.SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]
    k32.CreateFileW.restype = W.HANDLE
    k32.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, ctypes.c_void_p, W.DWORD, W.DWORD, W.HANDLE]
    k32.CreateEventW.restype = W.HANDLE
    k32.CreateEventW.argtypes = [ctypes.c_void_p, W.BOOL, W.BOOL, W.LPCWSTR]
    k32.WriteFile.argtypes = [W.HANDLE, ctypes.c_void_p, W.DWORD, ctypes.POINTER(W.DWORD), ctypes.c_void_p]
    k32.ReadFile.argtypes = [W.HANDLE, ctypes.c_void_p, W.DWORD, ctypes.POINTER(W.DWORD), ctypes.c_void_p]
    k32.GetOverlappedResult.argtypes = [W.HANDLE, ctypes.c_void_p, ctypes.POINTER(W.DWORD), W.BOOL]
    k32.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
    k32.CancelIo.argtypes = [W.HANDLE]
    k32.CloseHandle.argtypes = [W.HANDLE]
    INVALID = W.HANDLE(-1).value
    ERROR_IO_PENDING = 997

    class Device:
        def __init__(self, path, handle, out_len, in_len):
            self.path, self.handle, self.out_len, self.in_len = path, handle, out_len, in_len
            self.event = k32.CreateEventW(None, True, False, None)

        def _io(self, call, buf, size):
            ov = OVERLAPPED(hEvent=self.event)
            done = W.DWORD()
            if not call(self.handle, buf, size, None, ctypes.byref(ov)):
                if ctypes.get_last_error() != ERROR_IO_PENDING:
                    raise ViaError(f"HID I/O failed (Windows error {ctypes.get_last_error()})")
                if k32.WaitForSingleObject(self.event, TIMEOUT_MS) != 0:
                    k32.CancelIo(self.handle)
                    raise ViaError("the keyboard did not answer within a second")
            if not k32.GetOverlappedResult(self.handle, ctypes.byref(ov), ctypes.byref(done), True):
                raise ViaError(f"HID I/O failed (Windows error {ctypes.get_last_error()})")

        def exchange(self, msg):
            # Windows puts the report id in front of every report, 0 for none.
            out = (ctypes.c_ubyte * self.out_len)(0, *msg)
            self._io(k32.WriteFile, out, self.out_len)
            reply = (ctypes.c_ubyte * self.in_len)()
            self._io(k32.ReadFile, reply, self.in_len)
            return bytes(reply)[1:REPORT + 1]

        def close(self):
            k32.CloseHandle(self.event)
            k32.CloseHandle(self.handle)

    guid = GUID()
    hid.HidD_GetHidGuid(ctypes.byref(guid))
    info = setupapi.SetupDiGetClassDevsW(ctypes.byref(guid), None, None, 0x12)  # present | interface
    want = f"vid_{vid:04x}&" + (f"pid_{pid:04x}" if pid is not None else "")
    found = []
    try:
        index = 0
        while True:
            data = IFDATA(cbSize=ctypes.sizeof(IFDATA))
            if not setupapi.SetupDiEnumDeviceInterfaces(info, None, ctypes.byref(guid), index, ctypes.byref(data)):
                break
            index += 1
            need = W.DWORD()
            setupapi.SetupDiGetDeviceInterfaceDetailW(info, ctypes.byref(data), None, 0, ctypes.byref(need), None)
            detail = ctypes.create_string_buffer(need.value)
            ctypes.cast(detail, ctypes.POINTER(W.DWORD))[0] = 8  # cbSize of the fixed part on 64-bit
            if not setupapi.SetupDiGetDeviceInterfaceDetailW(info, ctypes.byref(data), detail, need, None, None):
                continue
            path = ctypes.wstring_at(ctypes.addressof(detail) + 4)
            if want not in path.lower():
                continue
            handle = k32.CreateFileW(path, 0xC0000000, 3, None, 3, 0x40000000, None)  # rw, share rw, overlapped
            if handle in (None, INVALID):
                continue
            caps, prep = CAPS(), ctypes.c_void_p()
            if hid.HidD_GetPreparsedData(handle, ctypes.byref(prep)):
                hid.HidP_GetCaps(prep, ctypes.byref(caps))
                hid.HidD_FreePreparsedData(prep)
            if caps.UsagePage == 0xFF60 and caps.Usage == 0x61:
                found.append(Device(path, handle, caps.OutLen, caps.InLen))
            else:
                k32.CloseHandle(handle)
    finally:
        setupapi.SetupDiDestroyDeviceInfoList(info)
    return found


def _linux_devices(vid, pid):
    import glob
    import os
    import select

    class Device:
        def __init__(self, path):
            self.path = path
            self.fd = os.open(path, os.O_RDWR)

        def exchange(self, msg):
            # hidraw takes the report number first, 0 for a device without numbered reports.
            os.write(self.fd, bytes([0, *msg]).ljust(REPORT + 1, b"\0"))
            if not select.select([self.fd], [], [], TIMEOUT_MS / 1000)[0]:
                raise ViaError("the keyboard did not answer within a second")
            return os.read(self.fd, REPORT)

        def close(self):
            os.close(self.fd)

    found = []
    for node in sorted(glob.glob("/sys/class/hidraw/hidraw*")):
        try:
            uevent = open(f"{node}/device/uevent").read()
            descriptor = open(f"{node}/device/report_descriptor", "rb").read()
        except OSError:
            continue
        hid_id = next((l.split("=", 1)[1] for l in uevent.splitlines() if l.startswith("HID_ID=")), "")
        parts = hid_id.split(":")
        if len(parts) != 3 or int(parts[1], 16) != vid or (pid is not None and int(parts[2], 16) != pid):
            continue
        # Usage Page (Vendor 0xFF60) followed by Usage (0x61), as QMK declares its raw HID interface.
        if b"\x06\x60\xff\x09\x61" not in descriptor:
            continue
        path = "/dev/" + os.path.basename(node)
        try:
            found.append(Device(path))
        except PermissionError:
            raise ViaError(f"no permission to open {path}; install the udev rule from the README")
    return found


def open_keyboard(vid, pid):
    devices = _windows_devices(vid, pid) if sys.platform == "win32" else _linux_devices(vid, pid)
    if not devices:
        raise ViaError(f"no VIA keyboard with vendor 0x{vid:04x}" + (f" and product 0x{pid:04x}" if pid else "")
                       + " is connected (on a Keychron the mode switch must be on cable)")
    if len(devices) > 1:
        for d in devices:
            d.close()
        raise ViaError("more than one VIA keyboard is connected; pick one with --pid")
    return Keyboard(devices[0])


class Keyboard:
    def __init__(self, device):
        self.device = device
        reply = self._command(ID_GET_PROTOCOL_VERSION)
        self.protocol = reply[1] << 8 | reply[2]
        self.layers = self._command(ID_GET_LAYER_COUNT)[1]

    def _command(self, *msg):
        reply = self.device.exchange(list(msg))
        if reply[0] == ID_UNHANDLED or reply[0] != msg[0]:
            raise ViaError(f"the keyboard did not take command 0x{msg[0]:02x} (answered 0x{reply[0]:02x})")
        return reply

    def get(self, layer, row, col):
        reply = self._command(ID_GET_KEYCODE, layer, row, col)
        return reply[4] << 8 | reply[5]

    def set(self, layer, row, col, keycode):
        self._command(ID_SET_KEYCODE, layer, row, col, keycode >> 8, keycode & 0xFF)
        now = self.get(layer, row, col)
        if now != keycode:
            raise ViaError(f"L{layer} r{row} c{col} reads 0x{now:04x} after writing 0x{keycode:04x}")

    def close(self):
        self.device.close()


def load_keymap(path):
    with open(path) as f:
        layers = json.load(f)["keymap"]
    return [(layer, key["row"], key["col"], key["val"]) for layer, keys in enumerate(layers) for key in keys]


def differences(keyboard, keymap):
    layers = 1 + max(layer for layer, _, _, _ in keymap)
    if layers > keyboard.layers:
        raise ViaError(f"the file has {layers} layers, the keyboard {keyboard.layers}")
    return [(layer, row, col, want, have) for layer, row, col, want in keymap
            if (have := keyboard.get(layer, row, col)) != want]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vid", type=lambda s: int(s, 0), default=0x3434)
    parser.add_argument("--pid", type=lambda s: int(s, 0))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("diff").add_argument("keymap")
    apply = sub.add_parser("apply")
    apply.add_argument("keymap")
    apply.add_argument("-n", "--dry-run", action="store_true", help="list the keys apply would write")
    for name in ("get", "set"):
        p = sub.add_parser(name)
        for field in ("layer", "row", "col"):
            p.add_argument(field, type=int)
        if name == "set":
            p.add_argument("keycode", type=lambda s: int(s, 0))
    args = parser.parse_args()

    keyboard = open_keyboard(args.vid, args.pid)
    try:
        if args.command == "get":
            print(f"0x{keyboard.get(args.layer, args.row, args.col):04x}")
        elif args.command == "set":
            keyboard.set(args.layer, args.row, args.col, args.keycode)
            print(f"L{args.layer} r{args.row} c{args.col} = 0x{args.keycode:04x}")
        else:
            diff = differences(keyboard, load_keymap(args.keymap))
            for layer, row, col, want, have in diff:
                print(f"L{layer} r{row} c{col}: keyboard 0x{have:04x}, file 0x{want:04x}")
            if args.command == "diff" or args.dry_run:
                print(f"{len(diff)} {'key differs' if len(diff) == 1 else 'keys differ'}" if diff else "the keyboard matches the file")
            else:
                for layer, row, col, want, _ in diff:
                    keyboard.set(layer, row, col, want)
                print(f"wrote {len(diff)} {'key' if len(diff) == 1 else 'keys'}" if diff else "the keyboard already matches the file")
    finally:
        keyboard.close()


if __name__ == "__main__":
    try:
        main()
    except ViaError as e:
        sys.exit(f"via_keymap: {e}")
