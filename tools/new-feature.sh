#!/usr/bin/env bash
# Start a feature the way docs/00-how-we-work.md describes: its own worktree,
# its own branch, its own module behind its own flag, and the places where its
# context will live.
#
#   tools/new-feature.sh fx3d "A 3D effect for the panel"
#
# Creates:
#   /Users/apple/AnimatedPixelClock-<name>      worktree on branch feat/<name>
#   src/<name>/{<name>.h,<name>.cpp,README.md}  module skeleton behind <NAME>_ENABLED
#   tools/flag_matrix.py                        one row: the flag on, and off
#   docs/NN-<name>.md (this repository)         the stub a later session reads
#
# It does not build, flash, commit or push: it puts you in a place where the
# first commit is yours.
set -euo pipefail

REPO=/Users/apple/AnimatedPixelClock
BASE_BRANCH=feature/market-climate-audio
KB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

name="${1:-}"
title="${2:-}"
if [[ -z "$name" ]]; then
  echo "usage: tools/new-feature.sh <name> [\"one line about it\"]" >&2
  exit 2
fi
if [[ ! "$name" =~ ^[a-z][a-z0-9_]*$ ]]; then
  echo "new-feature: the name is a C identifier in lower case, e.g. fx3d or flight_board" >&2
  exit 2
fi

tree="/Users/apple/AnimatedPixelClock-$name"
flag="$(echo "$name" | tr '[:lower:]' '[:upper:]')_ENABLED"
[[ -e "$tree" ]] && { echo "new-feature: $tree exists already" >&2; exit 1; }

git -C "$REPO" worktree add -b "feat/$name" "$tree" "$BASE_BRANCH"

mkdir -p "$tree/src/$name"
cat > "$tree/src/$name/$name.h" <<EOF
#pragma once
// ${title:-$name}. Behind -D$flag; a build without the flag must not change.
// See src/$name/README.md.

#if defined($flag)

void ${name}Begin();      // setup(), after the display is up
void ${name}Tick();       // every render tick, cheap when it has nothing to draw

#endif // $flag
EOF

cat > "$tree/src/$name/$name.cpp" <<EOF
#include "$name.h"

#if defined($flag)

#include <Arduino.h>

void ${name}Begin() {
}

void ${name}Tick() {
}

#endif // $flag
EOF

cat > "$tree/src/$name/README.md" <<EOF
# $name

${title:-One line about what this module is.}

**Flag:** \`-D$flag\`. Off by default; a build without it must be byte-identical
to the branch it started from.

## What it does

## What it costs

Internal heap, flash, and the time it takes in a render tick - measured, not
estimated.

## What it refuses to do

## Sources

Every figure here names where it came from.
EOF

python3 - "$tree" "$name" "$flag" <<'PY'
import pathlib, sys
tree, name, flag = sys.argv[1:4]
p = pathlib.Path(tree) / "tools/flag_matrix.py"
if not p.exists():
    sys.exit(0)
s = p.read_text()
anchor = '    ("nothing enabled",        "", True),\n'
row = f'    ("{name} only",{" " * max(1, 22 - len(name))}"-D{flag}", True),\n'
if anchor in s and row not in s:
    p.write_text(s.replace(anchor, anchor + row, 1))
    print(f"flag_matrix.py: added a row for {flag}")
PY

next_num=$(ls "$KB/docs" | grep -Eo '^[0-9]+' | sort -n | tail -1)
next_num=$(printf '%02d' $((10#$next_num + 1)))
doc="$KB/docs/$next_num-$name.md"
cat > "$doc" <<EOF
# $next_num. ${title:-$name}

**Worktree:** \`/Users/apple/AnimatedPixelClock-$name\` - **branch:** \`feat/$name\` -
**flag:** \`-D$flag\`. Started $(date +%Y-%m-%d). See [00](00-how-we-work.md).

## What it is for

The owner's words, not a paraphrase.

## Constraints it has to live inside

Internal heap, the render tick and the task watchdog, flash on the 4MB board,
and whatever else applies. Each with a source.

## Decisions taken

| Date | Decision | Why |
|---|---|---|

## Open questions

## Status

Nothing built yet.
EOF

echo
echo "worktree : $tree   (branch feat/$name)"
echo "module   : src/$name/   behind $flag"
echo "notes    : ${doc#$KB/}"
echo
echo "Next: open a session on that worktree with"
echo "  read docs/$next_num-$name.md and HANDOFF.md, branch feat/$name, worktree -$name"
