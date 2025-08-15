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

def isIdle(tempico_device):
    is_idle = False
    try:
        states = getStates(tempico_device)    
        
        #validate if state=1 (idle)
        if (set(states).issubset([1])) and (len(states) == my_device.number_of_channels): #if every item is '1'
            is_idle = True
    except Exception as e: 
        print(e)
        
    return is_idle

def isIdleOrDisabled(tempico_device):
    is_idle_or_disabled = False
    try:
        states = getStates(tempico_device)
        
        #validate if state=1 (idle) or state=0 (disabled)
        if (set(states).issubset([0,1])) and (len(states) == my_device.number_of_channels): #if every item is either '0' or '1'
            is_idle_or_disabled = True
    except Exception as e: 
        print(e)
            
    return is_idle_or_disabled

###Functions for this test only
def initialSettingsForThisTest(tempico_device):
    tempico_device.setDateTime()
    
    #configure a long measurement, with 1 channel disabled
    tempico_device.setNumberOfRuns(1000)
    tempico_device.setNumberOfStops(1, 5) #5 stops in channel A
    tempico_device.setNumberOfStops(2, 5) #5 stops in channel B
    tempico_device.setNumberOfStops(3, 5) #5 stops in channel C
    tempico_device.setNumberOfStops(4, 5) #5 stops in channel D
    tempico_device.disableChannel(3)


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



print('\nRESET TEST')
print('sending a measure request to device')
initialSettingsForThisTest(my_device)
datameas = my_device.measure()   #starts a measurement, and saves response in 'data'
# print('measured data, in ps:',datameas)

states_i = getStates(my_device)

### RESET TEST STARTS HERE
print('begin new reset routine')
ti = time.perf_counter()
num_try = 0
max_try = 3
min_wait_time_ms = 15 #wait 15ms is recommended to reset
reset_done = False
while(num_try < max_try) and (reset_done == False):
    num_try = num_try + 1 #keep counting number of trials
    my_device.writeMessage('*RST') #send a Reset request
    time.sleep(num_try*min_wait_time_ms/1000) #each try, wait longer than before
       
    #validate if state=1 (idle) after reset
    reset_done = isIdle(my_device)
tf = time.perf_counter()
### RESET TEST ENDS HERE

states_f = getStates(my_device)
print('Number of trials:',num_try)
print('Initial states are:',states_i)
print('Final states are:',states_f)
if reset_done:
    print('Reset done fine')
else:
    print('Reset failed')
print('time=',tf-ti)

print('\nTEST tempicoDevice.reset()')
print('sending a measure request to device')
initialSettingsForThisTest(my_device)
my_device.measure()
states_i = getStates(my_device)
ti = time.perf_counter()
my_device.reset()
tf = time.perf_counter()
states_f = getStates(my_device)
if my_device.isIdle():
    print('Reset done fine')
else:
    print('Reset failed')    

print('Initial states are:',states_i)
print('Final states are:',states_f)
print('time=',tf-ti)



initialSettingsForThisTest(my_device)
print('\nABORT TEST')
print('sending a measure request to device')
my_device.measure()
states_i_abort = getStates(my_device)

### ABORT TEST STARTS HERE
print('begin new abort routine')
ti = time.perf_counter()
num_try = 0
max_try = 3
min_wait_time_ms = 8 #wait 8ms is recommended to abort
abort_done = False
while(num_try < max_try) and (abort_done  == False):
    num_try = num_try + 1 #keep counting number of trials
    my_device.writeMessage('ABORT') #send an Abort request
    time.sleep(num_try*min_wait_time_ms/1000) #each try, wait longer than before
    
    #validate if state=1 (idle) or state=0 (disabled) after aborting
    abort_done = isIdleOrDisabled(my_device)

tf = time.perf_counter()
### ABORT TEST ENDS HERE

states_f_abort = getStates(my_device)
print('Number of trials:',num_try)
print('Initial states are:',states_i_abort)
print('Final states are:',states_f_abort)
if abort_done:
    print('Abort done fine')
else:
    print('Abort failed')
print('time=',tf-ti)


print('\nTEST tempicoDevice.abort()')
print('sending a measure request to device')
initialSettingsForThisTest(my_device)
my_device.measure()
states_i = getStates(my_device)
ti = time.perf_counter()
my_device.abort()
tf = time.perf_counter()
if my_device.isIdleOrDisabled():
    print('Abort done fine')
else:
    print('Abort failed')
    
states_f = getStates(my_device)
print('Initial states are:',states_i)
print('Final states are:',states_f)
print('time=',tf-ti)




my_device.close()            #close connection with device
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')