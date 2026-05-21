# Physical layout notes

How to translate the Bone layer design into a VIA keymap JSON for a new
keyboard.

## What VIA needs

VIA stores keymaps as a flat array of keycodes, one per matrix position, in
the order the keyboard's `via.json` (the device's *layout definition*, not
the keymap) declares. The board's matrix order is whatever its firmware
defines — usually row-by-row, left-to-right, but not always.

The easiest path: don't construct the JSON by hand. Configure the keymap
in VIA's GUI, then **File → Save Layout** to dump a JSON. That's the file
to commit.

## ANSI vs ISO

ISO boards have an extra key:

- Left of `Z` (the `<>|` key on QWERTZ).
- Vertical Enter (tall Enter), which means `\` is moved up.

Bone's letter block has 30 keys (3 rows × 10), so on either layout the
mapping is mechanical for the letters. The differences:

- **ISO `<>|` key (left of Z):** Bone doesn't claim it. Recommended: leave
  as QWERTZ default. Alternatively, repurpose as a Mod3 or Mod4 key.
- **ISO key right of `Ä` (`#`/`'`):** in Neo/Bone this is the Mod3
  trigger. Map it to `MO(2)` (or whichever layer you put Mod3 on).
- **Caps Lock:** also Mod3. Map to `MO(2)`.

## Adding a new board

1. Plug it in, open VIA, confirm it's recognised.
2. Switch to Layer 0. Click each physical key one at a time and assign the
   Bone L0 character (consult [`layer-design.md`](./layer-design.md)).
3. Repeat for L2 (Mod3) and L3 (Mod4) layers.
4. Test by typing in a text editor.
5. **File → Save Layout** → drop the resulting `.json` into
   `keymaps/<board-name>.json`.
6. Add a row to the table in the README.
7. PR.

That's it. The layer *content* is identical across boards; only the matrix
positions differ.
