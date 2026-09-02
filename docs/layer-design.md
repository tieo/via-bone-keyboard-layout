# Layer design

Canonical source: <https://neo-layout.org/Layouts/bone/>. This document
is a working reference for what the Keychron Q6 Pro keymap in this repo
produces. If it disagrees with neo-layout.org, neo-layout.org wins; open
an issue.

## Assumed host OS layout

**German (QWERTZ), default variant.** Every keycode below is the HID
keycode whose label, *on a QWERTZ keyboard*, produces the target Bone
character. Examples: Bone "ü" sends `KC_LBRC` (the key labelled `ü` on
a QWERTZ board). Bone "ß" sends `KC_MINS` (the key labelled `ß`).

If the host OS is anything other than plain QWERTZ, the firmware Bone
keymap will produce the wrong characters. See the README.

## Layer assignment in the Keychron Q6 Pro keymap

The Q6 Pro firmware has 4 layer slots and we use all of them:

| Slot | Contents | Activated by |
|---|---|---|
| L0 | Bone base | default with back toggle on Win side |
| L1 | Bone Mod3 (punctuation, brackets, AltGr-combo symbols) | hold Caps Lock, ISO `#`, or the FN1 key |
| L2 | Plain QWERTZ base | default with back toggle on Mac side |
| L3 | Bone Mod4 (nav cluster + numpad) | hold ISO `<` or Right Alt |

The Mac/Win back toggle picks between the two base layers. Mod3 and
Mod4 are momentary; the rest of those layers is transparent and falls
through to whichever base layer is active.

## L0, Bone base

Letter block (the only thing Bone changes relative to QWERTZ; number
row, modifiers, function row stay as QWERTZ):

```
top:    j  d  u  a  x   p  h  l  m  w  ß
home:   c  t  i  e  o   b  n  r  s  g
bottom: f  v  ü  ä  ö   y  z  ,  .  k
```

Y/Z swap (xkb's AB06=y AB07=z) is handled by sending `KC_Z` for `y` and
`KC_Y` for `z`, since the German OS layout already swaps the two
positions relative to ANSI.

ISO note: the extra key left of `Y` (`<>|` on QWERTZ) is reused as the
Mod4 trigger.

## Bone Shift layer (no remap needed)

Holding Shift produces the capital of each L0 letter via the OS
keymap. No firmware work. Capital ẞ on Shift+ß has been in mainline
xkb / Windows since ~2017.

Bone's "Level 2" symbols on the number row (`° § ℓ » « $ € „ " …`) are
**not** implemented in this firmware keymap. Most are Unicode-only and
the ASCII-reachable ones (`° § $ €` via their German positions, e.g.
Shift+`^` for °) would need mod-morph, which stock VIA / Keychron
firmware doesn't expose. Use xkb's `de(bone)` on Linux to get them.

## L1, Bone Mod3

Activated by holding Caps Lock or ISO `#` (xkb's `bksl_switch`
position). Also bound to the keyboard's FN1 key so the stock Keychron
`FN + ...` muscle memory still works.

Bone Mod3, on a German QWERTZ host:

```
top:    .  _  [  ]  ^   !  <  >  =  &  .
home:   \  /  {  }  *   ?  (  )  -  :  @
bottom: #  $  |  ~  .   +  %  "  '  ;
```

The dots are placeholders for Unicode-only Bone symbols (`° ̄ ſ ` `)
that can't be reached from a plain German layout. The slots are either
`KC_NO` or, where convenient, repurposed for hardware controls
(see below).

The mapping table in `scripts/build_keychron_q6_pro_iso.py` is the
source of truth for which German keystroke produces each symbol
(e.g. `[` = AltGr+8 = `RALT(KC_8)`).

### Hardware controls slotted into Mod3's Unicode-only positions

Bone's Mod3 leaves a handful of positions filled with characters that
need Unicode input. Those slots are repurposed here:

- Mod3 + Tab = `RGB_TOG` (matches Keychron's stock FN+Tab)
- Mod3 + Q = `RGB_MOD` (next backlight effect; matches FN+Q)
- Mod3 + ß = `RGB_RMOD` (previous backlight effect; uses Bone's `ſ` slot)

## L2, plain QWERTZ base

Standard German QWERTZ. The same F-row direct binding and macro-group
remap as L0 (Calculator / Prev / Play-Pause / Next on the four
rightmost F-row keys) but **no** modifier swap on the bottom-left
cluster. On Linux the user runs xkb's `de(bone)` and
`ctrl:swap_lalt_lctl_lwin` against this base layer; if L2 also swapped,
the two rotations would compose into the wrong order
(Alt/Ctrl/Win instead of Win/Alt/Ctrl).

## L3, Bone Mod4

Activated by holding ISO `<` or Right Alt. Navigation cluster on the
left, numpad on the right:

```
top:    PgUp BkSp  Up   Del  PgDn  .  7  8  9  +  .
home:   Home Left  Down Right End  .  4  5  6  ,  .
bottom: Esc  Tab   Ins  Enter Undo .  1  2  3  .  .
                                            0
```

Dots are unmapped (Bone's reference has Unicode-only or rarely-used
symbols there; left as `KC_TRNS` so they fall through to the base
layer).

## Layers 5-6 (Greek / math): out of scope

Bone layers 5 and 6 (`α β → ⇒ √ ∫ ° ∞ ≠ ≤` …) are Unicode-only and
unreachable from a plain German OS layout. Stock VIA / Keychron
firmware can't send arbitrary Unicode without macros tied to a
specific input method (`Ctrl+Shift+U` on Linux+IBus, `Alt+numpad` on
Windows, Option-dead-keys on macOS), which defeats the "Bone follows
the keyboard everywhere" goal.

On Linux you can layer xkb's `de(bone)` on top instead and get all 6
layers natively. The Mac/Win back toggle is wired so you flip the
keyboard to Mac (= L2 plain QWERTZ) when typing on Linux, and back to
Win (= L0 Bone) for everything else.
