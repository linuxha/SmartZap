#!/usr/bin/python3

VERSION = "0.2.19 py"

from configparser import SafeConfigParser

import curses
import curses.textpad
import serial
import signal

import sys,os,time
import traceback

#
import bincopy                  # Hex related 'stuff'

# -[ Notes ]--------------------------------------------------------------------
# I've tried to keep this simple. Basically following along with the simple menu
# model I created in 1987. Problem is that I've grown used to menu'd applications
# and the standard ways we interface with them. For now I'll stick to the menu
# Ignore the spinner and zWait and the fancy edit modes will need to wait. That
# might be something better left to C.
#
# The function of this program is to facilitate taking binary or hex files and
# writing them to an EPROM and reading an EPROM and writing them to binary or
# hex files.
#
# 20180409 - Did a little clean up on the main menu
# Still need to do:
#   Zap
#   Verify Erase
#   Verify memory
#   Fill
#   Edit (only partially complete)
#   Directory <- This needs to be made File < Move to Load/Save ?
#   Change module (partial done, need timing changes)
#   Clean EEPROM
#   
# ------------------------------------------------------------------------------

#
"""
###
### Read in file
###
>>> f = bincopy.BinFile("sbug-mod.s19")
>>> f.info()
'Data address ranges:\n                         0x0000f800 - 0x00010000\n'
>>> a = f.as_binary() # byte array
###
### Write ihex to a file
###
w = open('outfile.ihx', 'w')    # write to the file outfile.ihx
print(f.as_ihex())              # write the Intel hex to stdout
print(f.as_ihex(), file=w)      # write the Intel hex to the file outfile.ihx as w
w.close()                       # close the file object w
"""
# -[ Notes ]-------------------------------------------------------------------#
#                                                                              #
# Need to add error handling (echo doesn't match). I'm pretty sure it's an     #
# an error code that's being returned.                                         #
# Need to add an error window.                                                 #
# -----------------------------------------------------------------------------#
moduleID   = 0
beginT     = 0
endT       = 0
promSize   = 0
# Array of ints
stow       = [ 0xff ] * 64 * 1024 # 64K - 27512

filename   = "<None>"
devicename = "</dev/null>"
directory  = "/tmp/"
cfgFile    = "dot.SmartZap.ini"

#onfig = configparser.ConfigParser()
# use SafeConfigParser to turn %(HOME)s into /home/njc
# ${HOME} == %(HOME)s the s means return a string
config = SafeConfigParser(os.environ)
config.read(cfgFile)

filename  = config['SmartZap']['filename']
directory = config['SmartZap']['dir']

# Get the user options
if(len(sys.argv) == 2) :
    devicename = sys.argv[1];
else:
    devicename = config['SmartZap']['device']
#

# Check for the device
if(os.path.isfile(devicename) == False):
    print("Device not found: %s" % devicename, file=sys.stderr)
    #exit(2)
#

# ------------------------------------------------------------------------------
# configure the serial connections
try:
    ser = serial.Serial( port = devicename, baudrate = 9600, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout  = 0.250 )
except Exception as err:
    # FileNotFoundError actually ...
    # class 'serial.serialutil.SerialException (so serialutil.SerialException ?)
    # Okay what do we do here?

    print("=[ traceback ]==================================================================", file=sys.stderr)
    # https://docs.python.org/3/library/traceback.html
    # search for lumberjack()
    exc_type, exc_value, exc_traceback = sys.exc_info()
    formatted_lines = traceback.format_exc().splitlines()

    print(formatted_lines[-1], file=sys.stderr)
    print("*** tb_lineno:", exc_traceback.tb_lineno, file=sys.stderr)
    #print("*** ext_type:", exc_type, file=sys.stderr)
    print("=[ Oof ]========================================================================", file=sys.stderr)
    exit(1)
#

###
### Python Serial supports RFC2217 - Telnet Com Port Control Option I
### think I have at least one device that supports this but I also
### have the Digi EL162 (remote network serial ports as opposed to a
### terminal server).
###

# '1' != 0x31 (str != int)
# ba = bytearray(
"""
# Array of string
sa = [ '1', '2', '3', '4' ]
array_of_int = [ int(numeric_string) for numeric_string in sa ]

# Array of ints
>>> a = [ 0x31, 0x32, 0x33, 0x34, 0x01, 0x02, 0x03, 0x04, 0x20, 0x08 ]
>>> type(a[9])
<class 'int'>
>>> type(a[0])
<class 'int'>
>>> ba = bytearray(a)
>>> type(be)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'be' is not defined
>>> type(ba)
<class 'bytearray'>
>>> s = [ '1', '2', '3' ]
>>> sba = bytearray(s)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: an integer is required

>>> r = open("worfile", "rb")
>>> r.read(10)
b'1234\x01\x02\x03\x04 \x08'
>>> type(r.read(10))
<class 'bytes'>
>>> rb = r.read(10) # can't read 10 more, there are only 10 total
>>> rb
b''
>>> r.seek(0)       # seek back to the beginning
0
>>> rb = r.read(10)
>>> len(rb)
10
>>> rb
b'1234\x01\x02\x03\x04 \x08'
>>> rb[0]
49
>>> 

""

"""
#
# Write int to bytes
#
def sendEcho(i):
    #ser.write(bytearray.fromhex(s)) # from string '0xfb'
    ser.write(i.to_bytes(1, byteorder='big', signed=False)) # from int

    #time.sleep(0.150)

    #print("\rWaiting = %d" % ser.in_waiting)
    t = ser.read(1)
    #print("\r<Tx: 0x%02x>" % int.from_bytes(t, byteorder='big', signed=False))
    # s is a string, hex equivalent
    # 'ff' == 0xff
    return(int.from_bytes(t, byteorder='big', signed=False))
#

#
# Read 1 byte1 from the serial port
# return the int value of it
#
def recvEcho():
    #time.sleep(0.100)
    t = ser.read(1)
    #print("\r<Rx: 0x%02x>" % int.from_bytes(t, byteorder='big', signed=False))
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

def myExit():
    # Don't we need to clean up the ncurses stuff here?
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

# ------------------------------------------------------------------------------
def zZap():
    zMenu.addstr(mboxHt-2, 2, "Status: zZap")
    #
    pass
#

#
def zSetup():
    """
    Timing changes:
    Send 0xF9 (249) then the start address high byte, the start address low,
    the end address high, and then the end address low. The setup change can be
    used for zapping, verifying, or uploading from one location thru all locations.

    Need to get the default values from the source code (probably the Module's
    address settings ;-)
    """
    pass
#

#
def zTiming():
    """
    Timing changes:
    Send 0xFA (250) then the overzap byte (oz), the loopmax byte (lm), the
    delay time high byte, & then low byte.

    The overzap byte is used in the fast zapping mode (dip sw 2=on). Overzap
    pulse equals the overzap byte times the loop count. The loop max is the
    number of times the program will try to zap a location. Overzap byte and
    loop max bytes are standard Intel designations, set to that unless changed.
    The delay time bytes are a value used to generate the 1 millisecond delay
    when zapping, it is normally set to 0x0133 (307) but can be made smaller if
    necessary.

    Need to get the default values from the source code
    """
    oz=0x0                      # Check asm source for defaults
    lm=0x0133                   # 
    pass
#

def zDialog():
    l = 6
    w = 34
    # Want this pretty much middle of the screen
    xW = xMid - int(w/2)
    yW = yMid - int((l+2)/2) - 1
    diag = curses.newwin(l+2, w, yW, xW)
    diag.box(0,0)
    s    = "[ SmartZap Socket selection ]"
    slen = len(s)
    mid  = int((w-slen)/2)
    diag.addstr(0, mid, s, curses.color_pair(3))

    diag.addstr(2, 3, "1 for Master socket (right)")
    diag.addstr(3, 3, "2 for Clone socket (left)")

    diag.addstr(l-1, 8, "Prompt> ")
    k = diag.getch()

    del diag
    zRefresh()

    if(k == 0x32): # 0x32 is ASCII 2 (Clone socket)
        return(0x80)
    else:
        return(0x40)
    #
#

#
def spinner():
    """
    # Shell script version
    spin () {
        ARRAY=( "-", "\\", "|", "/", "-", "\\", "|", "/" )
        ELEMENTS=${#ARRAY[@]}
        # echo each element in array 
        # for loop
        for (( i=0;i<$ELEMENTS;i++)); do
           echo -n -e "\r${ARRAY[${i}]}"
           sleep $spinpause
        done
    }
    """
    pass
#

#
def checkErr():
    rtn = 0
    if(sendEcho(0xff) != 0xff):
        #print("\r    Error, hit the reset to clear", file=sys.stderr)
        rtn = 0
    else:
        #print("\r    Okay", file=sys.stderr)
        rtn = 1
    #
    while(ser.inWaiting()):
        recvEcho()
    #
    return(rtn)
#

#
def zUpload():
    global stow
    # From the main while loop for zMenu
    y = int(mboxHt * 0.75)
    x = int(mboxWd/2) - 9
    spinner = [ "-", "\\", "|", "/", "-", "\\", "|", "/" ]
    zMenu.addstr(mboxHt-2, 2, "Status: zUpload")

    # need to get which socket
    # for now it's the Master
    mySocket = zDialog()

    try:
        if(moduleID == 0):
            zModuleID()
            checkErr()
            #
            #print("inWaiting:  %d" % ser.inWaiting())
            #print("outWaiting: %d" % ser.out_waiting) # weird
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

        for idx in range(beginT, endT+1):
            # Spinner would go here
            zMenu.addstr(y, x+9, spinner[int(idx%8)])
            stow[idx] = recvEcho()
            zMenu.refresh()
        #
        if(checkErr()):
            zMenu.addstr(y, x+9, "Okay  ")
        else:
            zMenu.addstr(y, x+9, "Error, hit the reset to clear")
        #
    except Exception as err:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        #stdscr.refresh()
        curses.echo()
        stdscr.keypad(False)
        curses.endwin()

        print("\n\n=[ traceback ]==================================================================", file=sys.stderr)
        print("\nUnexpected error:", sys.exc_info()[0], file=sys.stderr)
        print("Oops, can't read ", err, file=sys.stderr)
        #rint("Oops, can't read ", sys.exc_traceback.tb_lineno, file=sys.stderr)
        print("TB", file=sys.stderr)
        traceback.print_tb(exc_traceback, file=sys.stderr)
        print("EXC", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        exit(1)
    #
    zRefresh()
#

def zErase():
    zMenu.addstr(mboxHt-2, 2, "Status: zErase")
    pass
#

def zVerify():
    zMenu.addstr(mboxHt-2, 2, "Status: zVerify")
    pass
#

# =[ @FIXME: Error checking ]===================================================
# Wow, I really need to work on error checking for these read and write routines
# at the moment they have none
# ==============================================================================

#
def rdBincopy(fname):
    zMenu.addstr(mboxHt-2, 2, "Status: rdBincopy(%s)" % fname)
    pass
#

#
def wrBincopy(fname):
    zMenu.addstr(mboxHt-2, 2, "Status: wrBincopy(%s)" % fname)

    ###
    ### WIP (Work In Progress)
    ###
    ba = bytearray(stow[beginT:endT]) # Limit the Array to the Current PROM Size
    bcObj = bincopy.BinFile()
    bcObj.add_binary(ba)        # We need to tell bincopy x thru y
    
    w = open(filename, 'w')        # write to the file outfile.ihx
    dummy, ext = fname.rsplit('.', 1)

    if(ext == 'ihx'):
        print(bcObj.as_srec(), file=w)    # write the Intel hex to the file outfile.ihx as w
    elif(ext == 'srec' or ext == 's19') :
        print(bcObj.as_ihex(), file=w)    # write the Intel hex to the file outfile.ihx as w
    elif(ext == 'hex') :
        print(bcObj.as_hexdump(), file=w) # write the Intel hex to the file outfile.ihx as w
    elif(ext == 'bin') :
        print(bcObj.as_binary(), file=w)  # write the Intel hex to the file outfile.ihx as w
    else :
        print(bcObj.as_binary(), file=w)  # write the Intel hex to the file outfile.ihx as w
    #
    w.close()                      # close the file object w
    #

    pass
#

"""
>>> filename = 'junk.bin'
>>> r = open(filename, 'rb')          # write to the file outfile.ihx
>>> stow = r.read()
>>> r.close()                         # close the file object w
>>> len(stow)
8191
>>> type(stow)
<class 'bytes'>
>>> stow[0]
255
>>> type(stow[0])
<class 'int'>
>>> 
"""
#
def rdBinfile(fname):
    global stow
    zMenu.addstr(mboxHt-2, 2, "Status: rdBinfile(%s)" % fname)
    r = open(filename, 'rb')          # write to the file outfile.ihx
    # TypeError: must be str, not bytearray
    stow = r.read()
    r.close()                         # close the file object w
    pass
#

#
def wrBinfile(fname):
    zMenu.addstr(mboxHt-2, 2, "Status: wrBinfile(%s)" % fname)

    ###
    ### WIP (Work In Progress)
    ###
    ba = bytearray(stow[beginT:endT]) # Limit the Array to the Current PROM Size
    #bcObj = bincopy.BinFile()
    #bcObj.add_binary(ba)             # We need to tell bincopy x thru y
    
    w = open(filename, 'wb')          # write to the file outfile.ihx
    # TypeError: must be str, not bytearray
    w.write(ba)
    w.close()                         # close the file object w
    #

    pass
#

#
###
### Write to the file
###
"""
###
### Read in file
###
>>> f = bincopy.BinFile("sbug-mod.s19")
>>> f.info()
'Data address ranges:\n                         0x0000f800 - 0x00010000\n'
>>> a = f.as_binary() # byte array
###
### Write ihex to a file
###
w = open('outfile.ihx', 'w')    # write to the file outfile.ihx
print(f.as_ihex())              # write the Intel hex to stdout
print(f.as_ihex(), file=w)      # write the Intel hex to the file outfile.ihx as w
w.close()                       # close the file object w

###
### Check that a file exists
###
>>> import os
>>> fname = "file.s1"           # a file that doesn't exist
>>> os.path.isfile(fname) 
False
>>> 

###
### take an array of strings and save them to file
###
>>> s = [ '1', '2', '3' ]
>>> s
['1', '2', '3']
>>> ba = bytearray(ord(i) for i in s)
>>> ba
bytearray(b'123')

>>> f = bincopy.BinFile()       # Create an empty bincopy object
>>> ba
bytearray(b'123')
>>> f.add_binary(ba)
>>> f.as_srec()
'S3080000000031323361\nS5030001FB\n'
>>> 

add_binary(data, address=0, overwrite=False)[source]
Add given data at given address. Set overwrite to True to allow already added data to be overwritten.
"""
###
### From the filename ext, determine which format to use
###   .bin  - raw format (should be in 1K increments) (starts at 0)
###   .srec - Motorola S-Records
###   .ihx  - Intel hex format
###
wrBincmd = {
    '.srec': wrBincopy,
    '.s19':  wrBincopy,
    '.ihx':  wrBincopy
}

#
def zSave():
    global directory, filename
    # for now I'll just create a new window with a text box, inside
    # the text box I'll have the path and the filename. Then when
    # that's selected we can either do a normal write or a print of
    # bincopy. I'm not sure how I'll handle a bincopy where the memory
    # is offset from zero.
    zMenu.addstr(mboxHt-2, 2, "Status: zSave")

    (fullFileName, directory, filename, ext) = fileTextbox(directory, filename)
    zInfoStuff(zInfo)
    zRefresh()

    # Now that we have everything we need to get the file
    if(wrBincmd.__contains__(ext)):
        wrBincmd[ext](fullFileName)
    else:
        wrBinfile(fullFileName)
    #
    zMenu.refresh()
    # Save
    #zMenu.getkey()
#

#
"""
###
### Read in file
###
>>> f = bincopy.BinFile("sbug-mod.s19")
>>> f.info()
'Data address ranges:\n                         0x0000f800 - 0x00010000\n'
>>> a = f.as_binary() # byte array
###
>>> f = open('file.bin', 'rb')
>>> b = f.read()
>>> len(b)
5
>>> type(b)
<class 'bytes'>
>>> b[0]
1
>>> b[4]
10
>>> w = open('file2.bin', 'wb')
>>> w.write(b)
5
>>> w.write(b)
5
>>> w.close()                   # file2.bin contain 10 bytes
>>> 
"""
###
### Read a file
###
rdBincmd = {
    '.srec': rdBincopy,
    '.s19':  rdBincopy,
    '.ihx':  rdBincopy
}

#
def zLoad():
    global directory, filename
    # for now I'll just create a new window with a text box, inside the text box
    # I'll have the path and the filename. Then when that's selected we can
    # either do a normal read or a bincopy. I'm not sure how I'll handle a
    # bincopy where the memory is offset from zero.
    zMenu.addstr(mboxHt-2, 2, "Status: zLoad")
    # Load a file into an array
    (fullFileName, directory, filename, ext) = fileTextbox(directory, filename)
    zInfoStuff(zInfo)
    zRefresh()

    # Now that we have everything we need to get the file
    if(rdBincmd.__contains__(ext)):
        rdBincmd[ext](fullFileName)
    else:
        rdBinfile(fullFileName)
    #
    zMenu.refresh()
    # Load
    #zMenu.getkey()
    #

    #
    pass
#

#
def zInfoStuff(scr):
    ###
    ### Info window
    ###
    scr.addstr(2, 20, "SmartZap")
    scr.addstr(2, 40, "Module ID: %02x" % moduleID) # In hex?
    scr.addstr(2, 80, "Begin Area for Zap: 0x%04x" % beginT)

    scr.addstr(3, 40, "PROM Size: 0x%04x" % promSize)
    scr.addstr(3, 80, "End Area for Zap:   0x%04x" % endT)

    scr.addstr(4, 40, "Filename:  %s" % filename)
    scr.addstr(4, 80, "Port:               %s" % devicename)
    scr.touchwin()
#

#
def zFile():
    zMenu.addstr(mboxHt-2, 2, "Status: zFile")
    pass
#

#
def zFill():
    zMenu.addstr(mboxHt-2, 2, "Status: zFill")
    pass
#

#
import string
def xchr(x):
    c = chr(x)
    #if(c in string.ascii_letters):
    if((c in string.printable) and (c not in string.whitespace)):
        return c
    else:
        return '.'
    #
#

# was zPrint
# addr  00 01 02 03 03 05 06 07 08 09 0A 0B 0C 0D 0E 0F  0123456789ABCDEF
# 0000
# 0100  
def zEdit():
    # Normal mode for zEdit is print
    # but I want to be able to edit the segments in memory and move them around
    # So that would be in the edit mode. Not sure how I'll deal with this yet.
    # For now I'll just keep it simple
    mode = "Print"
    zMenu.addstr(mboxHt-2, 2, "Status: zEdit")

    l = 23
    w = 75
    # Want this pretty much middle of the screen
    xW = xMid - int(w/2)
    yW = yMid - int((l+2)/2) - 1
    edit = curses.newwin(l+2, w, yW, xW)
    edit.box(0,0)
    s    = "[ SmartZap %s screen ]" % mode
    slen = len(s)
    mid  = int((w-slen)/2)
    edit.addstr(0, mid, s, curses.color_pair(3))
    line = 2
    edit.addstr(line, 2, "Addr  00 01 02 03 03 05 06 07 08 09 0A 0B 0C 0D 0E 0F  0123456789ABCDEF")
    line += 1
    edit.addstr(line, 2, "====  ===============================================  ================")
    offset = 0
    addr   = 0

    pages = int(promSize/256)
    while(offset < promSize):
        tLine = line
        # 16 bytes by 16 lines, 256 bytes/screen
        for x in range(16):
            tLine += 1
            # Print addr
            # We can only have 20 lines, yet we have 25
            edit.addstr(tLine, 2, "%04X" % addr)

            # Print hex value, Print ASCII value
            for a in range(16):
                v = stow[addr]
                addr += 1
                edit.addstr(tLine,  8+(a*3), "%02x" % v)
                edit.addstr(tLine, 57+a,     "%s"   % xchr(v))
            # That's one complete line
            #
        # That's one complete screen
        #
        offset += 256 # 1 page = 256 or 16x16
        page    = int(offset/256)
        s = "[ Page: %02d of %0d ]" % (page, pages)
        slen = len(s)
        mid  = int((w-slen)/2)
        edit.addstr(l+1, mid, s, curses.color_pair(3))
        #
        tLine += 1
        edit.addstr(tLine, 2, "====  ===============================================  ================")
        edit.addstr(l-1, 8, "Prompt> ")

        k = edit.getch()
        edit.addstr(l-1, 16, chr(k))
        if(k == 0x78):
            #del edit
            zRefresh()
            offset = promSize+1
            #return
        #
    # while
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
    w = 52
    # Want this pretty much middle of the screen
    xW = xMid - int(w/2)
    yW = yMid - int((l+2)/2) - 1
    #about = curses.newwin(l+2, 52, 20, 40)
    about = curses.newwin(l+2, w, yW, xW)
    about.box(0,0)
    about.addstr(0, (26-5), "[ About ]", curses.color_pair(3))

    line = 1
    for text in textArray:
        about.addstr(line, 2, text)
        line += 1

    about.touchwin()
    about.addstr(l, (26-3), "[ OK ]")
    about.addstr(l, (25), "")         # position the cursor on the 'O' of Ok
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
    myExit()
#

def zRefresh():
    zMenu.addstr(mboxHt-2, 2, "Status: zRefresh                    ")
    stdscr.touchwin()
    stdscr.refresh()
    myTitle.touchwin()
    myTitle.refresh()
    zInfo.touchwin()
    zInfo.refresh()
    zMenu.touchwin()
    zMenu.refresh()
#

###
### ARGH! thought there might be an easy way to use some form of threads
### or other concurrency with Python. My first attempt at it either runs
### thread A or thread B. Not what I want
###
#def zWait(waitString):
def zWait():
    spinner = [ "-", "\\", "|", "/", "-", "\\", "|", "/" ]
    # Create a wait box in the middle of the screen
    # Twiddle our thumbs until done (spinner)
    # then say yea or nay
    # we should probably have a timeout or something
    l = 4
    w = 34
    # Want this pretty much middle of the screen
    xW = xMid - int(w/2)
    yW = yMid - int((l+2)/2) - 1
    wait = curses.newwin(l+2, w, yW, xW)
    wait.box(0,0)
    s    = "[ The Busy Box ]"
    slen = len(s)
    mid  = int((w-slen)/2)
    wait.addstr(0, mid, s, curses.color_pair(3))

    try:
        # cursor state to
        #   invisible,   (0)
        #   normal,      (1)
        #   very visible (2)
        wait.curs_set(1)
    except:
        pass # Don't blow up if you can't do this
    #
    wait.addstr(2, 3, "Please wait ... ")
    wait.addstr(2, 19, spinner[int(idx%8)])
    for idx in range(0,80):
        # Spinner would go here
        wait.addstr(2, 19, spinner[int(idx%8)])
        wait.refresh()
        time.sleep(0.250)
    #
    wait.addstr(2, 19, "Good")
    s    =  "[ Okay ]"
    slen = len(s)
    mid  = int((w-slen)/2)
    try:
        wait.curs_set(2)
    except:
        pass # Don't blow up if you can't do this
    #
    wait.addstr(3, mid, s)
    wait.addstr(3, mid+2, "") # Put the cursor on Okay
    wait.getkey()

    del wait
    zRefresh()

#

#
# A text pad goes inside a window
# For some reason I get an ACS_HLINE error is I use curses.ACS_HLINE
# or just ACS_HLINE in the underlineChr
def maketextbox(screen, h, w, y, x, value="", deco=None, underlineChr="_", textColorpair=0, decoColorpair=0):
    nw = curses.newwin(h, w, y, x)
    txtbox = curses.textpad.Textbox(nw, insert_mode=True)

    if deco=="frame":
        screen.attron(decoColorpair)
        curses.textpad.rectangle(screen,y+1,x,y+h-2,x+w-2)
        screen.attroff(decoColorpair)
    elif deco=="underline":
        screen.hline(y+1, x, underlineChr, w, decoColorpair)
    #

    nw.addstr(0, 0, value, textColorpair)
    nw.attron(textColorpair)
    screen.refresh()

    return txtbox
#

#
def fileTextbox(dName, fName):
    # take the existing dir path and filename then present that to the user
    fpath = ("%s/%s") %(dName, fName)
    fnLen = len(fpath)
    #                                                 48
    #  0       8                                        50
    #  +------------------------------------------------+
    #  | Path: [                                      ] |
    #  +------------------------------------------------+
    l = 6
    w = fnLen + 80 + 4
    # Center the box
    global xMid, yMid
    xPos = xMid - int(w/2)
    yPos = yMid - int((l+2)/2) - 1
    xwin = curses.newwin(l, w, yPos, xPos)
    xwin.box(0, 0)
    xwin.addstr(0, 2, "[ File ]", curses.color_pair(1))
    xwin.addstr(2, 2, "Text: ")
    xwin.refresh()

    foo = maketextbox(stdscr,
                      1, w-9,
                      yPos+2, xPos+8,
                      fpath,
                      deco="underline",
                      textColorpair=curses.color_pair(0),
                      decoColorpair=curses.color_pair(1))
    text = foo.edit().strip()
    del foo, xwin
    zRefresh()
    # hey, what do we do if we don't get anything back?
    try:
        dName, fName = text.rsplit('/', 1)
        dummy, ext   = text.rsplit('.', 1)
        ext = '.' + ext
    except: # ValueError
        # temp, I need to restore to the original values
        dName = "/path/to"
        fName = "dummy"
        ext   = '.bin'
    #
    return(text, dName, fName, ext)
#

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
    '1':  zWait,
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
stdscr = curses.initscr()
stdscr.keypad(True)
curses.start_color()
curses.noecho()

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

xMid = int(XMax/2)              # X Mid point on the total screen
yMid = int(YMax/2)              # Y Mid point on the total screen
# ------------------------------------------------------------------------------

# Main stdscr
# Main box
stdscr.box(0,0)
# Title
stdscr.addstr(0, (xMid-6), "[ SmartZap ]", curses.color_pair(3))
#stdscr.border()
#stdscr.touchwin()
#stdscr.getch()

# ------------------------------------------------------------------------------
# Title box, this needs to be an odd size
myTitle = curses.newwin(5, (XMax-2-2), 1, 2)
myTitle.box(0,0)

slen = int(len(title)/2)
myTitle.addstr(2, (xMid-1-slen), title)

#stdscr.touchwin()
#stdscr.refresh()

#myTitle.touchwin()
#myTitle.refresh()
# ------------------------------------------------------------------------------
# Info box, this needs to be an odd size
zInfo = curses.newwin(7, (XMax-2-2), 6, 2)
zInfo.box(0,0)
#zInfo.touchwin()

zInfoStuff(zInfo)
#zInfo.refresh()                 # If you update multiple things
#stdscr.refresh()                # Also update stdscr

# -[ Menu ]---------------------------------------------------------------------
# Menu box, this needs to be an odd size
###
### menu window
###
mboxHt = (YMax-7-5-2)
mboxWd = (XMax-2-2)
zMenu = curses.newwin(mboxHt, mboxWd, 13, 2)
zMenu.box(0,0)
#zMenu.touchwin()

zRefresh()

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

    """
    zMenu.addstr(line, 80, "Y) y-Options")

    line += 1
    zMenu.addstr(line, 40, "X) x-Options")
    zMenu.addstr(line, 80, "Y) y-Options")

    line += 1
    zMenu.addstr(line, 40, "X) x-Options")
    zMenu.addstr(line, 80, "Y) y-Options")
    """

    zMenu.refresh()

    y = int(mboxHt * 0.50)
    x = int(mboxWd/2) - 29
    zMenu.addstr(y, 40, "Prompt:  ")
    #r = zMenu.getch()
    r = zMenu.getkey()
    k = ord(r)
    if( k < 0x7f and k > 0x19): # isPrintable(r)
        zMenu.addstr(y, x+9, "%s [%s]" % (r, r))
    #
    zMenu.refresh()
    callMe(r)
    stdscr.refresh()                # Also update stdscr
#
# ------------------------------------------------------------------------------
zExit()                         # I shouldn't reach here but just in case ...
# -[ fini ]----------------------------------------------------------------------------

"""
                try:
                except Exception as err:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    stdscr.refresh()
                    curses.echo()
                    stdscr.keypad(False)
                    curses.endwin()

                    print("\n\n=[ traceback ]==================================================================", file=sys.stderr)
                    print("\nUnexpected error:", sys.exc_info()[0], file=sys.stderr)
                    print("Oops, can't read ", err, file=sys.stderr)
                    #rint("Oops, can't read ", sys.exc_traceback.tb_lineno, file=sys.stderr)
                    print("TB", file=sys.stderr)
                    traceback.print_tb(exc_traceback, file=sys.stderr)
                    print("EXC", file=sys.stderr)
                    traceback.print_exc(file=sys.stderr)
                    print("\nline = %d\naddr = 0x%04x\noffset = %\n" % (tLine, addr, offset), file=sys.stderr)
                    exit()
                #

    if(MEMORY):
    else:
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
    #
"""
