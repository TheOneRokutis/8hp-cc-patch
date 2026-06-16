# E-Series 8HP Cruise Control Gear Patch

A small GUI tool that patches BMW **MSV80 / MSD80 / MSD81** DME firmware images to restore cruise control in **8th gear** after a native ZF **8HP** automatic swap into an E-series chassis.

## What it does

When an 8-speed ZF 8HP is natively swapped into an E-series BMW that never came with one from the factory (E8x / E9x / E6x), the engine DME's gearbox-data decode has no entry for 8th gear. The transmission reports 8th on the bus as gear code `0xC`, but the DME only recognizes the codes for gears 1–7 (plus reverse and neutral) and treats anything else as **neutral**. So the moment the car shifts into 8th, the DME thinks it's in neutral and cruise control drops out.

This tool patches the gear-decode routine so code `0xC` decodes correctly to 8th gear. Cruise then stays engaged in 8th. Gears 1–7, reverse, and neutral are unchanged.

## Supported ECUs

- MSV80 (N52 and related)
- MSD80 (N53)
- MSD81 (N54)

All three use the **identical** gear-decode byte sequence, so the same patch applies to each. The tool locates the patch site by **byte signature**, not a fixed address, so it works across software versions as long as the signature is present.

## How it works

It searches the loaded `.bin` for the 12-byte gear-decode signature (the gear 1–3 compares in the decode cascade):

```
Search:  DF 5F 15 00 DF 6F 15 00 DF 7F 15 00
```

and replaces it, in place, with a compact arithmetic decode of the same length:

```
Replace: BF 5F 25 80 FF DF 23 80 C2 CF 3C 21
```

which is equivalent to:

```c
if (code < 5 || code > 0xC) gear = 0;        // neutral / unused codes
else                        gear = code - 4; // codes 5..C -> gears 1..8
```

Reverse (the instruction immediately before the signature) and neutral are left intact, and because the replacement is exactly 12 bytes, nothing else in the image shifts. Net effect: gear code `0xC` now decodes to 8th instead of falling through to neutral.

### Safety logic

- **Signature not found** → patch refused; you're told to update the DME to a software version that contains this gear table.
- **Signature found more than once** → patch refused (ambiguous); open an issue.
- **Exactly one match** → patch proceeds.
- The **original file is never modified** — output is written to a new file you choose.

## Requirements

### To run the tool
- Python 3.8+ (any modern Python 3)
- Tkinter — bundled with Python on Windows/macOS; on Debian/Ubuntu: `sudo apt install python3-tk`
- No third-party packages.

### For the patch to be valid
- A **full, clean read** of the DME flash (complete dump, no missing/zeroed regions from a bad read).
- A car that is a **native 8HP swap** into an E-series that never had 8HP from the factory (E8x / E9x / E6x). This patch is only meaningful in that scenario.
- After patching you **must correct the flash checksum** with an MSV80/MSD8x-aware corrector (e.g. WinOLS with the matching module). **This tool does not correct checksums.**
- A recovery method (bench / BDM) available before flashing.

## Installation

```
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

## Usage

```
python msv80_gear_patch.py
```

1. **Open .bin** and select your full DME read.
2. The tool searches for the signature and either shows the matched address (Patch enabled), tells you to update the DME (not found), or refuses (multiple matches).
3. **Patch** and choose where to save the output. The original is left untouched.
4. **Correct the checksum** of the patched file.
5. Flash, with a recovery path ready.

## Disclaimer

This tool modifies engine control unit firmware. Flashing modified firmware carries risk, up to rendering the ECU inoperable. Use only on hardware you own or are authorized to modify; always keep an unmodified backup of the original read; correct checksums before flashing; have a recovery method available. You are solely responsible for any use. Provided as-is, without warranty of any kind.

## License

[MIT](LICENSE)
