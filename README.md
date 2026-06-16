# E-Series 8HP Cruise Control Gear Patch

A small GUI tool that patches BMW **MSV80 / MSD80 / MSD81 (Currently only tested MSV80, but should work on MSD)**  DME firmware images to restore cruise control in **8th gear** after a native ZF **8HP** automatic swap into an E-series chassis.


## What it does

When an 8-speed ZF 8HP is natively swapped into an E-series BMW that never came with one from the factory (E8x / E9x / E6x), the engine DME's gearbox-data decode has no entry for 8th gear. The transmission reports 8th on the bus as gear code `0xC`, but the DME only recognizes the codes for gears 1–7 (plus reverse and neutral) and treats anything else as **neutral**. So the moment the car shifts into 8th, the DME thinks it's in neutral and cruise control drops out.

This tool patches the gear-decode routine so code `0xC` decodes correctly to 8th gear. Cruise then stays engaged in 8th. Gears 1–7, reverse, and neutral are unchanged.

## Supported ECUs

- MSV80 (Tested. Works)
- MSD80 (Should work in theory)
- MSD81 (Should work in theory)

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

Reverse and neutral are left intact, and because the replacement is exactly 12 bytes, nothing else in the image shifts.

### Safety logic

- **Signature not found** → update the DME to latest version using winkfp, if it still does not work, open an issue.
- **Signature found more than once** → patch refused; open an issue. (Will probably never happen)

## Requirements

- Python 3.8+
- Tkinter

### For the patch to be valid
- A **full, clean read** of the DME flash (complete dump, no missing/zeroed regions from a bad read).
- A car that is a **native 8HP swap** into an E-series that never had 8HP from the factory (E8x / E9x / E6x). This patch is only meaningful in that scenario.
- After patching you **must correct the checksum** with an MSV80/MSD8x checksum correction tool. **This tool does not correct checksums.**
- A recovery method (bench / BDM) available before flashing, in case anything goes sideways.


## Usage

```
python msv80_gear_patch.py
```

## Community & Support

For questions, help, and general discussion regarding native 8HP swaps, join the Discord community:
[Join the 8HP Native Swap Discord](https://discord.gg/Pj3zseKPWk)

**All information regarding the native 8HP swap is completely free. If you know someone being charged money just for this information, tell them to join the Discord instead.**

## Credits

- **Aleksandre (NDH Automotive)** - for developing the native 8HP swap and for testing this patch
- **TheFiztec** - for creating the original MSD81 patch, which served as the foundation and starting point for this project.

## Disclaimer

This tool modifies engine control unit firmware. Flashing modified firmware carries risk, up to rendering the ECU inoperable. Use only on hardware you own or are authorized to modify; always keep an unmodified backup of the original read; correct checksums before flashing; have a recovery method available. You are solely responsible for any use. Provided as-is, without warranty of any kind.

## License

[MIT](LICENSE)
