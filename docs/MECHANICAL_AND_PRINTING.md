# Mechanical assembly and print status

The latest complete baseline is [Rev I](../cad/README.md),
dated 12 October. A separate 17 October B12 switch-panel correction supersedes
only its original B12. The baseline STEP assembly is preserved unchanged and
therefore still contains the old B12; do not assume it incorporates the correction.

`cad/current_print_files/` contains 19 reference pieces (15 unique designs), with
corrected B12 substituted. It is a file collection, **not a new print order**.
The B01 speaker-fit coupon in the four-file batch is not the full B01 shell.

| Design | Purpose | Quantity | Last known physical/print status |
|---|---|---:|---|
| B01 | Front body shell | 1 | Full shell held pending speaker/coupon trial |
| B02 | Rear body shell | 1 | Sent for printing in six-part batch |
| B03 | Front deck and fixed neck | 1 | Sent for printing |
| B04 | Vented rear lid / driver hood | 1 | Sent for printing |
| B05 | Rear electronics tray | 1 | Sent for printing |
| B06 | ESP32 carrier | 1 | Received; connected plugs must clear B05 slots |
| B07 | Battery cradle | 1 | Received; holder seats; strap/chassis retention pending |
| B08 | Head shell | 1 | Sent for printing |
| B09 | Rear head/buzzer cover | 1 | Received |
| B10 | Front visor / sensors | 1 | Sent for printing |
| B10R | OLED carrier | 1 | Received; owner reports OLED fit |
| B11 | Speaker rear retainer | 2 | One received; second held pending coupon fit |
| B12 | Rear switch panel | 1 | Corrected version received; latch fit unconfirmed |
| B13 | Chassis mounting feet | 4 | Received; retain fitting prints |
| B14 | Power/interface tray | 1 | Received |

All six sent parts are black, at 100% millimetre scale, with the established
material/profile and part-specific support instructions in the batch manifest.
Do not mix old HOLD revisions into current printing.

## Mounting facts and limits

The chassis reference is 255 x 148 x 3 mm. B13 feet retain through suitable
existing chassis openings using ties; the CAD does not reproduce an exact
surveyed acrylic hole pattern. Do not claim every acrylic bolt hole aligns or
drill based only on the paper template. Paper-fit checks were owner-reported passes.

B06 mounts above B05: its pin-row slots pass the female connectors and wires
downward. It need not sit flat on a table with jumpers attached. Row allowance:
4 x 38 x 20 mm, plus 6 mm lower lead-turn space; bulky multiway plugs are not covered.

B14 interface-board envelope is 50 x 30 x 16 mm including connections, protection
42 x 18 x 12, optional regulator 42 x 21 x 22, and fuse 26 x 13 x 13. Insulating
supports are nominally 4 mm. Purchased boards must actually fit these budgets.

The fixed neck has an 18 mm bore and an 8 mm checked harness corridor. Keep wires
away from tyres, cones, heatsinks and nut pockets. No servo mounts are included.
The current continuous-rotation SG90s cannot command an absolute scan angle.

Follow the baseline handoff for assembly and fastener candidates: 50 M3 and four
M2, excluding purchased chassis hardware and optional board mounting. M3 x 20
is not a universal substitute. Feet nominally use M3 x 12; full body/driver tool,
washer and actual print clearances still require dry assembly.

For B05 service: remove B04, B14 and relevant leads/fasteners, lift 35 mm, slide
14 mm rearward to retract the lower arms, then lift free. Do not force a straight
lift with the front deck in place.

## Verification scope

Baseline records: 171 printed-part pairs, 893 hardware/connector/routing checks,
82 fastener axes, nine sampled service paths, 15 closed print meshes and a
19-solid STEP round trip passed. The 22 October B02 review additionally checked
18 neighbours, 47 envelopes and 16 fastener axes. These are computational checks,
not guarantees of physical fit, temperature, strength or final cable motion.

Keep all fitting prints. Finish speaker/coupon, corrected switch clip fit and
connected carrier/tray trials before deciding any local adjustment or replacement.
