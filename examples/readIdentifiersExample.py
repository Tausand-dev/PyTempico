# -*- coding: utf-8 -*-
"""readIdentifiersExample

    Created on Thu Jan 29 11:03 2026
    
    Connects to a Tausand Tempico device and reads its identifier strings.
    
    Instructions: 
        * before running this example, pyTempico package must be installed.
        * change 'my_port' to your corresponding port.
        * run.
        
    You do **not** need a connected signal to run this example.

    This example:
        * opens connection to the device,
        * uses get methods to read identifier strings,
        * closes connection.
    
    | @author: David Guzman, Tausand Electronics 
    | dguzman@tausand.com 
    | https://www.tausand.com
"""
import pyTempico

my_port = 'COM7' #change this port to your Tempico device's port

my_device = pyTempico.TempicoDevice(my_port)    #create object

#Open connection
print('opening connection with device in port',my_port)
my_device.open()             #open connection with device
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')

#Use get methods to obtain identifier strings of a Tausand Tempico device
my_idn = my_device.getIdn()
my_model_idn = my_device.getModelIdn()
my_serial_number = my_device.getSerialNumber()
my_firmware = my_device.getFirmware()

#Print string identifiers
print('\nIDN string:\t\t',my_idn)
print('Model IDN:\t\t',my_model_idn)
print('Serial number:\t',my_serial_number)
print('Firmware:\t\t',my_firmware)

#Close connection
my_device.close()
if my_device.isOpen():
    print('\nconnection with my_device is open')
else:
    print('\nconnection with my_device is close')