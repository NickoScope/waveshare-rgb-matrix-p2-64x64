#!/bin/bash
# usage: bench-rpi.sh LABEL MAXSEC [extra engine flags...]
# One run: fresh flash (the chip is made from the image), nice -n 10, bash `time`, VmHWM polled from /proc.
set -u
B=/tmp/twin-bench; L=$1; S=$2; shift 2
cd $B || exit 1
rm -f $B/flash.bin
HWM=$B/logs/$L.hwm; : > $HWM
TIMEFORMAT='TIME real=%R user=%U sys=%S'
{ time (
  nice -n 10 $B/esp32sim --board panel --boot rom --rom $B/esp32s3_rev0_rom.elf \
    --flash-image $B/AnimatedPixelClock-waveshare-v2.7.4-Full.bin --flash-mb 32 --flash-id c28039 --psram-mb 16 \
    --efuse-regs $B/efuse-opi.txt --console usb --no-dump --flash-persist $B/flash.bin \
    --mac 02:54:57:49:4E:02 --cpi 2.45 --max-seconds $S "$@" > $B/logs/$L.out 2> $B/logs/$L.err &
  pid=$!
  while kill -0 $pid 2>/dev/null; do grep VmHWM /proc/$pid/status >> $HWM 2>/dev/null; sleep 0.2; done
  wait $pid; echo "EXIT=$?" >> $B/logs/$L.err
) ; } 2> $B/logs/$L.time
echo "$L $(cat $B/logs/$L.time) $(tail -1 $HWM) $(grep -o 'stop:.*' $B/logs/$L.err | cut -c1-200) $(tail -1 $B/logs/$L.err)"
