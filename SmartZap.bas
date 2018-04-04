REM ****************************************************************************
REM *                                                                          *
REM ****************************************************************************
REM
REM ****************************************************************************
REM ****************************************************************************
REM
REM ****************************************************************************
REM ****************************************************************************
REM
'
' #
' # Memory set up to replace the dim stor$
' #
'
Resvmem=70*1024
Reserve Fre(0)-Resvmem

Deffn Malloc(A)=Gemdos(72,L:A)
Deffn Mfree(A)=Gemdos(73,L:A)
Deffn Set_port(A,S,C)=Xbios(15,A,B,C,-1,-1,-1)
Deffn Current_drive=Gemdos(&H19)
'
Version=2.1
'
Promsize=&10000 ! * 64k + 1
Prom_addr=Fn Malloc(Promsize)
Gosub Promfill
'
Hidem ! * some kind of a bug has asisen where the hide/show mouse
Showm ! * routine doesn't work until after you've done a hidem
Hidem ! * shown and another hidem. Then the routines seem to work fine.
'
' #
' # Set the serial port to 9600 baud and RTS/CTS/
' #
'
Baud=1 ! * 9600 baud
Cntl=2 ! * RTS/CTS
Ucr=136 ! * 8 data bits. 1 stop, No Parity
Void=Fn Set_port(Baud,Cntl,Ucr)
'
' #
' # change to the current drive
' #
'
Drive=Fn Current_drive
Chdrive Drive+1 ! * current_drive returns drive starting at 0 instead of 1
Chdir '\' ! * change to the root directory
On Drive+1 A_drive,B_Drive,C_drive,D_drive
'
' #
' # Initialize the variables and stuff
' #
'
Cls
Begint=0
Zendt=0
N$='NONE'
O$='NONE'
C$='NONE'
Xx=0
'
' #
' # Wait for keyboard input ****************************************************
' #
'
Print
Print Tab(22);'ST is now set for 9600 baud, RTS/CTS.'
Print Tab(19);'Set the DIP switches to : 1-7 ON and 8 OFF.'
Print Tab(14);'Turn on Smart Zap and hit the space bar to continue.'
Box 0,0,639,80
Box 2,2,637,78
'
Gtkey:
Repeat
  A$=Inkey$
  If A$=Chr$(&F1A) ! * ^Z WILL exiy the hole program
    Gosub Finish
  Endif
Until A$=" "
'
' #
' # Open the port **************************************************************
' #
'
Open "r",#1,"AUX:"
Open "r",#2,"CON:"
'
' #
' # Clear the port *************************************************************
' #
'
Print
Print
Print Tab(33);"CLEARING PORT"
On
  A=Inp?(1)
  Exit If A=0
  Void=Inp(1)
Loop
Print Tab(34);'PORT CLEARED'
Print
'
' #
' # Send $FF out and wait for the echo *****************************************
' #
'
A=255
Out 1,A
Repeat
  A=Inp?(1)
Until A=1
A=Inp(1)
'
' #
' # Start of main routine Menu *************************************************
' #
'
Gmsub1:
Gosub Zread
Gmenu:
Gosub Zmenu
Gosub Gk1
Gosub Toupper
A=&H61
Gosub Zout
'
' #
' # CLI ************************************************************************
' #
'
' # Zap
'
If A$='Z' then
  Command=&HF0
  Temp=1
  Goto Zap
Endif
'
' # Verify
'
If A$='V' Then
  Command=&HF5
  Temp=0
  Goto Zap
Endif
'
' # Erase Check
'
if A$='E' Then
  Print At(11,23);'Checking PROM';
  Bad=0
  A=&HF6
  Gosub Zout
  A=&H50
  Gosub Zout
  If Bad=0
    Print At(11,23);'Erase Check - O.K.";
    Goto Zwaitkey
  Endif
Endif
'
' # Upload
'
If A$ = 'U' Then
  Goto Upload
Endif
'
' # Save to disk
'
If A$ = 'S' Then
  Goto Zsave
Endif
'
' # Load from disk
'
If A$ = 'L' Then
  Goto Zload
Endif
'
' # Change
'
If A$ = 'C' Then
  Goto Change
Endif

'
' # Exit program
'
If A$ = Chr$(&H18) Then
  Showm
  Goto Finish
Endif
'
' # Print to Screen
'
If A$ = 'P' Then
  Goto Zedit
Endif
'
' # Fill STOR$ with $FF
'
If A$ = 'F' Then
  Goto Zfill
Endif
'
' # Directory listing
'
If A$ = 'D' Then
  Goto Zdir
Endif
'
' # Information
'
If A$ = 'I' Then
  Goto Zinfo
Endif
'
' # Clean EEPROM
'
If A$ = 'A' AND Ee=1 Then
  Gosub Zfill2
  Command=&HF0
  Goto Zap
Endif
'
' #
' # Not a command, ring bell
' #
'
Print Chr$(7)
Goto Gmenu
'
' #
' # Command code for ID module read ********************************************
' #
'
Procedure Zread
  A=&HFB
  Gosub Zout
  Gosub Zin
  Module=A
  If A>15 And A<32
    Ee=1
  Else
    Ee=0
  Endif
  Gosub Zin
  Beginh=A
  Gosub Zin
  Beginl=A
  Gosub Zin
  Zendh=A
  Gosub Zin
  Zendl=A
  Begint=Beginh*256+Beginl
  Zendt=Zendh*256+Zendl
  Zsize=Zendt-Zbegin+1
Return
'
' #
' # Output to zapper and wait for echo *****************************************
' #
'
Procedure Zout
  Out #1,A
  B=0
  Repeat
    B=Inp?(1)
  Until B=-1
  X1=Inp(1)
  '
  If A<>X1
    Bad=1
    Gosub Zerr
  Endif
  '
Return
'
' #
' # Input from zapper then echo back *******************************************
' #
'
Procedure Zin
  Gosub Zin2
  Out #1,A
Return
'
' #
' # An error occured just get the error message ********************************
' #
'
Procedure Zin2
  A=0
  Do
    A=Inp?(1)
    Exit If A=-1
    Ch$=Inpkey
    If Ch$=$(&HAA) ! * ^X
      Gosub Finish
    Endif
  Loop
  '
  A=Inp(1)
Return
'
' #
' # Print error message ********************************************************
' #
'
Procedure Zerr
  Cls
  Print
  Print Tab(20);'Error in echo back ** maybe the PROM failed'
  Print Tab(17);'Failed address            Data sent      Data Prom'
  Gosub Zin2
  N=A*256
  Gosub Zin2
  N=N+A
  Print Tab(23);Hex$(N);
  Gosub Zin2
  Print Tab(47);Hex$(A);
  Gosub Zin2
  Print Tab(62);Hex$(A)
  Print
  Print Hex$(Xx), Hex$(Tbyte)
  Box 0,0,639,76
  Box 2,2,637,76
  Gosub Zwait
    X=Zendt*2
  Bad=1
Return
'
' #
' # Zap and verify *************************************************************
' #
' #
' # Rewritten 03/01/88
' #
'
Zap:
Bar=0
'
' #
' # ****************************************************************************
' #
'
'
' #
' # ****************************************************************************
' #
'
'
' #
' # ****************************************************************************
' #
'
'
' #
' # ****************************************************************************
' #
'
'
' #
' # ****************************************************************************
' #
'
'
' #
' # ****************************************************************************
' #
'

REM *[ Fini ]*******************************************************************
