# The three measurements that settled the broker argument

These are not tests. They are the protocols that produced the numbers in
`docs/32-net-broker.md`, kept because a number without its method is an
opinion, and because every one of them was written after a wrong conclusion
had already been drawn without it.

| script | question it answers | why it is shaped that way |
|---|---|---|
| `paired.py` | how much contiguous internal RAM does a build actually have | Reboots the panel and samples at a fixed offset with nothing driven. **Single readings of `largestHeapBlock` are worthless**: it does not move at all within one boot and varies between boots in 1,024-byte steps, one in seven landing 6 KB low. Two days of "before and after" here were built on that mistake. Run it seven times, compare distributions, never two samples. |
| `visit.py` | does the portal work, and does the panel survive it | One burst of six concurrent requests - what a browser does when it opens the page - then the idle polling a left-open tab does. This is the script that reproduced the owner's complaint on demand: `fix/panel-tonight` served every asset perfectly and then stopped answering altogether. |
| `stress.py` | what happens under deliberate abuse | 250 requests, ten at a time, for a hundred seconds, while a board fetches through the broker. Harsher than any browser. Its answer is not "does it stay fast" but "does it stay on the network". |

**All three perturb what they measure** - the panel stands aside for a web
client for 1,500 ms (`net_turns.h`), so the act of polling suppresses exactly
the background fetches being studied. That is acceptable only because both
builds get the same perturbation. Never compare a reading from one of these
against a reading taken any other way.

Host defaults to `192.168.4.62`; edit `HOST` at the top.
