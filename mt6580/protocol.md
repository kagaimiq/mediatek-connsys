# The protocol

**This talks about the protocol via an UART connection.**

## Packet layer

The data is transferred between the AP and CONNSYS using the packet-based protocol.

The packet can have up to 4095 bytes (12 bit size) of payload with an CRC16 checksum,
and 16 "types" (or directed to 16 "tasks" -- this seems to be more precise).

The same packet structure is used both on requests (AP -> CONNSYS) and responses (CONNSYS -> AP).

### Packet structure

```
[Header][Header checksum:8][Data][Data CRC16:16]
 |    |
 |    |
 |     \__________________
 |                        \
[1SsssAaa TtttLlll llllllll]

 * Ssss         = txseq <?>
 * Aaa          = txack <?>
 * Tttt         = type/task
 * Llllllllllll = length
```

Every packet starts with the MSB set to 1,
the next byte after it seems to always has the MSB set to 0 since the maximum number of types/tasks is 7.

There is also an syncronization byte `0x7f`...

The txseq/txack doesn't seem to do anything (at least in basic transfers),
but they might do when transferring data bigger than 4095 bytes.

The Header checksum/Data CRC16 is not set/checked unless the STP is configured to do so (via an WMT task)

### Type/Task IDs

| ID |     Name       |                    Description                    |
|----|----------------|---------------------------------------------------|
| 0  | BT             | Bluetooth (sending wrong packets leads to crash)  |
| 1  | FM             | FM Radio (sending wrong packets leads to crash)   |
| 2  | GPS            | The Global Positioning System                     |
| 3  | WIFI           | Wi-Fi                                             |
| 4  | WMT            | Wireless Management Task                          |
| 5  | STP            |                                                   |
| 6  | INFO/LPBK/TEST | info, loopback and test                           |
| 7  | ANT/COREDUMP   | antenna? and coredump                             |

## Command layer

`[Token:8][Command:8][Data length:16][Data]`

The token in requests seems to be always `0x01`,
while in responses they are `0x02` for WMT task and `0x04` for FM task.

The command responses has the same command id as the request.

The data can be theirotically up to 65535 bytes long, but the packet layer could do up to 4095 bytes.

**more short notes to follow?**
