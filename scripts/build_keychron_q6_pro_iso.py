#!/usr/bin/env python3
"""Generate Keychron Launcher JSON for Keychron Q6 Pro ISO with Bone layout.

Host OS must be set to plain German QWERTZ. The firmware sends the HID
codes that produce the Bone characters under that layout.

Strategy: start from a known-good QWERTZ export from Keychron Launcher
(passed as argv[1]), patch only positions that differ between Bone and
QWERTZ on layers 0/2/3. Layer 1 (Keychron FN) is left untouched.

Bone layout source: xkb's de(bone_base) symbol definition.
"""
import json, sys, hashlib

# --- HID keycodes (subset) -------------------------------------------------
KC = {
    "NO": 0,
    "A": 4, "B": 5, "C": 6, "D": 7, "E": 8, "F": 9, "G": 10,
    "H": 11, "I": 12, "J": 13, "K": 14, "L": 15, "M": 16, "N": 17,
    "O": 18, "P": 19, "Q": 20, "R": 21, "S": 22, "T": 23, "U": 24,
    "V": 25, "W": 26, "X": 27, "Y": 28, "Z": 29,
    "1": 30, "2": 31, "3": 32, "4": 33, "5": 34,
    "6": 35, "7": 36, "8": 37, "9": 38, "0": 39,
    "ENT": 40, "ESC": 41, "BSPC": 42, "TAB": 43, "SPC": 44,
    "MINS": 45, "EQL": 46, "LBRC": 47, "RBRC": 48, "BSLS": 49,
    "NUHS": 50, "SCLN": 51, "QUOT": 52, "GRV": 53,
    "COMM": 54, "DOT": 55, "SLSH": 56, "CAPS": 57,
    "RGHT": 79, "LEFT": 80, "DOWN": 81, "UP": 82,
    "HOME": 74, "END": 77, "PGUP": 75, "PGDN": 78,
    "DEL": 76, "INS": 73,
    "P1": 89, "P2": 90, "P3": 91, "P4": 92, "P5": 93,
    "P6": 94, "P7": 95, "P8": 96, "P9": 97, "P0": 98, "PDOT": 99,
    "PSLS": 84, "PAST": 85, "PMNS": 86, "PPLS": 87, "PENT": 88,
    "NUBS": 100,
    "LSFT": 225, "RSFT": 229, "LCTL": 224, "RCTL": 228,
    "LALT": 226, "RALT": 230, "LGUI": 227, "RGUI": 231,
    "TRNS": 1,
    "F1": 58, "F2": 59, "F3": 60, "F4": 61, "F5": 62, "F6": 63,
    "F7": 64, "F8": 65, "F9": 66, "F10": 67, "F11": 68, "F12": 69,
    "MUTE": 168, "VOLU": 169, "VOLD": 170,
    "MNXT": 171, "MPRV": 172, "MSTP": 173, "MPLY": 174,
    "CALC": 178,
}

def MO(n):  # momentary layer
    # QMK QK_MOMENTARY = 0x5220 (post-2022 reorganization). Verified
    # against Keychron's stock export: row 5 col 12 on layer 1 = 0x5221
    # = MO(1), the FN1 key.
    return 0x5220 | n

def LT(layer, kc):  # layer-tap: layer on hold, kc on tap
    return 0x4000 | (layer << 8) | kc

def RALT(kc):  # AltGr + key
    # QK_RALT = 0x1400 in current QMK; bits 8-11 are the mod mask,
    # bit 12 distinguishes right-side mods.
    return 0x1400 | kc

# --- Bone L0 letter mapping (xkb de(bone_base)) ----------------------------
# Each entry: (row, col, KC sent on plain-German OS to produce the Bone char)
#
# Row indexing matches the export: row 2 = top letter row (Q-P), row 3 =
# home row (A-L+ä/#), row 4 = bottom letter row (Y-M+,/./-/etc).
#
# Note on Y/Z: on German OS, KC_Y produces 'z' and KC_Z produces 'y'. We
# need to send the *KC* whose German-layout result equals the Bone char.

# AD01-AD11 → j d u a x p h l m w ß
L0_PATCH = [
    (2, 1, KC["J"]),
    (2, 2, KC["D"]),
    (2, 3, KC["U"]),
    (2, 4, KC["A"]),
    (2, 5, KC["X"]),
    (2, 6, KC["P"]),
    (2, 7, KC["H"]),
    (2, 8, KC["L"]),
    (2, 9, KC["M"]),
    (2, 10, KC["W"]),
    (2, 11, KC["MINS"]),   # ß on German = KC_MINUS

    # AC01-AC10 → c t i e o b n r s g  (AC11 = q but ISO# becomes MO(2))
    (3, 1, KC["C"]),
    (3, 2, KC["T"]),
    (3, 3, KC["I"]),
    (3, 4, KC["E"]),
    (3, 5, KC["O"]),
    (3, 6, KC["B"]),
    (3, 7, KC["N"]),
    (3, 8, KC["R"]),
    (3, 9, KC["S"]),
    (3, 10, KC["G"]),
    (3, 11, KC["Q"]),       # AC11 = q in Bone
    (3, 13, MO(1)),         # ISO # → Mod3 trigger
    (3, 0,  MO(1)),         # Caps Lock → Mod3 trigger

    # AB01-AB10 → f v ü ä ö y z , . k
    # AB01 in xkb is ISO< on ISO boards; Bone puts f there. But we steal
    # that key for Mod4. Real f stays on row 4 col 6 (was Y/Z position).
    # Actually re-read: AB01..AB10 are the bottom letter keys including
    # the < on ISO. xkb's bone_base puts f on AB01 (ISO <). Conflicting
    # with Mod4. We resolve by putting Mod4 on ISO< (closer to thumb)
    # and skipping f on AB01, f instead goes on row 4 col 6 (was 'b'
    # position B/N junction). Hmm, that's not how Bone works.
    #
    # Reality check: on most non-ISO Bone setups, AB01 just doesn't
    # exist. The Bone letter sequence is f v ü ä ö y z , . k starting at
    # AB02 effectively. We follow that: AB02-AB10 in our row 4 are
    # cols 2-10.
    (4, 2, KC["F"]),
    (4, 3, KC["V"]),
    (4, 4, KC["LBRC"]),     # ü on German = KC_LBRC
    (4, 5, KC["QUOT"]),     # ä = KC_QUOT
    (4, 6, KC["SCLN"]),     # ö = KC_SCLN
    (4, 7, KC["Z"]),        # y → KC_Z (German layout y/z swap)
    (4, 8, KC["Y"]),        # z → KC_Y
    (4, 9, KC["COMM"]),     # ,
    (4, 10, KC["DOT"]),     # .
    # AB10 = k goes where the German '-' lives, col 11 on row 4
    (4, 11, KC["K"]),
    # ISO < → Mod4 trigger
    (4, 1, MO(3)),
    # Right Alt → Mod4 trigger
    (5, 10, MO(3)),

    # (mod swap lives in L0_MOD_SWAP so it's not accidentally also
    # applied to L2)
]

# --- Layer 2 (Mod3 / punctuation) -----------------------------------------
# Bone's Mod3 layer, accessed via AltGr/Shift combinations on German.
# Subset that works without Unicode input. Many slots use RALT() which
# wraps the keycode in AltGr (QK_RALT).
#
# Bone Mod3 reference (neo-layout.org/bone, layer 3):
#   row1:  …  …  …  …  …  …  …  …  …  …  …
#   row2:  …  _  [  ]  ^  !  <  >  =  &  ſ
#   row3:  \  /  {  }  *  ?  (  )  -  :  @
#   row4:  #  $  |  ~  `  +  %  "  '  ;
#
# Producing these on German OS requires the right combination. Map below.

# Helper: shift a key
def S(kc): return 0x0200 | kc

L2_PATCH = [
    # Row 2 (top letter row), Mod3 layer
    (2, 1, KC["NO"]),                  # (unused in Bone Mod3 row 1)
    (2, 2, S(KC["MINS"])),             # _ (Shift+ß on German)
    (2, 3, RALT(KC["8"])),             # [ (AltGr+8)
    (2, 4, RALT(KC["9"])),             # ] (AltGr+9)
    (2, 5, KC["GRV"]),                 # ^ (German ^ key)
    (2, 6, S(KC["1"])),                # ! (Shift+1)
    (2, 7, KC["NUBS"]),                # < (German < key)
    (2, 8, S(KC["NUBS"])),             # > (Shift+<)
    (2, 9, S(KC["0"])),                # = (Shift+0)
    (2, 10, S(KC["6"])),               # & (Shift+6)
    (2, 11, KC["NO"]),                 # ſ, Unicode, not available

    # Row 3 (home row), Mod3 layer
    (3, 1, RALT(KC["MINS"])),          # \ (AltGr+ß)
    (3, 2, S(KC["7"])),                # / (Shift+7)
    (3, 3, RALT(KC["7"])),             # { (AltGr+7)
    (3, 4, RALT(KC["0"])),             # } (AltGr+0)
    (3, 5, S(KC["RBRC"])),             # * (Shift+ +)
    (3, 6, S(KC["MINS"])),             # ? , wait this should be (Shift+ß) for ? on German
    (3, 7, S(KC["8"])),                # ( (Shift+8)
    (3, 8, S(KC["9"])),                # ) (Shift+9)
    (3, 9, KC["SLSH"]),                # - on German = KC_SLASH (- is at slash position)
    (3, 10, S(KC["DOT"])),             # : (Shift+.)
    (3, 11, RALT(KC["Q"])),            # @ (AltGr+Q)

    # Row 4 (bottom letter row), Mod3 layer
    (4, 2, KC["NUHS"]),                # # on German = KC_NUHS
    (4, 3, S(KC["4"])),                # $ on German = Shift+4
    (4, 4, RALT(KC["NUBS"])),          # | (AltGr+<)
    (4, 5, RALT(KC["RBRC"])),          # ~ (AltGr+ +)
    (4, 6, KC["NO"]),                  # ` literal not reachable as single keystroke on German
                                       #   (KC_EQL is dead-acute; Shift+KC_EQL is dead-grave)
    (4, 7, KC["RBRC"]),                # + on German = KC_RBRC
    (4, 8, S(KC["5"])),                # % (Shift+5)
    (4, 9, S(KC["2"])),                # " (Shift+2)
    (4, 10, S(KC["NUHS"])),            # ' (Shift+#)
    (4, 11, S(KC["COMM"])),            # ; (Shift+,)

    # Pass mods through to L0 so the swap from there stays effective
    (5, 0, KC["TRNS"]),
    (5, 1, KC["TRNS"]),
    (5, 2, KC["TRNS"]),
]

# --- Layer 3 (Mod4 / navigation + numpad) ---------------------------------
# Bone Mod4: left half = nav cluster, right half = numpad.
#
#   row2:  PgUp Bksp Up   Del  PgDn   …  7 8 9 +
#   row3:  Home Left Down Right End   …  4 5 6 ,
#   row4:  Esc  Tab  Ins  Ent  Undo   …  1 2 3 .
#                                    0 (space)

L3_PATCH = [
    # Row 2 nav (cols 1-5 on left half)
    (2, 1, KC["PGUP"]),
    (2, 2, KC["BSPC"]),
    (2, 3, KC["UP"]),
    (2, 4, KC["DEL"]),
    (2, 5, KC["PGDN"]),
    # Row 2 numpad (cols 7-10)
    (2, 7, KC["P7"]),
    (2, 8, KC["P8"]),
    (2, 9, KC["P9"]),
    (2, 10, KC["PPLS"]),

    # Row 3 nav
    (3, 1, KC["HOME"]),
    (3, 2, KC["LEFT"]),
    (3, 3, KC["DOWN"]),
    (3, 4, KC["RGHT"]),
    (3, 5, KC["END"]),
    # Row 3 numpad
    (3, 7, KC["P4"]),
    (3, 8, KC["P5"]),
    (3, 9, KC["P6"]),
    (3, 10, KC["COMM"]),

    # Row 4 misc
    (4, 2, KC["ESC"]),
    (4, 3, KC["TAB"]),
    (4, 4, KC["INS"]),
    (4, 5, KC["ENT"]),
    # numpad bottom row
    (4, 7, KC["P1"]),
    (4, 8, KC["P2"]),
    (4, 9, KC["P3"]),
    (4, 10, KC["PDOT"]),
    # space on bottom
    (5, 6, KC["P0"]),

    # Pass mods through to L0
    (5, 0, KC["TRNS"]),
    (5, 1, KC["TRNS"]),
    (5, 2, KC["TRNS"]),
]


def patch_layer(layer, patches):
    """Return a new layer with given (row,col,val) entries overwritten."""
    by_key = {(e["row"], e["col"]): dict(e) for e in layer}
    for row, col, val in patches:
        if (row, col) in by_key:
            by_key[(row, col)]["val"] = val
        else:
            # position not present in original, skip silently rather than
            # invent a new matrix slot
            sys.stderr.write(f"warn: no slot at row={row} col={col}\n")
    # preserve original order
    return [by_key[(e["row"], e["col"])] for e in layer]


def make_trns_layer(template_layer):
    """Copy of template_layer with every val set to KC_TRNS (passthrough)."""
    return [{"col": e["col"], "row": e["row"], "val": KC["TRNS"]}
            for e in template_layer]


# Stuff applied to both base layers (Bone L0 and QWERTZ L2): F-row
# direct (Keychron stock hides F1-F12 behind FN; we want them direct
# since FN is now Mod3) and the macro group remap.
BASE_COMMON_PATCH = [
    # F-row direct (no FN required)
    (0, 1, KC["F1"]),   (0, 2, KC["F2"]),   (0, 3, KC["F3"]),
    (0, 4, KC["F4"]),   (0, 5, KC["F5"]),   (0, 6, KC["F6"]),
    (0, 7, KC["F7"]),   (0, 8, KC["F8"]),   (0, 9, KC["F9"]),
    (0, 10, KC["F10"]), (0, 11, KC["F11"]), (0, 12, KC["F12"]),
    # right-side macro group (was F13-F16)
    (0, 17, KC["MPRV"]),  # back
    (0, 18, KC["MPLY"]),  # play/pause
    (0, 19, KC["MNXT"]),  # next
    (0, 20, KC["CALC"]),  # calculator
]

# L0-only mod swap (Ctrl/Win/Alt → Win/Alt/Ctrl). NOT applied to L2:
# on Linux the keyboard sits in Mac/QWERTZ switch position and xkb's
# ctrl:swap_lalt_lctl_lwin handles the swap. If L2 also swapped, the
# two rotations would compose into Alt/Ctrl/Win, which is wrong.
L0_MOD_SWAP = [
    (5, 0, KC["LGUI"]),
    (5, 1, KC["LALT"]),
    (5, 2, KC["LCTL"]),
]


def main(template_path, out_path):
    with open(template_path) as f:
        tpl = json.load(f)

    layers = tpl["keymap"]
    if len(layers) < 4:
        raise SystemExit(f"template has {len(layers)} layers, expected ≥4")

    # Apply F-row / mod-swap / macro-group changes to a shared base
    # first, so L0 (Bone) and L2 (QWERTZ) both inherit them.
    common_base = patch_layer(layers[0], BASE_COMMON_PATCH)
    # L2 = QWERTZ base. Inherits common_base verbatim, letters stay
    # QWERTZ since BONE_PATCH only applies to L0.
    layers[2] = [dict(e) for e in common_base]
    # L1 = Bone Mod3 and L3 = Bone Mod4. Both start fully transparent so
    # any unpatched key falls through to whichever base layer is active.
    layers[1] = make_trns_layer(layers[1])
    layers[3] = make_trns_layer(layers[3])

    layers[0] = patch_layer(common_base, L0_PATCH + L0_MOD_SWAP)
    layers[1] = patch_layer(layers[1], L2_PATCH)  # Mod3 patches go on L1
    layers[3] = patch_layer(layers[3], L3_PATCH)

    # Recompute MD5 of the keymap structure (Keychron's checksum)
    payload = json.dumps(layers, separators=(",", ":"), sort_keys=False).encode()
    tpl["MD5"] = hashlib.md5(payload).hexdigest()
    tpl["keymap"] = layers

    with open(out_path, "w") as f:
        json.dump(tpl, f, separators=(",", ":"))
    print(f"wrote {out_path} ({len(open(out_path).read())} bytes, "
          f"layers={len(layers)}, MD5={tpl['MD5']})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: build_keychron_q6_pro_iso.py <template.json> <out.json>")
    main(sys.argv[1], sys.argv[2])
