"""
Created on Jan 30 2024

| @author: David Guzman at Tausand Electronics 
| dguzman@tausand.com 
| https://www.tausand.com

Core class and methods for PyTempico library. 

To use with Tausand Electronics' Time-to-Digital Converters (TDCs) of the 
family *Tausand Tempico*.
"""

import serial
import time
import hid
import serial.tools.list_ports
import os
from datetime import datetime


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

def simpletest():
    """ simple function for tests
        
        Args:
            none
        Returns:
            str: 'simple test ok'

    """
    return 'simple test ok'



class TempicoDevicesSearch():
    """
    A class for discovering Tempico devices.

    This class provides methods to search for Tempico devices in a network or connected system.
    """
    def __init__(self):
        pass
    
    def getVidPid(self,vid_pid_information):
        """
        Extracts the Vendor ID (VID) and Product ID (PID) from a string and returns them as a tuple.

        This function processes a string that contains the VID and PID information in the format 
        'VID:PID=xxxx:yyyy'. It splits the string and retrieves the VID and PID values, returning 
        them as a tuple of strings.

        :param vid_pid_information: A string containing the VID and PID information.
        :type vid_pid_information: str
        :returns: A tuple containing the VID and PID as strings (vid, pid).
        :rtype: tuple
        """
        without_spaces = vid_pid_information.split(' ')
        tuple = ()
        key_word = 'VID:PID'
        for i in without_spaces:
            if key_word in i:
                vid_pid_value = i.split('=')
                numbers_value = vid_pid_value[1].split(":")
                vid = numbers_value[0]
                pid = numbers_value[1]
                tuple = (vid, pid)
        return tuple
    
    def findDevices(self):
        """
        Finds and verifies whether a device with the given VID and PID is a Tempico device.

        This function takes the Vendor ID (VID) and Product ID (PID) as inputs, converts them to integers, 
        and attempts to open the device using these values. It then checks if the manufacturer and product 
        strings match the expected values for a Tempico device.

        :param vid_s: The Vendor ID (VID) of the device in string format.
        :type vid_s: str
        :param pid_s: The Product ID (PID) of the device in string format.
        :type pid_s: str
        :returns: `True` if the device is a Tempico, `False` otherwise.
        :rtype: bool
        """
        ports = []
        portsFound = serial.tools.list_ports.comports()
        if not portsFound:
            print("No serial ports found.")
        else:
            bluetoothWord = "Bluetooth"
            for port in portsFound:
                if bluetoothWord not in port.description:
                    vidPidString = port.hwid
                    valuesPacket = self.getVidPid(vidPidString)
                    if len(valuesPacket) == 2:
                        value = self.verifyPyTempico(valuesPacket)
                        if value == True and os.name!="posix":
                            ports.append(port.name)
                if "Tempico" in port.description and os.name!= "posix":
                    ports.append(port.device)
                elif "Tempico" in port.description and os.name== "posix":
                    ports.append(port.device)
        return ports


    def verifyPyTempico(self,tuple_vid_pid):
        """
        Verifies whether the connected device is a Tempico device.

        This function checks if the device’s Vendor ID (VID) and Product ID (PID) match the values 
        corresponding to a Tempico device. It returns `True` if the device is identified as a Tempico, 
        and `False` otherwise.

        :param tuple_vid_pid: A tuple containing the VID and PID of the device.
        :type tuple_vid_pid: tuple
        :returns: `True` if the device is a Tempico, `False` otherwise.
        :rtype: bool
        """
        vid = tuple_vid_pid[0]
        pid = tuple_vid_pid[1]
        if vid == "04D8" and pid == "00DD":
            value = self.tryOpenDevices(vid, pid)
        else:
            value = self.tryOpenDevices(vid, pid)
        return value

    def tryOpenDevices(self,vid_s, pid_s):
        """
        Finds and verifies whether a device with the given VID and PID is a Tempico device.

        This function takes the Vendor ID (VID) and Product ID (PID) as inputs, converts them to integers, 
        and attempts to open the device using these values. It then checks if the manufacturer and product 
        strings match the expected values for a Tempico device.

        :param vid_s: The Vendor ID (VID) of the device in string format.
        :type vid_s: str
        :param pid_s: The Product ID (PID) of the device in string format.
        :type pid_s: str
        :returns: `True` if the device is a Tempico, `False` otherwise.
        :rtype: bool
        """
        vid = int(vid_s, 16)
        pid = int(pid_s, 16)

        try:
            h = hid.device()
            h.open(vid, pid)
            Manufacturer = h.get_manufacturer_string()
            Product = h.get_product_string()
            if Manufacturer == "Tausand electronics" and "Tempico" in Product:
                h.close()
                return True
            else:
                h.close()
                return False
        except:
            return False


class TempicoChannel():
    """Single channel on a Tempico Device.
    
    To modify or access attributes, **please use methods**. For example, to get 
    average cycles on channel 2,
    
    >>> my_tempico_device_object.ch2.getAverageCycles()
    
    or, as an alternative, send the channel number as a parameter
    
    >>> my_tempico_device_object.getAverageCycles(2)
    
    Changing attributes without using methods, do not change the actual 
    parameters in the device.
    
    Accesing attributes without using methods, returns values registered in 
    local memory that may not be updated.
    
    Attributes:
        id_tempico_channel (int): Unique identifier for a :func:`~pyTempico.core.TempicoChannel`
            object.
        id_tempico_device (int): Identifier of the :func:`~pyTempico.core.TempicoDevice` linked to this
            :func:`~pyTempico.core.TempicoChannel` object.
        average_cycles (int): Average cycles.
        channel_number (int): Number of the channel in the device (1=A, 2=B,...).
        enable (bool): True when the channel is enabled.
        mode (int): Measurement mode. 1|2.
        
            * 1: Short measurement range. Start-stop times from 12ns to 500ns.
            * 2: Large measurement range. Start-stop times from 125ns to 4ms.

        number_of_stops (int): Number of stop pulses expected after a 
            start pulse arrives. 1..5.
        parent_tempico_device (TempicoDevice): Pointer reference to parent 
            object of :func:`~pyTempico.core.TempicoDevice` class.
        start_edge (str): Edge type on the start pulse used to begin timing.
            RISE|FALL.
        stop_edge (str): Edge type on the stop pulses used to end timing.
            RISE|FALL.
        stop_mask (int): Time that stop pulses are ignored after receiving a 
            start pulse on the TDC. Value in microseconds. 0..4000.
    
    """
    id_tempico_channel = 0
    id_tempico_device = 0 #every channel must have an associated device
    parent_tempico_device = None #pointer reference to parent object of TempicoDevice() class
    channel_number = 0
    #Channel configuration parameters
    average_cycles = 1
    enable = True
    mode = 1
    number_of_stops = 1
    start_edge = 'RISE'
    stop_edge = 'RISE'
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
            #Look for the last created TempicoDevice. Validate if is the parent, and link.
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
        """Returns the average cycles of the TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, average cycles = 1 (no multi-cycle averaging).
        
        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        request the device for the value. If not, the most recent value is 
        returned.
        
        Args:
            (none)
    
        Returns:
            integer: Number of average cycles.
        """
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
        """Modifies the average cycles of the TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, average cycles = 1 (no multi-cycle averaging).
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice` of the :func:`~pyTempico.core.TempicoChannel`.
        
        Args:
            number (int): desired average cycles for the TDC.
                Valid values are 1|2|4|8|16|32|64|128.
    
        """
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
        """Returns if a TDC :func:`~pyTempico.core.TempicoChannel` is enabled.
        
        By default, channels are enabled.
        
        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        request the device for the value. If not, the most recent value is 
        returned.
        
        Args:
            (none)
    
        Returns:
            bool: True, when TDC channel is enabled.
        """
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
        """Disables a TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, channels are enabled.
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice` of the :func:`~pyTempico.core.TempicoChannel`.
        
        To validate the status of the channel, method 
        :func:`~pyTempico.core.TempicoChannel.isEnabled` 
        may be used.
        
        Args:
            (none)
    
        """
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
        """Enables a TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, channels are enabled.
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice` of the :func:`~pyTempico.core.TempicoChannel`.
        
        To validate the status of the channel, method 
        :func:`~pyTempico.core.TempicoChannel.isEnabled` 
        may be used.
        
        Args:
            (none)
    
        """
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
        """Returns the expected number of stop pulses of the TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, number of stops = 1 (single start -> single stop).
        
        The TDC must receive all the expected number of stops to register them 
        as a valid measurement; otherwise, the measurements are discarded.
        
        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        request the device for the value. If not, the most recent value is 
        returned.
        
        Args:
            (none)
    
        Returns:
            integer: Number of stops.
        """
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
        """Modifies the expected number of stop pulses of the TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, number of stops = 1 (single start -> single stop).
        
        The TDC must receive all the expected number of stops to register them 
        as a valid measurement; otherwise, the measurements are discarded. For
        extending the valid time range, consider using measurement mode 2.
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice` of the :func:`~pyTempico.core.TempicoChannel`.
        
        Args:
            number (int): desired number of stops for the TDC. 
                Valid values are from 1 to 5.
    
        """
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
        """Returns the measurement mode of the TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, mode = 1.
        
        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        request the device for the value. If not, the most recent value is 
        returned.
        
        Args:
            (none)
    
        Returns:
            integer: Mode. Possible values are,
                
            - 1: Short measurement range. Start-stop times from 12ns to 500ns.
            - 2: Large measurement range. Start-stop times from 125ns to 4ms.
        """
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
        """Modifies the measurement mode of the TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, mode = 1. Possible values are,
            
        - 1: Short measurement range. Start-stop times from 12ns to 500ns.
        - 2: Large measurement range. Start-stop times from 125ns to 4ms.
                
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice` of the :func:`~pyTempico.core.TempicoChannel`.
        
        Args:
            number (int): desired measurement mode for the TDC. 
                Valid values are 1 or 2.
        
        """
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
        """Returns the edge type used on start pulses of the TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, start edge = 'RISE'.
        
        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        request the device for the value. If not, the most recent value is 
        returned.
        
        Args:
            (none)
    
        Returns:
            string: start edge type. Possible values are,
                
            - 'RISE': TDC timing starts on a rising edge of the start pulse.
            - 'FALL': TDC timing starts on a falling edge of the start pulse.
        """
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
        """Sets the edge type used on start pulses of the TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, start edge = 'RISE'. Possible values are,
            
        - 'RISE': TDC timing starts on a rising edge of the start pulse.
        - 'FALL': TDC timing starts on a falling edge of the start pulse.
                
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice` of the :func:`~pyTempico.core.TempicoChannel`.
        
        Args:
            edge_type (str): desired start edge type for the TDC.
                Valid values are 'RISE', 1, 'FALL', 0.
                
            
        """
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
        """Returns the edge type used on stop pulses of the TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, stop edge = 'RISE'.
        
        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        request the device for the value. If not, the most recent value is 
        returned.
        
        Args:
            (none)
    
        Returns:
            string: stop edge type. Possible values are,
                
            - 'RISE': TDC timing ends on a rising edge of the stop pulse.
            - 'FALL': TDC timing ends on a falling edge of the stop pulse.
        """
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
        """Sets the edge type used on stop pulses of the TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, stop edge = 'RISE'. Possible values are,
            
        - 'RISE': TDC timing ends on a rising edge of the stop pulse.
        - 'FALL': TDC timing ends on a falling edge of the stop pulse.
                
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice` of the :func:`~pyTempico.core.TempicoChannel`.
        
        Args:
            edge_type (str): desired stop edge type for the TDC.
                Valid values are 'RISE', 1, 'FALL', 0.
            
        """
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
        """Returns the time that stop pulses are ignored after receiving a start
        pulse on the TDC :func:`~pyTempico.core.TempicoChannel`. In microseconds.
        
        By default, stop mask = 0 (no masking).
        
        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        request the device for the value. If not, the most recent value is 
        returned.
        
        Args:
            (none)
    
        Returns:
            integer: stop mask time, in microseconds.
        """
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
        """Modifies the time that stop pulses are ignored after receiving a 
        start pulse on the TDC :func:`~pyTempico.core.TempicoChannel`.
        
        By default, stop mask = 0 (no masking).
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice` of the :func:`~pyTempico.core.TempicoChannel`.
        
        Args:
            stop_mask_in_us (int): desired stop mask for the TDC, in microseconds.
                Valid values are from 0 to 4000.
        
        """
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
    """Tausand Tempico TDC device object.
    
    To create an object of the :func:`~pyTempico.core.TempicoDevice` class, it is required to send as
    parameter the desired com_port. For example,
    
    >>> my_tempico_device_object = pyTempico.TempicoDevice('COM5')
    
    To modify or access attributes, **please use methods**. For example,
    
    >>> my_tempico_device_object.getIdn()
    
    To access attributes of a particular channel, use methods of the 
    :func:`~pyTempico.core.TempicoChannel` class through attributes ch1, ch2, ch3, ch4 of this class.
    For example, to get average cycles on channel 2,
    
    >>> my_tempico_device_object.ch2.getAverageCycles()
    
    or, as an alternative, send the channel number as a parameter
    
    >>> my_tempico_device_object.getAverageCycles(2)
    
    Changing attributes without using methods, do not change the actual 
    parameters in the device.
    
    Accesing attributes without using methods, returns values registered in 
    local memory, that may not be updated.
    
    To begin a measurement and read its results, use methods 
    :func:`~pyTempico.core.TempicoDevice.measure` and 
    :func:`~pyTempico.core.TempicoDevice.fetch`.
    
    
    
    Attributes:
        id_tempico_device (int): Unique identifier of the :func:`~pyTempico.core.TempicoDevice` object.
        ch1 (TempicoChannel): Object of the :func:`~pyTempico.core.TempicoChannel` class linked to 
            TDC in channel 1 (input A).
        ch2 (TempicoChannel): Object of the :func:`~pyTempico.core.TempicoChannel` class linked to 
            TDC in channel 2 (input B).
        ch3 (TempicoChannel): Object of the :func:`~pyTempico.core.TempicoChannel` class linked to 
            TDC in channel 3 (input C).
        ch4 (TempicoChannel): Object of the :func:`~pyTempico.core.TempicoChannel` class linked to 
            TDC in channel 4 (input D).
        device (Serial): Serial port object.
        idn (str): Identification string.
        number_of_channels (int): number of stop inputs of the device.
        number_of_runs (int): Number of measurement runs of the TDCs in 
            :func:`~pyTempico.core.TempicoDevice`.
        port (str): Serial port string.
        threshold (float): Threshold voltage on the rising edge of start and 
            stops inputs of TDCs in the :func:`~pyTempico.core.TempicoDevice`.
    
    """
    id_tempico_device = 0
    device = None
    ch1 = None
    ch2 = None
    ch3 = None
    ch4 = None
    #Communication and identification parameters        
    idn = ""   #when opening a connection, getIdn() updates this parameter
    port = ""    
    serial_timeout = 1 #by default, 1 second of timeout
    sn = "" #when opening a connection, getSerialNumber() updates this parameter
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
        self.TempicoDevices=TempicoDevicesSearch()
    
    ##open and closing connection methods
    def open(self):
        """Establishes (opens) a connection with a :func:`~pyTempico.core.TempicoDevice`.
        
        It is mandatory to establish a connection with this method before 
        to be able to send/to receive data to/from the device.
        
        Args:
            (none)
    
        """
        tempicoDevices=self.TempicoDevices.findDevices()
        if self.port in tempicoDevices:
            try:
                if self.__connected == True:
                    print('Device connection was already open.')
                    print('Open request ignored.')
                    #TO DO: raise exception/warning?
                else:
                    desired_port = self.port
                    self.device = serial.Serial(port = desired_port, baudrate=self.getBaudRate(), timeout=self.serial_timeout) # open serial port
                    self.__connected = self.device.is_open #gets if the device was connected from the serial object property 'is_open'
                    self.sn = self.getSerialNumber() #get serial number when opening
                    self.idn = self.getIdn() #get identification string when opening
            except Exception as e:
                print('verify the device in port',desired_port
                    ,'is connected, is turned on, and is not being used by other software.')
                raise e
                return
        else:
            print("The port has not a tempico device connected")
    
    def openTempico(self):
        """Establishes (opens) a connection with a :func:`~pyTempico.core.TempicoDevice`.
        
        Same as method :func:`~pyTempico.core.TempicoDevice.open`.
        
        Args:
            (none)
    
        """
        self.open()
        
    def close(self):
        """Ends (closes) a connection with a :func:`~pyTempico.core.TempicoDevice`.
        
        It is recommended to close connection at the end of a routine, to free 
        the device's port for future use.
        
        Args:
            (none)
    
        """
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
        """Ends (closes) a connection with a :func:`~pyTempico.core.TempicoDevice`.
        
        Same as method :func:`~pyTempico.core.TempicoDevice.close`.
        
        Args:
            (none)
    
        """
        
        self.close()
    
    def isOpen(self):
        """Returns if a TDC :func:`~pyTempico.core.TempicoDevice` connection is established (open).
                     
        Args:
            (none)
    
        Returns:
            bool: True when :func:`~pyTempico.core.TempicoDevice` connection is open.
        """
        return self.__connected
    
    ##general requests methods
    def getBaudRate(self):
        """Returns the :func:`~pyTempico.core.TempicoDevice` baud rate.
                     
        Args:
            (none)
    
        Returns:
            int: baud rate.
        """
        return self.__baudrate
    
    
    def getFirmware(self):
        """Returns the :func:`~pyTempico.core.TempicoDevice` firmware version.
                     
        Args:
            (none)
    
        Returns:
            str: firmware version.
        """
        if (self.__connected == True) and (self.__firmware == ""):
            #try to read IDN (and firmware) from device
            self.readIdnFromDevice()
        elif (self.__connected == False) and (self.__firmware == ""):
            print("Device connection not opened. First open a connection.")
            print("Unable to get Firmware.")
            #TO DO: raise expection?
        return self.__firmware
    
    def getIdn(self):
        """Returns the :func:`~pyTempico.core.TempicoDevice` identification string.
        
        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        request the device for the string. If not, the most recent read string 
        is returned.
                     
        Args:
            (none)
    
        Returns:
            str: identification string.
        """
        if (self.__connected == True) and (self.idn == ""):
            #try to read IDN from device
            self.readIdnFromDevice()
        elif (self.__connected == False) and (self.idn == ""):
            print("Device connection not opened. First open a connection.")
            print("Unable to get Idn.")
            #TO DO: raise expection?
        return self.idn
    
    def readIdnFromDevice(self):
        """Returns the :func:`~pyTempico.core.TempicoDevice` identification string, by requesting it to
        the device.
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`. As an alternative, method 
        :func:`~pyTempico.core.TempicoDevice.getIdn` may be used.
                     
        Args:
            (none)
    
        Returns:
            str: identification string.
        """
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
        """Sends a reset command to the :func:`~pyTempico.core.TempicoDevice`.
        
        Applying a reset clears all the settings of the :func:`~pyTempico.core.TempicoDevice` and its 
        TempicoChannels to their default values.
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`.
                     
        Args:
            (none)
        """
        try:
            self.writeMessage('*RST')
            #TO DO: validate if device has applied the reset request; if not, 
            #try again to reset.
        except Exception as e: 
            print(e)
    
    ##read and write via serial port methods
    def readMessage(self):
        """Reads pending messages sent by a :func:`~pyTempico.core.TempicoDevice` from its serial port.
        
        If no message is received, it waits the port timeout, typically 1s.
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`.
                     
        Args:
            (none)
            
        Returns:
            str: read message.
        """
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
    
    def abort(self):
        """
        Cancels an ongoing measurement on the :func:`~pyTempico.core.TempicoDevice`.

        This function sends a cancel command to the :func:`~pyTempico.core.TempicoDevice` to stop any 
        measurement currently in progress. It ensures that all measurement processes 
        are halted and the device is ready for a new operation or safely turned off.

        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`.

        Args:
            (none)
        """
        try:
            self.writeMessage('ABORt')
        except Exception as e: 
            print(e)
    
    def selfTest(self):
        """
        Performs a self-test on the :func:`~pyTempico.core.TempicoDevice` hardware.

        This function initiates a self-diagnostic test on the :func:`~pyTempico.core.TempicoDevice` to verify 
        its hardware integrity. If the self-test is successful, it prints the message 
        "Self test passed. Device is working properly." If the self-test fails, 
        it prints the message "Self test failed. Device may have a problem.", 
        indicating a potential issue with the hardware that may require further investigation 
        or support.

        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`.

        Args:
            (none)

        Returns:
            None
        """
        try:
            self.writeMessage('*TST?')
            data = self.readMessage()
            dataPure=data
            data=data.replace("\n","")
            data=data.replace("\r","")  
            if data == '0':
                print('Self test passed. Device is working properly.')
            else:
                print(dataPure)  
        except Exception as e: 
            print(e)
            
        
        
    def isPendingReadMessage(self):
        """Determines if a pending message is available to be read in a 
        :func:`~pyTempico.core.TempicoDevice` serial port.
                     
        Args:
            (none)
            
        Returns:
            bool: True, when a pending message is found.
        """
        if (self.device.in_waiting > 0):
            return True
        else:
            return False
        
    def waitAndReadMessage(self,wait_time_ms=1):
        """Waits the specified time, and then reads pending messages sent by a 
        :func:`~pyTempico.core.TempicoDevice` from its serial port, if any.
        
        If no message is received, it does not wait for a port timeout.
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`.
                     
        Args:
            wait_time_ms (int, optional): Waiting time, in miliseconds.
                Defaults to 1.
            
        Returns:
            str: read message.
        """
        time.sleep(wait_time_ms/1000) #wait 1ms for a device response, if any
        response = ''
        if self.isPendingReadMessage():
            response = self.readMessage()
        return response        
        
    def writeMessage(self,message):
        """Writes a message to a :func:`~pyTempico.core.TempicoDevice` in its serial port.
        
        If a response is expected after writing a message, the 
        :func:`~pyTempico.core.TempicoDevice.readMessage` 
        method should be called afterwards to obtain the response.
               
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`.
                     
        Args:
            message (str): message to be sent.
        """
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
        """Reads the most recent measurement data set form a :func:`~pyTempico.core.TempicoDevice`.
        
        The dataset of a :func:`~pyTempico.core.TempicoDevice` is in the following format::
            
            [[ch,run,start_s,stop_ps1,...,stop_psN],...,[ch,run,start_time_us,stop_ps1,...,stop_psN]]
        
        where
        
        - 'ch' (int) indicates the TDC channel,
        - 'run' (int) goes from 1 to NumberOfRuns,
        - 'start_s' (float) is the epoch timestamp of start pulse, in seconds with microsecond resolution. This value overflows (go back to zero) after 2^32 seconds,
        - 'stop_ps1' (int) is the measured precision timelapse between start and the 1st stop pulse, in picoseconds,
        - 'N' (int) is the NumberOfStops.
          
        Every value in the dataset is either an integer or a float number.
        
        If no measurement has been done, the device may respond with an empty 
        dataset. To make a new measurement, method 
        :func:`~pyTempico.core.TempicoDevice.measure` must be used.
               
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`. 
                     
        Args:
            (none)
            
        Returns:
            list(number): measured dataset.
        """
        try:
            self.writeMessage('FETCH?')
            #TO DO: save measured data in local memory, and validate data
            data = self.readMessage()
            #mylist = self.convertReadDataToIntList(data)
            #mylist = self.convertReadDataToFloatList(data)
            mylist = self.convertReadDataToNumberList(data)
            return mylist
        except Exception as e: 
            print(e)
    
    def measure(self):
        """Begins a measurement sequence and reads its dataset from a 
        :func:`~pyTempico.core.TempicoDevice`.
        
        The dataset of a :func:`~pyTempico.core.TempicoDevice` is in the following format::
            
            [[ch,run,start_s,stop_ps1,...,stop_psN],...,[ch,run,start_time_us,stop_ps1,...,stop_psN]]
            
        where
        
        - 'ch' (int) indicates the TDC channel,
        - 'run' (int) goes from 1 to NumberOfRuns,
        - 'start_s' (float) is the epoch timestamp of start pulse, in seconds with microsecond resolution. This value overflows (go back to zero) after 2^32 seconds,
        - 'stop_ps1' (int) is the measured precision timelapse between start and the 1st stop pulse, in picoseconds,
        - 'N' (int) is the NumberOfStops.
          
        Every value in the dataset is either an integer or a float number.
        
        If measurement cannot be completed within timeout, the device may 
        respond with an incomplete or empty dataset. In this case, to obtain a 
        complete dataset, the method 
        :func:`~pyTempico.core.TempicoDevice.fetch` may be called later.
               
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`. 
                     
        Args:
            (none)
            
        Returns:
            list(number): measured dataset.
        """
        try:
            #TO DO: validate if a measurement is in progress, before 
            #requesting a new measurement
            self.writeMessage('MEAS?')
            #TO DO: save measured data in local memory, and validate data
            data = self.readMessage()
            #mylist = self.convertReadDataToIntList(data)
            #mylist = self.convertReadDataToFloatList(data)
            mylist = self.convertReadDataToNumberList(data)
            return mylist
        except Exception as e: 
            print(e)   
            
    def convertReadDataToNumberList(self,data_string):
        """Converts a string with a read dataset message issued by a 
        :func:`~pyTempico.core.TempicoDevice`, into an number of number 2D-list (integer or float).
        
        The dataset of a :func:`~pyTempico.core.TempicoDevice` is in the following format::
            
            [[ch,run,start_s,stop_ps1,...,stop_psN],...,[ch,run,start_time_us,stop_ps1,...,stop_psN]]
            
        where
        
        - 'ch' (int) indicates the TDC channel,
        - 'run' (int) goes from 1 to NumberOfRuns,
        - 'start_s' (float) is the epoch timestamp of start pulse, in seconds, with microseconds precision; this value overflows (go back to zero) after 2^32 seconds,
        - 'stop_ps1' (int) is the measured precision timelapse between start and the 1st stop pulse, in picoseconds,
        - 'N' (int) is the NumberOfStops.
          
        Every value in the dataset is either an integer or a float.
                     
        Args:
            data_string (str): dataset message to convert.
            
        Returns:
            list(number): dataset message converted.
        """
        data_list = []
        if data_string != '':
            d = data_string.splitlines() #split lines, to remove \r\n chars
            d0 = d[0] #take only first line; ignore additional lines
            d0=d0.split(';') #split data into rows
            for row in d0:
                if len(row) > 0:
                    float_row = []
                    #separate cols by ',' and convert to integers
                    for x in row.split(','):
                        try:
                            float_row.append(int(x))
                        except: #if not an integer, save as float
                            float_row.append(float(x))                    
                else:
                    #if empty row, write empty (do not try to convert to int)
                    float_row = []
                #append integer row to data_list
                data_list.append(float_row) 
            
            if len(d) > 1:
                #if a second line exists, a warning/error message has arrived
                for extraline in d[1:]: #from 2nd to end
                    print(extraline)
                #TO DO: rise exception        

        return data_list
    
    def convertReadDataToFloatList(self,data_string):
        """Converts a string with a read dataset message issued by a 
        :func:`~pyTempico.core.TempicoDevice`, into an float 2D-list.
        
        The dataset of a :func:`~pyTempico.core.TempicoDevice` is in the following format::
            
            [[ch,run,start_s,stop_ps1,...,stop_psN],...,[ch,run,start_time_us,stop_ps1,...,stop_psN]]
            
        where
        
        - 'ch' indicates the TDC channel,
        - 'run' goes from 1 to NumberOfRuns,
        - 'start_s' is the epoch timestamp of start pulse, in seconds, with microseconds precision; this value overflows (go back to zero) after 2^32 seconds,
        - 'stop_ps1' is the measured precision timelapse between start and the 1st stop pulse, in picoseconds,
        - 'N' is the NumberOfStops.
          
        Every value in the dataset is converted to a float.
                     
        Args:
            data_string (str): dataset message to convert.
            
        Returns:
            list(float): dataset message converted.
        """
        data_list = []
        if data_string != '':
            d = data_string.splitlines() #split lines, to remove \r\n chars
            d0 = d[0] #take only first line; ignore additional lines
            d0=d0.split(';') #split data into rows
            for row in d0:
                if len(row) > 0:
                    #separate cols by ',' and convert to integers
                    float_row = [float(x) for x in row.split(',')] 
                else:
                    #if empty row, write empty (do not try to convert to int)
                    float_row = []
                #append integer row to data_list
                data_list.append(float_row) 
            
            if len(d) > 1:
                #if a second line exists, a warning/error message has arrived
                for extraline in d[1:]: #from 2nd to end
                    print(extraline)
                #TO DO: rise exception

        return data_list
            
    # def convertReadDataToIntList(self,data_string):
    #     """Converts a string with a read dataset message issued by a 
    #     TempicoDevice, into an integer 2D-list.
        
    #     The dataset of a TempicoDevice is in the following format::
            
    #         [[ch,run,start_us,stop_ps1,...,stop_psN],...,[ch,run,start_time_us,stop_ps1,...,stop_psN]]
            
    #     where
        
    #     - 'ch' indicates the TDC channel,
    #     - 'run' goes from 1 to NumberOfRuns,
    #     - 'start_us' is the timestamp of start pulse, in microseconds; this value overflows (go back to zero) after 2^32-1 seconds
    #     - 'stop_ps1' is the measured precision timelapse between start and the 1st stop pulse, in picoseconds,
    #     - 'N' is the NumberOfStops.
          
    #     Every value in the dataset is converted to an integer.
                     
    #     Args:
    #         data_string (str): dataset message to convert.
            
    #     Returns:
    #         list(int): dataset message converted.
    #     """
    #     data_list = []
    #     if data_string != '':
    #         d = data_string.splitlines() #split lines, to remove \r\n chars
    #         d0 = d[0] #take only first line; ignore additional lines
    #         d0=d0.split(';') #split data into rows
    #         for row in d0:
    #             if len(row) > 0:
    #                 #separate cols by ',' and convert to integers
    #                 int_row = [int(x) for x in row.split(',')] 
    #             else:
    #                 #if empty row, write empty (do not try to convert to int)
    #                 int_row = []
    #             #append integer row to data_list
    #             data_list.append(int_row) 
            
    #         if len(d) > 1:
    #             #if a second line exists, a warning/error message has arrived
    #             for extraline in d[1:]: #from 2nd to end
    #                 print(extraline)
    #             #TO DO: rise exception

    #     return data_list
            
    ##settings methods
    def getSettings(self):
        """Reads the current settings form a :func:`~pyTempico.core.TempicoDevice`.
        
        The response for settings query on a :func:`~pyTempico.core.TempicoDevice` is in the following 
        format::
            
            CH1:ACYC 1;CH1:ENAB 1;CH1:NST 1;...;CH4:STOP:MASK 0;NRUN 1;THR 1.00
            
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`. 
                     
        Args:
            (none)
            
        Returns:
            str: device settings.
        """
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
        """Returns the number of measurement runs of the TDCs in :func:`~pyTempico.core.TempicoDevice`.
        
        By default, number of runs = 1 (single measurement).
        
        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        request the device for the value. If not, the most recent value is 
        returned.
        
        Args:
            (none)
    
        Returns:
            integer: Number of number of runs.
        """
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
        """Modifies the number of measurement runs of the TDCs in :func:`~pyTempico.core.TempicoDevice`.
        
        By default, number of runs = 1 (single measurement).
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`.
        
        Args:
            number (int): desired number of runs for every TDC.
                Valid values are from 1 to 1000.
    
        """
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
            #TO DO: raise exception?
            
    def getThresholdVoltage(self):
        """Returns the threshold voltage on the rising edge of start and stops 
        inputs of TDCs in the :func:`~pyTempico.core.TempicoDevice`.
        
        Start and stop inputs are coupled to 50 ohms.
        
        By default, threshold voltage = 1.00V (recommended for TTL>2.5V).
        
        All inputs are 5V tolerant.
        
        Gate input. This parameter does not have effect on the gate input. 
        Gate input accepts 3.3V TTL and 5V TTL signals. 
        
        - When gate is disconnected, system is enabled. 
        - When gate is connected to 0V, system is disabled. 
        - When gate is connected to 3.3V/5V, system is enabled.
        
        
        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        request the device for the value. If not, the most recent value is 
        returned.
        
        Args:
            (none)
    
        Returns:
            float: start and stop inputs threshold voltage.
        """
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
        """Changes the threshold voltage on the rising edge of start and stops 
        inputs of TDCs in the :func:`~pyTempico.core.TempicoDevice`.
        
        Start and stop inputs are coupled to 50 ohms.
        
        By default, threshold voltage = 1.00V (recommended for TTL>2.5V).
        
        All inputs are 5V tolerant.
        
        Gate input. This parameter does not have effect on the gate input. 
        Gate input accepts 3.3V TTL and 5V TTL signals. 
        
        - When gate is disconnected, system is enabled. 
        - When gate is connected to 0V, system is disabled. 
        - When gate is connected to 3.3V/5V, system is enabled.
        
        To validate the actual threshold voltage applied, method 
        :func:`~pyTempico.core.TempicoDevice.getThresholdVoltage`
        should be called.
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`.
        
        Args:
            desired_voltage (float): desired start and stop inputs threshold 
                voltage. Valid parameters are MINimum|MAXimum|DOWN|UP or a 
                number from 0.90 to 1.60.
        """
        
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
        """Reduces the threshold voltage on the rising edge of start and stops 
        inputs of TDCs in the :func:`~pyTempico.core.TempicoDevice`.
        
        To validate the actual threshold voltage applied, method
        :func:`~pyTempico.core.TempicoDevice.getThresholdVoltage` 
        should be called.
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`.
        
        Args:
            (none)
        """
        self.setThresholdVoltage("DOWN")
    
    def incrementThresholdVoltage(self):
        """Increases the threshold voltage on the rising edge of start and 
        stops inputs of TDCs in the :func:`~pyTempico.core.TempicoDevice`.
        
        To validate the actual threshold voltage applied, method
        :func:`~pyTempico.core.TempicoDevice.getThresholdVoltage`
        should be called.
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`.
        
        Args:
            (none)
        """
        self.setThresholdVoltage("UP")
    
    def setThresholdVoltageToMaximum(self):
        """Sets to the maximum valid value the threshold voltage on the 
        rising edge of start and stops inputs of TDCs in the :func:`~pyTempico.core.TempicoDevice`.
        
        To validate the actual threshold voltage applied, method 
        :func:`~pyTempico.core.TempicoDevice.getThresholdVoltage`
        should be called.
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`.
        
        Args:
            (none)
        """
        self.setThresholdVoltage("MAX")
        
    def setThresholdVoltageToMinimum(self):
        """Sets to the minimum valid value the threshold voltage on the 
        rising edge of start and stops inputs of TDCs in the :func:`~pyTempico.core.TempicoDevice`.
        
        To validate the actual threshold voltage applied, method
        :func:`~pyTempico.core.TempicoDevice.getThresholdVoltage`
        should be called.
        
        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`.
        
        Args:
            (none)
        """
        self.setThresholdVoltage("MIN")
    
    def getDatetime(self,convertToDatetime=False):
        """
        Returns the number of seconds since the Tempico device was powered on, 
        based on its internal clock. If the device has been synchronized, the 
        seconds count corresponds to the system time of the host PC.

        This function sends the `DTIMe?` command to the device, reads the response,
        and parses it into a float representing the elapsed time in seconds.
        If the device does not respond correctly, the function returns -1.

        The timestamp resolution is in microseconds (µs), and the count starts from 
        power-up by default. Synchronization with the PC time must be previously configured 
        on the device, otherwise the value is relative to the device's uptime.

        Args:
            convertToDatetime (bool, optional): If True, the value is returned as a 
                datetime object. Default is False.

        Returns:
            float: Elapsed time in seconds since the device was powered on 
            or synchronized with the PC clock. Returns -1 if no valid response is received.
        """
        time_response=-1
        if self.isOpen():
            self.writeMessage('DTIMe?')
            response = self.readMessage()
            response = response.splitlines()
            if len(response)>0:
                response_first_line= response[0]
                try:
                    if response_first_line!="":
                        time_response= float(response_first_line)
                        if convertToDatetime:
                            time_response = datetime.fromtimestamp(time_response)
                    else:
                        print("Device does not respond correctly to DTIMe? request")
                except:
                    print("Device does not respond correctly to DTIMe? request")
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to get.")
            
            
        return time_response            
                
    #TO DO: Optional parameter for the user timestamp      
    def setDatetime(self, timeStampDateTime=None):
        """
        Sets the internal clock of the Tempico device to a specified timestamp 
        or to the current system time.

        Sends a `DTIMe <timestamp>` command using either the provided 
        `timeStampDateTime` or the current time in Unix format with microsecond 
        precision. If no response is received from the device, the function 
        verifies the update by comparing timestamps.

        Args:
            timeStampDateTime (float, optional): Unix timestamp (in seconds) to set 
                on the device. If not provided, the current system time is used.

        Returns:
            None
        """
        my_tempico = self
        if my_tempico.isOpen():
            my_tempico.waitAndReadMessage()
            if timeStampDateTime==None:
                currentDate= datetime.now().timestamp()
            else:
                maximumTime=self.getMaximumDatetime()
                minimumTime=self.getMinimumDatetime()
                if timeStampDateTime>=minimumTime and timeStampDateTime<=maximumTime:
                    currentDate= timeStampDateTime
                else:
                    print(f"Time stamp out of range valid values need to be between {minimumTime} and {maximumTime}")
                    return
            
            msg= f"DTIMe {currentDate}"
            my_tempico.writeMessage(msg)
            response=my_tempico.waitAndReadMessage()
            if response !='':
               print(response.splitlines()[0]) 
            else:
                new_date = self.getDateTime()
                if new_date>= currentDate:
                    pass
                else:
                    print('Failed.')            
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
    
    
    def getMaximumDatetime(self,convertToDatetime=False):
        """Returns the maximum datetime value allowed by the :func:`~pyTempico.core.TempicoDevice`.

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        requests the device for the maximum allowed date using the 
        'DTIMe:MAXimum?' command. If not, the value -1 is returned.
        
        The returned value corresponds to the latest timestamp that can be set 
        on the device without causing an error. If `convertToDatetime` is set to True, 
        the value is returned as a datetime object instead of a float.

        Args:
            convertToDatetime (bool, optional): If True, the value is returned as a 
                datetime object. Default is False.

        Returns:
            float or datetime: Maximum allowed datetime, either as a float (Unix 
            timestamp) or as a datetime object if convertToDatetime is True.
        """
        time_maximum = -1
        if self.isOpen():
            self.waitAndReadMessage()
            msg="DTIMe:MAXimum?"
            self.writeMessage(msg)
            response= self.readMessage()
            response= response.splitlines()
            if len(response)>0:
                response_first_line = response[0]
                try:
                    if response_first_line!="":
                        time_maximum= float(response_first_line)
                        if convertToDatetime:
                            time_maximum = datetime.fromtimestamp(time_maximum)
                    else:
                        print("Device does not respond correctly to DTIMe:MAXimum? request")
                except:
                    print("Device does not respond correctly to DTIMe:MAXimum? request")
            else:
                print("Device does not respond correctly to DTIMe:MAXimum? request")
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to get.")
                
        return time_maximum
    
    
    #Change not implemented yet in tempico firmware
    def setMaximumDatetime(self, maximumDateTime):
        """Sets the maximum datetime value allowed by the :func:`~pyTempico.core.TempicoDevice`.

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        sends the 'DTIMe:MAXimum <timestamp>' command to update the maximum 
        allowed timestamp. If the device accepts the value, it should return 
        a confirmation response. If no response is received, the value is 
        validated by re-reading it from the device.

        Args:
            maximumDateTime (float): New maximum timestamp to configure on the device.

        Returns:
            None
        """
        if self.isOpen():
            self.waitAndReadMessage()
            msg=f"DTIMe:MAXimum {maximumDateTime}"
            self.writeMessage(msg)
            response = self.waitAndReadMessage()
            if response !='':
               print(response.splitlines()[0]) 
            else:
                new_maximum_time = self.getMaximumDatetime()
                if new_maximum_time== maximumDateTime:
                    pass
                else:
                    print('Failed.')
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
            

    def getMinimumDatetime(self, convertToDatetime=False):
        """Returns the minimum datetime value allowed by the :func:`~pyTempico.core.TempicoDevice`.

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        requests the device for the minimum allowed date using the 
        'DTIMe:MINimum?' command. If not, the value -1 is returned.

        The returned value corresponds to the earliest timestamp that can be set 
        on the device without causing an error. If `convertToDatetime` is set to True, 
        the value is returned as a datetime object instead of a float.

        Args:
            convertToDatetime (bool, optional): If True, the value is returned as a 
                datetime object. Default is False.

        Returns:
            float or datetime: Minimum allowed datetime, either as a float (Unix 
            timestamp) or as a datetime object if convertToDatetime is True.
        """
        time_minimum = -1
        if self.isOpen():
            self.waitAndReadMessage()
            msg="DTIMe:MINimum?"
            self.writeMessage(msg)
            response= self.readMessage()
            response= response.splitlines()
            if len(response)>0:
                response_first_line = response[0]
                try:
                    if response_first_line!="":
                        time_minimum= float(response_first_line)
                        if convertToDatetime:
                            time_minimum = datetime.fromtimestamp(time_minimum)      
                    else:
                        print("Device does not respond correctly to DTIMe:MINimum? request")
                except:
                    print("Device does not respond correctly to DTIMe:MINimum? request")
            else:
                print("Device does not respond correctly to DTIMe:MINimum? request")
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to get.")
                
        return time_minimum
    
    
    def setMinimumDatetime(self, minimumDateTime):
        """Sets the minimum datetime value allowed by the :func:`~pyTempico.core.TempicoDevice`.

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        sends the 'DTIMe:MINimum <timestamp>' command to update the minimum 
        allowed timestamp. If the device accepts the value, it should return 
        a confirmation response. If no response is received, the value is 
        validated by re-reading it from the device.

        Args:
            minimumDateTime (float): New minimum timestamp to configure on the device.

        Returns:
            None
        """
        if self.isOpen():
            self.waitAndReadMessage()
            msg=f"DTIMe:MINimum {minimumDateTime}"
            self.writeMessage(msg)
            response = self.waitAndReadMessage()
            if response !='':
               print(response.splitlines()[0]) 
            else:
                new_minimum_time = self.getMinimumDatetime()
                if new_minimum_time== minimumDateTime:
                    pass
                else:
                    print('Failed.')
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to set.")
            
    #alternative naming for "Datetime" methods, as "DateTime" with capital 'T'
    def getDateTime(self,convertToDatetime=False):
        """Same as getDatetime
        """
        return self.getDatetime(convertToDatetime)
        
    def setDateTime(self, timeStampDateTime=None):
        """Same as setDatetime
        """
        self.setDatetime(timeStampDateTime)
        
    def getMaximumDateTime(self,convertToDatetime=False):
        """Same as getMaximumDatetime
        """
        return self.getMaximumDatetime(convertToDatetime)
        
    def setMaximumDateTime(self, maximumDateTime):
        """Same as setMaximumDatetime
        """
        self.setMaximumDatetime(maximumDateTime)
        
    def getMinimumDateTime(self, convertToDatetime=False):
        """Same as getMinimumDatetime
        """
        return self.getMinimumDatetime(convertToDatetime)
    
    def setMinimumDateTime(self, minimumDateTime):
        """Same as setMinimumDatetime
        """
        self.setMinimumDatetime(minimumDateTime)    

    def getLastStart(self, convertToDatetime=False):
        """Returns the datetime of the last start event registered by the :func:`~pyTempico.core.TempicoDevice`.

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        requests the device for the last start timestamp using the 
        'DTIMe:LSTart?' command. If not, the value -1 is returned.

        The returned value corresponds to the timestamp of the most recent start 
        event. If no start has occurred yet, the device returns 0.
        If `convertToDatetime` is set to True, the value is 
        returned as a datetime object instead of a float.

        Args:
            convertToDatetime (bool, optional): If True, the value is returned as a 
                datetime object. Default is False.

        Returns:
            float or datetime: Timestamp of the last start event, either as a float 
            (Unix timestamp) or as a datetime object if convertToDatetime is True. 
            Returns -1 if the value could not be retrieved.
        """
        time_last_start = -1
        if self.isOpen():
            self.waitAndReadMessage()
            msg="DTIMe:LSTart?"
            self.writeMessage(msg)
            response= self.readMessage()
            response= response.splitlines()
            if len(response)>0:
                response_first_line = response[0]
                try:
                    if response_first_line!="":
                        time_last_start= float(response_first_line)
                        if convertToDatetime and time_last_start!=-1:
                            time_last_start = datetime.fromtimestamp(time_last_start)
                    else:
                        print("Device does not respond correctly to DTIMe:LSTart? request")
                except:
                    print("Device does not respond correctly to DTIMe:LSTart? request")
            else:
                print("Device does not respond correctly to DTIMe:LSTart? request")
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to get.")
                
        return time_last_start
        
        
    def getLastSync(self, convertToDatetime=False):
        """Returns the datetime of the last synchronization performed on the :func:`~pyTempico.core.TempicoDevice`.

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        requests the device for the last synchronization timestamp using the 
        'DTIMe:LSYNc?' command. If not, the value -1 is returned.

        The returned value corresponds to the timestamp of the most recent 
        synchronization with the host system. If no synchronization has occurred yet, 
        the device returns 0. If `convertToDatetime` is 
        set to True, the value is returned as a datetime object instead of a float.

        Args:
            convertToDatetime (bool, optional): If True, the value is returned as a 
                datetime object. Default is False.

        Returns:
            float or datetime: Timestamp of the last synchronization event, either 
            as a float (Unix timestamp) or as a datetime object if convertToDatetime is True. 
            Returns -1 if the value could not be retrieved.
        """
        time_last_sync = -1
        if self.isOpen():
            self.waitAndReadMessage()
            msg="DTIMe:LSYNc?"
            self.writeMessage(msg)
            response= self.readMessage()
            response= response.splitlines()
            if len(response)>0:
                response_first_line = response[0]
                try:
                    if response_first_line!="":
                        time_last_sync= float(response_first_line)
                        if convertToDatetime and time_last_sync!=-1:
                            time_last_sync = datetime.fromtimestamp(time_last_sync)
                    else:
                        print("Device does not respond correctly to DTIMe:LSYNc? request")
                except:
                    print("Device does not respond correctly to DTIMe:LSYNc? request")
            else:
                print("Device does not respond correctly to DTIMe:LSYNc? request")
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to get.")         
        return time_last_sync
    
    #Functions come from tempico device
    # The channels could be A or 1, B or 2, C or 3, D or 4

    # This function will be use in order to reuse the code
    def getTempicoChannel(self, channel):
        """Returns the :func:`~pyTempico.core.TempicoChannel` object corresponding to the specified channel.

        This function allows selecting a channel by its number (1–4) or label 
        ('A'–'D'). If the input is valid, it returns the corresponding 
        :func:`~pyTempico.core.TempicoChannel` instance. If the input is invalid, an error message 
        is printed and -1 is returned.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

        Returns:
            TempicoChannel or int: The corresponding :func:`~pyTempico.core.TempicoChannel` object if the 
            input is valid, or -1 if the channel is invalid.
        """
        if channel==1 or channel=="A" or channel=="a":
            channelSelected=self.ch1
        elif channel==2 or channel=="B" or channel=="b":
            channelSelected=self.ch2
        elif channel==3 or channel=="C" or channel=="c":
            channelSelected=self.ch3
        elif channel==4 or channel=="D" or channel=="d":
            channelSelected=self.ch4
        else:
            print("Invalid channel")
            return -1
        return channelSelected

    #Getters tempico device
    def getAverageCycles(self,channel):
        """Returns the average cycles of the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, average cycles = 1 (no multi-cycle averaging).

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        delegates the query to the selected channel object and retrieves its 
        average cycles value. If the connection is not open, or the channel is 
        invalid, the function returns -1.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access the corresponding 
        :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

        Returns:
            integer: Number of average cycles, or -1 if the channel is invalid.
        """
        channelSelected=self.getTempicoChannel(channel)
        averageCycles=-1
        if channelSelected!=-1:
            averageCycles=channelSelected.getAverageCycles()
        return averageCycles
    
    
    def getNumberOfStops(self,channel):
        """Returns the expected number of stop pulses for the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, number of stops = 1 (single start → single stop).

        The TDC must receive all the expected number of stops to register them 
        as a valid measurement; otherwise, the measurements are discarded.

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        delegates the query to the selected channel object and retrieves its 
        number of stops. If the connection is not open, or the channel is invalid, 
        the function returns -1.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access the corresponding 
        :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

        Returns:
            integer: Number of stops, or -1 if the channel is invalid.
        """
        channelSelected=self.getTempicoChannel(channel)
        numberOfStops=-1
        if channelSelected!=-1:
            numberOfStops=channelSelected.getNumberOfStops()
        return numberOfStops
    
    
    def getMode(self,channel):
        """Returns the measurement mode of the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, mode = 1.

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        delegates the query to the selected channel object and retrieves its 
        current measurement mode. If the connection is not open, or the channel 
        is invalid, the function returns -1.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access the corresponding 
        :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

        Returns:
            integer: Mode. Possible values are:
                
            - 1: Short measurement range. Start-stop times from 12ns to 500ns.
            - 2: Large measurement range. Start-stop times from 125ns to 4ms.
            
            Returns -1 if the channel is invalid.
        """
        channelSelected=self.getTempicoChannel(channel)
        mode=-1
        if channelSelected!=-1:
            mode=channelSelected.getMode()
        return mode
    
    def getStartEdge(self,channel):
        """Returns the edge type used on start pulses of the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, start edge = 'RISE'.

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        delegates the query to the selected channel object and retrieves its 
        configured start edge type. If the connection is not open, or the channel 
        is invalid, the function returns -1.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access the corresponding 
        :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

        Returns:
            string or int: Start edge type. Possible values are:
            
            - 'RISE': TDC timing starts on a rising edge of the start pulse.
            - 'FALL': TDC timing starts on a falling edge of the start pulse.
            
            Returns -1 if the channel is invalid.
        """
        channelSelected=self.getTempicoChannel(channel)
        startEdge=-1
        if channelSelected!=-1:
            startEdge=channelSelected.getStartEdge()
        return startEdge
    
    def getStopEdge(self,channel):
        """Returns the edge type used on stop pulses of the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, stop edge = 'RISE'.

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        delegates the query to the selected channel object and retrieves its 
        configured stop edge type. If the connection is not open, or the channel 
        is invalid, the function returns -1.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access the corresponding 
        :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

        Returns:
            string or int: Stop edge type. Possible values are:
            
            - 'RISE': TDC timing ends on a rising edge of the stop pulse.
            - 'FALL': TDC timing ends on a falling edge of the stop pulse.
            
            Returns -1 if the channel is invalid.
        """
        channelSelected=self.getTempicoChannel(channel)
        stopEdge=-1
        if channelSelected!=-1:
            stopEdge=channelSelected.getStopEdge()
        return stopEdge
    
    def getStopMask(self,channel):
        """Returns the stop mask time (in microseconds) of the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, stop mask = 0 (no masking).

        The stop mask defines the period after receiving a start pulse during which 
        stop pulses are ignored. This helps eliminate unwanted noise or early pulses.

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        delegates the query to the selected channel object and retrieves its 
        current stop mask time. If the connection is not open, or the channel is 
        invalid, the function returns -1.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access the corresponding 
        :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

        Returns:
            integer: Stop mask time in microseconds, or -1 if the channel is invalid.
        """
        channelSelected=self.getTempicoChannel(channel)
        stopMask=-1
        if channelSelected!=-1:
            stopMask=channelSelected.getStopMask()
        return stopMask

    #Setters
    
    def setAverageCycles(self,channel,averageCycles):
        """Modifies the average cycles of the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, average cycles = 1 (no multi-cycle averaging).

        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`, and delegates the configuration to the selected 
        :func:`~pyTempico.core.TempicoChannel`. If the channel is invalid, the function does nothing.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access and configure the 
        corresponding :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

            averageCycles (int): Desired average cycles for the TDC.
                Valid values are: 1, 2, 4, 8, 16, 32, 64, 128.
        """
        channelSelected=self.getTempicoChannel(channel)
        if channelSelected!=-1:
            channelSelected.setAverageCycles(averageCycles)
        
    def setNumberOfStops(self,channel,numberOfStops):
        """Modifies the expected number of stop pulses of the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, number of stops = 1 (single start → single stop).

        The TDC must receive all the expected number of stops to register them 
        as a valid measurement; otherwise, the measurements are discarded. For 
        extending the valid time range, consider using measurement mode 2.

        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`, and delegates the configuration to the selected 
        :func:`~pyTempico.core.TempicoChannel`. If the channel is invalid, the function does nothing.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access and configure the 
        corresponding :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

            numberOfStops (int): Desired number of stops for the TDC.
                Valid values are from 1 to 5.
        """
        channelSelected=self.getTempicoChannel(channel)
        if channelSelected!=-1:
            channelSelected.setNumberOfStops(numberOfStops)
    
    def setMode(self,channel,mode):
        """Modifies the measurement mode of the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, mode = 1. Possible values are:

            - 1: Short measurement range. Start-stop times from 12ns to 500ns.
            - 2: Large measurement range. Start-stop times from 125ns to 4ms.

        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`, and delegates the configuration to the selected 
        :func:`~pyTempico.core.TempicoChannel`. If the channel is invalid, the function does nothing.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access and configure the 
        corresponding :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

            mode (int): Desired measurement mode for the TDC.
                Valid values are 1 or 2.
        """
        channelSelected=self.getTempicoChannel(channel)
        if channelSelected!=-1:
            channelSelected.setMode(mode)
    
    def setStartEdge(self,channel,startEdge):
        """Sets the edge type used on start pulses of the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, start edge = 'RISE'. Possible values are:

            - 'RISE': TDC timing starts on a rising edge of the start pulse.
            - 'FALL': TDC timing starts on a falling edge of the start pulse.

        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`, and delegates the configuration to the selected 
        :func:`~pyTempico.core.TempicoChannel`. If the channel is invalid, the function does nothing.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access and configure the 
        corresponding :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

            startEdge (str or int): Desired start edge type for the TDC.
                Accepted values are 'RISE', 1, 'RIS' or 'FALL', 0, 'FAL'.
        """
        channelSelected=self.getTempicoChannel(channel)
        if channelSelected!=-1:
            channelSelected.setStartEdge(startEdge)
    
    def setStopEdge(self,channel,stopEdge):
        """Sets the edge type used on stop pulses of the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, stop edge = 'RISE'. Possible values are:

            - 'RISE': TDC timing ends on a rising edge of the stop pulse.
            - 'FALL': TDC timing ends on a falling edge of the stop pulse.

        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`, and delegates the configuration to the selected 
        :func:`~pyTempico.core.TempicoChannel`. If the channel is invalid, the function does nothing.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access and configure the 
        corresponding :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

            stopEdge (str or int): Desired stop edge type for the TDC.
                Accepted values are 'RISE', 1, 'RIS' or 'FALL', 0, 'FAL'.
        """
        channelSelected=self.getTempicoChannel(channel)
        if channelSelected!=-1:
            channelSelected.setStopEdge(stopEdge)
    
    def setStopMask(self,channel,stopMask):
        """Modifies the stop mask time of the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, stop mask = 0 (no masking).

        The stop mask defines the period (in microseconds) after receiving a start 
        pulse during which stop pulses are ignored. This can help suppress 
        unwanted noise or early signals.

        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`, and delegates the configuration to the selected 
        :func:`~pyTempico.core.TempicoChannel`. If the channel is invalid, the function does nothing.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access and configure the 
        corresponding :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

            stopMask (int): Desired stop mask time in microseconds.
                Valid values are from 0 to 4000.
        """
        channelSelected=self.getTempicoChannel(channel)
        if channelSelected!=-1:
            channelSelected.setStopMask(stopMask)
    
    #Other functions
    def isEnabled(self,channel):
        """Returns whether the specified :func:`~pyTempico.core.TempicoChannel` is enabled.

        By default, channels are enabled.

        If the connection is established with the :func:`~pyTempico.core.TempicoDevice`, this function 
        delegates the query to the selected channel object and retrieves its 
        current enable status. If the connection is not open, or the channel is 
        invalid, the function returns -1.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access and query the 
        corresponding :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'

        Returns:
            bool or int: True if the channel is enabled, False if disabled, or 
            -1 if the channel is invalid.
        """
        channelSelected=self.getTempicoChannel(channel)
        enable=-1
        if channelSelected!=-1:
            enable=channelSelected.isEnabled()
        return enable
    
    def enableChannel(self,channel):
        """Enables the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, channels are enabled.

        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`, and delegates the enabling operation to the selected 
        :func:`~pyTempico.core.TempicoChannel`. If the channel is invalid, the function does nothing.

        To validate the status of the channel, method 
        :func:`~pyTempico.core.TempicoChannel.isEnabled` may be used.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access and configure the 
        corresponding :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'
        """
        channelSelected=self.getTempicoChannel(channel)
        if channelSelected!=-1:
            channelSelected.enableChannel()
    
    def disableChannel(self,channel):
        """Disables the specified :func:`~pyTempico.core.TempicoChannel`.

        By default, channels are enabled.

        This function requires that a connection is established with the 
        :func:`~pyTempico.core.TempicoDevice`, and delegates the disabling operation to the selected 
        :func:`~pyTempico.core.TempicoChannel`. If the channel is invalid, the function does nothing.

        To validate the status of the channel, method 
        :func:`~pyTempico.core.TempicoChannel.isEnabled` may be used.

        This version belongs to the :func:`~pyTempico.core.TempicoDevice` class and requires specifying 
        the channel number or label ('A'–'D') to access and configure the 
        corresponding :func:`~pyTempico.core.TempicoChannel`.

        Args:
            channel (int or str): Channel identifier. Accepted values are:
            
                - 1 or 'A' or 'a'
                - 2 or 'B' or 'b'
                - 3 or 'C' or 'c'
                - 4 or 'D' or 'd'
        """
        channelSelected=self.getTempicoChannel(channel)
        if channelSelected!=-1:
            channelSelected.disableChannel()
    
    
    def getSerialNumber(self):
        """Returns the serial number of the connected :func:`~pyTempico.core.TempicoDevice`.

        This function searches for the serial number associated with the current 
        COM port used by the device. If the connection is established, it queries 
        the list of available serial ports to match the active one and extract 
        its serial number.

        If the connection is not open, a message is printed and an empty string 
        is returned.

        Args:
            (none)

        Returns:
            string: Serial number of the device, or empty string if not found 
            or if the connection is not open.
            e.g: "TP1004-220500"
        """
        completeSerial=""
        if self.isOpen():
            current_port = self.device.port
            for port in serial.tools.list_ports.comports():
                if port.device == current_port:
                    completeSerial=port.serial_number     
                    break
            else:
                completeSerial=""
            return completeSerial
        elif (self.sn != ""):
            #if current registered sn is not empty
            return self.sn  #return saved string
        else:
            print("Device connection not opened. First open a connection.")
            print("Unable to get.")
        
    