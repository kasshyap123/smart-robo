# Power and motors — unresolved design items

There is no released full-power schematic. Battery holder topology, cell current
capability, correct charger/protection, fuse and motor voltage/current are still
unconfirmed. Neither the holder, LM2596 nor ESP32 charges or protects lithium cells.

If the two conventional 4.2 V maximum cells are in series, the pack would be 7.4 V
nominal and 8.4 V fully charged; verify the actual cells and wiring first. A
single-cell TP4056 is not a two-series-cell pack charger. Do not infer allowable
motor voltage from the L298N's losses. A regulator output must be measured before
connecting electronics; labels on the LM2596 identify IN+/IN-/OUT+/OUT-.

## First motor test preparation

Keep all power disconnected while attaching one motor to OUT1/OUT2. Lift the wheels
for the eventual bench test. Identify the delivered module's regulator and ENA/ENB
jumpers before powering it; the enable inputs must remain disabled during reset.
The proposed final controls are in the pin-map CSV and have not been tested.

The two left motors may eventually share channel A, and the two right motors
channel B, **only after** combined startup/stall current and heat are checked.
The L298 has two bridges; it is not four independent motor channels. Its 2 A DC
per-channel value is a device limit, not a guarantee that a small breakout board
can run continuously at that current. Do not stall the motors by hand as a test.

An earlier design proposal used external regulated logic 5 V with the module's
5V-EN regulator link removed, and removed ENA/ENB links for PWM. This requires
confirming the actual module wiring; it is not a universal instruction for every
board. Never join regulator outputs. Do not connect external 5 V to a USB-powered
ESP32 until its USB/external-power isolation is established.

## Distribution and routing

Plan separate protected motor and electronics branches with a common return
connection, adequately rated wires/connectors and an accessible motor-isolation
switch. Keep switching motor wiring away from microphone and analogue audio.
Do not use small Dupont jumpers for motor supply current. B14 reserves mechanical
room for an interface board, protection, optional regulator and fuse, but mechanical
space does not select their electrical ratings or establish a charging circuit.

Reference: [ST L298 datasheet](https://www.st.com/resource/en/datasheet/l298.pdf).
