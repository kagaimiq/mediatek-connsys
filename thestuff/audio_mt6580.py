from periphery import MMIO, GPIO
from periphery import sleep_ms, sleep_us
import os, math, sys

audio = MMIO(0x11140000, 0x10000)

def reg32_read(mmap, off):
    return mmap.read32(off)

def reg32_write(mmap, off, val):
    mmap.write32(off, val)

def reg32_wsmask(mmap, off, shift, mask, val):
    mmap.write32(off, (mmap.read32(off) & ~(mask << shift)) | ((val & mask) << shift))

def reg32_rsmask(mmap, off, shift, mask):
    return mmap.read32(off) >> shift & mask

#======================

AUDIO_TOP_CON0          = 0x000
AUDIO_TOP_CON1          = 0x004
AUDIO_TOP_CON2          = 0x008
AUDIO_TOP_CON3          = 0x00C
AFE_DAC_CON0            = 0x010
AFE_DAC_CON1            = 0x014
AFE_I2S_CON             = 0x018
AFE_CONN0               = 0x020
AFE_CONN1               = 0x024
AFE_CONN2               = 0x028
AFE_CONN3               = 0x02C
AFE_CONN4               = 0x030
AFE_I2S_CON1            = 0x034
AFE_I2S_CON2            = 0x038
AFE_DL1_BASE            = 0x040
AFE_DL1_CUR             = 0x044
AFE_DL1_END             = 0x048
AFE_I2S_CON3            = 0x04C
AFE_DL2_BASE            = 0x050
AFE_DL2_CUR             = 0x054
AFE_DL2_END             = 0x058
AFE_AWB_BASE            = 0x070
AFE_AWB_END             = 0x078
AFE_AWB_CUR             = 0x07C
AFE_VUL_BASE            = 0x080
AFE_VUL_END             = 0x088
AFE_VUL_CUR             = 0x08C
AFE_MOD_DAI_BASE        = 0x330
AFE_MOD_DAI_END         = 0x338
AFE_MOD_DAI_CUR         = 0x33C
AFE_GAIN1_CON0          = 0x410
AFE_GAIN1_CON1          = 0x414
AFE_GAIN1_CON2          = 0x418
AFE_GAIN1_CON3          = 0x41C
AFE_GAIN1_CONN          = 0x420
AFE_GAIN1_CUR           = 0x424
AFE_GAIN2_CON0          = 0x428
AFE_GAIN2_CON1          = 0x42C
AFE_GAIN2_CON2          = 0x430
AFE_GAIN2_CON3          = 0x434
AFE_GAIN2_CONN          = 0x438
AFE_GAIN2_CUR           = 0x43C
AFE_GAIN2_CONN2         = 0x440
AFE_ASRC_CON0           = 0x500
AFE_ASRC_CON1           = 0x504
AFE_ASRC_CON2           = 0x508
AFE_ASRC_CON3           = 0x50C
AFE_ASRC_CON4           = 0x510
AFE_ASRC_CON5           = 0x514
AFE_ASRC_CON6           = 0x518
AFE_ASRC_CON7           = 0x51C
AFE_ASRC_CON8           = 0x520
AFE_ASRC_CON9           = 0x524
AFE_ASRC_CON10          = 0x528
AFE_ASRC_CON11          = 0x52C
AFE_ASRC_CON13          = 0x550
AFE_ASRC_CON14          = 0x554
AFE_ASRC_CON15          = 0x558
AFE_ASRC_CON16          = 0x55C
AFE_ASRC_CON17          = 0x560
AFE_ASRC_CON18          = 0x564
AFE_ASRC_CON19          = 0x568
AFE_ASRC_CON20          = 0x56C
AFE_ASRC_CON21          = 0x570

'''
    AUDIO_AFE_DAC_CON0:
      b0  = Enable AFE operation
      b1  = Enable MEMIF DL1
      b2  = Enable MEMIF DL2
      b3  = Enable MEMIF VUL
      b6  = Enable MEMIF AWB
      b7  = Enable MEMIF MOD_DAI
      b11 = Enable Modem1 PCM
      b12 = Enable Modem2 PCM
      b13 = Enable I2S1 Out DAC
      b15 = Enable I2S1 In ADC
      b17 = Enable I2S2 Out
      b18 = Enable I2S2 In
      b19 = Enable HW Gain1
      b20 = Enable HW Gain2
    
    AUDIO_AFE_DAC_CON1:
       b0~b3  = DL1 sample rate 
       b4~b7  = DL2 sample rate
       b8~b11 = I2S sample rate
      b12~b15 = AWB sample rate
      b16~b20 = VUL sample rate
      b21     = DL1 channels (stereo/mono)
      b22     = DL2 channels (stereo/mono)
      b24     = AWB channels (stereo/mono)
      b27     = VUL channels (stereo/mono)
      b30     = MOD_DAI sample rate
      b31     = MOD_DAI duplicate write [to form the stereo channel i guess]
    
    -----------------
    
    I2S1 In   => I2S2
    I2S1 Out  => I2S1
    I2S2 In   => I2S0
    I2S2 Out  => I2S3
    
    DL1/DL2/AWB/I2S/VUL sample rates:
      0 = 8000
      1 = 11025
      2 = 12000
      4 = 16000
      5 = 22050
      6 = 24000
      8 = 32000
      9 = 44100
      A = 48000
    
    MOD_DAI/VUL? smaple rates:
      0 = 8000
      1 = 16000
      2 = 32000
      3 = 48000
'''

# Main samplerate
samplerate = 10   # == 48000

##==================== AFE CONFIG =====================##
##--- I2S config ---##
reg32_wsmask(audio,AFE_DAC_CON1,  8, 15, samplerate) # I2S2[i2s0+i2s3] sample rate

# i2s0 config (For CONNSYS)
reg32_wsmask(audio,AFE_I2S_CON, 31, 1, 1)   # phase shift fix
reg32_wsmask(audio,AFE_I2S_CON, 28, 1, 0)   # in pad sel [0:connsys|1:iomux]
reg32_wsmask(audio,AFE_I2S_CON,  5, 1, 0)   # invert lrck [0:normal|1:inverted]
reg32_wsmask(audio,AFE_I2S_CON,  3, 1, 1)   # format [0:eiaj|1:i2s]
reg32_wsmask(audio,AFE_I2S_CON,  2, 1, 1)   # slave  [0:master|1:slave]
reg32_wsmask(audio,AFE_I2S_CON,  1, 1, 0)   # wlen [0:16 bit|1:32 bit]
reg32_wsmask(audio,AFE_I2S_CON,  0, 1, 1)   # enable

# sample rate conversion (NECCESSARY FOR THE I2S SLAVE MODE!!!)
### for 32000->48000hz conversion (32000 * 0x600000 / 0x400000 == 48000)
reg32_wsmask(audio,AFE_ASRC_CON13, 16, 1, 0)  # [0:stereo|1:mono]
reg32_write(audio,AFE_ASRC_CON14, 0x600000)   # delimoe
reg32_write(audio,AFE_ASRC_CON15, 0x400000)   # delitel
reg32_write(audio,AFE_ASRC_CON17, 0xcb2)

reg32_write(audio,AFE_ASRC_CON16, 0x75987)
reg32_write(audio,AFE_ASRC_CON20, 0x1b00)

reg32_wsmask(audio,AFE_ASRC_CON0, 0, 0x41, 0x41) # reset? + enable

##----- GAIN config -----##
# gain1
reg32_wsmask(audio,AFE_GAIN1_CON0, 0, 1, 0) # disable
reg32_write(audio,AFE_GAIN1_CUR, 0) # reset gain to ramp it up
reg32_write(audio,AFE_GAIN1_CON1, 0x10000) # max = 0x80000
reg32_wsmask(audio,AFE_GAIN1_CON0, 4, 15, samplerate) # sample rate
reg32_wsmask(audio,AFE_GAIN1_CON0, 8, 0xff, 0x40) # samples per step
reg32_wsmask(audio,AFE_GAIN1_CON0, 0, 1, 1) # enable

# gain2
reg32_wsmask(audio,AFE_GAIN2_CON0, 0, 1, 0) # disable
reg32_write(audio,AFE_GAIN2_CUR, 0) # reset gain to ramp it up
reg32_write(audio,AFE_GAIN2_CON1, 0x30000) # max = 0x80000
reg32_wsmask(audio,AFE_GAIN2_CON0, 4, 15, samplerate) # sample rate
reg32_wsmask(audio,AFE_GAIN2_CON0, 8, 0xff, 0x40) # samples per step
reg32_wsmask(audio,AFE_GAIN2_CON0, 0, 1, 1) # enable

##--- interconnect ---##
reg32_write(audio,AFE_CONN0, 0)
reg32_write(audio,AFE_CONN1, 0)
reg32_write(audio,AFE_CONN2, 0)
reg32_write(audio,AFE_CONN3, 0)
reg32_write(audio,AFE_CONN4, 0)
reg32_write(audio,AFE_GAIN1_CONN, 0)
reg32_write(audio,AFE_GAIN2_CONN, 0)
reg32_write(audio,AFE_GAIN2_CONN2, 0)

'''
AUDIO_AFE_CONN0:
  b0  = I2S_I.L -> I2S_O.L
  b1  = I2S_I.R -> I2S_O.L
  b3  = ADC.L -> I2S_O.L
  b4  = ADC.R -> I2S_O.L
  b5  = DL1.L -> I2S_O.L
  b6  = DL1.R -> I2S_O.L
  b7  = DL2.L -> I2S_O.L
  b8  = DL2.R -> I2S_O.L
  b9  = MD2_O -> I2S_O.L
  b16 = I2S_I.L -> I2S_O.R
  b17 = I2S_I.R -> I2S_O.R
  b19 = ADC.L -> I2S_O.R
  b20 = ADC.R -> I2S_O.R
  b21 = DL1.L -> I2S_O.R
  b22 = DL1.R -> I2S_O.R
  b23 = DL2.L -> I2S_O.R
  b24 = DL2.R -> I2S_O.R
  b25 = MD2_O -> I2S_O.R

AUDIO_AFE_CONN1:
  b16 = I2S_I.L -> DAC.L
  b17 = I2S_I.R -> DAC.L 
  b19 = ADC.L -> DAC.L
  b20 = ADC.R -> DAC.L
  b21 = DL1.L -> DAC.L
  b22 = DL1.R -> DAC.L
  b23 = DL2.L -> DAC.L
  b24 = DL2.R -> DAC.L
  b25 = MD2_O -> DAC.L

AUDIO_AFE_CONN2:
  b0  = I2S_I.L -> DAC.R
  b1  = I2S_I.R -> DAC.R
  b3  = ADC.L -> DAC.R
  b4  = ADC.R -> DAC.R
  b5  = DL1.L -> DAC.R
  b6  = DL1.R -> DAC.R
  b7  = DL2.L -> DAC.R
  b8  = DL2.R -> DAC.R
  b9  = MD2_O -> DAC.R
  b16 = I2S_I.L -> AWB.L
  b18 = ADC.L -> AWB.L
  b19 = DL1.L -> AWB.L
  b20 = DL2.L -> AWB.L
  b21 = MD2_O -> AWB.L
  b22 = I2S_I.R -> AWB.R
  b23 = ADC.R -> AWB.R
  b24 = DL1.R -> AWB.R
  b25 = DL2.R -> AWB.R
  b26 = ADC.L -> MD2_I.L
  b27 = DL1.L -> MD2_I.L
  b28 = DL2.L -> MD2_I.L
  b29 = ADC.R -> MD2_I.R
  b30 = DL1.R -> MD2_I.R
  b31 = DL2.R -> MD2_I.R

AUDIO_AFE_CONN3:
  b0  = ADC.L -> VUL.L
  b1  = DL1.L -> VUL.L
  b2  = DL2.L -> VUL.L
  b3  = ADC.R -> VUL.R
  b4  = DL1.R -> VUL.R
  b5  = DL2.R -> VUL.R
  b9  = DL1.R -> MOD_DAI
  b10 = DL2.R -> MOD_DAI
  b11 = MD2_O -> MOD_DAI
  b12 = MD1_O -> I2S_O.L
  b17 = MD1_O -> I2S_O.R
  b17 = MD1_O -> DAC.L

AUDIO_AFE_CONN4:
  b0  = MD1_O -> DAC.R
  b5  = MD1_O -> AWB.L
  b12 = MD1_O -> MOD_DAI
  b13 = ADC.L -> MD1_I.L
  b14 = DL1.L -> MD1_I.L
  b15 = DL2.L -> MD1_I.L
  b16 = ADC.R -> MD1_I.R
  b17 = DL1.R -> MD1_I.R
  b18 = DL2.R -> MD1_I.R

AUDIO_AFE_GAIN1_CONN:
  b0  = GAIN1_O.L -> I2S_O.L
  b2  = GAIN1_O.R -> I2S_O.R
  b8  = GAIN1_O.L -> DAC.L
  b10 = GAIN1_O.R -> DAC.R
  b12 = GAIN1_O.L -> AWB.L
  b13 = GAIN1_O.R -> AWB.R
  b14 = GAIN1_O.L -> GAIN1_I.R
  b15 = GAIN1_O.R -> GAIN2_I.L
  b16 = DL1.L -> GAIN1_I.L
  b17 = DL1.R -> GAIN1_I.L
  b18 = DL2.L -> GAIN1_I.L
  b19 = DL2.R -> GAIN1_I.L
  b20 = DL1.L -> GAIN1_I.R
  b21 = DL1.R -> GAIN1_I.R
  b22 = DL2.L -> GAIN1_I.R
  b23 = DL2.R -> GAIN1_I.R
  b24 = GAIN1_O.L -> MD1_I.L
  b25 = GAIN1_O.R -> MD1_I.R

AUDIO_AFE_GAIN2_CONN:
  b0  = GAIN2_O.L -> I2S_O.L
  b2  = GAIN2_O.R -> I2S_O.R
  b8  = GAIN2_O.L -> DAC.L
  b10 = GAIN2_O.R -> DAC.R
  b12 = GAIN2_O.R -> AWB.L
  b13 = GAIN2_O.L -> AWB.R
  b14 = GAIN2_O.R -> MD2_I.L
  b15 = GAIN2_O.L -> MD2_I.R
  b16 = I2S_I.L -> GAIN2_I.L
  b17 = I2S_I.R -> GAIN2_I.L
  b21 = MD2_O -> GAIN2_I.L
  b22 = I2S_I.L -> GAIN2_I.R
  b23 = I2S_I.R -> GAIN2_I.R
  b27 = MD2_O -> GAIN2_I.L
  b28 = MD1_O -> GAIN2_I.L

AUDIO_AFE_GAIN2_CONN2:
  b1  = MD1_O -> GAIN2_I.R
  b6  = GAIN2_O.L -> MD1_I.L
  b7  = GAIN2_O.R -> MD1_I.R
'''

reg32_wsmask(audio,AFE_CONN1, 19, 1, 0)  # ADC.L -> DAC.L
reg32_wsmask(audio,AFE_CONN2,  4, 1, 0)  # ADC.R -> DAC.R

reg32_wsmask(audio,AFE_CONN1, 21, 1, 1)  # DL1.L -> DAC.L
reg32_wsmask(audio,AFE_CONN2,  6, 1, 1)  # DL1.R -> DAC.R
reg32_wsmask(audio,AFE_CONN4, 14, 1, 1)  # DL1.L -> MD1_I.L
reg32_wsmask(audio,AFE_CONN4, 17, 1, 1)  # DL1.R -> MD1_I.R

reg32_wsmask(audio,AFE_CONN2, 16, 1, 1)  # I2S_I.L -> AWB.L
reg32_wsmask(audio,AFE_CONN2, 22, 1, 1)  # I2S_I.R -> AWB.R
reg32_wsmask(audio,AFE_CONN2, 18, 1, 0)  # ADC.L -> AWB.L
reg32_wsmask(audio,AFE_CONN2, 23, 1, 0)  # ADC.R -> AWB.R
reg32_wsmask(audio,AFE_CONN4,  5, 1, 1)  # MD1_O -> AWB.L

reg32_wsmask(audio,AFE_CONN3,  0, 1, 1)  # ADC.L -> VUL.L
reg32_wsmask(audio,AFE_CONN3,  3, 1, 1)  # ADC.R -> VUL.R

reg32_wsmask(audio,AFE_GAIN1_CONN, 16, 1, 1)  # DL1.L -> GAIN1_I.L
reg32_wsmask(audio,AFE_GAIN1_CONN, 21, 1, 1)  # DL1.R -> GAIN1_I.R
reg32_wsmask(audio,AFE_GAIN1_CONN, 8,  1, 0)  # GAIN1_O.L -> DAC.L
reg32_wsmask(audio,AFE_GAIN1_CONN, 10, 1, 0)  # GAIN1_O.R -> DAC.R

reg32_wsmask(audio,AFE_GAIN2_CONN, 16, 1, 1)  # I2S_I.L -> GAIN2_I.L
reg32_wsmask(audio,AFE_GAIN2_CONN, 23, 1, 1)  # I2S_I.R -> GAIN2_I.R
reg32_wsmask(audio,AFE_GAIN2_CONN, 8,  1, 1)  # GAIN2_O.L -> DAC.L
reg32_wsmask(audio,AFE_GAIN2_CONN, 10, 1, 1)  # GAIN2_O.R -> DAC.R
reg32_wsmask(audio,AFE_GAIN2_CONN, 12, 1, 0)  # GAIN2_O.L -> AWB.L
reg32_wsmask(audio,AFE_GAIN2_CONN, 13, 1, 0)  # GAIN2_O.R -> AWB.R



reg32_wsmask(audio,AFE_DAC_CON0,  1, 1, 0)
reg32_wsmask(audio,AFE_DAC_CON0,  6, 1, 0)

"""
#
# Config DL1 (downlink1 - playback)
#
reg32_write(audio,AFE_DL1_BASE, audio.base+0x1000)
reg32_write(audio,AFE_DL1_END, audio.base+0x1000+0x2000-1)
reg32_wsmask(audio,AFE_DAC_CON1,  0, 15, samplerate)
reg32_wsmask(audio,AFE_DAC_CON1, 21, 1, 0)      # stereo
reg32_wsmask(audio,AFE_DAC_CON0,  1, 1, 1)      # enable
"""

#
# Config AWB (audio writeback - capture)
#
reg32_write(audio,AFE_AWB_BASE, audio.base+0x3000)
reg32_write(audio,AFE_AWB_END, audio.base+0x3000+0x2000-1)
reg32_wsmask(audio,AFE_DAC_CON1, 12, 15, samplerate)
reg32_wsmask(audio,AFE_DAC_CON1, 24, 1, 0)     # stereo
reg32_wsmask(audio,AFE_DAC_CON0,  6, 1, 1)     # enable


#
# Start the AFE!
#
reg32_wsmask(audio,AFE_DAC_CON0, 0, 1, 1)

try:
    awb_oslice = 0
    awb_base = reg32_read(audio,AFE_AWB_BASE)
    awb_len = reg32_read(audio,AFE_AWB_END) - awb_base + 1
    awb_slen = awb_len // 2

    while True:
        awb_cur = reg32_read(audio,AFE_AWB_CUR) - awb_base
        awb_slice = awb_cur // awb_slen

        if awb_slice != awb_oslice:
            awb_cur = (awb_base - audio.base) + (awb_oslice * awb_slen)

            sys.stdout.buffer.write(audio.read(awb_cur, awb_slen))

            awb_oslice = awb_slice

        sleep_ms(5)

except Exception as e:
    print('Dies:', e, file=sys.stderr)

except KeyboardInterrupt:
    pass


reg32_wsmask(audio,AFE_DAC_CON0, 0, 1, 0)

