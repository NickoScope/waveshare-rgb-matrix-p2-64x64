#!/bin/bash
# Re-fetch the vendor drawings and verify they are the ones we checked against.
set -euo pipefail
cd "$(dirname "$0")/../reference-drawings/controller"
BASE="https://raw.githubusercontent.com/waveshareteam/ESP32-S3-RGB-Matrix/main/hardware"
curl -sL -o ESP32-S3-RGB-Matrix-Schematics.pdf "$BASE/schematics/ESP32-S3-RGB-Matrix-Schematics.pdf"
curl -sL -o ESP32-S3-RGB-Matrix-2D.pdf         "$BASE/dimensions/ESP32-S3-RGB-Matrix-2D.pdf"
shasum -a 256 *.pdf
cat <<'EOF'
Expected as of 2026-09-10:
  cbe74d347afbc5dd...  ESP32-S3-RGB-Matrix-Schematics.pdf
  2cb249fe4275bab7...  ESP32-S3-RGB-Matrix-2D.pdf
A changed hash means Waveshare revised the board - re-verify docs/02.
EOF
