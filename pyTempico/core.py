"""
Created on Jan 30 2024

@author: David Guzman @ Tausand
Core class and methods for PyTempico library.

Last edited on 2024-02-05.
"""

import serial
import time


##Global variables. 
#Create, if they do not exist already
if not('last_id_tempico_device' in globals()):
    last_id_tempico_device = 0
if not('last_id_tempico_channel' in globals()):
    last_id_tempico_channel = 100   #begin at 100, to distinguish easily from device ids

#Create lists containing reference pointers to every created device and channel
if not('tempico_devices_list' in globals()):
    tempico_devices_list = []
if not('tempico_channels_list' in globals()):    
    tempico_channels_list = []


##Classes definitions

def prueba():
    return 'prueba ok'

class TempicoChannel():
    id_tempico_channel = 0
    id_tempico_device = 0 #every channel must have an associated device
    parent_tempico_device = None #pointer reference to parent object of TempicoDevice() class
    channel_number = 0
    #Channel configuration parameters
    average_cycles = 1
    enable = True
    mode = 1
    number_of_stops = 1
    start_edge = 'rise'
    stop_edge = 'rise'
    stop_mask = 0    
    def __init__(self,id_device,ch_num):
        #set Ch-ID as a consecutive number
        global last_id_tempico_channel
        new_id = last_id_tempico_channel + 1
        self.id_tempico_channel = new_id
        last_id_tempico_channel = new_id
        #append new object's pointer to global list
        global tempico_channels_list
        tempico_channels_list.append(self)
        #link to an existing TempicoDevice
        global tempico_devices_list
        self.id_tempico_device = id_device        
        if tempico_devices_list[-1].id_tempico_device == id_device:
            #Look for the last created TausandDevice. Validate if is the parent, and link.
            self.parent_tempico_device = tempico_devices_list[-1]
        #set channel number
        self.channel_number = ch_num
        
        
    
    #Method chao() for tests only. TO DO: Delete after testing.
    def chao(self):
        #example to access upper level class methods
        print('chao',self.channel_number)
        #find port of device
        dev_id = self.id_tempico_device
        this_port = ''
        my_tempico_dev = None
        global tempico_devices_list
        for d in tempico_devices_list:
            if d.id_tempico_device == dev_id:
                my_tempico_dev = d
                print(d) #print device object of TempicoDevice class
                this_port = d.port
                print(this_port)
        print('using id:     ',my_tempico_dev.getIdn())
        #other alternative, using parent_tempico_device reference
        print('using parent: ',self.parent_tempico_device.getIdn())
    
    def getAverageCycles(self):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen():
            #read from device and update local variable
            my_tempico.waitAndReadMessage() #to clear any previous response
            msg = 'CONF:CH'+str(self.channel_number)+':ACYC?'
            #print(msg)
            my_tempico.writeMessage(msg)
            response = my_tempico.readMessage()
            response = response.splitlines()
            response = int(response[0])
            if response > 0:
                 #update local variable
                 self.average_cycles = response
        return self.average_cycles
    
    def setAverageCycles(self,number):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen() == True:
            number = int(number) #coherce to an integer number
            if number <= 0:
                print('Parameter out of range. Must be a positive integer.')
            else:            
                msg = 'CONF:CH'+str(self.channel_number)+':ACYC ' + str(number)
                #print(msg)
                my_tempico.writeMessage(msg)
                
                #verify if an error message is issued by the device
                response = my_tempico.waitAndReadMessage()
                if response != '':
                    #an error or warning was found
                    #TO DO: rise exception
                    print(response.splitlines()[0])
                else:            
                    #validate if message was applied
                    new_acyc = self.getAverageCycles()
                    if new_acyc == number:
                        #ok
                        pass
                    else:
                        #TO DO: rise exception, or retry
                        print('Failed.')
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
            #TO DO: raise expection?
    
    def isEnabled(self):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen():
            #read from device and update local variable
            my_tempico.waitAndReadMessage() #to clear any previous response
            msg = 'CONF:CH'+str(self.channel_number)+':ENAB?'
            #print(msg)
            my_tempico.writeMessage(msg)
            response = my_tempico.readMessage()
            response = response.splitlines()
            try:
                response = bool(int(response[0])) #first convert to int, then to bool
                #update local variable
                self.enable = response
            except:
                #TO DO: rise exception, or retry
                print('Failed')
        return self.enable
    
    def disableChannel(self):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen() == True:
            msg = 'CONF:CH'+str(self.channel_number)+':ENAB 0' #0: disable
            #print(msg)
            my_tempico.writeMessage(msg)
            
            #verify if an error message is issued by the device
            response = my_tempico.waitAndReadMessage()
            if response != '':
                #an error or warning was found
                #TO DO: rise exception
                print(response.splitlines()[0])
            else:            
                #validate if message was applied
                if self.isEnabled() == False:
                    #ok, disabled
                    pass
                else:
                    #TO DO: rise exception, or retry
                    print('Failed.')
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
            #TO DO: raise expection?
    
    def enableChannel(self):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen() == True:
            msg = 'CONF:CH'+str(self.channel_number)+':ENAB 1' #1: enable
            #print(msg)
            my_tempico.writeMessage(msg)
            
            #verify if an error message is issued by the device
            response = my_tempico.waitAndReadMessage()
            if response != '':
                #an error or warning was found
                #TO DO: rise exception
                print(response.splitlines()[0])
            else:            
                #validate if message was applied
                if self.isEnabled() == True:
                    #ok, enabled
                    pass
                else:
                    #TO DO: rise exception, or retry
                    print('Failed.')
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
            #TO DO: raise expection?
    
    def getNumberOfStops(self):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen():
            #read from device and update local variable
            my_tempico.waitAndReadMessage() #to clear any previous response
            msg = 'CONF:CH'+str(self.channel_number)+':NST?'
            #print(msg)
            my_tempico.writeMessage(msg)
            response = my_tempico.readMessage()
            response = response.splitlines()
            response = int(response[0])
            if response > 0:
                 #update local variable
                 self.number_of_stops = response
        return self.number_of_stops
    
    def setNumberOfStops(self,number):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen() == True:
            number = int(number) #coherce to an integer number
            if number <= 0:
                print('Parameter out of range. Must be a positive integer.')
            else:            
                msg = 'CONF:CH'+str(self.channel_number)+':NST ' + str(number)
                #print(msg)
                my_tempico.writeMessage(msg)
                
                #verify if an error message is issued by the device
                response = my_tempico.waitAndReadMessage()
                if response != '':
                    #an error or warning was found
                    #TO DO: rise exception
                    print(response.splitlines()[0])
                else:            
                    #validate if message was applied
                    new_nst = self.getNumberOfStops()
                    if new_nst == number:
                        #ok
                        pass
                    else:
                        #TO DO: rise exception, or retry
                        print('Failed.')
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
            #TO DO: raise expection?
    
    def getMode(self):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen():
            #read from device and update local variable
            my_tempico.waitAndReadMessage() #to clear any previous response
            msg = 'CONF:CH'+str(self.channel_number)+':MODE?'
            #print(msg)
            my_tempico.writeMessage(msg)
            response = my_tempico.readMessage()
            response = response.splitlines()
            response = int(response[0])
            if (response == 1) or (response == 2):
                 #update local variable
                 self.mode = response
        return self.mode
    
    def setMode(self,number):
        #Valid modes: 1|2
        #Mode 1: Minimum start-stop time: 12ns. Maximum start-stop time: 500ns. 
        #Mode 2: Minimum start-stop time: 125ns. Maximum start-stop time: 4ms.
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen() == True:
            number = int(number) #coherce to an integer number
            if number <= 0:
                print('Parameter out of range. Must be a positive integer.')
            else:            
                msg = 'CONF:CH'+str(self.channel_number)+':MODE ' + str(number)
                #print(msg)
                my_tempico.writeMessage(msg)
                
                #verify if an error message is issued by the device
                response = my_tempico.waitAndReadMessage()
                if response != '':
                    #an error or warning was found
                    #TO DO: rise exception
                    print(response.splitlines()[0])
                else:            
                    #validate if message was applied
                    new_mode = self.getMode()
                    if new_mode == number:
                        #ok
                        pass
                    else:
                        #TO DO: rise exception, or retry
                        print('Failed.')
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
            #TO DO: raise expection?
            
    def getStartEdge(self):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen():
            #read from device and update local variable
            my_tempico.waitAndReadMessage() #to clear any previous response
            msg = 'CONF:CH'+str(self.channel_number)+':START:EDGE?'
            #print(msg)
            my_tempico.writeMessage(msg)
            response = my_tempico.readMessage()
            if response != '':
                response = response.splitlines()
                response = response[0]
                if (response == "RISE") or (response == "FALL"):
                    #ok
                    #update local variable
                    self.start_edge = response
                else:
                    #TO DO: rise exception, or retry
                    print('Failed.')
            else:
                #TO DO: rise exception, or retry
                print('Failed.')
        return self.start_edge 
    
    def setStartEdge(self,edge_type):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen() == True:
            if (edge_type.upper() == 'RISE') or (edge_type.upper() == 'RIS') or (edge_type == 1):
                edge_type = 'RISE'
            elif (edge_type.upper() == 'FALL') or (edge_type.upper() == 'FAL') or (edge_type == 0):
                edge_type = 'FALL'
            
            msg = 'CONF:CH'+str(self.channel_number)+':START:EDGE ' + str(edge_type)
            #print(msg)
            my_tempico.writeMessage(msg)
            
            #verify if an error message is issued by the device
            response = my_tempico.waitAndReadMessage()
            if response != '':
                #an error or warning was found
                #TO DO: rise exception
                print(response.splitlines()[0])
            else:            
                #validate if message was applied
                new_edge = self.getStartEdge()
                if new_edge == edge_type:
                    #ok
                    pass
                else:
                    #TO DO: rise exception, or retry
                    print('Failed.')
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
            #TO DO: raise expection?
    
    def getStopEdge(self):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen():
            #read from device and update local variable
            my_tempico.waitAndReadMessage() #to clear any previous response
            msg = 'CONF:CH'+str(self.channel_number)+':STOP:EDGe?'
            #print(msg)
            my_tempico.writeMessage(msg)
            response = my_tempico.readMessage()
            if response != '':
                response = response.splitlines()
                response = response[0]
                if (response == "RISE") or (response == "FALL"):
                    #ok
                    #update local variable
                    self.stop_edge = response
                else:
                    #TO DO: rise exception, or retry
                    print('Failed.')
            else:
                #TO DO: rise exception, or retry
                print('Failed.')
                
        return self.stop_edge 
    
    def setStopEdge(self,edge_type):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen() == True:
            if (edge_type.upper() == 'RISE') or (edge_type.upper() == 'RIS') or (edge_type == 1):
                edge_type = 'RISE'
            elif (edge_type.upper() == 'FALL') or (edge_type.upper() == 'FAL') or (edge_type == 0):
                edge_type = 'FALL'
            
            msg = 'CONF:CH'+str(self.channel_number)+':STOP:EDGE ' + str(edge_type)
            #print(msg)
            my_tempico.writeMessage(msg)
            
            #verify if an error message is issued by the device
            response = my_tempico.waitAndReadMessage()
            if response != '':
                #an error or warning was found
                #TO DO: rise exception
                print(response.splitlines()[0])
            else:            
                #validate if message was applied
                new_edge = self.getStopEdge()
                if new_edge == edge_type:
                    #ok
                    pass
                else:
                    #TO DO: rise exception, or retry
                    print('Failed.')
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
            #TO DO: raise expection?
            
    def getStopMask(self):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen():
            #read from device and update local variable
            my_tempico.waitAndReadMessage() #to clear any previous response
            msg = 'CONF:CH'+str(self.channel_number)+':STOP:MASK?'
            #print(msg)
            my_tempico.writeMessage(msg)
            response = my_tempico.readMessage()
            response = response.splitlines()
            response = int(response[0])
            if response > 0:
                 #update local variable
                 self.stop_mask = response
        return self.stop_mask
    
    def setStopMask(self,stop_mask_in_us):
        my_tempico = self.parent_tempico_device
        if my_tempico.isOpen() == True:
            number = stop_mask_in_us
            number = int(number) #coherce to an integer number
            if number < 0:
                print('Parameter out of range. Must be a non-negative integer.')
            else:            
                msg = 'CONF:CH'+str(self.channel_number)+':STOP:MASK ' + str(number)
                #print(msg)
                my_tempico.writeMessage(msg)
                
                #verify if an error message is issued by the device
                response = my_tempico.waitAndReadMessage()
                if response != '':
                    #an error or warning was found
                    #TO DO: rise exception
                    print(response.splitlines()[0])
                else:            
                    #validate if message was applied
                    new_mask = self.getStopMask()
                    if new_mask == number:
                        #ok
                        pass
                    else:
                        #TO DO: rise exception, or retry
                        print('Failed.')
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
            #TO DO: raise expection?


class TempicoDevice():       
    id_tempico_device = 0
    device = None
    ch1 = None
    ch2 = None
    ch3 = None
    ch4 = None
    #Communication and identification parameters        
    idn = ""
    port = ""    
    serial_timeout = 1 #by default, 1 second of timeout
    sn = "N/A" #TO DO: get serial number
    __baudrate = 500000 #by default, 500kbaud
    __connected = False
    __firmware = ""    
    #Configuration parameters
    number_of_channels = 4 #for Tempico TP1004, 4 channels.
    number_of_runs = 1 #by default, nruns=1.        
    threshold = 1 #by default, thr=1.00
    #Measured data parameters
    ##TO DO: add parameters to save measured data
    
    def __init__(self,com_port):
        #set Dev-ID as a consecutive number
        global last_id_tempico_device
        new_id = last_id_tempico_device + 1
        self.id_tempico_device = new_id
        last_id_tempico_device = new_id
        #append new object's pointer to global list
        global tempico_devices_list
        tempico_devices_list.append(self)
        #Communication and identification parameters        
        self.port = com_port         
        #create channels, and link to this device
        self.ch1 = TempicoChannel(new_id,1)
        self.ch2 = TempicoChannel(new_id,2)
        self.ch3 = TempicoChannel(new_id,3)
        self.ch4 = TempicoChannel(new_id,4)
    
    ##open and closing connection methods
    def open(self):
        try:
            if self.__connected == True:
                print('Device connection was already open.')
                print('Open request ignored.')
                #TO DO: raise exception/warning?
            else:
                desired_port = self.port
                self.device = serial.Serial(port = desired_port, baudrate=self.getBaudRate(), timeout=self.serial_timeout) # open serial port
                self.__connected = self.device.is_open #gets if the device was connected from the serial object property 'is_open'
        except Exception as e:
            print('verify the device in port',desired_port
                  ,'is connected, is turned on, and is not being used by other software.')
            raise e
            return
    
    def openTempico(self):
        self.open()
        
    def close(self):
        try:
            if self.__connected == True:
                self.device.close()  # close port
                self.__connected = self.device.is_open #gets if the device was connected from the serial object property 'is_open'
            else:
                print("Device connection not opened. First open a connection.")
                print("Close request ignored.")
                #TO DO: raise expection?
        except Exception as e:
            print(e)
            
    def closeTempico(self):
        self.close()
    
    def isOpen(self):
        return self.__connected
    
    ##general requests methods
    def getBaudRate(self):
        return self.__baudrate
    
    def getFirmware(self):
        return self.__firmware
    
    def getIdn(self):
        if (self.__connected == True) and (self.idn == ""):
            #try to read IDN from device
            self.readIdnFromDevice()
        elif (self.__connected == False) and (self.idn == ""):
            print("Device connection not opened. First open a connection.")
            print("Unable to get Idn.")
            #TO DO: raise expection?
        return self.idn
    
    def readIdnFromDevice(self):
        #expected format for IDN string: 'Tausand,Tempico TP1004,,1.0\r\n'
        self.writeMessage('*IDN?') #request IDN
        response = self.readMessage() #get response
        response = response.splitlines() #if several lines are read, split
        response_first_line = response[0]
        if len(response) > 0:
            #something was read
            splitted_response = response_first_line.split(',') #split first line by ','
            
            if len(splitted_response) == 4: #expected 4 words
                manufacturer_idn_string = splitted_response[0]  #e.g.: Tausand
                model_idn_string = splitted_response[1]         #e.g.: Tempico TP1004
                ##splitted_response[2] should be empty
                version_idn_string = splitted_response[3]       #e.g.: 1.0
                self.idn = manufacturer_idn_string + ' ' + model_idn_string
                self.__firmware = version_idn_string
            else:
                self.idn = response #save non-splitted string
        else:
            print("Device does not respond to *IDN? request. Idn has not been updated.")
            
        return self.idn
    
    def reset(self):
        try:
            self.writeMessage('*RST')
            #TO DO: validate if device has applied the reset request; if not, 
            #try again to reset.
        except Exception as e: 
            print(e)
    
    ##read and write via serial port methods
    def readMessage(self):
        ##This function reads a message from serial port. If no message is ready, it waits the port timeout, typically 1s.
        try:
            txt = ''
            if self.__connected == True:
                txt = self.device.readline() #reads bytes until a newline or a port timeout arrives
                txt = txt.decode() #convert bytes to string (decode)
                #remaining_bytes = self.device.in_waiting
                #if remaining_bytes > 0:
                if self.isPendingReadMessage():
                    #print('some bytes remaining:' + str(remaining_bytes))
                    txt = txt + self.readMessage() #read again and append, until port is empty
            else:
                print("Device connection not opened. First open a connection.")
                print("Unable to read message.")
                #TO DO: raise expection?                
            return txt
        except Exception as e:
            print(e)
            return ''
        
    def isPendingReadMessage(self):
        if (self.device.in_waiting > 0):
            return True
        else:
            return False
        
    def waitAndReadMessage(self,wait_time_ms=1):
        ##This function waits the specified time, and then reads a message from serial port if any. It does not wait for a port timeout.
        time.sleep(wait_time_ms/1000) #wait 1ms for a device response, if any
        response = ''
        if self.isPendingReadMessage():
            response = self.readMessage()
        return response        
        
    def writeMessage(self,message):
        try:
            if message.find('\n') == -1:
                #no newline has been included in the message
                message = message + '\n' #append a newline char
            message_encoded = str.encode(message) #converts the string to bytes (encode)
            
            if self.__connected == True:
                self.device.reset_input_buffer() #clear previous write messages residuals, if any
                self.device.write(message_encoded) # write in device port the message
            else:
                print("Device connection not opened. First open a connection.")
                print("Unable to write message.")
                #TO DO: raise expection?
                
        except Exception as e: 
            print(e)
            

    ##measure methods
    def fetch(self):
        try:
            self.writeMessage('FETCH?')
            #TO DO: save measured data in local memory, and validate data
            data = self.readMessage()
            mylist = self.convertReadDataToIntList(data)
            return mylist
        except Exception as e: 
            print(e)
    
    def measure(self):
        try:
            #TO DO: validate if a measurement is in progress, before 
            #requesting a new measurement
            self.writeMessage('MEAS?')
            #TO DO: save measured data in local memory, and validate data
            data = self.readMessage()
            mylist = self.convertReadDataToIntList(data)
            return mylist
        except Exception as e: 
            print(e)   
            
    def convertReadDataToIntList(self,data_string):
        #convert a read data message string to a 2D-list with integer numbers
        #
        #The response of Tempico FETCH?/MEAS? is in the following format:
        #    channel,run,start_time_us,stop_ps1,...,stop_psN;channel,...,stop_psN;...\r\n
        #where:
        #   'run' goes from 1 to NumberOfRuns,
        #   'N' is the NumberOfStops,
        #   every value in the message is an integer.
        data_list = []
        if data_string != '':
            d = data_string.splitlines() #split lines, to remove \r\n chars
            d0 = d[0] #take only first line; ignore additional lines
            d0=d0.split(';') #split data into rows
            for row in d0:
                if len(row) > 0:
                    #separate cols by ',' and convert to integers
                    int_row = [int(x) for x in row.split(',')] 
                else:
                    #if empty row, write empty (do not try to convert to int)
                    int_row = []
                #append integer row to data_list
                data_list.append(int_row) 
            
            if len(d) > 1:
                #if a second line exists, a warning/error message has arrived
                for extraline in d[1:]: #from 2nd to end
                    print(extraline)
                #TO DO: rise exception

        return data_list
            
    ##settings methods
    def getSettings(self):
        try:
            self.writeMessage('CONF?')
            data = self.readMessage()
            data = data.splitlines() #save as a list of lines. Ideally, a single line is read.
            
            #The response of Tempico is in the following format:
            #    CH1:ACYC 1;CH1:ENAB 1;CH1:NST 1;...;CH4:STOP:MASK 0;NRUN 1;THR 1.00
            if len(data) > 0: #if a response was received
                data = data[0]  #assume response is obtained in the first line
                #TO DO: validate if several lines were received, which one is the answer for conf? request
                #First step: split by semicolons (;)
                data = data.split(';')
                for s in data:
                    txt = s.split(' ') #split by blank space
                    config_name = txt[0]
                    config_value = txt[1]
                    if config_name == "NRUN":
                        self.number_of_runs = config_value
                    if config_name == "THR":
                        self.threshold = config_value
                    if config_name.startswith("CH"):
                        #get number of channel
                        first_sep = config_name.find(':')
                        numch = config_name[2:first_sep] #e.g. CH3:STAR:EDG
                        #remove prefix with number of channel from config_name
                        config_name = config_name[first_sep+1:]
                        
                        numch = int(numch)
                        
                        if numch == 1:
                            mych = self.ch1
                        elif numch == 2:
                            mych = self.ch2
                        elif numch == 3:
                            mych = self.ch3
                        elif numch == 4:
                            mych = self.ch4
                        else:
                            mych = None
                            
                        
                        if int(numch) <= self.number_of_channels:
                            if config_name == "ACYC":
                                mych.average_cycles = int(config_value)
                            elif config_name == "ENAB":
                                #required first converting to int, then converting to bool
                                mych.enable = bool(int(config_value)) 
                            elif config_name == "NST":
                                mych.number_of_stops = int(config_value)
                            elif config_name == "MODE":
                                mych.mode = int(config_value)
                            elif config_name == "STAR:EDG":
                                mych.start_edge = config_value
                            elif config_name == "STOP:EDG":
                                mych.stop_edge = config_value
                            elif config_name == "STOP:MASK":
                                mych.stop_mask = int(config_value)
            #print("Data:",data)
            return data
        except Exception as e: 
            print(e)
            
    def getNumberOfRuns(self):
        if self.isOpen():
            #read from device and update local variable
            self.waitAndReadMessage() #to clear any previous response
            msg = 'CONF:NRUN?'
            self.writeMessage(msg)
            response = self.readMessage()
            response = response.splitlines()
            response = int(response[0])
            if response > 0:
                #update local variable
                self.number_of_runs = response
        return self.number_of_runs
    
    def setNumberOfRuns(self,number):
        if self.isOpen() == True:
            number = int(number) #coherce to an integer number
            if number <= 0:
                print('Parameter out of range. Must be a positive integer.')
            else:            
                msg = 'CONF:NRUN ' + str(number)
                #print(msg)
                self.writeMessage(msg)
                
                #verify if an error message is issued by the device
                response = self.waitAndReadMessage()
                if response != '':
                    #an error or warning was found
                    #TO DO: rise exception
                    print(response.splitlines()[0])
                else:            
                    #validate if message was applied
                    new_nruns = self.getNumberOfRuns()
                    if new_nruns == number:
                        #ok
                        pass
                    else:
                        #TO DO: rise exception, or retry
                        print('Failed.')
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
            #TO DO: raise expection?
            
    def getThresholdVoltage(self):
        if self.isOpen():
            #read from device and update local variable
            self.waitAndReadMessage() #to clear any previous response
            msg = 'CONF:THR?'
            self.writeMessage(msg)
            response = self.readMessage()
            response = response.splitlines()
            response = float(response[0])
            if response > 0:
                #update local variable
                self.threshold = response
        return self.threshold
    
    def setThresholdVoltage(self,desired_voltage):
        #Valid desired_voltage parameters are MINimum|MAXimum|DOWN|UP or a number from 0.90 to 1.60.
        
        if self.isOpen() == True:
            #try to convert to a float
            try:
                desired_voltage = float(desired_voltage) #coherce to a float number
            except:
                pass
            
            msg = 'CONF:THR ' + str(desired_voltage)
            self.writeMessage(msg)
            
            #verify if an error message is issued by the device
            response = self.waitAndReadMessage()
            if response != '':
                #an error or warning was found
                #TO DO: rise exception
                print(response.splitlines()[0])
            else:            
                #validate if message was applied
                new_thr = self.getThresholdVoltage()
                if type(desired_voltage) == float:
                    if round(new_thr*10) == round(desired_voltage*10):
                        #if desired and real voltages are close by 0.1
                        #ok
                        pass
                    else:
                        print('Failed')
                        #TO DO: rise exception, or retry
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
            #TO DO: raise expection?
    
    def decrementThresholdVoltage(self):
        self.setThresholdVoltage("DOWN")
    
    def incrementThresholdVoltage(self):
        self.setThresholdVoltage("UP")
    
    def setThresholdVoltageToMaximum(self):
        self.setThresholdVoltage("MAX")
        
    def setThresholdVoltageToMinimum(self):
        self.setThresholdVoltage("MIN")