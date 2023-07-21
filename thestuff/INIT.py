import struct

wmt_INVALID    = 0x00
wmt_PATCH      = 0x01
wmt_TEST       = 0x02
wmt_WAKEUP     = 0x03
wmt_HIF        = 0x04
wmt_STRAP_CONF = 0x05
wmt_FUNC_CTRL  = 0x06
wmt_RESET      = 0x07
wmt_INT        = 0x08

#======== Init BTIF ========#

'''
# query stp
print(cs_sendcmd(4, wmt_HIF, b'\x04'))

# set stp
print(cs_sendcmd(4, wmt_HIF, b'\x03\xdf\x0e\x68\x01'))

# btif full mode switch
# --- Probably enables the CRC&Checksum&Whatnot --- #

# query stp
print(cs_sendcmd(4, wmt_HIF, b'\x04'))
'''

#======== Poweron DLM =========#

cs_sendcmd(4, wmt_INT, struct.pack('<IIII', 0x01000101, 0x80100060, 0x00000000, 0x00000F00))
cs_sendcmd(4, wmt_INT, struct.pack('<IIII', 0x01000101, 0x80100060, 0x00000000, 0x000000F0))
cs_sendcmd(4, wmt_INT, struct.pack('<IIII', 0x01000101, 0x80100060, 0x00000000, 0x00000008))

#======== Donwload patch !! =========#

#
# Set MCUCLK to 138.67 MHz (what an odd frequency)
#
cs_sendcmd(4, wmt_INT, struct.pack('<IIII', 0x01000101, 0x80000334, 0x00010000, 0xFFFFFFFF))
cs_sendcmd(4, wmt_INT, struct.pack('<IIII', 0x01000101, 0x8000010C, 0x00844D59, 0xFFFFFFFF))

for patch in ['FW/ROMv2_lm_patch_1_1_hdr.bin', 'FW/ROMv2_lm_patch_1_0_hdr.bin']:
    with open(patch, 'rb') as patchf:
        hdr = patchf.read(28)
        dat = patchf.read()

        addr = (hdr[25] << 8) | (hdr[26] << 16) | (hdr[27] << 24)

        cs_sendcmd(4, wmt_INT, struct.pack('<IIII', 0x01000101, 0x02090240, 0x00000000, 0xFFFFFFFF))
        cs_sendcmd(4, wmt_INT, struct.pack('<IIII', 0x01000101, 0x020904C8, addr,       0xFFFFFFFF))

        fragsz = 1000
        frags = (len(dat) + fragsz - 1) // fragsz

        for frag in range(frags):
            fragd = dat[:fragsz]
            dat = dat[fragsz:]

            if frag == 0: 
                fragd = b'\x01' + fragd
            elif frag == (frags - 1):
                fragd = b'\x03' + fragd
            else:
                fragd = b'\x02' + fragd

            print(' '.join(['%02x' % b for b in fragd[:16]]))
            print(cs_sendcmd(4, wmt_PATCH, fragd))
            print()

            frag += 1

    print(cs_sendcmd(4, wmt_RESET, b'\x04'))

#========= RF Calibartion ===========#


#============= FM Strap =============#

