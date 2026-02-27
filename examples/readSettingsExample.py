# -*- coding: utf-8 -*-
"""readSettingsExample

    Created on Tue May  7 09:49 2024
    
    Connects to a Tausand Tempico device and reads its settings.
    
    Instructions: 
        * before running this example, pyTempico package must be installed.
        * change 'my_port' to your corresponding port.
        * run.
    
    | @author: David Guzman, Tausand Electronics 
    | dguzman@tausand.com 
    | https://www.tausand.com
"""

import pyTempico

my_port = 'COM7' #change this port to your Tempico device's port

my_device = pyTempico.TempicoDevice(my_port)    #create object

print('opening connection with device in port',my_port)
my_device.open()             #open connection with device
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')

print('\n1) reading general getSettings')
my_settings = my_device.getSettings()
print('settings:')
print(my_settings)

print('\n2) reading specific settings')
print('NumberOfRuns:', my_device.getNumberOfRuns())
print('ThresholdVoltage:', my_device.getThresholdVoltage())

print('\n2.1) reading channel specific settings')
print('Ch1 AverageCycles:', my_device.ch1.getAverageCycles())
print('Ch2 AverageCycles:', my_device.ch2.getAverageCycles())
print('Ch3 AverageCycles:', my_device.ch3.getAverageCycles())
print('Ch4 AverageCycles:', my_device.ch4.getAverageCycles())
print('Ch1 Mode:', my_device.ch1.getMode())
print('Ch1 NumberOfStops:', my_device.ch1.getNumberOfStops())
print('Ch1 isEnabled:', my_device.ch1.isEnabled())
print('Ch1 StartEdge:', my_device.ch1.getStartEdge())
print('Ch1 StopEdge:', my_device.ch1.getStopEdge())
print('Ch1 StopMask:', my_device.ch1.getStopMask())

print('\n2.2) alternative method reading channel specific settings')
print('Ch1 AverageCycles:', my_device.getAverageCycles(1))
print('Ch2 AverageCycles:', my_device.getAverageCycles(2))
print('Ch3 AverageCycles:', my_device.getAverageCycles(3))
print('Ch4 AverageCycles:', my_device.getAverageCycles(4))
print('Ch1 Mode:', my_device.getMode(1))
print('Ch1 NumberOfStops:', my_device.getNumberOfStops(1))
print('Ch1 isEnabled:', my_device.isEnabled(1))
print('Ch1 StartEdge:', my_device.getStartEdge(1))
print('Ch1 StopEdge:', my_device.getStopEdge(1))
print('Ch1 StopMask:', my_device.getStopMask(1))

print('\nclosing connection with device in port',my_port)
my_device.close()            #close connection with device
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')