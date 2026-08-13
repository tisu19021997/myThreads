#!/usr/bin/env python3
"""Line-drawn part glyphs for the kit list.

A keyword search returns a hundred things. These say what the right one looks like.

Drawn rather than photographed on purpose: a shop's product photo is not ours to
republish and dies when the seller delists, while a schematic line drawing is
self-contained, never 404s, and is the idiom the rest of the thread already uses.

Every glyph is stroke-only in a 120x80 viewBox and inherits `currentColor`, so one
drawing works at 18px inside a chip and at 220px in the hover preview.
"""

import math

W, H = 120, 80

# Modules that are visually a small PCB are drawn by _board() with their own
# silkscreen text, because on a real breakout the printed part number IS the
# distinguishing feature. Everything else gets its own shape.
_BOARD_LABELS = {
    "mpu6050": "MPU-6050", "lsm6ds3": "LSM6DS3", "drv2605l": "DRV2605L",
    "max98357a": "MAX98357A", "inmp441": "INMP441", "apds9960": "APDS-9960",
    "vl53l0x": "VL53L0X", "tp4056": "TP4056", "wroom": "ESP32-S3\nWROOM-1",
}


def _board(label):
    """A breakout board: outline, mounting holes, a header strip, silkscreen text."""
    lines = label.split("\n")
    y0 = 40 if len(lines) == 1 else 34
    text = "".join(
        f'<text x="60" y="{y0 + i * 13}" text-anchor="middle" font-size="13" '
        f'font-family="ui-monospace,Menlo,monospace" fill="currentColor" '
        f'stroke="none">{ln}</text>'
        for i, ln in enumerate(lines)
    )
    pins = "".join(f'<line x1="{28 + i * 8}" y1="62" x2="{28 + i * 8}" y2="70"/>'
                   for i in range(9))
    return (
        '<rect x="18" y="14" width="84" height="48" rx="2"/>'
        '<circle cx="25" cy="21" r="2.5"/><circle cx="95" cy="21" r="2.5"/>'
        f'{pins}{text}'
    )


def _glyphs():
    g = {}
    for key, lab in _BOARD_LABELS.items():
        g[key] = _board(lab)

    # --- dev boards and displays -------------------------------------------
    g["devkit"] = (
        '<rect x="10" y="18" width="100" height="44" rx="2"/>'
        '<rect x="2" y="32" width="10" height="14" rx="2"/>'          # USB-C end
        '<rect x="46" y="26" width="28" height="20" rx="1"/>'          # module can
        '<line x1="50" y1="31" x2="70" y2="31"/><line x1="50" y1="36" x2="70" y2="36"/>'
        + "".join(f'<line x1="{18 + i * 9}" y1="62" x2="{18 + i * 9}" y2="70"/>'
                  for i in range(11))
        + "".join(f'<line x1="{18 + i * 9}" y1="10" x2="{18 + i * 9}" y2="18"/>'
                  for i in range(11))
    )
    g["oled"] = (
        '<rect x="16" y="12" width="88" height="50" rx="2"/>'
        '<rect x="26" y="20" width="68" height="30" rx="1"/>'
        '<line x1="32" y1="30" x2="58" y2="30" stroke-width="3"/>'
        '<line x1="32" y1="38" x2="72" y2="38" stroke-width="3"/>'
        + "".join(f'<line x1="{46 + i * 9}" y1="62" x2="{46 + i * 9}" y2="70"/>'
                  for i in range(4))
    )
    g["pcb"] = (
        '<rect x="14" y="14" width="92" height="52" rx="2"/>'
        '<circle cx="22" cy="22" r="3"/><circle cx="98" cy="22" r="3"/>'
        '<circle cx="22" cy="58" r="3"/><circle cx="98" cy="58" r="3"/>'
        '<path d="M34 34h20l8 8h22"/><path d="M34 48h14l10-10h24"/>'
    )
    g["usbc"] = (
        '<rect x="24" y="28" width="72" height="24" rx="12"/>'
        '<rect x="34" y="36" width="52" height="8" rx="4"/>'
        '<line x1="24" y1="52" x2="18" y2="62"/><line x1="96" y1="52" x2="102" y2="62"/>'
    )

    # --- prototyping --------------------------------------------------------
    g["breadboard"] = (
        '<rect x="10" y="12" width="100" height="56" rx="3"/>'
        '<line x1="10" y1="40" x2="110" y2="40" stroke-dasharray="3 3"/>'
        '<line x1="18" y1="18" x2="102" y2="18"/><line x1="18" y1="62" x2="102" y2="62"/>'
        + "".join(f'<circle cx="{22 + i * 8}" cy="30" r="1.6"/>' for i in range(11))
        + "".join(f'<circle cx="{22 + i * 8}" cy="50" r="1.6"/>' for i in range(11))
    )
    g["jumpers"] = (
        '<path d="M14 24c22-16 40 16 60 0s24-14 32-4"/>'
        '<path d="M14 40c22-16 40 16 60 0s24-14 32-4"/>'
        '<path d="M14 56c22-16 40 16 60 0s24-14 32-4"/>'
        '<rect x="8" y="20" width="7" height="9" rx="1"/>'
        '<rect x="8" y="36" width="7" height="9" rx="1"/>'
        '<rect x="8" y="52" width="7" height="9" rx="1"/>'
    )
    g["wirespool"] = (
        '<ellipse cx="34" cy="40" rx="8" ry="26"/>'                     # spool end
        '<path d="M34 14h44M34 66h44"/><ellipse cx="78" cy="40" rx="8" ry="26"/>'
        + "".join(f'<line x1="{42 + i * 9}" y1="18" x2="{42 + i * 9}" y2="62"/>'
                  for i in range(4))
        + '<path d="M86 40c8 0 12-8 22-6"/>'
    )

    # --- discretes ----------------------------------------------------------
    g["resistor"] = (
        '<line x1="6" y1="40" x2="34" y2="40"/><line x1="86" y1="40" x2="114" y2="40"/>'
        '<rect x="34" y="28" width="52" height="24" rx="10"/>'
        '<line x1="46" y1="28" x2="46" y2="52" stroke-width="4"/>'
        '<line x1="56" y1="28" x2="56" y2="52" stroke-width="4"/>'
        '<line x1="66" y1="28" x2="66" y2="52" stroke-width="4"/>'
    )
    g["capacitor"] = (
        '<path d="M40 46a22 20 0 1 1 40 0z"/>'
        '<line x1="52" y1="46" x2="52" y2="70"/><line x1="68" y1="46" x2="68" y2="70"/>'
        '<text x="60" y="34" text-anchor="middle" font-size="11" fill="currentColor" '
        'stroke="none" font-family="ui-monospace,Menlo,monospace">104</text>'
    )
    g["led"] = (
        '<path d="M42 44V26a18 18 0 0 1 36 0v18z"/>'
        '<line x1="42" y1="44" x2="78" y2="44"/>'
        '<line x1="50" y1="44" x2="50" y2="72"/><line x1="70" y1="44" x2="70" y2="66"/>'
        '<path d="M86 16l8-8M92 24l10-6" stroke-width="2"/>'
    )
    g["transistor"] = (
        '<path d="M38 52a22 22 0 0 1 44 0z"/><line x1="38" y1="52" x2="82" y2="52"/>'
        '<line x1="48" y1="52" x2="48" y2="74"/><line x1="60" y1="52" x2="60" y2="74"/>'
        '<line x1="72" y1="52" x2="72" y2="74"/>'
        '<text x="60" y="44" text-anchor="middle" font-size="10" fill="currentColor" '
        'stroke="none" font-family="ui-monospace,Menlo,monospace">S8050</text>'
    )
    g["diode"] = (
        '<line x1="6" y1="40" x2="38" y2="40"/><line x1="82" y1="40" x2="114" y2="40"/>'
        '<rect x="38" y="30" width="44" height="20" rx="3"/>'
        '<line x1="74" y1="30" x2="74" y2="50" stroke-width="5"/>'
    )

    # --- controls -----------------------------------------------------------
    g["button"] = (
        '<rect x="30" y="24" width="60" height="36" rx="2"/>'
        '<circle cx="60" cy="42" r="11"/>'
        '<line x1="30" y1="30" x2="20" y2="30"/><line x1="30" y1="54" x2="20" y2="54"/>'
        '<line x1="90" y1="30" x2="100" y2="30"/><line x1="90" y1="54" x2="100" y2="54"/>'
    )
    g["encoder"] = (
        '<rect x="34" y="34" width="52" height="30" rx="2"/>'
        '<rect x="52" y="8" width="16" height="26" rx="2"/>'
        + "".join(f'<line x1="52" y1="{13 + i * 5}" x2="68" y2="{13 + i * 5}"/>'
                  for i in range(4))
        + '<line x1="42" y1="64" x2="42" y2="74"/><line x1="60" y1="64" x2="60" y2="74"/>'
          '<line x1="78" y1="64" x2="78" y2="74"/>'
    )
    g["pot"] = (
        '<circle cx="60" cy="44" r="22"/><line x1="60" y1="44" x2="60" y2="24"/>'
        '<rect x="54" y="8" width="12" height="16" rx="2"/>'
        '<line x1="44" y1="66" x2="44" y2="76"/><line x1="60" y1="66" x2="60" y2="76"/>'
        '<line x1="76" y1="66" x2="76" y2="76"/>'
    )
    g["slideswitch"] = (
        '<rect x="26" y="30" width="68" height="26" rx="3"/>'
        '<rect x="32" y="18" width="20" height="14" rx="2"/>'
        '<line x1="38" y1="56" x2="38" y2="68"/><line x1="60" y1="56" x2="60" y2="68"/>'
        '<line x1="82" y1="56" x2="82" y2="68"/>'
    )

    # --- instruments and tools ---------------------------------------------
    g["multimeter"] = (
        '<rect x="26" y="8" width="68" height="64" rx="5"/>'
        '<rect x="34" y="16" width="52" height="18" rx="2"/>'
        '<text x="60" y="30" text-anchor="middle" font-size="12" fill="currentColor" '
        'stroke="none" font-family="ui-monospace,Menlo,monospace">0.00</text>'
        '<circle cx="60" cy="50" r="12"/><line x1="60" y1="50" x2="60" y2="41"/>'
        '<circle cx="44" cy="66" r="2.5"/><circle cx="76" cy="66" r="2.5"/>'
    )
    g["iron"] = (
        '<rect x="30" y="32" width="52" height="16" rx="4"/>'
        '<path d="M30 40H16"/><path d="M82 34l14 6-14 6z"/>'
        '<path d="M96 40l16 0"/>'
        '<line x1="40" y1="32" x2="40" y2="48"/><line x1="48" y1="32" x2="48" y2="48"/>'
    )
    g["solderspool"] = (
        '<circle cx="60" cy="40" r="28"/><circle cx="60" cy="40" r="10"/>'
        '<line x1="60" y1="12" x2="60" y2="30"/><line x1="60" y1="50" x2="60" y2="68"/>'
        '<path d="M88 40c10 2 14 10 24 8"/>'
    )
    g["fluxpen"] = (
        '<rect x="20" y="34" width="66" height="14" rx="3"/>'
        '<path d="M86 34l16 7-16 7z"/><rect x="26" y="30" width="10" height="22" rx="2"/>'
    )
    g["wick"] = (
        '<path d="M10 34h96v12H10z"/>'                                  # flat braid ribbon
        + "".join(f'<path d="M{14 + i * 12} 34l8 12M{22 + i * 12} 34l-8 12"/>'
                  for i in range(8))
    )
    g["cutters"] = (
        '<path d="M18 30l30 8-30 8z"/>'                                 # blunt cutting head
        '<line x1="48" y1="34" x2="48" y2="46"/>'
        '<circle cx="52" cy="40" r="4"/>'                               # pivot
        '<path d="M56 36l40-14"/><path d="M56 44l40 14"/>'              # handles
        '<path d="M96 22c10-4 14 2 10 8l-14 6"/>'
        '<path d="M96 58c10 4 14-2 10-8l-14-6"/>'
    )
    g["strippers"] = (
        '<path d="M20 28h30v6H20z"/><path d="M20 46h30v6H20z"/>'        # flat jaws
        '<circle cx="30" cy="31" r="4"/><circle cx="30" cy="49" r="4"/>' # stripping notches
        '<circle cx="42" cy="31" r="3"/><circle cx="42" cy="49" r="3"/>'
        '<circle cx="54" cy="40" r="4"/>'                               # pivot
        '<path d="M58 36l38-12"/><path d="M58 44l38 12"/>'
        '<path d="M96 24c10-4 14 2 10 8l-14 6"/>'
        '<path d="M96 56c10 4 14-2 10-8l-14-6"/>'
    )
    g["tweezers"] = (
        '<path d="M56 8h8l14 56-8 4z"/>'                                # right arm, tapered
        '<path d="M56 8h8l-14 56 8 4z" transform="translate(-8 0)"/>'   # left arm
        '<path d="M52 4h16v8H52z"/>'                                    # joined top
    )
    g["helpinghands"] = (
        '<ellipse cx="60" cy="68" rx="26" ry="7"/>'                     # heavy base
        '<line x1="60" y1="61" x2="60" y2="30"/>'                       # post
        '<path d="M60 38L34 26"/><path d="M60 34l26-14"/>'              # arms
        '<path d="M34 26l-12-4 2 8z"/><path d="M22 22l-8 2 6 4"/>'      # clip jaws
        '<path d="M86 20l12-4-2 8z"/><path d="M98 16l8 2-6 4"/>'
    )
    g["caliper"] = (
        '<rect x="6" y="36" width="108" height="9" rx="2"/>'          # beam
        '<path d="M24 36V12h7v24"/><path d="M24 45v10h7V45"/>'         # fixed jaw
        '<path d="M44 36V18h7v18"/><path d="M44 45v10h7V45"/>'         # sliding jaw
        '<rect x="58" y="20" width="40" height="22" rx="2"/>'          # display
        '<text x="78" y="35" text-anchor="middle" font-size="11" fill="currentColor" '
        'stroke="none" font-family="ui-monospace,Menlo,monospace">0.00</text>'
        '<path d="M58 45h40v8H58z"/>'                                   # slider body
    )
    g["hotair"] = (
        '<rect x="14" y="26" width="46" height="40" rx="4"/>'
        '<rect x="20" y="32" width="34" height="14" rx="2"/>'
        '<circle cx="30" cy="58" r="4"/><circle cx="46" cy="58" r="4"/>'
        '<path d="M60 40h16"/><rect x="76" y="32" width="30" height="14" rx="4"/>'
        '<path d="M106 34l8-6M106 44l8 6M108 39h8"/>'
    )
    g["pastesyringe"] = (
        '<rect x="24" y="30" width="56" height="20" rx="2"/>'
        '<rect x="14" y="34" width="10" height="12" rx="2"/>'
        '<path d="M80 34l18 6-18 6z"/><path d="M98 40h10"/>'
        '<line x1="38" y1="30" x2="38" y2="50" stroke-dasharray="3 3"/>'
    )
    g["bottle"] = (
        '<path d="M46 24h28v44a6 6 0 0 1-6 6H52a6 6 0 0 1-6-6z"/>'
        '<rect x="52" y="10" width="16" height="14" rx="2"/>'
        '<line x1="46" y1="40" x2="74" y2="40"/>'
        '<text x="60" y="60" text-anchor="middle" font-size="11" fill="currentColor" '
        'stroke="none" font-family="ui-monospace,Menlo,monospace">IPA</text>'
    )

    # --- power and actuators ------------------------------------------------
    g["lipo"] = (
        '<rect x="20" y="20" width="72" height="40" rx="4"/>'
        '<path d="M92 32h10v16H92"/>'
        '<line x1="30" y1="30" x2="30" y2="50"/>'
        '<text x="58" y="46" text-anchor="middle" font-size="12" fill="currentColor" '
        'stroke="none" font-family="ui-monospace,Menlo,monospace">3.7V</text>'
    )
    g["jst"] = (
        '<rect x="30" y="28" width="34" height="24" rx="3"/>'
        '<line x1="40" y1="52" x2="40" y2="62"/><line x1="54" y1="52" x2="54" y2="62"/>'
        '<path d="M64 34c16 0 20 12 40 12"/><path d="M64 44c16 0 20 12 40 12"/>'
    )
    g["coinmotor"] = (
        '<circle cx="56" cy="40" r="24"/><circle cx="56" cy="40" r="8"/>'
        '<path d="M80 36h26M80 46h26"/>'
        '<path d="M100 30l6 6-6 6" stroke-dasharray="0"/>'
    )
    g["lramotor"] = (
        '<circle cx="52" cy="40" r="22"/><rect x="40" y="30" width="24" height="20" rx="2"/>'
        '<path d="M74 40h30"/><path d="M84 28c8 6 8 18 0 24" stroke-dasharray="3 3"/>'
        '<path d="M94 24c12 8 12 24 0 32" stroke-dasharray="3 3"/>'
    )
    g["speaker"] = (
        '<rect x="20" y="12" width="80" height="56" rx="6"/>'           # square frame
        '<circle cx="60" cy="40" r="22"/><circle cx="60" cy="40" r="8"/>'
        '<circle cx="28" cy="20" r="2.5"/><circle cx="92" cy="20" r="2.5"/>'
        '<circle cx="28" cy="60" r="2.5"/><circle cx="92" cy="60" r="2.5"/>'
    )
    g["ledring"] = (
        '<circle cx="60" cy="40" r="28"/><circle cx="60" cy="40" r="16"/>'
        + "".join(
            f'<rect x="{60 + 22 * math.cos(i * 3.14159 / 4) - 3.5:.1f}" '
            f'y="{40 + 22 * math.sin(i * 3.14159 / 4) - 3.5:.1f}" '
            'width="7" height="7" rx="1"/>'
            for i in range(8)
        )
    )
    g["ledstrip"] = (
        '<rect x="8" y="30" width="104" height="20" rx="3"/>'
        + "".join(f'<rect x="{16 + i * 20}" y="34" width="12" height="12" rx="1"/>'
                  for i in range(5))
        + '<line x1="8" y1="50" x2="112" y2="50" stroke-dasharray="4 4"/>'
    )

    # --- craft, finishing ---------------------------------------------------
    g["foamsheet"] = (
        '<path d="M16 22h76v40H16z"/><path d="M92 22l12-8v40l-12 8"/>'
        '<path d="M16 22l12-8h76"/><line x1="16" y1="42" x2="92" y2="42" '
        'stroke-dasharray="3 3"/>'
    )
    g["craftknife"] = (
        '<path d="M14 52l58-30 10 6-58 30z"/><path d="M82 28l18-10 6 10-18 10z"/>'
        '<line x1="30" y1="44" x2="66" y2="26" stroke-dasharray="3 3"/>'
    )
    g["cuttingmat"] = (
        '<rect x="10" y="14" width="100" height="52" rx="3"/>'
        + "".join(f'<line x1="{24 + i * 14}" y1="14" x2="{24 + i * 14}" y2="66" '
                  'stroke-dasharray="2 4"/>' for i in range(6))
        + "".join(f'<line x1="10" y1="{27 + i * 13}" x2="110" y2="{27 + i * 13}" '
                  'stroke-dasharray="2 4"/>' for i in range(3))
    )
    g["taperoll"] = (
        '<ellipse cx="48" cy="40" rx="16" ry="26"/><ellipse cx="48" cy="40" rx="6" ry="10"/>'
        '<path d="M48 14h30v52H48"/><ellipse cx="78" cy="40" rx="16" ry="26"/>'
        '<path d="M94 40h16" stroke-dasharray="4 3"/>'
    )
    g["stickynotes"] = (
        '<rect x="18" y="16" width="54" height="50" rx="1"/>'
        '<rect x="30" y="24" width="54" height="50" rx="1"/>'
        '<line x1="40" y1="40" x2="72" y2="40"/><line x1="40" y1="50" x2="66" y2="50"/>'
    )
    g["notebook"] = (
        '<rect x="26" y="10" width="68" height="60" rx="2"/>'
        '<line x1="38" y1="10" x2="38" y2="70"/>'
        '<line x1="50" y1="28" x2="84" y2="28"/><line x1="50" y1="40" x2="84" y2="40"/>'
        '<line x1="50" y1="52" x2="72" y2="52"/>'
        '<text x="66" y="20" text-anchor="middle" font-size="9" fill="currentColor" '
        'stroke="none" font-family="ui-monospace,Menlo,monospace">A5</text>'
    )
    g["pen"] = (
        '<path d="M18 62l10-10 44-44 10 10-44 44z"/><path d="M18 62l14-4-10-10z"/>'
        '<line x1="72" y1="8" x2="82" y2="18"/>'
        '<rect x="84" y="6" width="16" height="10" rx="2" transform="rotate(45 92 11)"/>'
    )
    g["sandpaper"] = (
        '<path d="M20 18h80v44H20z"/>'
        + "".join(f'<circle cx="{28 + (i * 17) % 64}" cy="{26 + (i * 11) % 28}" r="1.8"/>'
                  for i in range(14))
        + '<path d="M100 18l6 6v44l-6-6z"/>'
    )
    g["screw"] = (
        '<rect x="50" y="8" width="20" height="10" rx="2"/>'
        '<path d="M54 18h12v46l-6 10-6-10z"/>'
        + "".join(f'<line x1="54" y1="{24 + i * 8}" x2="66" y2="{20 + i * 8}"/>'
                  for i in range(5))
    )
    g["insert"] = (
        '<path d="M44 16h32v48H44z"/><path d="M52 16v48M68 16v48" stroke-dasharray="3 3"/>'
        + "".join(f'<line x1="44" y1="{22 + i * 9}" x2="76" y2="{22 + i * 9}"/>'
                  for i in range(5))
    )
    g["gluetube"] = (
        '<path d="M46 26h28v40a4 4 0 0 1-4 4H50a4 4 0 0 1-4-4z"/>'
        '<path d="M52 26l4-12h8l4 12"/><rect x="54" y="4" width="12" height="10" rx="2"/>'
        '<line x1="46" y1="46" x2="74" y2="46"/>'
    )
    g["printedpart"] = (
        '<path d="M60 10l34 18v30L60 76 26 58V28z"/>'
        '<path d="M60 10v30l34 18M60 40L26 58M60 40v36"/>'
        '<path d="M26 28l34 12 34-12" stroke-dasharray="3 3"/>'
    )
    g["smdbook"] = (
        '<rect x="16" y="12" width="88" height="56" rx="3"/>'
        '<line x1="16" y1="26" x2="104" y2="26"/><line x1="16" y1="40" x2="104" y2="40"/>'
        '<line x1="16" y1="54" x2="104" y2="54"/>'
        + "".join(f'<rect x="{24 + i * 20}" y="16" width="10" height="6" rx="1"/>'
                  for i in range(4))
        + "".join(f'<rect x="{24 + i * 20}" y="30" width="10" height="6" rx="1"/>'
                  for i in range(4))
    )
    return g


GLYPHS = _glyphs()


def svg(key, cls="ic"):
    """Inline SVG for one glyph. Falls back to a neutral box rather than breaking."""
    body = GLYPHS.get(key)
    if body is None:
        body = '<rect x="20" y="18" width="80" height="44" rx="3"/><path d="M20 62l80-44"/>'
    return (
        f'<svg class="{cls}" viewBox="0 0 {W} {H}" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{body}</svg>'
    )


def known():
    return set(GLYPHS)


if __name__ == "__main__":
    print(f"{len(GLYPHS)} glyphs: {', '.join(sorted(GLYPHS))}")
