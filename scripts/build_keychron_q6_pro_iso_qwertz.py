#!/usr/bin/env python3
"""Generate Keychron Launcher JSON for Keychron Q6 Pro ISO with the stock
QWERTZ keymap plus the multimedia row fix.

Stock Keychron firmware maps the four rightmost F-row keys to KC_F13..F16,
which the Linux kernel reports as XF86Launch5/6/7/(none). KDE's media
bindings expect XF86AudioPrev/Play/Next, so the dedicated multimedia row
silently does nothing. This keymap patches just those four positions to
real media keycodes so they actually control playback.

Everything else is left identical to the stock Keychron export.
"""
import json, sys, hashlib

# Media + calculator HID codes
KC_MPRV = 172   # KC_MEDIA_PREV_TRACK
KC_MPLY = 174   # KC_MEDIA_PLAY_PAUSE
KC_MNXT = 171   # KC_MEDIA_NEXT_TRACK
KC_CALC = 178   # KC_CALCULATOR

# Stock has KC_F13..F16 at row 0 cols 17..20. Patch the base layers
# (L0 Win, L2 Mac) so the keys actually do media on every host.
PATCH = [
    (0, 17, KC_MPRV),
    (0, 18, KC_MPLY),
    (0, 19, KC_MNXT),
    (0, 20, KC_CALC),
]
BASE_LAYERS = (0, 2)


def patch(layer, entries):
    by_key = {(e["row"], e["col"]): dict(e) for e in layer}
    for row, col, val in entries:
        by_key[(row, col)]["val"] = val
    return [by_key[(e["row"], e["col"])] for e in layer]


def main(template_path, out_path):
    with open(template_path) as f:
        tpl = json.load(f)
    for L in BASE_LAYERS:
        tpl["keymap"][L] = patch(tpl["keymap"][L], PATCH)
    payload = json.dumps(tpl["keymap"], separators=(",", ":")).encode()
    tpl["MD5"] = hashlib.md5(payload).hexdigest()
    with open(out_path, "w") as f:
        json.dump(tpl, f, separators=(",", ":"))
    print(f"wrote {out_path} ({len(open(out_path).read())} bytes)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: build_keychron_q6_pro_iso_qwertz.py <template.json> <out.json>")
    main(sys.argv[1], sys.argv[2])
