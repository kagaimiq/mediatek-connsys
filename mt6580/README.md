# MT6580

## General specs

-  NDS32-based MCU
-  128 KiB ROM
-  somewhere about 48 KiB + 32 KiB + 64 KiB (= 144 KiB) of SRAM

## Memory map

Memory map as visible by the NDS32 MCU:

| Address    | Length           | Description                 |
|------------|------------------|-----------------------------|
| 0x00000000 | 128 KiB          | ROM                         |
| 0x00060000 | 48 KiB           | SRAM for code?              |
| 0x00100000 | 1 MiB (32 KiB)   | SRAM bank 2                 |
| 0x02090000 | 64 KiB           | SRAM                        |
| 0x04100000 | 1 MiB            | Alias of 0x00100000         |
| 0x08100000 | 1 MiB            | Alias of 0x00100000         |
| 0x0C100000 | 1 MiB            | Alias of 0x00100000         |
| 0x70000000 | 256 MiB          | ?!                          |
| 0x80000000 | 256 MiB (32 MiB) | CONSYS peripherals          |
| 0x90000000 | 256 MiB          | AP peripherals              |
| 0xF0000000 | 256 MiB (2 MiB)  | EMI map                     |

### EMI map

This maps a portion of the system memory to the NDS32's memory map at address 0xF0000000.

The block is 2 MiB long, and the offset has 1 MiB granularity.

This is controlled by the `INFRACFG_AO`'s register at offset 0x320;
specifically bits 0..11 define the base address in EMI (bits 20..31), and bit 12 enables the map.

The CONSYS's ROM reserves some areas in the EMI map for the following:

| Offset  | Length   | Description          |
|---------|----------|----------------------|
| 0x80000 | 1 KiB    | Coredump info        |
| 0x80400 | 32 KiB   | Coredump paged trace |
| 0x88400 | 32 KiB   | Coredump paged dump  |
| 0x90400 | 124 KiB  | Coredump full dump   |

## AP peripherals

These are most related to the bringup and operation of the CONNSYS:

| AP address | Name              | Description                      |
|------------|-------------------|----------------------------------|
| 0x10001000 | `INFRACFG_AO`     | Infrastructure config            |
| 0x10006000 | `SLEEP` or `SPM`  | System power management          |
| 0x10007000 | `TOPRGU`          | Reset Generation Unit            |
| 0x10205000 | `EMI`             | External memory interface        |
| 0x1100E000 | `BTIF`            | Bluetooth(?) Interface           |
| 0x18070000 | `CONN_MCU_CONFIG` | CONNSYS MCU config               |
| 0x18080000 | `SRAM_BANK2`      | The SRAM at 0x00100000 in CONSYS |
| 0x180F0000 | `WIFI`            | Something Wi-Fi related          |

### BTIF

The BTIF (supposedly, BlueTooth InterFace) is basically an 8250 UART where the UART transceiver section
was replaced with a direct connection to another BTIF in the CONSYS side, so that a communication with the CONSYS
could be estabilished.

The protocol used for communication between AP and CONSYS over BTIF is described [there](protocol.md)

## CONSYS peripherals

| Address    | Name              | Description        |
|------------|-------------------|--------------------|
| 0x80000000 | `CONN_MCU_CONFIG` | CONNSYS MCU config |
