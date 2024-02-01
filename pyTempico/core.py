"""
Created on Jan 30 2024

@author: David Guzman @ Tausand
Core class and methods for PyTempico library.

Last edited on 2024-02-01.
"""

import serial

def prueba():
    return 'prueba ok'

class Tempico():
    def __init__(self,com_port):
        #Communication and identification parameters
        self.connected = False
        self.device = None
        self.idn = ""
        self.port = com_port
        self.serial_timeout = 1 #by default, 1 second of timeout
        self.sn = "N/A" #TO DO: get serial number
        self.__baudrate = 500000 #by default, 500kbaud
        self.__firmware = ""
        #Configuration parameters
        self.last_config_read = 0
        self.number_of_runs = 1 #by default, nruns=1. TO DO: read from device
        ##TO DO: add all configuration parameters
        #Measured data parameters
        ##TO DO: add parameters to save measured data
        
    
    ##open and closing connection methods
    def open(self):
        try:
            if self.connected == True:
                print('Device connection was already open.')
                print('Open request ignored.')
                #TO DO: raise exception/warning?
            else:
                desired_port = self.port
                self.device = serial.Serial(port = desired_port, baudrate=self.getBaudRate(), timeout=self.serial_timeout) # open serial port
                self.connected = self.device.is_open #gets if the device was connected from the serial object property 'is_open'
        except Exception as e:
            print('verify the device in port',desired_port
                  ,'is connected, is turned on, and is not being used by other software.')
            raise e
            return
    
    def openTempico(self):
        self.open()
        
    def close(self):
        try:
            if self.connected == True:
                self.device.close()  # close port
                self.connected = self.device.is_open #gets if the device was connected from the serial object property 'is_open'
            else:
                print("Device connection not opened. First open a connection.")
                print("Close request ignored.")
                #TO DO: raise expection?
        except Exception as e:
            print(e)
            
    def closeTempico(self):
        self.close()
    
    
    ##general requests methods
    def getBaudRate(self):
        return self.__baudrate
    
    def getFirmware(self):
        return self.__firmware
    
    def getIdn(self):
        if (self.connected == True) and (self.idn == ""):
            #try to read IDN from device
            self.readIdnFromDevice()
        elif (self.connected == False) and (self.idn == ""):
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
        try:
            txt = ''
            if self.connected == True:
                txt = self.device.readline() #reads bytes until a newline or a port timeout arrives
                txt = txt.decode() #convert bytes to string (decode)
                remaining_bytes = self.device.in_waiting
                if remaining_bytes > 0:
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
        
    def writeMessage(self,message):
        try:
            if message.find('\n') == -1:
                #no newline has been included in the message
                message = message + '\n' #append a newline char
            message_encoded = str.encode(message) #converts the string to bytes (encode)
            
            if self.connected == True:
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
            print("Data:",data)
            return "fetch"
        except Exception as e: 
            print(e)
    
    def measure(self):
        try:
            #TO DO: validate if a measurement is in progress, before 
            #requesting a new measurement
            self.writeMessage('MEAS?')
            #TO DO: save measured data in local memory, and validate data
            data = self.readMessage()
            print("Data:",data)
            return "measure"
        except Exception as e: 
            print(e)   
    