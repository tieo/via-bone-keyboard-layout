# Physical layout notes

How to translate the Bone layer design into a keymap JSON for a new
board.

## VIA vs Keychron Launcher (and why the JSON format matters)

Different vendor configurators use different on-disk formats. They are
all "VIA-style" but the JSON layout is not portable:

- **Stock VIA** (the desktop app and `usevia.app`) saves keymaps as
  `{ "name", "vendorProductId", "macros", "layers": [[kc, kc, ...]] }`
  with one flat array per layer, keycodes as strings like `"KC_A"`,
  `"MO(2)"`, `"RALT(KC_8)"`.
- **Keychron Launcher** (`launcher.keychron.com`) saves as
  `{ "id", "keymap": [[{col,row,val}]], "version", "MD5", "knob" }`
  with explicit `(col, row)` for each entry and integer keycode values
  encoded in the QMK 16-bit numbering. Importing a VIA-style JSON
  produces "Invalid Configuration".

For Keychron boards the safest workflow is to **start from an export
of the board's current keymap** (the Launcher's Save Layout button)
and patch only the slots you need to change. The build script in this
repo (`scripts/build_keychron_q6_pro_iso.py`) does exactly that:
loads the user's stock export, applies a list of `(row, col, val)`
overrides, recomputes the MD5, and writes the result.

## Keychron Launcher keycode encoding (subset)

Useful values when patching by hand:

| Macro | Value |
|---|---|
| `KC_A` ... `KC_Z` | `0x04 .. 0x1D` (4 .. 29) |
| `KC_1` ... `KC_0` | `0x1E .. 0x27` (30 .. 39) |
| `KC_LCTL/LSFT/LALT/LGUI` | `224 / 225 / 226 / 227` |
| `KC_TRNS` | `1` |
| `KC_NO` | `0` |
| `MO(layer)` | `0x5220 \| layer` |
| `LT(layer, kc)` | `0x4000 \| (layer << 8) \| kc` |
| `LSFT(kc)` | `0x0200 \| kc` |
| `RALT(kc)` (i.e. AltGr) | `0x1400 \| kc` |
| Media `MPRV/MPLY/MNXT/MUTE/VOLD/VOLU` | `172 / 174 / 171 / 168 / 170 / 169` |
| `KC_CALCULATOR` | `178` |
| `RGB_TOG / RGB_MOD / RGB_RMOD` | `0x7820 / 0x7821 / 0x7822` |

The QMK encoding changed around 2022 from older base addresses
(e.g. `MO(layer)` was `0x5100 | layer`) to the current ones above. If
your firmware version doesn't accept the new values, fall back to the
old ones, or check what your stock export uses at a known position
(e.g. row 5 col 12 on layer 1 is usually FN1 = `MO(1)`).

## ANSI vs ISO

ISO boards have two extras the design has to place:

- **Left of the first letter on the bottom row** (`<>|` on QWERTZ):
  the xkb keycode is `<LSGT>`, **not** part of Bone's letter block.
  Use it as the Mod4 trigger (`MO(3)`).
- **Right of `Ä` (`#`/`'`)**: xkb `<BKSL>`. Bone treats it as a Mod3
  trigger; also map it to `MO(1)` so it works the same as Caps Lock.

Plus the vertical Enter on ISO means the `\` slot moves up; this
doesn't affect Bone's letter block.

## Adding a new board

1. Configure the board to stock (or any known-good state) in your
   vendor's launcher / VIA. Export the keymap to JSON.
2. Copy `scripts/build_keychron_q6_pro_iso.py` and adapt:
   - Re-derive the `(row, col)` positions for your matrix from the
     exported JSON (each physical key has its own `(col, row)` pair).
   - Adjust the F-row / mod-cluster / encoder bindings if the board's
     layout differs from the Q6 Pro ISO Knob.
3. Run the generator against your export, get back a Bone-patched
   JSON.
4. Import the result in your vendor's launcher.
5. Test (every Bone letter, Caps + every Mod3 letter, etc.).
6. Drop the script and the produced JSON into `scripts/` and
   `keymaps/`. Add a row to the README's board table. PR.

For non-Keychron boards whose launcher cannot import JSON, the
fallback is the manual route: edit in the GUI per
`layer-design.md`, then **File -> Save Layout** to dump the file for
the repo.
