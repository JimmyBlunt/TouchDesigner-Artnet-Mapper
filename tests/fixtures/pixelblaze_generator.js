// Pixelblaze mapper generator: preserved, never evaluated by Python.
function mapPixels(pixelCount) {
  var map = [];
  for (var i = 0; i < pixelCount; i++) {
    map.push([i / pixelCount, 0.5, 0.5]);
  }
  return map;
}
