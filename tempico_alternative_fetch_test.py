# -*- coding: utf-8 -*-
"""
Created on Fri Aug  8 17:17:00 2025

@author: David Guzman @ Tausand
Goal: to test a new fetch function for Tempico TP1004, validating the received 
data structure and values.
"""

import pyTempico
import time



##Validation functions definition
def isValidNumberListRow(row):
    #single number list (read data) row validation
    #validations:
    #   *length of row
    #   *type of data (integers)
    #   *ch in range
    #   *seq in range
    #   *sorted stops
    #   *stops in range
    
    #TO DO: validate size of received data with nstops per channel    
    try:    
        length = len(row)
        ##Validate length of row
        if (length<4) or (length >8):  #0: ch, 1: seq, 2: start, 3: stop1, ..., 7: stop5
            print(row)
            print('error: length=',length)
            #discard this row
            return False #return: is NOT valid
    
        ch = row[0]
        seq = row[1]
        start = row[2]
        stops = row[3:]
        ##Validate all numbers are integers, except for the start register.
        if not all(isinstance(a, int) for a in [ch] + [seq] + stops):
            #looks if all elements in [ch],[seq] and stops are integers
            #if not, error found.
            #notice that [start] should be a float
            print(row)
            print('error: unexpected non-integer=',row)
            #discard this row
            return False #return: is NOT valid
        ##Validate channel number is within 1..ch_MAX
        if ch not in ch_range:
            print(row)
            print('error: ch=',ch)
            #discard this row
            return False #return: is NOT valid
        ##Validate sequential number is within 1..nruns_MAX
        if seq not in nruns_range:
            print(row)
            print('error: seq=',seq)
            #discard this row
            return False #return: is NOT valid
        
        ##Validate stop values are sorted
        stops_sorted = sorted(stops)#make a copy of stops and sort them
        if (stops != stops_sorted):
            #if stops are not ordered
            print(row)
            print('error: stops are not progressive=',stops)
            #discard this row
            return False #return: is NOT valid
        
        ##Validate stop values are in valid range stop_MIN..stop_MAX
        #Method 1:
        # if not (all(a>=stop_MIN for a in stops) and all(a<=stop_MAX for a in stops)):
        #     #if any stop is out of range, from stop_MIN to stop_MAX
        #     print(row)
        #     print('error: stop is out of valid range=',stops)
        #     #discard this row
        #     continue #discard and continue with next row    
        #Method 2 (faster than method 1):
        if (stops_sorted[0] < stop_MIN) or (stops_sorted[-1] > stop_MAX):
            #if any stop is out of range, from stop_MIN to stop_MAX
            print(row)
            print('error: stop is out of valid range=',stops)
            #discard this row
            return False #return: is NOT valid 
        ##All validations passed
        return True #otherwise return: is valid
    except Exception as e: 
        print(e)
        return False #failed to validate

def isValidConsecutiveNumberListRows(row,next_row):
    #pair of consecutive number list (read data) rows validation
    #validations:
    #   *length of next_row
    #   *sequential seq values
    #   *increasing start
    
    try:
        ###Validate continuity of data, comparing a row with the next one
        lengthnext = len(next_row)
        ##Validate next row length
        if (lengthnext < 3):    #required to have at least 0:ch, 1:seq, and 2: start.
            print(next_row)
            print('warning: next row length=',lengthnext)
            #can't compare, but do not discard this one; the wrong one is the next
            return True #return: is valid (there are not enough info to declare it as invalid)
        ch = row[0]
        seq = row[1]
        start = row[2]
        chnext = next_row[0]
        seqnext = next_row[1]
        startnext = next_row[2]
        ##Validate sequential number is incremented by one
        if ((seqnext - seq) != 1) and (ch == chnext):
            #if seq is not sequential, and channel is the same
            print(row)
            print(next_row)
            print('error: not consecutive seq=',seq,seqnext)
            #discard this row, not the next one
            return False #return: is NOT valid
        ##Validate start time is increasing
        if (startnext < start) and (ch == chnext):
            #if start is not incremental, and channel is the same
            print(row)
            print(next_row)
            print('error: not incrementing start=',start,startnext)
            #discard this row, not the next one
            return False #return: is NOT valid 
        
        ##All validations passed
        return True #otherwise return: is valid
    except Exception as e: 
        print(e)
        return False #failed to validate
    
def cleanNumberList(number_list):
    #removes non-valid elements of a Tempico dataset, given in number_list
    cleanlist = []
    try:        
        for line, nextline in zip(number_list,number_list[1:]): #get each line and the next one
            ##Validate single row contents of data
            if not isValidNumberListRow(line):
                #if validation is not passed, discard this row
                continue #discard and continue with next row
            
            ##Validate continuity of data, comparing this row with the next one
            if not isValidConsecutiveNumberListRows(line, nextline):
                #if validation is not passed, discard this row
                continue #discard and continue with next row
            
            ##Done all validations.
            #once that all validations are passed, append this line into clean list
            cleanlist.append(line)
    
        ##Validate last row by itself; the previous for loop removes the last row.
        lastline = number_list[-1]
        if isValidNumberListRow(lastline):
            #if all validations are passed, append this line into clean list
            cleanlist.append(lastline)    
        
        return cleanlist
    except Exception as e: 
        print(e)
        return cleanlist

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

my_device.setNumberOfRuns(1000)
my_device.setNumberOfStops(1, 5) #5 stops in channel A
my_device.setNumberOfStops(2, 1) #1 stops in channel B
my_device.setNumberOfStops(3, 3) #3 stops in channel C
my_device.setNumberOfStops(4, 5) #5 stops in channel D

print('\nsending a measure request to device')
datameas = my_device.measure()   #starts a measurement, and saves response in 'data'
print('measured data, in ps:',datameas)

##ALTERNATIVE FETCH STARTS HERE

print('Sending fetch request to device')
try:
    my_device.writeMessage('FETCH?')
    #TO DO: save measured data in local memory, and validate data
    datafetch = my_device.readMessage()
    listfetch = my_device.convertReadDataToNumberList(datafetch)
    print(listfetch)
    #return mylist
except Exception as e: 
    listfetch = []
    print(e)


print('Validating fetched data...')
ti = time.time() 
#declare global variables
ch_MAX = my_device.number_of_channels
ch_range = range(1,ch_MAX+1) #range starting in 1, ending in ch_MAX+1 exclusive (e.g. 4+1 ends in 4)
nruns_MAX = my_device.number_of_runs
nruns_range = range(1,nruns_MAX+1) #range starting in 1, ending in nruns_MAX+1 exclusive (e.g. 1000+1 ends in 1000)
stop_MIN = -1e6 #-1000000 for overflow in TP1204
stop_MAX =  5e9 #5ms

#create clean list
cleanlist = cleanNumberList(listfetch)   

tf = time.time()     
print('Time interval for validation:',tf-ti)    
#note: the maximum measured time interval for validation has been 20ms

##ALTERNATIVE FETCH ENDS HERE


my_device.close()            #close connection with device
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')