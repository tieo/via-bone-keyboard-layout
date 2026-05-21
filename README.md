# via-bone-keyboard-layout

[Bone](https://neo-layout.org/Layouts/bone/) keyboard layout for VIA-compatible
keyboards (Keychron Q/V/K Pro, ZSA, GMMK Pro, …). The keyboard itself sends
Bone characters via firmware-level remapping, no OS-side xkb config, no
per-host setup. As long as the host OS is set to plain German (QWERTZ),
typing produces Bone on Linux, Windows, macOS, BIOS, KVM, your phone, or
someone else's computer.

## Layer layout

| Layer | Content | Trigger |
|---|---|---|
| **L0** | Bone base (letters in Bone positions; numbers, mods, F-row as QWERTZ) | default (OS-switch on Win side) |
| **L1** | Bone Mod3, punctuation & brackets (`[ ] { } ( ) < > / \\ + - = …`) | hold Caps Lock or ISO `#` |
| **L2** | Plain QWERTZ base, escape hatch for when you don't want Bone | OS-switch on Mac side |
| **L3** | Bone Mod4, nav cluster on the left, numpad on the right | hold ISO `<` or Right Alt |

Capitals come from holding Shift on top of L0 (standard HID behavior; no
dedicated layer needed).

Full per-position mapping: [`docs/layer-design.md`](./docs/layer-design.md).

## Extras baked into the Keychron Q6 Pro keymap

These aren't part of canonical Bone, they reflect personal preferences. Edit
[`scripts/build_keychron_q6_pro_iso.py`](./scripts/build_keychron_q6_pro_iso.py)
if you want them off.

- **Bottom-left modifier swap.** Physical `Ctrl / Win / Alt` keys send
  `Win / Alt / Ctrl` instead, the firmware equivalent of xkb's
  `ctrl:swap_lalt_lctl_lwin`.
- **F-row direct.** F1-F12 are on the F-row without holding FN. (Keychron's
  stock keymap hides them behind FN and puts media keys on the F-row.)
- **Macro group remap.** The four rightmost F-row keys (F13-F16 stock) are
  Prev Track / Play-Pause / Next Track / Calculator.
- **OS switch repurposed.** The back-left Mac/Win toggle now flips between
  Bone (L0) and plain QWERTZ (L2) instead of Mac/Win modifier layout.

## Requirements

- A VIA-compatible keyboard. Currently only the **Keychron Q6 Pro ISO Knob**
  has a ready-made keymap (`keymaps/keychron-q6-pro-iso.json`).
- Host OS keyboard layout set to **plain German (QWERTZ)**, *not*
  `de(bone)`. The firmware handles Bone; let the OS do plain German.
- A VIA-style configurator:
  - **Keychron boards**: [Keychron Launcher](https://launcher.keychron.com)
    (Chrome / Edge / Brave, WebHID required).
  - **Other VIA boards**: [usevia.app](https://usevia.app) or the standalone
    VIA desktop app.

## Install (Keychron Q6 Pro ISO)

1. Set your OS keyboard layout to **German (Germany)**, default variant, no
   bone variant.
2. Open <https://launcher.keychron.com> in Chrome / Edge / Brave.
3. Connect the keyboard via USB. The mode toggle on the back-left must be in
   **Cable** position.
4. **Settings (gear icon) → Import Keymap** → choose
   [`keymaps/keychron-q6-pro-iso.json`](./keymaps/keychron-q6-pro-iso.json).
5. Type. You're on Bone.

If the import fails with "Invalid Configuration", the JSON format may have
drifted relative to your firmware version. Export your current keymap from
the launcher and regenerate (see *Adding a board* below).

### Linux side notes

- If `/dev/hidraw*` is root-only and the Launcher can't see the keyboard,
  you need a udev rule. The recipe used here on NixOS:
  ```
  KERNEL=="hidraw*", ENV{ID_USB_VENDOR_ID}=="3434",
    ENV{ID_USB_INTERFACE_NUM}=="01", TAG+="uaccess",
    GROUP="input", MODE="0660"
  ```
  The interface-number filter (`01`) restricts user access to the VIA raw
  HID channel only, leaving the boot keyboard interface (`00`) and the
  mouse interface (`02`) root-only. That way an unprivileged user-level
  process can't read keystrokes straight from `/dev/hidraw0`.

  Adjust `ID_USB_VENDOR_ID` for non-Keychron boards (`3434` covers all
  Keychron Q/V/K Pro models); the VIA interface number is consistently
  `01` on Keychron boards but may differ elsewhere, check with
  `udevadm info -a /dev/hidrawN` and look for the `bInterfaceNumber`
  whose parent's HID descriptor has usage page `0xFF60`.

  After editing the rule: `sudo udevadm control --reload`, then replug
  the keyboard.

- If you were previously using KDE / xkb tweaks like
  `ctrl:swap_lalt_lctl_lwin` or `de(bone)`, **disable them** before flashing
  this keymap, otherwise the OS will double-translate and produce garbage.

## Adding a board

The Keychron Q6 Pro keymap is generated from a Python script that takes a
stock keymap export as a template and patches only the positions that need
changing. To add a new board:

1. Configure it to stock (or any known-good layout) in your vendor's
   launcher / VIA.
2. Export the layout JSON.
3. Copy
   [`scripts/build_keychron_q6_pro_iso.py`](./scripts/build_keychron_q6_pro_iso.py)
   and adapt the row/col indices to your board's matrix.
4. Run it against your export, get back a Bone-patched JSON.
5. Import the result.

The non-Keychron VIA workflow is simpler if your tool can't do JSON imports:
edit the keymap in the GUI per [`docs/layer-design.md`](./docs/layer-design.md),
then **File → Save Layout** to dump a JSON for the repo.

## Contributing

PRs adding a new board are welcome. The layer design is fixed; only the
matrix mapping changes per board. Open an issue first if you want to discuss
the optional extras (mod swap, F-row, OS-switch repurpose), those are
opinionated and reasonable people will disagree.

## AI-assisted

This keymap, generator script, and documentation were drafted by an AI
model and iterated on by hand. Verify keymap values against your own
typing before relying on them.

## License

MIT, see [`LICENSE`](./LICENSE).
