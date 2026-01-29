# -*- coding: utf-8 -*-
"""calibrateExample

    Created on Thu Jan 29 11:26 2026
    
    This script demonstrates how to calibrate a Tausand Tempico TP1200 device.
    
    In TP1000 the theoretical hardware delay is 0ns. Calibration has no effect.
    In TP1200 the theoretical hardware delay is 250ns. Calibration measures the 
    actual hardware delay, and adjusts the measurement values in consequence.
    
    Instructions: 
        * before running this example, pyTempico package must be installed.
        * change 'my_port' to your corresponding port.
        * run.
        
    You do **not** need a connected signal to run this example.

    This example:
        * opens connection to the device,
        * resets the device (optional step),
        * reads current hardware delays,
        * calibrates,
        * reads updated hardware delays,
        * closes connection.
    
    | @author: David Guzman, Tausand Electronics 
    | dguzman@tausand.com 
    | https://www.tausand.com
"""
import pyTempico

my_port = 'COM7' #change this port to your Tempico device's port

my_device = pyTempico.TempicoDevice(my_port)    #create object

try:
    print('opening connection with device in port',my_port)
    my_device.open()             #open connection with device
    if my_device.isOpen():
        print('connection with my_device is open')
    else:
        print('connection with my_device is close')
        raise Exception("Failed opening a conection in port "+my_port)

    print('\n1) Reseting device. This clears previous measurements, and changes settings to default values.')
    my_device.reset()
    
    #get the number of channels of the connected device
    my_number_of_channels = my_device.number_of_channels
    
    #Read current inner delay in each channel
    print('\n2) Read inner start-stop hardware delay.')
    for i in range(1,my_number_of_channels+1): #from 1 to 4 inclusive if TP1xx4
        print('      delay in channel',i,end='\t')
        print(my_device.getDelay(i),end='')
        print('ps')
        
    #Get last calibration time
    print(f"\nLast delay calibration via my_device.getLastDelaySync(): {my_device.getLastDelaySync()}")
    print(f"Last delay calibration (formatted): {my_device.getLastDelaySync(True)}")
        
    #Read current inner delay in each channel
    print('\n3) Request a calibration.')
    my_device.calibrateDelay()
    
    print('\n4) Read again inner start-stop hardware delay, after calibration.')
    for i in range(1,my_number_of_channels+1): #from 1 to 4 inclusive if TP1xx4
        print('      delay in channel',i,end='\t')
        print(my_device.getDelay(i),end='')
        print('ps')
    
    
    #Get last calibration time
    print(f"\nLast delay calibration via my_device.getLastDelaySync(): {my_device.getLastDelaySync()}")
    print(f"Last delay calibration (formatted): {my_device.getLastDelaySync(True)}")
    
    
    my_device.close()
    if my_device.isOpen():
        print('\nconnection with my_device is open')
    else:
        print('\nconnection with my_device is close')
    
except Exception as e:
    print(e)
    
finally:
    if my_device.isOpen():
        my_device.close() #close a connection, if it is still open