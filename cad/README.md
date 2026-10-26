# Mechanical CAD

- `rev_i_baseline/` contains the editable Rev I STEP masters, input and positioned
  parts, assembly, STL exports, and Python CAD generation/checking source.
- `current_print_files/` contains 19 reference STL pieces, with the corrected B12
  switch body substituted for the original B12.

The original Rev I B12 remains in the baseline for design provenance. Use the
corrected B12 from the current collection when consulting the current design.
See [mechanical assembly notes](../docs/MECHANICAL_AND_PRINTING.md).

The website carries an earlier HOLD CAD revision specifically for its 3D model.
Its geometry is separate from the current robot printing references. CAD source
does not establish completed physical assembly or fit.

CAD build scripts can contain workstation-specific executable locations. Read
and adapt them in a working copy before running. Original test/validation result
records and historical print batches are not included in this public repository.
