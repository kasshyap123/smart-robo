#pragma once
#include <math.h>

// Compare both wire slots without relying on the module's L/R setting.
// A nonzero level alone does not establish a valid acoustic response.
inline double sampleLevel(const int32_t *words, size_t count, size_t offset,
                          int32_t &smallest, int32_t &largest) {
  double total = 0;
  double squares = 0;
  size_t used = 0;
  smallest = 8388607;
  largest = -8388608;
  for (size_t i = offset; i < count; i += 2) {
    const int32_t value = words[i] >> 8;
    if (value < smallest) smallest = value;
    if (value > largest) largest = value;
    total += value;
    squares += double(value) * value;
    ++used;
  }
  if (!used) {
    smallest = largest = 0;
    return -120.0;
  }
  const double mean = total / used;
  const double rms = sqrt(fmax(0.0, squares / used - mean * mean));
  return 20.0 * log10(fmax(rms / 8388608.0, 0.000001));
}
