from periphery import MMIO, Serial, sleep_ms
import sys, time

topckgen        = MMIO(0x10000000, 0x1000)
infracfg_ao     = MMIO(0x10001000, 0x1000)
sleep           = MMIO(0x10006000, 0x1000)
toprgu          = MMIO(0x10007000, 0x1000)
pwrap           = MMIO(0x1000f000, 0x1000)
emi             = MMIO(0x10205000, 0x1000)
btif            = MMIO(0x1100E000, 0x100)
conn_mcu_config = MMIO(0x18070000, 0x200)
sram_bank2      = MMIO(0x18080000, 0x8000)
wifi            = MMIO(0x180F0000, 0x10000)

konata          = MMIO(0x88000000, 0x8000000)  #<< Marked as Reserved memory in Device tree

# clear all the codeDumps
konata.write(0x80000, bytes(0x400))
konata.write(0x80400, bytes(0x8000))
konata.write(0x88400, bytes(0x8000))
konata.write(0x90400, bytes(0x1f000))

## en sleep regs control ##
sleep.write32(0x000, 0x0B160001)

##################################################

def dump8(mmap, off=0, size=-1):
    if size < 0: size = mmap.size

    print("=============== %08x ~ %08x ===============" % (mmap.base+off, mmap.base+off+size-1))

    for i in range(0, size, 16):
        sstr = "%08x: " % (mmap.base+i+off)

        for j in range(0, 16):
            try:
                sstr += "%02X " % mmap.read8(i+j+off)
            except:
                sstr += "XX "

        sstr += "|"

        for j in range(0, 16):
            try:
                c = mmap.read8(i+j+off)
                if c < 0x20 or c >= 0x7f: c = ord('.')
                sstr += chr(c)
            except:
                sstr += "X"

        sstr += "|"

        print(sstr)

def dump32(mmap, off=0, size=-1):
    if size < 0: size = mmap.size

    print("=============== %08x ~ %08x ===============" % (mmap.base+off, mmap.base+off+size-1))

    for i in range(0, size, 32):
        sstr = "%08x: " % (mmap.base+i+off)

        for j in range(0, 32, 4):
            try:
                sstr += "%08X " % mmap.read32(i+j+off)
            except:
                sstr += "XXXXXXXX "

        print(sstr)

def pwrap_wait_busy():
    for i in range(1000):
        ## if it wants to have vldclr cleared then we do that! ##
        if (pwrap.read32(0xa0) >> 16) & 7 == 6:
            pwrap.write32(0xa4, 1)

        ## if it is not busy then we exit! ##
        if (pwrap.read32(0xa0) >> 16) & 7 == 0:
            return

    ## Otherwise we raise exception!! ##
    raise Exception('pwrap: timed out waiting to pwrap be not busy!')

def pwrap_read(addr):
    pwrap_wait_busy()

    ## send command to read from the addr ##
    pwrap.write32(0x9c, ((addr & 0xfffe) << 15))

    ## wait until data becomes ready ##
    for i in range(1000):
        ## if it wants to have vldclr cleared then we do that and return! ##
        if (pwrap.read32(0xa0) >> 16) & 7 == 6:
                val = pwrap.read32(0xa0) & 0xffff
                pwrap.write32(0xa4, 1)
                return val

    ## Otherwise we raise exception! ##
    raise Exception('pwrap: failed to read from addr %x!' % addr)

def pwrap_write(addr, val):
    pwrap_wait_busy()

    ## send command to write to the addr ##
    pwrap.write32(0x9c, (1<<31) | ((addr & 0xfffe) << 15) | (val & 0xffff))

def pwrap_rsmask(addr, shift, mask):
    return (pwrap_read(addr) >> shift) & mask

def pwrap_wsmask(addr, shift, mask, val):
    pwrap_write(addr, (pwrap_read(addr) & (mask << shift)) | ((val & mask) << shift))

def conn_power_ctl(en):
    if en:
        ## disable connsys (clock) sleep mode ##
        infracfg_ao.write32(0x800, infracfg_ao.read32(0x800) | (1<<10))

        ## turn on vcn18 ##
        pwrap_wsmask(0x0512,  1, 1, 0) #< don't sleep
        pwrap_wsmask(0x0512, 14, 1, 1) #< enable

        ## turn on vcn28 ##
        pwrap_wsmask(0x041E,  1, 1, 0) #< don't sleep
        pwrap_wsmask(0x041C, 12, 1, 1) #< enable

        ## turn on vcn33_bt/vcn33_wifi ##
        pwrap_wsmask(0x0416,  2, 3, 0) #< voltage = [3.3/3.4/3.5/3.6]
        pwrap_wsmask(0x0420,  1, 1, 0) #< don't sleep
        pwrap_wsmask(0x0416,  7, 1, 1) #< enable (vcn33_bt)
        pwrap_wsmask(0x0418, 12, 1, 1) #< enable (vcn33_wifi)

        sleep_ms(10)

        ## turn on conn ##
        sleep.write32(0x280, sleep.read32(0x280) | (1<<2))    #<< set pwr_on
        sleep.write32(0x280, sleep.read32(0x280) | (1<<3))    #<< set pwr_on_2nd
        sleep.write32(0x280, sleep.read32(0x280) & ~(1<<4))   #<< clr pwr_clk_dis
        sleep.write32(0x280, sleep.read32(0x280) & ~(1<<1))   #<< clr pwr_iso
        sleep.write32(0x280, sleep.read32(0x280) | (1<<0))    #<< set pwr_rst_b
        sleep.write32(0x280, sleep.read32(0x280) & ~(0x1<<8)) #<< clr sram_pdn

        ## disable AXI protection ##
        infracfg_ao.write32(0x220, infracfg_ao.read32(0x220) & ~0x310)
    else:
        ## enable AXI protection ##
        infracfg_ao.write32(0x220, infracfg_ao.read32(0x220) | 0x310)

        ## turn off conn ##
        sleep.write32(0x280, sleep.read32(0x280) | (0x1<<8))           #<< set sram_pdn
        sleep.write32(0x280, (sleep.read32(0x280) & ~(1<<0)) | (1<<1)) #<< clr pwr_rst_b, set pwr_iso
        sleep.write32(0x280, sleep.read32(0x280) | (1<<4))             #<< set pwr_clk_dis
        sleep.write32(0x280, sleep.read32(0x280) & ~((1<<2)|(1<<3)))    #<< clr pwr_on, pwr_on_2nd

        ## turn off vcn33_bt/vcn33_wifi ##
        pwrap_wsmask(0x0416,  7, 1, 0) #< disable (vcn33_bt)
        pwrap_wsmask(0x0418, 12, 1, 0) #< disable (vcn33_wifi)

        ## turn off vcn28 ##
        pwrap_wsmask(0x041C, 12, 1, 0) #< disable

        ## turn off vcn18 ##
        pwrap_wsmask(0x0512, 14, 1, 0) #< disable

        sleep_ms(10)

        ## enable connsys (clock) sleep mode ##
        infracfg_ao.write32(0x800, infracfg_ao.read32(0x800) & ~(1<<10))

conn_power_ctl(False)

#====== Disable MPU against CONN =====#
'''
grp0 = "secure os"
grp1 = "md0 rom"
grp2 = "md0 r/w+"
grp3 = "md0 share"
grp4 = "connsys code"
grp5 = "ap-connsys? share"
grp6 = "ap"
grp7 = "ap"
---the first group has higher priority than the folloeing

dev0 = AP
dev1 = MD0
dev2 = CONNSYS
dev3 = MM

0 = No protection
1 = Secure R/W only
2 = Secure R/W and nonsecure R
3 = Secure R/W and nonsecure W
4 = Secure R and nonsecure R
5 = Forbidden
6 = Secure R and nonsecure R/W
'''

# just disable everythong
emi.write32(0x1A0, 0x00000000) # group1, group0
emi.write32(0x1A8, 0x00000000) # group3, group2
emi.write32(0x1B0, 0x00000000) # group5, group4
emi.write32(0x1B8, 0x0b680000) # group7, group6

konarange = (konata.base&0x7fff0000)|(((konata.base+konata.size+0xffff)&0x7fff0000)>>16)
emi.write32(0x160, 0x00000000) # group0
emi.write32(0x168, 0x00000000) # group1
emi.write32(0x170, 0x00000000) # group2
emi.write32(0x178, 0x00000000) # group3
emi.write32(0x180, konarange)  # group4
emi.write32(0x188, 0x00000000) # group5
emi.write32(0x190, 0x00000000) # group6
emi.write32(0x198, 0x00008000) # group7

#========= Map CONNSYS memory ========#
# map into Konata Memmap
infracfg_ao.write32(0x320, (infracfg_ao.read32(0x320) & ~0x1fff) | (konata.base >> 20) | (1<<12))

#====== Assert CONNSYS CPU reset =====#
toprgu.write32(0x018, (toprgu.read32(0x018) | (0x88<<24)) | (1<<12))

#========= Power on CONNSYS ==========#
conn_power_ctl(True)
sleep_ms(10)

#============== Do something ================#
# mbist enable
conn_mcu_config.write32(0x110, conn_mcu_config.read32(0x110) | (1<<18))

#===== Release CONNSYS CPU reset =====#
toprgu.write32(0x018, (toprgu.read32(0x018) | (0x88<<24)) & ~(1<<12))

#====================================================================================#

sleep_ms(100)

topckgen.write32(0x84, (1<<12)) #<< ungate BTIF clk

btif.write8(0x04, 0) # no ints
btif.write8(0x0c, 0x03) # fake LCR <= 8n1

def btif_tstc():
    return (btif.read8(0x14) & 0x01) == 0x01

def btif_putc(c):
    btif.write8(0x00, c)
    while (btif.read8(0x14) & 0x60) != 0x60: pass

def btif_getc():
    st = time.time()
    while (btif.read8(0x14) & 0x01) != 0x01:
        if time.time() - st >= 5:
            return None

    return btif.read8(0x00)

def btif_send(dat):
    for b in dat: btif_putc(b)

def btif_recv(len):
    dat = bytearray(len)
    for i in range(len): dat[i] = btif_getc()
    return bytes(dat)



crc16table = [
    0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
    0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
    0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
    0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
    0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
    0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
    0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
    0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
    0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
    0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
    0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
    0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
    0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
    0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
    0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
    0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
    0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
    0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
    0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
    0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
    0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
    0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
    0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
    0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
    0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
    0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
    0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
    0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
    0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
    0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
    0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
    0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040
]

def cs_txframe(type, dat=b'', txseq=0, txack=0):
    hdr = (1<<23)
    hdr |= (txseq & 0xf) << 19
    hdr |= (txack & 0x7) << 16
    hdr |= (type & 0xf) << 12
    hdr |= len(dat) & 0xfff

    frame = hdr.to_bytes(3, 'big')
    frame += bytes([(frame[0]+frame[1]+frame[2]) & 0xff])
    frame += dat

    crc = 0
    for b in dat: crc = (crc >> 8) ^ crc16table[(crc ^ b) & 0xff]
    frame += int.to_bytes(crc, 2, 'little')

    #print('Sending', frame)
    btif_send((b'\x7f' * 8) + frame)

def cs_rxframe(type=None, retry=True):
    while True:
        rx = btif_getc()
        if rx & 0x80:
            head = [rx, btif_getc(), btif_getc(), btif_getc()]
            #if (head[0]+head[1]+head[2]) & 0xff != head[3]: continue

            rlen = (head[1] << 8 | head[2]) & 0xfff
            if rlen > 0:
                rdat = btif_recv(rlen)
                rcrc = int.from_bytes(btif_recv(2), 'little')
            else:
                rdat = b''
                rcrc = 0xdead

            rtype = head[1] >> 4

            #print('Received', head,rtype,rlen,rdat,rcrc)

            if (not type is None) and (not type is rtype): continue

            return {'type': rtype, 'data': rdat}

        if not retry: break

    return None




###############

'''
conn_mcu_confug
  +160 ==> PC?
'''

'''
EMI Base:
  +80000~803ff = Coredump info         [0x400]
  +80400~883ff = Coredump paged trace  [0x8000]
  +88400~903ff = Coredump paged dump   [0x8000]
  +90400~af3ff = Coredump full dump    [0x1f000]
  +E0000 => Patch data 2


CoreDump info:
  +00 => 
  +04 => 
  +08 => 
  +0C => 
  +10 => 
  +14 => Paged dump address (ConnMCU space)
  +18 => Paged dump size
  +1C => Log<?> address (ConnMCU space)
  +20 => Log<?> area size
  +24 => Log<?> size

'''

'''
Conn MCU map:
  +00000000 => ROM (128k)
  +00060000 => Code RAM? (48k)
  +02090000 => SRAM (xx)
  +70000000 => ??
  +80000000 => CONN regs
  +90000000 => AP regs!!!!   ---> Can re config the EMI MAP and Disable EMI MPU ===== Spyware Confirmed!!
  +F0000000 => emi map (2 MiB)
'''

'''
type::
  0 => BT
  1 => FM
  2 => GPS
  3 => WIFI
  4 => WMT
  5 => STP
  6 => INFO   |LPBK     |TEST
  7 => ANT    |COREDUMP
'''

try:
    def cs_sendcmd(type, cmd, dat, noresp=False):
        tx = bytes([0x01,cmd]) + len(dat).to_bytes(2, 'little') + dat
        #print('will send cmd ', tx)
        cs_txframe(type, tx)
        
        if noresp: return None
        
        while True:
            rx = cs_rxframe(type)['data']
            if len(rx) < 4: continue
            #if rx[0] != 0x04: continue
            if rx[1] != cmd: continue
            dlen = int.from_bytes(rx[2:4], 'little')
            return (rx[0], rx[4:4+dlen])

    ######################

    with open(sys.argv[1], 'r') as script:
        print("============ Entering the script =============")
        exec(script.read())
        print("==============================================")

except Exception as e:
    print(e)

except KeyboardInterrupt:
    pass

print(">>>> Main Loop")

while True:
    try:
        if btif_tstc():
            rxc = btif_getc()

            if rxc & 0x80:
                pload = [rxc, btif_getc(), btif_getc(), btif_getc()]
                plen = (pload[1] << 8 | pload[2]) & 0xfff
                pdat = btif_recv(plen)
                pcrc = int.from_bytes(btif_recv(2), 'little')
                print('%02x:%d:%02x=%04x' % (pload[0], pload[1]>>4, pload[3], pcrc), pdat)

    except Exception as e:
        print(e)
        break

    except KeyboardInterrupt:
        break

def nt2str(dat):
    slen = len(dat)
    for i in range(len(dat)):
        if dat[i] == 0:
            slen = i
            break
    return str(dat[:slen], 'ascii')

print('\n\x1b[1;37;44m========= Paged trace/Log =========\n' + nt2str(konata.read(0x80400,0x8000)) + '\x1b[0m')
print('\n\x1b[1;37;41m========= Paged dump =========\n' + nt2str(konata.read(0x88400,0x8000)) + '\x1b[0m')

#========= Power down CONNSYS =========#
conn_power_ctl(False)
