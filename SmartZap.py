#!/usr/bin/python3

from configparser import SafeConfigParser
import curses
import serial
import sys,os
import signal

# -[ Notes ]-------------------------------------------------------------------#
#                                                                              #
# Need to add error handling (echo doesn't match). I'm pretty sure it's an     #
# an error code that's being returned.                                         #
# Need to add an error window.                                                 #
# -----------------------------------------------------------------------------#
VERSION = "0.2.4 py"

moduleID   = 0
beginT     = 0
endT       = 0
promSize   = 0
stow       = [ 0xff ] * 64 * 1024 # 64K - 27512

filename   = "<None>"
devicename = "</dev/null>"
directory  = "/tmp/"
cfgFile    = "dot.SmartZap.ini"

# Get the user options
if(len(sys.argv) == 2) :
    devicename = sys.argv[1];
else :
    devicename = "/dev/zapper"
#

#onfig = configparser.ConfigParser()
# use SafeConfigParser to turn %(HOME)s into /home/njc
# ${HOME} == %(HOME)s the s means return a string
config = SafeConfigParser(os.environ)
config.read(cfgFile)

"""
Python
# -[ Local ]--------------------------------------------------------------------
txTopic    = config['local']['TXTOPIC']

Config file
# -[ .broadlink.ini ]-----------------------------------------------------------
[SmartZap]
    # Be careful with indentation it's quite picky
    #
    dir      = ${HOME}/dev/SmartZap/t
    device   = /dev/smartzap
    filename = blank.bin
#

# -[ Fini ]---------------------------------------------------------------------
"""
filename   = config['SmartZap']['filename']
devicename = config['SmartZap']['device']
directory  = config['SmartZap']['dir']
    
# ------------------------------------------------------------------------------
# configure the serial connections
ser = serial.Serial(
    port     = '/dev/ttyUSB0',
    baudrate = 9600,
    parity   = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout  = 0.250
)

#
def sendEcho(i):
    #ser.write(bytearray.fromhex(s)) # from string '0xfb'
    ser.write(i.to_bytes(1, byteorder='big', signed=False)) # from int

    #time.sleep(0.150)

    print("Waiting = %d" % ser.in_waiting)
    t = ser.read(1)
    print("<Tx: 0x%02x>" % int.from_bytes(t, byteorder='big', signed=False))
    # s is a string, hex equivalent
    # 'ff' == 0xff
    return(int.from_bytes(t, byteorder='big', signed=False))
#

def recvEcho():
    #time.sleep(0.100)
    t = ser.read(1)
    print("<Rx: 0x%02x>" % int.from_bytes(t, byteorder='big', signed=False))
    ser.write(t)
    return(int.from_bytes(t, byteorder='big', signed=False))
#

def zModuleID():
    global moduleID
    global beginT
    global endT
    global promSize

    t = sendEcho(0xfb)
        
    moduleID = recvEcho()
            
    h = (recvEcho()*256)
    l = recvEcho()
    beginT = h + l
        
    h = (recvEcho()*256)                     # 
    l = recvEcho()
    endT = h + l
    promSize = endT+1
#

def zUpload(mySocket):
    global stow

    print("Socket: 0x%02x" % mySocket)
    try:
        if(moduleID == 0):
            print("Get module information")
            zModuleID()
            print('ID: 0x%02x' % moduleID)
            print('B:  0x%04x' % beginT)
            print('E:  0x%04x' % endT)
            checkErr()
            print("Now get PROM contents")
            #
            print("inWaiting:  %d" % ser.inWaiting())
            print("outWaiting: %d" % ser.out_waiting) # weird
        #
        # Send cmd = F7
        # then 40 for Master socket
        # or   80 for the clone socket
        #  (get echo)
        #  then
        # idx = 0
        # for i in beginT to EndT:
        #    stow[idx] = recvEcho()
        #    idx += 1
        sendEcho(0xf7)
        sendEcho(mySocket)
        print("Data:")
        for idx in range(beginT, endT+1):
            stow[idx] = recvEcho()
            if(DEBUG):
                ###
                ### For debugging, don't keep this here
                ###
                if(stow[idx] != 0x02):
                    print("Not 0x02 (stow[0x%04x] = (0x%02x))" % (idx, stow[idx]), file=sys.stderr)
                #
            #
        #
        checkErr()
    except Exception as err:
        print("Unexpected error:", sys.exc_info()[0])
    #
#

def checkErr():
    if(sendEcho(0xff) != 0xff):
        print("Error, hit the reset to clear", file=sys.stderr)
    else:
        print("Okay", file=sys.stderr)
    #
    while(ser.inWaiting()):
        recvEcho()
    #
#

def myExit():
    ser.close()
    exit(0)
#

###
ser.isOpen()

# Device Check
print("Device check ...", file=sys.stderr, end='', flush=True)
while(sendEcho(0xff) != 0xff):
    # Has curses started at this point?
    print(" failed, check for power and connectivity", file=sys.stderr)
    # Hit any key to continue, X to exit
    if(input("X to exit: ").lower() == 'x'):
        myExit()
    #
#
print(" passed", file=sys.stderr)
zModuleID()                     #  get the Module info

###
### Python Serial supports RFC2217 - Telnet Com Port Control Option
### I think I have at least one device that supports this but I also
### the Digi EL162 (remote network serial ports as opposed to a terminal
### server).
###
# ------------------------------------------------------------------------------
def zOut():
    pass
#

###
### Get Input from zapper then echo back
###
def zIn():
    pass
#
###
### Just get the one character (an Error occurred?)
###
def zIn2():
    pass
#

# ------------------------------------------------------------------------------
def zZap():
    zMenu.addstr(mboxHt-2, 2, "Status: zZap")
    pass
#

def zUpload():
    zMenu.addstr(mboxHt-2, 2, "Status: zUpload")
    pass
#

def zErase():
    zMenu.addstr(mboxHt-2, 2, "Status: zErase")
    pass
#

def zVerify():
    zMenu.addstr(mboxHt-2, 2, "Status: zVerify")
    pass
#

def zSave():
    zMenu.addstr(mboxHt-2, 2, "Status: zSave")
    pass
#

def zLoad():
    zMenu.addstr(mboxHt-2, 2, "Status: zLoad")
    pass
#

def zFill():
    zMenu.addstr(mboxHt-2, 2, "Status: zFill")
    pass
#

# was zPrint
# addr  00 01 02 03 03 05 06 07 08 09 0A 0B 0C 0D 0E 0F  0123456789ABCDEF
# 0000
# 0100  
def zEdit():
    mode = "Print"
    zMenu.addstr(mboxHt-2, 2, "Status: zEdit")

    l = 23
    w = 75
    edit = curses.newwin(l+2, w, 20, 40)
    edit.box(0,0)
    s    = "[ SmartZap %s screen ]" % mode
    slen = len(s)
    mid  = int((w-slen)/2)
    edit.addstr(0, mid, s, curses.color_pair(3))
    line = 2
    edit.addstr(line, 2, "addr  00 01 02 03 03 05 06 07 08 09 0A 0B 0C 0D 0E 0F  0123456789ABCDEF")
    line += 1
    edit.addstr(line, 2, "====  ===============================================  ================")
    offset = 0
    # 16 bytes by 16 lines, 256 bytes/screen
    for x in range(16):
        line += 1
        # Print addr
        edit.addstr(line, 2, "%04X" % offset)
        # Print hex value, Print ASCII value
        for a in range(16):
            offset += 1
            v = a
            edit.addstr(line,  8+(a*3), "%02x" % v)
            edit.addstr(line, 57+a,     "%x"   % v)
        # offset += 16 # This will be handled by the for loop
    #
    line += 1
    edit.addstr(line, 2, "====  ===============================================  ================")
    edit.addstr(l-1, 8, "Prompt> ")
    k = edit.getch()
    if(k == 'x'):
        del edit
        zRefresh()
        return
    #
    del edit
    zRefresh()
#

def zDir():
    zMenu.addstr(mboxHt-2, 2, "Status: zDir")
    pass
#

textArray = [
    "",
    "Smart Zap EPROM burner by Micro Kit Electronics",
    "SmartZap written by Neil Cherry 03/01/88",
    "",
    "Set for:",
    "    9600 baud",
    "    1 Start bit",
    "    8 Data bits",
    "    1 Stop bit",
    "    No Parity",
    "    RTS/CTS on",
    "    Xon/Xoff off",
    "",
    "Version: %s can handle 64K 27256 PROMS" % VERSION,
    ""
]
#
def zInformation():
    zMenu.addstr(mboxHt-2, 2, "Status: zInformation")
    ###
    ### 40x20 -for the about window
    ###
    l = len(textArray)
    about = curses.newwin(l+2, 52, 20, 40)
    about.box(0,0)
    about.addstr(0, (26-5), "[ About ]", curses.color_pair(3))

    line = 1
    for text in textArray:
        about.addstr(line, 2, text)
        line += 1

    about.touchwin()
    about.addstr(l, (26-3), "[ OK ]")
    about.getch()

    del about
    zRefresh()
#

def zChange():
    zMenu.addstr(mboxHt-2, 2, "Status: zChange")
    pass
#

def zCleanEE():
    zMenu.addstr(mboxHt-2, 2, "Status: zCleanup")
    pass
#

def zExit():
    zMenu.addstr(mboxHt-2, 2, "Status: zExit")
    stdscr.clear()
    stdscr.refresh()
    curses.echo()
    stdscr.keypad(False)
    curses.endwin()
    myExit(0)
#

def zRefresh():
    zMenu.addstr(mboxHt-2, 2, "Status: zRefresh")
    stdscr.touchwin()
    stdscr.refresh()
    myTitle.touchwin()
    myTitle.refresh()
    zInfo.touchwin()
    zInfo.refresh()
    zMenu.touchwin()
    zMenu.refresh()
#

zCmds = {
    'z':  zZap,
    'u':  zUpload,
    'e':  zErase,
    'v':  zVerify,
    's':  zSave,
    'l':  zLoad,
    'f':  zFill,
    'p':  zEdit,
    'd':  zDir,
    'i':  zInformation,
    'c':  zChange,
    'a':  zCleanEE,
    'x':  zExit,
    0x0C: zRefresh
}

#
def callMe(name):
    if(zCmds.__contains__(name)):
        zCmds[name]()
    else:
        zMenu.addstr(mboxHt-2, 2, "Status:              ")
    #
#

# -[ Main() ]-------------------------------------------------------------------
#
#YMax = int(os.getenv('LINES', 25))
#XMax = int(os.getenv('COLUMNS', 80))
#print("%d x %d" % (XMax, YMax))

stdscr = curses.initscr()
stdscr.keypad(True)
curses.start_color()
curses.noecho()

# Oops backwards
#curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_YELLOW)
#curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
#curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_RED)
#
curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
curses.init_pair(3, curses.COLOR_RED, curses.COLOR_WHITE)
curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
#
YMax = curses.LINES
XMax = curses.COLS

# ------------------------------------------------------------------------------
# Now that curses has been init we can figure out the size
title = "-=<[ SmartZap EPROM Burner Program Version %s - by N.Cherry ]>=-" % VERSION

titleX = 1                      # X Position
titleY = 2                      # Y Position
titleZ = 5                      # Size (depth)
infoX  = 2
infoY  = 6
infoZ  = 7
menuX  = 0
menuY  = 2
menuZ  = 13

# ------------------------------------------------------------------------------

# Main stdscr
stdscr.addstr(12, 25, "Python curses in action!", curses.color_pair(2))
stdscr.addstr(13, 26, "Python curses in action!", curses.color_pair(1))
stdscr.addstr(22, 2, "%d x %d" % (XMax, YMax))
stdscr.addstr(23, 2, "%d x %d" % (curses.COLS, curses.LINES))
stdscr.refresh()
stdscr.getch()

# Main box
stdscr.box(0,0)
# Title
stdscr.addstr(0, (int((XMax)/2)-6), "[ SmartZap ]", curses.color_pair(3))
#stdscr.border()
#stdscr.touchwin()
#stdscr.getch()

# Title box, this needs to be an odd size
myTitle = curses.newwin(5, (XMax-2-2), 1, 2)
myTitle.box(0,0)
slen = int(len(title)/2)
myTitle.addstr(2, (int((XMax-2)/2)-slen), title)
myTitle.touchwin()
myTitle.refresh()
stdscr.touchwin()
stdscr.refresh()

# Info box, this needs to be an odd size
zInfo = curses.newwin(7, (XMax-2-2), 6, 2)
zInfo.box(0,0)
zInfo.touchwin()

###
### Info window
###
zInfo.addstr(2, 20, "SmartZap")
zInfo.addstr(2, 40, "Module ID: %02x" % moduleID) # In hex?
zInfo.addstr(2, 80, "Begin Area for Zap: 0x%04x" % beginT)

zInfo.addstr(3, 40, "PROM Size: 0x%0x4" % promSize)
zInfo.addstr(3, 80, "End Area for Zap:   0x%04x" % endT)

zInfo.addstr(4, 40, "Filename:  %s" % filename)
zInfo.addstr(4, 80, "Port: %s" % devicename)

zInfo.refresh()                 # If you update multiple things
stdscr.refresh()                # Also update stdscr

# -[ Menu ]---------------------------------------------------------------------
# Menu box, this needs to be an odd size
###
### menu window
###
mboxHt = (YMax-7-5-2)
mboxWd = (XMax-2-2)
zMenu = curses.newwin(mboxHt, mboxWd, 13, 2)
zMenu.box(0,0)
zMenu.touchwin()

r = ''
while(r != 'x'):
    line = 2
    zMenu.addstr(line, 40, "Z) Zap from memory")
    zMenu.addstr(line, 80, "U) Upload PROM to memory")

    # I'm not sure what this is
    #zMenu.addstr(mboxHt-1, 2, "X")

    line += 1
    zMenu.addstr(line, 40, "E) Verify Erase")
    zMenu.addstr(line, 80, "V) Verify from memory")

    line += 1
    zMenu.addstr(line, 40, "S) Save memory to disk")
    zMenu.addstr(line, 80, "L) Load from disk to memory")

    line += 1
    zMenu.addstr(line, 40, "F) Fill stored data area")
    zMenu.addstr(line, 80, "P) Edit uploaded string")

    line += 1
    zMenu.addstr(line, 40, "I) General Information")
    zMenu.addstr(line, 80, "D) Directory of %s" % directory)

    line += 1
    zMenu.addstr(line, 40, "C) Change IO module")
    zMenu.addstr(line, 80, "A) Clean EEPROM")

    line += 1
    zMenu.addstr(line, 40, "X) Exit")
    #zMenu.addstr(line, 80, "Y) y-Options")

    line += 1
    zMenu.addstr(line, 40, "X) x-Options")
    zMenu.addstr(line, 80, "Y) y-Options")

    line += 1
    zMenu.addstr(line, 40, "X) x-Options")
    zMenu.addstr(line, 80, "Y) y-Options")

    zMenu.refresh()

    y = int(mboxHt * 0.75)
    x = int(mboxWd/2) - 9
    zMenu.addstr(y, x, "Prompt:  ")
    #r = zMenu.getch()
    r = zMenu.getkey()
    zMenu.addstr(y, x+9, "%s [%s]" % (r, r))
    zMenu.refresh()
    callMe(r)
    stdscr.refresh()                # Also update stdscr
#
# ------------------------------------------------------------------------------
zExit()                         # I shouldn't reach here but just in case ...
# -[ fini ]----------------------------------------------------------------------------
