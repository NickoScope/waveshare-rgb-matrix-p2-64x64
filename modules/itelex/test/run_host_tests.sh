#!/usr/bin/env bash
# Host tests for the i-Telex module: the codec, the packets and two sessions
# wired back to back. No Arduino, no network, no panel.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src="$here/../src"
out="${TMPDIR:-/tmp}/itx_host_test.$$"
trap 'rm -f "$out"' EXIT
${CXX:-g++} -std=c++17 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined \
  -I"$src" "$here/host/test_itx.cpp" "$src/itx_baudot.cpp" "$src/itx_packet.cpp" \
  "$src/itx_session.cpp" -o "$out"
"$out"
