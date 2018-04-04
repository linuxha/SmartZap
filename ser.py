#!/usr/bin/python3

# https://stackoverflow.com/questions/44639741/pyserial-only-reading-one-byte

import time
import serial
import signal
import os, sys

# Global variables
DEBUG    = False
moduleID = 0
beginT   = 0
endT     = 0
promSize = 0
stow     = [0xff]*0x10000

try:

    # configure the serial connections
    ser = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0.250
    )

    #
    def signal_handler(signal, frame):
        print('\nYou pressed ^C!')
        ser.close()
        exit(0)
    #

    #
    signal.signal(signal.SIGINT, signal_handler)

    #
    # Read 1 byte1 from the serial port
    # return the int value of it
    #
    def sendEcho(i):
        #ser.write(bytearray.fromhex(s)) # from string '0xfb'
        ser.write(i.to_bytes(1, byteorder='big', signed=False)) # from int

        #time.sleep(0.150)

        #print("Waiting = %d" % ser.in_waiting)
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
    ###
    ser.isOpen()

    print('Enter your commands below.\r\nInsert "exit" to leave the application.')

    while 1 :
        # get keyboard input
        data_in = input(">> ")

        if data_in == 'exit' or data_in == 'q' or data_in == 'x':
            ser.close()
            exit()
        elif data_in == 'id':
            print('Requesting module ID')

            t = sendEcho(0xfb)
            moduleID = recvEcho()
            print('ID: 0x%02x' % moduleID)           # Module ID

            h = (recvEcho()*256)
            l = recvEcho()
            beginT = h + l
            print('B:  0x%04x' % beginT)             # Start addr (16b)

            h = (recvEcho()*256)                     # 
            l = recvEcho()
            endT = h + l
            print('E:  0x%04x' % endT)                  # End addr (16b)
        elif data_in == 'oid':
            print('Requesting module ID')
            # send the character to the device
            #ser.write(data_in.decode('hex') + '\r\n')
            #print('Rx: %02x' % sendEcho('fb'))
            t = sendEcho(0xfb)

            print('ID: 0x%02x' % recvEcho())           # Start

            print('B:  0x%02x' % recvEcho(), end='')  # Hi Start
            print('%02x' % recvEcho())                # Lo Start 

            print('E:  0x%02x' % recvEcho(), end='')  # Hi End
            print('%02x' % recvEcho())                # Lo End
        elif(data_in == 'ul'):
            if(moduleID == 0):
                t = sendEcho(0xfb)

                moduleID = recvEcho()

                h = (recvEcho()*256)
                l = recvEcho()
                beginT = h + l

                h = (recvEcho()*256)                     # 
                l = recvEcho()
                endT = h + l
            #
            sendEcho(0xf7)
            sendEcho(0x40)
            for idx in range(beginT, endT+1):
                stow[idx] = recvEcho()
                if(stow[idx] != 0x02):
                    print("Not 0x02 (0x%04x = 0x%02x)" % (idx, stow[idx]), file=sys.stderr)
                #
            #
            checkErr()
        elif data_in == 'upload':
            zUpload(0x40)
        elif data_in == 'uploadC':
            zUpload(0x80)
        elif data_in == 'nada':
            ###
            ### Sample initial code, not needed anymore
            ###

            # send the character to the device
            #ser.write(data_in.decode('hex') + '\r\n')
            ser.write(bytearray.fromhex('ff'))

            out = ''
            t1 = time.time()
            time.sleep(0.250)
            t2 = time.time()

            cnt = 11
            print("T diff: %f\nCount = %d" % ((t2-t1), ser.inWaiting()))
            while ser.inWaiting() > 0:
                if(cnt > 10):
                    print('.',)
                    cnt = 0
                #
                cnt += 1
                out += ser.read(1)
            #

            if out != '':
                print(">> " + " ".join(hex(ord(n)) for n in out))
            else:
                print("Empty out")
            #
        elif(data_in == 'flush'):
            cnt = 0
            while(sendEcho(0xff) != 0xff and cnt < 10):
                cnt += 1
            #
        else:
            print("inWaiting:  %d" % ser.inWaiting())
            print("outWaiting: %d" % ser.out_waiting) # weird
            print("Resp: 0x%02x" % sendEcho(0xff))
            while(ser.inWaiting() > 0):
                print("Waiting: 0x%02x" % ser.read(1))
            #
        #
    #
except EOFError:
    print()
    ser.close()
    exit(0)
#
# -[ Fini ]---------------------------------------------------------------------
