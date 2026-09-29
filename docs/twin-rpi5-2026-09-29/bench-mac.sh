#!/bin/bash
# usage: bench-mac.sh EXE LABEL MAXSEC [extra engine flags...]
set -u
D=/private/tmp/claude-502/-Users-apple-LED-MATRIX-APOLLO/b713b961-29c5-417c-977c-81dddbb4b228/scratchpad/rpi5/mac
E=$1; L=$2; S=$3; shift 3
mkdir -p $D/logs; cd $D; rm -f $D/flash.bin
/usr/bin/time -l $E --board panel --boot rom --rom $HOME/twin/rom/esp32s3_rev0_rom.elf \
  --flash-image /Users/apple/AnimatedPixelClock-twin/docs/firmware/latest/AnimatedPixelClock-waveshare-v2.7.4-Full.bin \
  --flash-mb 32 --flash-id c28039 --psram-mb 16 --efuse-regs $HOME/twin/efuse-opi.txt --console usb --no-dump \
  --flash-persist $D/flash.bin --mac 02:54:57:49:4E:02 --cpi 2.45 --max-seconds $S "$@" > $D/logs/$L.out 2> $D/logs/$L.err
echo "EXIT=$?" >> $D/logs/$L.err
echo "$L $(grep -E '^ +[0-9.]+ real' $D/logs/$L.err | xargs) | maxrss $(awk '/maximum resident set size/{printf "%.1f MB", $1/1048576}' $D/logs/$L.err) | $(grep -o 'stop:.*' $D/logs/$L.err | cut -c1-190)"
