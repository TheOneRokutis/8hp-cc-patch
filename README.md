# E-Series 8HP Cruise Control Gear Patch
 
A small GUI tool that patches BMW **MSV80 / MSD80 / MSD81** DME firmware images to restore cruise control in **8th gear** after a native ZF **8HP** automatic swap into an E-series chassis.
 
*(Currently tested on MSV80. MSD80 / MSD81 should work too — they share the same gear-decode bytes — but are unconfirmed.)*
 
## What it does
 
When an 8-speed ZF 8HP is natively swapped into an E-series BMW that never came with one from the factory (E8x / E9x / E6x), the engine DME's gearbox-data decode has no entry for 8th gear. The transmission reports 8th on the bus as gear code `0xC`, but the DME only recognizes the codes for gears 1–7 (plus reverse and neutral) and treats anything else as **neutral**. So the moment the car shifts into 8th, the DME thinks it's in neutral and cruise control drops out.
 
This tool patches the gear-decode routine so code `0xC` decodes correctly to 8th gear. Cruise then stays engaged in 8th. Gears 1–7, reverse, and neutral are unchanged.
 
## Supported ECUs
 
- **MSV80** — tested, works
- **MSD80** — should work (untested)
- **MSD81** — should work (untested)

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
 
## Safety logic
 
- **Signature not found** → update the DME to the latest version with WinKFP and read it again. If it still isn't found, open an issue.
- **Signature found more than once** → patch refused; open an issue. (Should never happen in practice.)
## DSC coding
 
The gear patch fixes the engine side. On some cars you also need a DSC coding change — symptoms are:
 
- when you try to engage cruise in 8th you still get **5E62 – DSC: Transmission control interface**, and/or
- the DSC logs **D378**, a PT-CAN timeout on the reverse-gear-status message.
Read the DSC with NCS Expert, load its `FSW_PSW.trc` in NCS Dummy, and change:
 
- **`C0F_GETRIEBE` → `wert_00`** — switches the DSC's gearbox logic to manual. This clears the 5E62 interface error and lets cruise hold in 8th.
- **`C0F_AFH_HSA` → `wert_00`** — disables Hill Start Assist. HSA is the only DSC function that needs the reverse-gear-status message, which a native 8HP swap never broadcasts, so it times out as D378. Turning HSA off removes the dependency and the fault disappears.
Code the DSC, clear the fault memory, and both errors should be gone. The only thing you lose is Hill Start Assist (the brief brake-hold when pulling away on an incline); ABS, traction, and the rest of DSC are unaffected.
 
## Requirements
 
- Python 3.8+
- Tkinter

**For the patch to be valid:**
 
- A **full, clean read** of the DME flash (complete dump, no missing or zeroed regions from a bad read).
- A car that is a **native 8HP swap** into an E-series that never had 8HP from the factory (E8x / E9x / E6x). This patch is only meaningful in that scenario.
- After patching you **must correct the checksum** with an MSV80 / MSD8x checksum correction tool. **This tool does not correct checksums.**
- A recovery method (bench / BDM) available before flashing, in case anything goes sideways.
## Usage
 
```
1. Install Python 3.8+
2. Run gear.table.patcher.py
3. Select your full DME read — the tool finds the signature and writes a patched copy
4. Correct the checksum, then flash
```
 
## Community & Support
 
For questions, help, and general discussion regarding native 8HP swaps, join the Discord community:
[Join the 8HP Native Swap Discord](https://discord.gg/Pj3zseKPWk)
 
**All information regarding the native 8HP swap is completely free. If you know someone being charged money just for this information, tell them to join the Discord instead.**
 
## Credits
 
- **Aleksandre (NDH Automotive)** — for developing the native 8HP swap and for testing this patch
- **TheFiztec** — for creating the original MSD81 patch, which served as the foundation and starting point for this project
## Disclaimer
 
This tool modifies engine control unit firmware. Flashing modified firmware carries risk, up to rendering the ECU inoperable. Use only on hardware you own or are authorized to modify; always keep an unmodified backup of the original read; correct checksums before flashing; have a recovery method available. You are solely responsible for any use. Provided as-is, without warranty of any kind.
 
## License
 
[GNU GPLv3](LICENSE)
