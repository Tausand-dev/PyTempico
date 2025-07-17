# -*- coding: utf-8 -*-
"""singleMeasureExample

    Created on Tue May  7 09:23 2024
    
    Connects to a Tausand Tempico device, starts a measurement and reads the 
    results.
    
    Instructions: 
        * before running this example, pyTempico package must be installed.
        * change 'my_port' to your corresponding port.
        * connect signals to your Tempico Device. If no signals are measured, 
        this example will return an empty data array.
        * run.
    
    | @author: David Guzman at Tausand Electronics 
    | dguzman@tausand.com 
    | https://www.tausand.com
"""

import pyTempico

my_port = 'COM16' #change this port to your Tempico device's port

my_device = pyTempico.TempicoDevice(my_port)    #create object

print('opening connection with device in port',my_port)
my_device.open()             #open connection with device
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')

print('sending a measure request to device')
data = my_device.measure()   #starts a measurement, and saves response in 'data'
print('measured data, in ps:',data)

my_device.close()            #close connection with device
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')