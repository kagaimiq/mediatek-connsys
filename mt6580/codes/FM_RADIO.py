
def fm_sendcmd(cmd, dat):
    return cs_sendcmd(1, cmd, dat)[1]

def fm_cmd_read(addr):
    return int.from_bytes(fm_sendcmd(0x03, bytes([addr&0xff])), 'little')

def fm_cmd_write(addr, val):
    return int.from_bytes(fm_sendcmd(0x04, bytes([addr&0xff, val&0xff, (val>>8)&0xff])), 'little')

def fm_cmd_enable(bops=b''):
    return fm_sendcmd(0x07, bops)

def fm_cmd_tune(bops=b''):
    return fm_sendcmd(0x09, bops)

def fm_cmd_dummy11(bops=b''):
    return fm_sendcmd(0x11, bops)

def fm_cmd_dlpatch(cnt, i, dat):
    return fm_sendcmd(0x12, bytes([cnt&0xff, i&0xff]) + dat)

def fm_cmd_dlcoeff(cnt, i, dat):
    return fm_sendcmd(0x13, bytes([cnt&0xff, i&0xff]) + dat)

def fm_cmd_hostread(addr):
    return int.from_bytes(fm_sendcmd(0x18, int.to_bytes(addr & 0xffffffff, 4, 'little')), 'little')

def fm_cmd_hostwrite(addr, val):
    return fm_sendcmd(0x19, int.to_bytes(addr & 0xffffffff, 4, 'little') + int.to_bytes(val & 0xffffffff, 4, 'little'))

########

def fm_bop_gen(bop, data):
    return bytes([0x80 + bop, len(data)]) + data

def fm_bop_write(addr, val):
    return fm_bop_gen(0x00, bytes([addr&0xff, val&0xff, (val>>8)&0xff]))

def fm_bop_udelay(us):
    return fm_bop_gen(0x01, us.to_bytes(4, 'little'))

def fm_bop_rduntil(addr, mask, val):
    return fm_bop_gen(0x02, bytes([addr&0xff, mask&0xff, (mask>>8)&0xff, val&0xff, (val>>8)&0xff]))

def fm_bop_modify(addr, mask, val):
    return fm_bop_gen(0x03, bytes([addr&0xff, mask&0xff, (mask>>8)&0xff, val&0xff, (val>>8)&0xff]))

def fm_bop_topwrite(addr, val):
    return fm_bop_gen(0x05, b'\x04' + addr.to_bytes(2, 'little') + val.to_bytes(4, 'little'))

#################################################################

## >>>>> 26 clock mannual on ##
fm_cmd_hostwrite(0x80000224, fm_cmd_hostread(0x80000224) | (1<<0))
fm_cmd_hostwrite(0x80000224, fm_cmd_hostread(0x80000224) | (1<<6))
fm_cmd_hostwrite(0x80000224, fm_cmd_hostread(0x80000224) | (1<<16))
fm_cmd_hostwrite(0x80000224, fm_cmd_hostread(0x80000224) | (1<<22))
## >>>>> rx_det_out gating off ##
fm_cmd_hostwrite(0x80102090, fm_cmd_hostread(0x80102090) | (1<<16))
## >>>>> adc_dq gating off ##
fm_cmd_hostwrite(0x80102090, fm_cmd_hostread(0x80102090) | (1<<15))
## >>>>> adc_id gating off ##
fm_cmd_hostwrite(0x80102090, fm_cmd_hostread(0x80102090) | (1<<14))
## >>>>> adc_ck gating off ##
fm_cmd_hostwrite(0x80102090, fm_cmd_hostread(0x80102090) | (1<<7))
## >>>>> dig_ck gating off ##
fm_cmd_hostwrite(0x80102090, fm_cmd_hostread(0x80102090) | (1<<6))

#################################################################

# turn on topclk
bops = fm_bop_topwrite(0x0A10, 0xffffffff)
# enable MtcMos
bops += fm_bop_topwrite(0x0060, 0x00000030)
bops += fm_bop_topwrite(0x0060, 0x00000005)
bops += fm_bop_udelay(10)
bops += fm_bop_topwrite(0x0060, 0x00000045)
# enable Digitel OSC
bops += fm_bop_write(0x60, 0x00000001)
# set OSC clock out to FM
bops += fm_bop_write(0x60, 0x00000003)
# enable DSP auto cock gate
bops += fm_bop_write(0x60, 0x00000007)
# deemphesis settings
bops += fm_bop_modify(0x61, ~(1<<12), (0<<12))

fm_cmd_enable(bops)

print('MT%04x' % fm_cmd_read(0x62))

##--->get the rom version
fm_cmd_write(0x90, 0x000e)
fm_cmd_write(0x90, 0x0000)
fm_cmd_write(0x90, 0x0040)
fm_cmd_write(0x90, 0x0000)
# dsp rom code ver req enable
fm_cmd_dummy11(fm_bop_modify(0x61, ~(1<<15), (1<<15)))
# release asip rst
fm_cmd_dummy11(fm_bop_modify(0x61, ~(1<<1), (1<<1)))
# en asip power
fm_cmd_dummy11(fm_bop_modify(0x61, ~(1<<0), 0))
# wait dsp code ver ready
sleep_ms(100)
print('X>%04x' % fm_cmd_read(0x84))
print('Y>%04x' % fm_cmd_read(0x83))
# dsp rom code ver req dis
fm_cmd_dummy11(fm_bop_modify(0x61, ~(1<<15), 0))
# reset asip
fm_cmd_dummy11(fm_bop_modify(0x61, ~(1<<1), 0))

##---> download patch
with open('FW/mt6580/mt6580_fm_v1_patch.bin', 'rb') as pf:
    pdat = pf.read()

    segsz = 512
    nsegs = (len(pdat) + segsz - 1) // segsz

    for i in range(nsegs):
        fm_cmd_dlpatch(nsegs, i, pdat[:segsz])
        pdat = pdat[segsz:]

##---> download coeff
with open('FW/mt6580/mt6580_fm_v1_coeff.bin', 'rb') as pf:
    pdat = pf.read()

    segsz = 512
    nsegs = (len(pdat) + segsz - 1) // segsz

    for i in range(nsegs):
        fm_cmd_dlcoeff(nsegs, i, pdat[:segsz])
        pdat = pdat[segsz:]

##---> ???
fm_cmd_write(0x92, 0x0000)
fm_cmd_write(0x90, 0x0040)
fm_cmd_write(0x90, 0x0000)

##---> DIIGTAL INIT
bops = fm_bop_write(0x6A, 0x0021)
bops += fm_bop_write(0x6B, 0x0021)
bops += fm_bop_write(0x60, 0x000F)
bops += fm_bop_modify(0x61, ~(1<<1), (1<<1))
bops += fm_bop_modify(0x61, ~(1<<0), 0)
bops += fm_bop_udelay(100000)
bops += fm_bop_rduntil(0x64, 0x001F, 0x0002)
bops += fm_bop_write(0x60, 0x0007)
bops += fm_bop_write(0x2D, 0x01FA)
bops += fm_bop_write(0x60, 0x000F)
fm_cmd_enable(bops)

##---> Audio out I2S TX mode
fm_cmd_write(0x9B, 0x0003)

##############

print('%04x' % fm_cmd_read(0x9C))

fm_cmd_write(0x60, 0x0007)

fm_cmd_write(0x39, 0xCA02)

fm_cmd_write(0x6A, 0x0021)
fm_cmd_write(0x6B, 0x0021)
fm_cmd_write(0x60, 0x000F)

#--> Tune to 106.4 [RETRO FM]
fm_cmd_dummy11(fm_bop_modify(0x65, 0xfc00, (10640 - 6400) * 2 // 10))
fm_cmd_dummy11(fm_bop_modify(0x65, 0x0fff, 0x0000))

bops = fm_bop_write(0x6A, 0x0000)
bops += fm_bop_write(0x6B, 0x0000)
bops += fm_bop_modify(0x63, ~(7<<0), (1<<0))
bops += fm_bop_rduntil(0x69, (1<<0), (1<<0))
bops += fm_bop_modify(0x69, 0xffff, (1<<0))
fm_cmd_tune(bops)
