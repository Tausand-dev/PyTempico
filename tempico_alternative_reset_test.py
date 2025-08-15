# -*- coding: utf-8 -*-
"""
Created on Thu Aug 14 11:29:50 2025

@author: David Guzman @ Tausand
Goal: to test new reset and abort functions for Tempico TP1004, waiting
for the reset (abort) to be applied, and validating if the command has been 
correctly implemented.

Notes:
    States per channel:
      state=0  disabled.
      state=1  idle, enabled.
      state=10 while processing a reset.
      state=11 while processing an abort.
    other states are related with measurement process.
      
    Every channel goes to idle (state=1) after reset.
    Every channel goes to idle (state=1) or disabled (state=0) after abort.

"""

import pyTempico
import time

def getStatus(tempico_channel):
    status_dict = {}
    my_tempico = tempico_channel.parent_tempico_device
    if my_tempico.isOpen():
        #read from device and update local variable
        my_tempico.waitAndReadMessage() #to clear any previous response
        msg = 'STATus:CH'+str(tempico_channel.channel_number)+'?'
        #print(msg)
        my_tempico.writeMessage(msg)
        response = my_tempico.readMessage()
        if response != '':
            response = response.splitlines()
            response = response[0]
            #replace string format to dict assignment format
            #for example "FIELD=#,FIELD=#" to "{'FIELD':#,'FIELD':#"}"
            response=response.replace('=','\':').replace(',',',\'')
            response='{\''+response+'}'
            status_dict=eval(response) #save response string as a Python dict
            if (len(status_dict) < 10): #if dict contains less than 10 fields
                #TO DO: rise exception, or retry
                print('Failed.')
        else:
            #TO DO: rise exception, or retry
            print('Failed.')
        return status_dict
    

def getStates(tempico_device):
    states=[]
    try:
        ch1_status = getStatus(my_device.ch1)
        ch2_status = getStatus(my_device.ch2)
        ch3_status = getStatus(my_device.ch3)
        ch4_status = getStatus(my_device.ch4)
        
        states = [ch1_status["STATE"],ch2_status["STATE"],
                  ch3_status["STATE"],ch4_status["STATE"]]
    except Exception as e: 
        print(e)    
    
    return states

########################
#Main code
########################

my_port = 'COM25' #change this port to your Tempico device's port
my_device = pyTempico.TempicoDevice(my_port)    #create object

print('opening connection with device in port',my_port)
my_device.open()             #open connection with device
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')
    
#print some details of connected device
print('\nSerial number: ',my_device.getSerialNumber())
print('IDN:           ',my_device.getIdn())
print('Firmware:      ',my_device.getFirmware())

my_device.setDateTime()

#configure a long measurement
my_device.setNumberOfRuns(1000)
my_device.setNumberOfStops(1, 5) #5 stops in channel A
my_device.setNumberOfStops(2, 5) #5 stops in channel B
my_device.setNumberOfStops(3, 5) #5 stops in channel C
my_device.setNumberOfStops(4, 5) #5 stops in channel D
my_device.disableChannel(3)


print('\nRESET TEST')
print('sending a measure request to device')
# datameas = my_device.measure()   #starts a measurement, and saves response in 'data'
# print('measured data, in ps:',datameas)

# ch1_status = getStatus(my_device.ch1)
# ch2_status = getStatus(my_device.ch2)
# ch3_status = getStatus(my_device.ch3)
# ch4_status = getStatus(my_device.ch4)
# states_initial = [ch1_status["STATE"],ch2_status["STATE"],ch3_status["STATE"],ch4_status["STATE"]]
states_initial = getStates(my_device)

### RESET TEST STARTS HERE
# print('sending a reset request')
#my_device.reset()
numTry = 0
maxTry = 3
reset_done = False
while(numTry < maxTry) or (reset_done == True):
    numTry = numTry + 1 #keep counting number of trials
    my_device.writeMessage('*RST') #send a Reset request
    time.sleep(0.016) #wait at least 16ms for a reset to be applied

    # ch1_status_after = getStatus(my_device.ch1)
    # ch2_status_after = getStatus(my_device.ch2)
    # ch3_status_after = getStatus(my_device.ch3)
    # ch4_status_after = getStatus(my_device.ch4)
    # states_after = [ch1_status_after["STATE"],ch2_status_after["STATE"],ch3_status_after["STATE"],ch4_status_after["STATE"]]
    
    states_after = getStates(my_device)
    
    #validate if state=1 (idle) after reset    
    if set(states_after).issubset([1]): #if every item is '1'
        reset_done = True
        break #reset done succesfully, get out of while

print('Number of trials:',numTry)
if reset_done:
    print('Reset done fine')
print('Initial states are:',states_initial)
print('Final states are:',states_after)

### RESET TEST ENDS HERE



my_device.setDateTime()

#configure a long measurement
my_device.setNumberOfRuns(1000)
my_device.setNumberOfStops(1, 5) #5 stops in channel A
my_device.setNumberOfStops(2, 5) #5 stops in channel B
my_device.setNumberOfStops(3, 5) #5 stops in channel C
my_device.setNumberOfStops(4, 5) #5 stops in channel D
my_device.disableChannel(3)

print('\nABORT TEST')
print('sending a measure request to device')
my_device.measure()
# ch1_status = getStatus(my_device.ch1)
# ch2_status = getStatus(my_device.ch2)
# ch3_status = getStatus(my_device.ch3)
# ch4_status = getStatus(my_device.ch4)
# states_i_abort = [ch1_status["STATE"],ch2_status["STATE"],ch3_status["STATE"],ch4_status["STATE"]]

states_i_abort = getStates(my_device)

### ABORT TEST STARTS HERE
numTry = 0
maxTry = 3
abort_done = False
while(numTry < maxTry) or (abort_done  == True):
    numTry = numTry + 1 #keep counting number of trials
    my_device.writeMessage('ABORT') #send an Abort request
    time.sleep(0.009) #wait at least 9ms for an abort to be applied
    
    # ch1_status_after = getStatus(my_device.ch1)
    # ch2_status_after = getStatus(my_device.ch2)
    # ch3_status_after = getStatus(my_device.ch3)
    # ch4_status_after = getStatus(my_device.ch4)    
    # states_f_abort = [ch1_status_after["STATE"],ch2_status_after["STATE"],ch3_status_after["STATE"],ch4_status_after["STATE"]]
    
    states_f_abort = getStates(my_device)
    #validate if state=1 (idle) or state=0 (disabled) after aborting
    if set(states_f_abort).issubset([0,1]): #if every item is either '0' or '1'
        abort_done  = True
        break #abort done succesfully, get out of while

print('Number of trials:',numTry)
if abort_done:
    print('Abort done fine')
print('Initial states are:',states_i_abort)
print('Final states are:',states_f_abort)

### RESET TEST ENDS HERE



my_device.close()            #close connection with device
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')