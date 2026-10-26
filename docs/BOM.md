# Parts, tools and purchase status

The complete recorded inventory is in [hardware/bom.csv](../hardware/bom.csv).
Quantities are historical inventory reports, not a fresh physical stock count.
Suggested purchases are labelled separately from confirmed owned components.

The microphone is **INMP441 I2S**. Calling it an I2C module leads to wrong wiring.
One speaker is marked **4 ohm 3 W**; the second has no readable rating. Its matching
appearance/purchase does not independently verify the same impedance.

## Perfboard

The suggested blank is 75 x 45 mm with 2.54 mm hole spacing. Lay out the circuit
before cutting; a roughly 40 x 25 mm board leaves room for wires inside the
50 x 30 x 16 mm interface-board installation envelope on B14. This allowance
includes components, connectors and lead bends. Individual perfboard pads are
not internally joined like breadboard groups. Build separate GND, 3V3 and 5V nets.
Do not route motor current through small signal distribution wiring.

## Soldering handoff already discussed

- Four motors: two flexible wires each; owner chose approximately 20 cm leads,
  subject to actual routing and a small service loop.
- Buck: four labelled IN+/IN-/OUT+/OUT- leads, approximately 20 cm.
- PAM8403: five power/input leads, approximately 20 cm; separate speaker pairs
  approximately 15 cm, kept short and together.
- Microphone: all six labelled connections, with final connector depth checked
  against its head seat; bulky headers were not guaranteed by the CAD.
- Switches: approximately 20 cm leads if fitted; verify the route first.

These are routing allowances, not measured final harness lengths. Label both
ends. Motor screw terminals should clamp suitable stranded copper/ferrules;
avoid solder-tinned ends under screw clamps. Returned components were reported
on 23 October; this is not a request to resolder all of them again.

## Supplier references already used

- [Small perfboard](https://probots.co.in/perforated-board-small.html)
- [Multistrand wire](https://probots.co.in/multi-stranded-hookup-wire.html)
- [Straight headers](https://probots.co.in/40-x-1-male-header-pins-straight.html)
- [3 mm heat shrink](https://probots.co.in/3-mm-heat-shrink-tube.html)
- [Wire stripper/cutter](https://probots.co.in/wire-stripper.html)
- [Mini nipper](https://probots.co.in/mini-nipper.html)
- [Desoldering pump](https://probots.co.in/desoldering-pump.html)

These are historical product links; price, availability and suitability have not
been rechecked for this export. No new purchase or hardware substitution is made.
