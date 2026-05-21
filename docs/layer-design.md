# Layer design

Canonical source: <https://neo-layout.org/Layouts/bone/>. This document is a
working reference for what each VIA keymap should produce. If it disagrees
with neo-layout.org, neo-layout.org wins — open an issue.

## Assumed host OS layout

**German (QWERTZ), default variant.** Every keycode below is the HID
keycode whose label, *on a QWERTZ keyboard*, produces the target Bone
character. Examples: Bone "ü" → send `KC_LBRC` (the key labelled `ü` on a
QWERTZ board). Bone "ß" → send `KC_MINS` (the key labelled `ß`).

If the host OS is anything other than plain QWERTZ, this won't work. See
the README.

## L0 — Bone base

Letter block (the only thing Bone changes relative to QWERTZ — number row,
modifiers, function row, etc. stay as the board's QWERTZ default):

```
top:    j  d  u  a  x   p  h  l  m  w  ß
home:   c  t  i  e  o   b  n  r  s  g
bottom: f  v  ü  ä  ö   y  z  ,  .  k
```

ISO note: the extra key left of `Y` on ISO boards is **not part of Bone's
letter block**. Suggested mapping: leave it as the QWERTZ default (`<>|`),
or map to a Mod3/Mod4 layer key — your call.

## L1 — Shift (implicit)

Holding Shift produces the capital of each L0 letter plus the shifted
symbols on the number row. No remapping needed — the OS handles this from
L0.

Note: Bone places **uppercase ẞ** (capital eszett) on Shift+ß. QWERTZ
already does this from Linux ~2017+, so it works for free.

## L2 — Mod3

Activated by holding the Mod3 key (typically the Caps Lock position, and
the `#` key right of `ä` on ISO).

Contains common punctuation and brackets. Layout (same physical grid as
L0):

```
top:    .  _  [  ]  ^   !  <  >  =  &  ſ
home:   \  /  {  }  *   ?  (  )  -  :  @
bottom: #  $  |  ~  `   +  %  "  '  ;
```

Most of these are direct QWERTZ-shifted symbols or AltGr combos. Mapping
table: see [`mod3-keycodes.md`](./mod3-keycodes.md) (TODO).

## L3 — Mod4

Activated by holding the Mod4 key (typically the right-Alt position).

Navigation cluster on the left half, numpad on the right:

```
top:    PgUp BkSp  Up  Del PgDn   ¡   7  8  9  +  −
home:   Home Left Down Right End  ¿   4  5  6  ,  .
bottom: Esc  Tab  Ins  Ent Undo   :   1  2  3  ;
```

Plus `0` typically on a Mod4-modified space or similar — check
neo-layout.org for the exact spec.

Most entries are standard HID nav/keypad codes. `¡`/`¿`/`−` need AltGr
combos on QWERTZ; document the exact sequence per board.

## L4 and L5 (out of scope)

Layers 5 and 6 of Bone contain Greek letters and math symbols (`α β → ⇒ √
∫ ° ∞ ≠ ≤` etc). These are Unicode characters with no QWERTZ keycode, so
VIA can't reach them without custom firmware that knows `UC()`. If you
need them, either:

- Use xkb's `de(bone)` instead of this repo, or
- Build custom QMK with Unicode keycodes and replace the relevant L2/L3
  slots with `UC(0x03B1)` etc.

Out of scope here.
