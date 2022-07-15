############################################
#     MediaTek MT6580 FM Radio Bringup     #
############################################
import base64

## Commands ##

def fm_sendcmd(cmd, dat):
    return cs_sendcmd(1, cmd, dat)[1]

def fm_cmd_read(addr):
    return int.from_bytes(fm_sendcmd(0x03, bytes([addr])), 'little')

def fm_cmd_write(addr, val):
    return int.from_bytes(fm_sendcmd(0x04, bytes([addr, val&0xff, (val>>8)&0xff])), 'little')

def fm_cmd_enable(bops=b''):
    return fm_sendcmd(0x07, bops)

def fm_cmd_tune(bops=b''):
    return fm_sendcmd(0x09, bops)

def fm_cmd_rampdown(bops=b''):
    return fm_sendcmd(0x0e, bops)

def fm_cmd_dummy11(bops=b''):
    return fm_sendcmd(0x11, bops)

def fm_cmd_dlpatch(chunks, chunk, dat):
    return fm_sendcmd(0x12, bytes([chunks, chunk]) + dat)

def fm_cmd_dlcoeff(chunks, chunk, dat):
    return fm_sendcmd(0x13, bytes([chunks, chunk]) + dat)

def fm_cmd_hostread(addr):
    return int.from_bytes(fm_sendcmd(0x18, addr.to_bytes(4, 'little')), 'little')

def fm_cmd_hostwrite(addr, val):
    return fm_sendcmd(0x19, addr.to_bytes(4, 'little') + int.to_bytes(val & 0xffffffff, 4, 'little'))

## Basic Operations ##

def fm_bop_gen(bop, data):
    return bytes([0x80 + bop, len(data)]) + data

def fm_bop_write(addr, val):
    return fm_bop_gen(0x00, bytes([addr, val&0xff, (val>>8)&0xff]))

def fm_bop_udelay(us):
    return fm_bop_gen(0x01, us.to_bytes(4, 'little'))

def fm_bop_rduntil(addr, mask, val):
    return fm_bop_gen(0x02, bytes([addr, mask&0xff, (mask>>8)&0xff, val&0xff, (val>>8)&0xff]))

def fm_bop_modify(addr, mask, val):
    return fm_bop_gen(0x03, bytes([addr, mask&0xff, (mask>>8)&0xff, val&0xff, (val>>8)&0xff]))

def fm_bop_topwrite(addr, val):
    return fm_bop_gen(0x05, b'\x04' + addr.to_bytes(2, 'little') + val.to_bytes(4, 'little'))

#################################################################

## FM regs ##
FM_STH2D                    = 0x2D
FM_MAIN_MCLKDESENSE         = 0x38  # maybe 0x68?
FM_STH39                    = 0x39
FM_MAIN_CG1_CTRL            = 0x60
FM_MAIN_CG2_CTRL            = 0x61
FM_MAIN_HWVER               = 0x62
FM_MAIN_CTRL                = 0x63
FM_STH64                    = 0x64
FM_CHANNEL_SET              = 0x65
FM_MAIN_CFG1                = 0x66
FM_MAIN_CFG2                = 0x67
FM_MAIN_INTR                = 0x69
FM_MAIN_INTRMASK            = 0x6A
FM_MAIN_EXTINTRMASK         = 0x6B
FM_RSSI_IND                 = 0x6C
FM_RSSI_TH                  = 0x6D
FM_MAIN_RESET               = 0x6E
FM_MAIN_CHANDETSTAT         = 0x6F
FM_RDS_CFG0                 = 0x80
FM_RDS_INFO                 = 0x81
FM_RDS_DATA_REG             = 0x82
FM_RDS_GOODBK_CNT           = 0x83  # or FM_DAC_CON1?
FM_RDS_BADBK_CNT            = 0x84  # or FM_DAC_CON2?
FM_RDS_PWDI                 = 0x85
FM_RDS_PWDQ                 = 0x86  # or FM_FT_CON0? 
FM_RDS_FIFO_STATUS0         = 0x87
FM_FT_CON9                  = 0x8F
FM_DSP_PATCH_CTRL           = 0x90  # or FM_I2S_CON0?
FM_DSP_PATCH_OFFSET         = 0x91
FM_DSP_PATCH_DATA           = 0x92
FM_DSP_MEM_CTRL4            = 0x93
FM_I2S_CON0                 = 0x9B
FM_STH9C                    = 0x9C # maybe I2S_CON1?
FM_ADDR_PAMD                = 0xB4
FM_RDS_BDGRP_ABD_CTRL       = 0xB6
FM_RDS_POINTER              = 0xF0

'''
FM_MAIN_CG1_CTRL:
    b4~b6 = osc freq [0:26MHz|1:19MHz|2:24MHz|3:38.4MHz|4:40MHz|5:52MHz]

FM_MAIN_CG2_CTRL:
    b12 = deemphasis [0:50us|1:75us]
    b7 = output [0:lineout|1:i2s]
    b4 = antenna [0:long|1:short]

FM_MAIN_CTRL:
    b0 = tune
    b1 = seek
    b2 = scan
    b3 = cqi read
    b4 = rds mask
    b5 = mute
    b6 = rds brst
    b8 = ramp down

FM_CHANNEL_SET:
    b12~b15 = channel parameter
    b0~b9 = channel (64-115.2 MHz, 50khz step)

FM_MAIN_INTR:
    b0 = stc done
    b1 = iqcal done
    b2 = desense hit
    b3 = chnl chg
    b4 = sw intr
    b5 = rds

FM_RSSI_IND:
    b12 = stereo flag
    b0~b9 = rssi

FM_I2S_CON0:
    b0 = enable
    b1 = format [0:eiaj|1:i2s]
    b2 = word length [0:16bit|1:32bit]
    b3 = i2s source

STH_9C:
    b0 = mute right/left channel
    b1 = mute left/right channel

'''

#################################################################

#-------- Enable PMIC TLDO --------#
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
#---------------------------------#

#-------- Powerup clock on -------#
# turn on topclk
bops = fm_bop_topwrite(0x0A10, 0xffffffff)

# enable MTCMOS
bops += fm_bop_topwrite(0x0060, 0x00000030)
bops += fm_bop_topwrite(0x0060, 0x00000005)
bops += fm_bop_udelay(10)
bops += fm_bop_topwrite(0x0060, 0x00000045)

# enable digital OSC
bops += fm_bop_write(FM_MAIN_CG1_CTRL, 0x00000001)
# set OSC clock out to FM
bops += fm_bop_write(FM_MAIN_CG1_CTRL, 0x00000003)
# enable DSP auto clock gate
bops += fm_bop_write(FM_MAIN_CG1_CTRL, 0x00000007)

# deemphasis
bops += fm_bop_modify(FM_MAIN_CG2_CTRL, ~(1<<12), (0<<12))  # 0 = 50us, 1 = 75us

fm_cmd_enable(bops)
#---------------------------------#

print('Hardware ver -> %04x' % fm_cmd_read(FM_MAIN_HWVER))

#-------- Get DSP ROM Version -------#
fm_cmd_write(FM_DSP_PATCH_CTRL, 0x000e)
fm_cmd_write(FM_DSP_PATCH_DATA, 0x0000)
fm_cmd_write(FM_DSP_PATCH_CTRL, 0x0040)
fm_cmd_write(FM_DSP_PATCH_CTRL, 0x0000)
# dsp rom code ver req enable
fm_cmd_dummy11(fm_bop_modify(FM_MAIN_CG2_CTRL, ~(1<<15), (1<<15)))
# release asip rst
fm_cmd_dummy11(fm_bop_modify(FM_MAIN_CG2_CTRL, ~(1<<1), (1<<1)))
# en asip power
fm_cmd_dummy11(fm_bop_modify(FM_MAIN_CG2_CTRL, ~(1<<0), 0))
# wait dsp code ver ready
sleep_ms(100)
print('Ready>%04x' % fm_cmd_read(FM_RDS_BADBK_CNT))
print('Version>%04x' % fm_cmd_read(FM_RDS_GOODBK_CNT))
# dsp rom code ver req dis
fm_cmd_dummy11(fm_bop_modify(FM_MAIN_CG2_CTRL, ~(1<<15), 0))
# reset asip
fm_cmd_dummy11(fm_bop_modify(FM_MAIN_CG2_CTRL, ~(1<<1), 0))
#---------------------------------#

##--------> download patch <---------##
fm_patch_data = base64.b64decode(
'ACD/IQy8DkAAjsi9DUAAjjy9DEAAjgCOAI4AjgCOAI4AjriOILyYICG8HgAAvIoJ' +
'AkMjvBkgAI5y+yS86AMAjgK8AEAAjgC8AQmCQyO8GSAAjnL7AI4CvABAAI4gvKQg' +
'AI4Q+gCzCgkGjyK8CgkjvKQgAI5y+wC8AgkAvAwJwkMjvBkgAI5y+yS86AMAjgK8' +
'AEAAjgC8BAniQyO8GSAAjnL7JLzoAwCOArwAQACOALwFCQJAI7wZIACOcvskvOgD' +
'AI4CvABAAI4AvAcJ4kMjvBkgAI5y+yS86AMAjgK8AEAAjgC8CQnCQyO8GSAAjnL7' +
'JLzoAwCOArwAQACOALwKCSC8kCAhvAABEvoC6VEIhGnVHzePAI4DjQCOILyQICG8' +
'AIAQ+gEIACb1jyC8kCAhvJEgT3EQuiK8bWYocDK7+HEyuwOixAQCCASixQSAaTM7' +
'NPsivEUlHqPGBDL7DI8BJuJPDY8CJiK8gAMJj4MmAkAFjwK80kAEjSK8/wMCo8ME' +
'AqPCBACixQQBosQEDyYCjwCOA4wBNEk0AEDVzwCjxQTAjv7pAaPEBCC8kSAhvG1m' +
'EfshvBILEfvAjiG8RSUR+wLpIrwAgJBw1R8hvADAArxqCYBBIbwDBAK8SAmgQSG8' +
'SCcCvEgJAEEhvLYBArxICWBIIbwtgQK8SAkAjgCOAI7VzwCOwI7+6QCOAAAAAAAA' +
'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
'AAAAAAAAAAAAAAAAAAAAAAAAAAA='
)

segsz = 512
nsegs = (len(fm_patch_data) + segsz - 1) // segsz

for i in range(nsegs):
    fm_cmd_dlpatch(nsegs, i, fm_patch_data[:segsz])
    fm_patch_data = fm_patch_data[segsz:]

##--------> download coeff <---------##
fm_coeff_data = base64.b64decode(
'AAAfAgAAiAkQQLkCFkB0ACNAKgk9QAQJSkAFCVdABwlkQHQAcUAAAAAEBgCrKgYB' +
'BgEGAVcAVwBXABERWRIBAFoAmw7/D/8PIAABAAEAzQzg/9j//wCs/7z/AP8gAEgA' +
'UABQAA4AAgAAcAAI+P8IACsA9v/4//7/AwAIAA0ADwAUABkAAAAACIBlAAAAAP9/' +
'MABwAPX+6P4DAAAAAACAAYABBgCAwADwYAaA2gAAAQABAOT/6P+AADQAAQD//wEA' +
'/v/AOkAzwCvAB8AF4AMAAAAAEAXeFBMmEybeFBAFAAAAAABACAALAAAQACDY/r3/' +
'9P+oDSVADgbf/yH/If/Y/tj+2P4AAFAAUAAB/xQFOg3p/w4AXvc2EXvsPA2a+kf8' +
'i/VVENo92j1VEIv1R/wXGyo2FxvaZ5inpv2++G7z1PBo8xj7KAApACgAKQAoACkA' +
'KAAoACkAKAApACgAKAApACgAKQAoACkAKAAscajx1PmOIMJLgPKA8sJLjiDU+ajx' +
'LHEAAAACAAGAAEAAIAAQAAgABAACAAEA3AJuAbcAhwKfAxMDVQN2A7sBAQLcA+4B' +
'9wCnAo8DGwP8APwAmAGYAWgBUAO0AbQBiQAsAFgALAAABAAAAwDt+tD+4glqFu8b' +
'ahbiCdD+7foVJ+tY61gVJ4//Jf+h/hL+iv0m/QT9Q/0A/k7/OQG5A7sGGgqlDR8R' +
'SxTsFswYxxkCAAQAs0fFuoULBQCaKQQACgBgBs0MAwAGAP9/gACAACwAIAAnAE//' +
'sf0u/mUE8Q4eFoITgwl7AGb9ff7i/zEADQAAQCT9OlHsyhQ1xq7cAgBAte+ubquN' +
'VXJSkUsQKzNFJUQT9QkmBakCYAG2AF4AMQAAAAAAAAAYJbsfohRqDbkIrAWwA2YC' +
'jwEEAakAbgBHAAEAZAGaAQEAAgD/fwGAOH8AAAAAAAAAAP9/AAAAAQD1ABwAWgAB' +
'AP8A+AAgAE8AAQD+APwAIgBHAAAA/QABACMAPQD/AP4ABQAiADYA/wD/AAkAIQAv' +
'AAAAAQAMAB8AKQAAAAMADgAdACUAAAAAAAAAAP9/AAAAAAAAAAAAAAQACAAIAxID' +
'zAF8ARkAAAAAAAAAAAAA4EAYgMju/wAAAECAJoH/AOAAUIDQs/8A+ABFgNPi/wAA' +
'AAAAAAAAgA+A28AhzP8AAIDGQAUjAMAzwNoAWdr/wAqA30AZ9///f8NQ+kcmQCw5' +
'9TJqLXooEyQnIKgcihnDFkkUFBIdEF0OzQxoCysKEAkTCBUAFAACAIAASCgfBQEA' +
'EABA/ED8lP2A/YD+gP58/n/+9AIBAIAAgAAAEIAAABAAEAAEmlmaGWYGIQAAIAAg' +
'ACDk/zIACgAAIABAAAgABAwABQAMANX/AQB1Ax4AqwoAIKsqQAAFAB4AAQDAAAsA' +
'BQABAAgABACeAE8AAgAEAEgBSAH/fygAEAAEAH5A3kAAAAAA'
)

segsz = 512
nsegs = (len(fm_coeff_data) + segsz - 1) // segsz

for i in range(nsegs):
    fm_cmd_dlcoeff(nsegs, i, fm_coeff_data[:segsz])
    fm_coeff_data = fm_coeff_data[segsz:]

fm_cmd_write(FM_DSP_PATCH_DATA, 0x0000)
fm_cmd_write(FM_DSP_PATCH_CTRL, 0x0040)
fm_cmd_write(FM_DSP_PATCH_CTRL, 0x0000)

#------ Powerup digital init -----#
bops = fm_bop_write(FM_MAIN_INTRMASK, 0x0021)
bops += fm_bop_write(FM_MAIN_EXTINTRMASK, 0x0021)
bops += fm_bop_write(FM_MAIN_CG1_CTRL, 0x000F)
bops += fm_bop_modify(FM_MAIN_CG2_CTRL, ~(1<<1), (1<<1))
bops += fm_bop_modify(FM_MAIN_CG2_CTRL, ~(1<<0), 0)
bops += fm_bop_udelay(100000)
bops += fm_bop_rduntil(FM_STH64, 0x001F, 0x0002)
bops += fm_bop_write(FM_MAIN_CG1_CTRL, 0x0007)
bops += fm_bop_write(FM_STH2D, 0x01FA)
bops += fm_bop_write(FM_MAIN_CG1_CTRL, 0x000F)
fm_cmd_enable(bops)
#---------------------------------#

# Audio out I2S TX mode
fm_cmd_write(FM_I2S_CON0, 0x0003) # src=0, wlen=16 bit, std=i2s, enable

#################################################################

def fm_rampdown():
    fm_cmd_write(FM_MAIN_CG1_CTRL, 0x0007)
    fm_cmd_write(FM_MAIN_CG1_CTRL, 0x000f)

    bops = fm_bop_modify(FM_MAIN_CTRL, 0xfff0, 0x0000) # clear dsp state
    bops += fm_bop_modify(FM_MAIN_CTRL, 0xffff, (1<<8)) # set dsp ramp down state
    bops += fm_bop_rduntil(FM_MAIN_INTR, (1<<0), (1<<0)) # wait for 'stc done' int
    bops += fm_bop_modify(FM_MAIN_CTRL, ~(1<<8), 0) # clear dsp ramp down state
    bops += fm_bop_modify(FM_MAIN_INTR, 0xffff, (1<<0)) # clear 'stc done' int
    fm_cmd_rampdown(bops)

def fm_tune(freq):
    fm_cmd_write(FM_MAIN_CG1_CTRL, 0x0007)

    if   freq <= 72.9:  fm_cmd_write(FM_STH39, 0xD002)
    elif freq <= 84.1:  fm_cmd_write(FM_STH39, 0xCE02)
    elif freq <= 98.15: fm_cmd_write(FM_STH39, 0xCC02)
    elif freq <= 98.3:  fm_cmd_write(FM_STH39, 0xCA02)
    elif freq <= 99.4:  fm_cmd_write(FM_STH39, 0xCC02)
    else:               fm_cmd_write(FM_STH39, 0xCA02)

    fm_cmd_write(FM_MAIN_INTRMASK, 0x0021)
    fm_cmd_write(FM_MAIN_EXTINTRMASK, 0x0021)
    fm_cmd_write(FM_MAIN_CG1_CTRL, 0x000F)

    fm_cmd_dummy11(fm_bop_modify(FM_CHANNEL_SET, ~0x3ff, int((freq - 64) / 0.05)))
    fm_cmd_dummy11(fm_bop_modify(FM_CHANNEL_SET, ~(0xf<<12), (0x0<<12)))

    bops = b''
    bops += fm_bop_write(FM_MAIN_INTRMASK, 0x0000)
    bops += fm_bop_write(FM_MAIN_EXTINTRMASK, 0x0000)
    bops += fm_bop_modify(FM_MAIN_CTRL, ~(7<<0), (1<<0)) # execute tune action
    bops += fm_bop_rduntil(FM_MAIN_INTR, (1<<0), (1<<0)) # wait until 'stc done' int
    bops += fm_bop_modify(FM_MAIN_INTR, 0xffff, (1<<0))  # clear 'stc done' int
    fm_cmd_tune(bops)

while True:
    inp = input('MTK-FM> ').split(' ')
    if len(inp) < 1: continue

    if inp[0] == 'exit':
        break

    elif inp[0] == 'tune':
        fm_rampdown()
        fm_tune(float(inp[1]))

#################################################################

# clear interrupts
ints = fm_cmd_read(FM_MAIN_INTR)
if ints & 1: fm_cmd_write(FM_MAIN_INTR, ints)

fm_rampdown()

#---------- Power down -----------#
# set audio output i2s tx mode
bops = fm_bop_modify(FM_I2S_CON0, ~0x7, 0)

# disable hw clock control
bops += fm_bop_write(FM_MAIN_CG1_CTRL, 0x330f)

# reset asip
bops += fm_bop_write(FM_MAIN_CG2_CTRL, 0x0001)

# digital core + digital rgf reset
bops += fm_bop_modify(FM_MAIN_RESET, ~0x7, 0x0)
bops += fm_bop_modify(FM_MAIN_RESET, ~0x7, 0x0)
bops += fm_bop_modify(FM_MAIN_RESET, ~0x7, 0x0)
bops += fm_bop_modify(FM_MAIN_RESET, ~0x7, 0x0)

# disable all clock
bops += fm_bop_write(FM_MAIN_CG1_CTRL, 0x0000)

# reset rgfrf
bops += fm_bop_write(FM_MAIN_CG1_CTRL, 0x4000)
bops += fm_bop_write(FM_MAIN_CG1_CTRL, 0x0000)

# mtcmos power off
bops += fm_bop_write(FM_MAIN_CG1_CTRL, 0x0005)
bops += fm_bop_write(FM_MAIN_CG1_CTRL, 0x0015)
#---------------------------------#

#-------- Disable PMIC TLDO --------#
## >>>>> 26 clock mannual off ##
fm_cmd_hostwrite(0x80000224, fm_cmd_hostread(0x80000224) & ~(1<<22))
fm_cmd_hostwrite(0x80000224, fm_cmd_hostread(0x80000224) & ~(1<<16))
fm_cmd_hostwrite(0x80000224, fm_cmd_hostread(0x80000224) & ~(1<<6))
fm_cmd_hostwrite(0x80000224, fm_cmd_hostread(0x80000224) & ~(1<<0))
## >>>>> rx_det_out gating on ##
fm_cmd_hostwrite(0x80102090, fm_cmd_hostread(0x80102090) & ~(1<<16))
## >>>>> adc_dq gating on ##
fm_cmd_hostwrite(0x80102090, fm_cmd_hostread(0x80102090) & ~(1<<15))
## >>>>> adc_id gating on ##
fm_cmd_hostwrite(0x80102090, fm_cmd_hostread(0x80102090) & ~(1<<14))
## >>>>> adc_ck gating on ##
fm_cmd_hostwrite(0x80102090, fm_cmd_hostread(0x80102090) & ~(1<<7))
## >>>>> dig_ck gating on ##
fm_cmd_hostwrite(0x80102090, fm_cmd_hostread(0x80102090) & ~(1<<6))
#---------------------------------#

##################################################################################################

"""
while True:
    
    rssi = fm_cmd_read(FM_RSSI_IND)
    stereo = bool(rssi & 0x1000)
    rssi &= 0x3ff

    pamd = fm_cmd_read(FM_ADDR_PAMD)
    if pamd > 511: pamd -= 1024
    pamd = pamd / 16 * 6

    print('RSSI = %d%s, PAMD = %d dB' % (rssi, " <<STEREO>>" if stereo else "", pamd))
    

    ln = input('MTK> ').split(' ')
    if len(ln) < 1: continue

    if ln[0] == 'exit':
        break

    elif ln[0] == 'tune':
        fm_rampdown()
        fm_tune(float(ln[1]))
"""

#fm_cmd_write(FM_RDS_CFG0, 6)  # buf_start_th
#fm_cmd_dummy11(fm_bop_modify(FM_MAIN_CTRL, ~(1<<4), (1<<4)))

"""
while True:
    '''
    print("good:%5d bad:%5d" % (fm_cmd_read(FM_RDS_GOODBK_CNT), fm_cmd_read(FM_RDS_BADBK_CNT)))

    fifostat = fm_cmd_read(FM_RDS_FIFO_STATUS0)
    print("fifo: %04x" % fifostat)

    fifodiff = fifostat & 0x7f

    if fifodiff >= 4:
        for i in range(4):
            print("info: %04x" % fm_cmd_read(FM_RDS_INFO))
            print("data: %04x" % fm_cmd_read(FM_RDS_DATA_REG))

        print("I:%04x Q:%04x" % (fm_cmd_read(FM_RDS_PWDI), fm_cmd_read(FM_RDS_PWDQ)))
        print("pointer: %04x" % fm_cmd_read(FM_RDS_POINTER))

    print()
    '''

    fifostat = fm_cmd_read(FM_RDS_FIFO_STATUS0)

    if (fifostat & 0x7f) >= 4:
        rdsblk = [-1,-1,-1,-1]

        for i in range(4):
            info = fm_cmd_read(FM_RDS_INFO)
            data = fm_cmd_read(FM_RDS_DATA_REG)

            if info & 1:
                rdsblk[i] = data

        print(' '.join('----' if b < 0 else '%04x' % b for b in rdsblk))

    '''
    fifostat = fm_cmd_read(FM_RDS_FIFO_STATUS0)
    print("fifo stat %04x" % fifostat)

    if (fifostat & 0x7f) >= 4:
        print("\x1b[1;1H")

        for i in range(4):
            info = fm_cmd_read(FM_RDS_INFO)
            data = fm_cmd_read(FM_RDS_DATA_REG)

            print("%d: %04x %04x" % (i, info, data))

        print()
    '''

    sleep_ms(10)
"""

"""
import socket

with socket.socket() as sock:
    sock.bind(('', 8751))
    sock.listen(1)

    while True:
        csock, caddr = sock.accept()
        print(csock, caddr)

        while True:
            fifostat = fm_cmd_read(FM_RDS_FIFO_STATUS0)

            if (fifostat & 0x7f) >= 4:
                rdsblk = [-1,-1,-1,-1]

                for i in range(4):
                    info = fm_cmd_read(FM_RDS_INFO)
                    data = fm_cmd_read(FM_RDS_DATA_REG)

                    if info & 1: rdsblk[i] = data

                composed = 'G:\r\n' + ''.join('----' if b < 0 else '%04X' % b for b in rdsblk) + '\r\n\r\n'
                csock.send(bytes(composed, 'ascii'))

            sleep_ms(10)

        csock.close()
"""

