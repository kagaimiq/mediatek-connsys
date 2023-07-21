# The Stuff

There are the stuff that actually does something with the hardware..

## bringup_mt6580.py

The main script that messes up your hardware (namely your CONSYS, your MT6350 PMIC, and few other places as well)

It initializes the CONSYS, and then runs scripts in sequence as specified on the command line,
and then simply displays whatever packets were received from CONSYS.

After pressing Ctrl-C it dumps the Coredump info and finally shutdowns CONSYS.

The portion of the system memory used for the CONSYS's EMI map is located at 0x88000000 so be sure to mark it as `reserved-memory` to not have any issues!
(or remap this to a different region)

Messing with the PMIC is needed to enable the neccessary power rails used for the CONSYS (namely vcn18, vcn28, vcn33_bt and vcn33_wifi),
so I could've just defined these rails as `regulator-always-on` or something like that in the DT, but whatever.

The scripts that can be used with this script are listed below:

### INIT.py

This should be the CONSYS init as done by the vendor's driver, but for some reason it doesn't work..

### FM_RADIO.py

This initializes the FM radio receiver, and hosts a TCP server at port 8751,
to which you can connect with [RDS Surveyor](https://github.com/ChristopheJacquet/RdsSurveyor)
and watch the RDS packets and control the frequency.

By default it tunes to 106.4 MHz (because that's what I'm mostly listening to;)

To hear the audio you need to initialize the audio subsystem's I2S input port to receive the I2S signal
from CONSYS (the FM radio is an I2S master in this case), this is accomplished by the audio script below.

## audio_mt6580.py

This more or less initializes the audio subsystem so that you can hear (and capture) the audio from CONSYS.

However, it doesn't initialize the MT6350's audio codec as well as the corresponding interface in the AFE
(because that's done in my [ARM Linux boot wrapper](https://github.com/kagaimiq/mtkproto/blob/c55c440dff2c6d869d0aed4308d4068dc32b0630/payload-mt6580-LinuxBoot/sperd.c#L444),
and so I'm too lazy to do something about it..)

Note that it also outputs the received audio stream to the stdout, as a 16-bit LPCM stereo stream at 48 kHz sample rate,
so that you can e.g. feed it into ffmpeg (like so: `sudo python3 audio_mt6580.py | ffmpeg -y -f s16le -ac 2 -ar 48000 -i - -ab 192k mtk3.mp3`)
and record!

Just for you to know, this code was originally an "audio server" that was playing and capturing the data from/to the FIFO sockets
that were made with the PulseAudio's `module-pipe-sink` and `module-pipe-source` modules, but I'm currently running Arch on MT6580,
and so I didn't feel like installing PulseAudio, as I didn't also need to playback any audio, so I thought simply dumping audio stream
to stdout to later grab it with e.g. ffmpeg should suffice as well.

This does not use the system DRAM as the audio stream is stored on the tiny SRAM in the audio subsystem itself.
