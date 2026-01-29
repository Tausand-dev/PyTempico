# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 11:54:18 2024

@author: David Guzman @ Tausand
Goal: to make some initial tests communicating with a Tausand Tempico TP1004 
device. This should serve as basis for PyTempico library.

Last edited on 2024-01-24.
"""

import serial

#Define local constants
MYPORT = 'COM6' #change this to the corresponding port
MYBAUDRATE = 500000 #in bauds, do not change

###Function definitions
def openTempico(desired_port):
    try:
        device = serial.Serial(port = desired_port, baudrate=MYBAUDRATE, timeout=1) # open serial port
        return device
    except Exception as e:
        print('double check the port in variable MYPORT, verify that the device'
              ,'is turned on and not being used by other software.')
        raise e
        return
    
def writeMessage(device,message):
    try:
        if message.find('\n') == -1:
            #no newline has been included in the message
            message = message + '\n' #append a newline char
        message_encoded = str.encode(message) #converts the string to bytes (encode)
        device.reset_input_buffer() #clear previous write messages residuals, if any
        device.write(message_encoded) # write in device port the message
    except Exception as e: 
        print(e)

def readMessage(device):
    try:
        txt = device.readline() #reads bytes until a newline or a port timeout arrives
        txt = txt.decode() #convert bytes to string (decode)
        remaining_bytes = device.in_waiting
        if remaining_bytes > 0:
            #print('some bytes remaining:' + str(remaining_bytes))
            txt = txt + readMessage(device) #read again and append, until port is empty    
        return txt
    except Exception as e:
        print(e)
        return ''

def closeTempico(device):
    try:
        device.close()  # close port
    except Exception as e:
        print(e)



###Main function
try:
    print('Opening port...')
    tempicoDevice = None
    tempicoDevice = openTempico(MYPORT)
    if (tempicoDevice != None):
        print("port name is " + tempicoDevice.name)         # check which port was really used
    
    ##send a mesurement request
    writeMessage(tempicoDevice,'MEAS?')
    print("MEAS response is "+readMessage(tempicoDevice))
    
    ##send an IDN request, and read it
    writeMessage(tempicoDevice,'*IDN?')
    print("IDN is "+readMessage(tempicoDevice))
     
    ##send an CONF? request, and read it
    writeMessage(tempicoDevice,'CONF?')
    print("CONF is "+readMessage(tempicoDevice))
    
    ##send a reset request
    writeMessage(tempicoDevice,'*RST')

except Exception as e:
    print(e)

finally:
    #always try to close the port at the end of the routine
    print('Closing port...')
    closeTempico(tempicoDevice)
    print('Done')
