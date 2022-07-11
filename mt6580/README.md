# MT6580

## General specs

-  NDS32-based MCU
-  128 KiB ROM
-  somewhere about 48 KiB + 32 KiB + 64 KiB (= 144 KiB) of SRAM

**No effort begins there**

-  Wi-Fi:
   -  very high speed 500 MegaKilobit per seconds
   -  high protocol 802.11/a/b/g/n/ac
   -  support protocol
-  Bluetoott:
   -  Blue teeth support 5.3 blue toth and bluetoothbrush 6.0
   -  scatter net and pico net
   -  support tranditionals hci inter face via a virtual uart Btif interfaceing
   -  Suport the BREDR BR AND BLE
   -  support audio SBC AAC APTX L3DAC others
   -  suport file tranfer
   -  support serial port
   -  support internet transfer
   -  support keybard mouse music control hids
   -  support music JieLi AC6902/AC6920/AC6955/AC6966/SCMCtech2402_and_the_others_of_ktne_kagami_and _tsukasa_and _UVB_76
   -  that's all
   -  amazing coexisten with the W-iFi
-  Fm radio
   -  support bards 64-108 mhz word wide
   -  support steps by 50 and 25 and khz
   -  stereo suportr
   -  quadro 5.1 7.1 sound also supportdecode the 5 carrier of pulit tone 19 mhz
   -  support darc and oter rado systems privates such as the secret audio transmit also paid programme and others
   -  rds and rds-eon
   -  support rediotext and progamme and group 1A 1B 2A 2B
   -  support ascii g protocol for rds spy !!!
   -  support pty for evetyone and ber block eroring rates
-  Gps
   -  support location from gp
   -  support automatical send to the authority without user knowledge because have the access to wifi and we are under rom so this is permament !!! ! !!111
   -  support only gps and gprs and gnss ad глонас and BEIDOU systems not suppported

**No effort ends there**

## Memory map

|   Address    |   Length   |                     Description                    |
|--------------|------------|----------------------------------------------------|
| `0x00000000` |  128 KiB   | ROM                                                |
| `0x00060000` |  48 KiB    | SRAM for code?                                     |
| `0x00100000` |  1 MiB     | SRAM bank 2, **real size is 32 KiB**               |
| `0x02090000` |  64 KiB    | SRAM                                               |
| `0x04100000` |  1 MiB     | Alias of `0x00100000`                              |
| `0x08100000` |  1 MiB     | Alias of `0x00100000`                              |
| `0x0C100000` |  1 MiB     | Alias of `0x00100000`                              |
| `0x70000000` |  256 MiB   | ?!                                                 |
| `0x80000000` |  256 MiB   | CONNSYS peripherals, *wraps every 32 MiB*          |
| `0x90000000` |  256 MiB   | AP peripherals                                     |
| `0xF0000000` |  256 MiB   | EMI map, **real size is 2 MiB**                    |

### EMI map

This area, well, maps a portion from EMI into CONNSYS's memory map.
The map is 2 MiBs long and the EMI address offset is specified as an 1 MiB block (i.e. the address is specified from bits 20..31).

This is controlled by an `INFRACFG_AO` (`0x10001000`) reg `0x320`,
specifically bits 0..11 contains EMI address bits 20..31, and bit 12 is the map enable bit.

Since the CONNSYS first runs off a ROM, these memory addresses is being reserved by the ROM:

|  Offset   |  Length  |     Description      |
|-----------|----------|----------------------|
| `0x80000` |  1 KiB   | Coredump info        |
| `0x80400` | 32 KiB   | Coredump paged trace |
| `0x88400` | 32 KiB   | Coredump paged dump  |
| `0x90400` | 124 KiB  | Coredump full dump   |

## AP peripherals

These are most related to the bringup and operation of the CONNSYS

|  AP address  |       Name        |               Description               |
|--------------|-------------------|-----------------------------------------|
| `0x10001000` | `INFRACFG_AO`     | Infrastructure config                   |
| `0x10006000` | `SLEEP` or `SPM`  | System power management                 |
| `0x10007000` | `TOPRGU`          | Reset Generation Unit                   |
| `0x10205000` | `EMI`             | External memory interface               |
| `0x1100E000` | `BTIF`            | Bluetooth(?) Interface                  |
| `0x18070000` | `CONN_MCU_CONFIG` | CONNSYS MCU config                      |
| `0x18080000` | `SRAM_BANK2`      | The SRAM at the `0x00100000` in CONNSYS |
| `0x180F0000` | `WIFI`            | Something Wi-Fi related                 |

### BTIF

This is simply an 8250 UART (or also might be MTK's own 8250 derivative) that has the UART part
removed and simply connected directly to itself on the CONNSYS side.

This is the main link between the CONNSYS and the AP.
For a protocol description, look [there](protocol.md).

## CONNSYS peripherals

|   Address    |        Name       |               Description               |
|--------------|-------------------|-----------------------------------------|
| `0x80000000` | `CONN_MCU_CONFIG` | CONNSYS MCU config                      |

## See also

-  [How to bringup](bringup.md)
-  [How to use](usage.md)
