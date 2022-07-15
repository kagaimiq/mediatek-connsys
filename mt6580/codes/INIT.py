
'''
WMT (type 4):
  00 = Invalid
  01 = Patch
  02 = Test
  03 = Wakeup
  04 = HIF "Host InterFace"
  05 = Strap conf
  06 = Func ctrl
  07 = Reset
  08 = Int
'''

#======== Init BTIF ========#

'''
# query stp
print(cs_sendcmd(4, 0x04, b'\x04'))

# set stp
print(cs_sendcmd(4, 0x04, b'\x03\xdf\x0e\x68\x01'))

# btif full mode switch
# --- Probably enables the CRC&Checksum&Whatnot --- #

# query stp
print(cs_sendcmd(4, 0x04, b'\x04'))
'''

#======== Poweron DLM =========#

cs_sendcmd(4, 0x08, b'\x01\x01\x00\x01' + b'\x60\x00\x10\x80' + b'\x00\x00\x00\x00' + b'\x00\x0f\x00\x00')
cs_sendcmd(4, 0x08, b'\x01\x01\x00\x01' + b'\x60\x00\x10\x80' + b'\x00\x00\x00\x00' + b'\xf0\x00\x00\x00')
cs_sendcmd(4, 0x08, b'\x01\x01\x00\x01' + b'\x60\x00\x10\x80' + b'\x00\x00\x00\x00' + b'\x08\x00\x00\x00')

#======== Donwload patch !! =========#



#--- Set MCUCLK to 138.67 MHz ---#
cs_sendcmd(4, 0x08, b'\x01\x01\x00\x01' + b'\x34\x03\x00\x80' + b'\x00\x00\x01\x00' + b'\xff\xff\xff\xff')
cs_sendcmd(4, 0x08, b'\x01\x01\x00\x01' + b'\x0c\x01\x00\x80' + b'\x59\x4d\x84\x00' + b'\xff\xff\xff\xff')

for patch in ['FW/ROMv2_lm_patch_1_1_hdr.bin', 'FW/ROMv2_lm_patch_1_0_hdr.bin']:
    with open(patch, 'rb') as patchf:
        hdr = patchf.read(28)
        dat = patchf.read()

        addr = (hdr[25] << 8) | (hdr[26] << 16) | (hdr[27] << 24)

        cs_sendcmd(4, 0x08, b'\x01\x01\x00\x01' + b'\x40\x02\x09\x02' + b'\x00\x00\x00\x00' + b'\xff\xff\xff\xff')
        cs_sendcmd(4, 0x08, b'\x01\x01\x00\x01' + b'\xc8\x04\x09\x02' + addr.to_bytes(4, 'little') + b'\xff\xff\xff\xff')

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
            print(cs_sendcmd(4, 0x01, fragd))
            print()

            frag += 1

    print(cs_sendcmd(4, 0x07, b'\x04'))

#========= RF Calibartion ===========#


#============= FM Strap =============#

