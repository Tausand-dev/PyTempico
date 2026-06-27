# -*- coding: utf-8 -*-
"""
calibrateOffsetExample
    
    Created on Mon Feb 16 10:32 2026
    Last updated on Wed May 20 16:34 2026

    This script demonstrates how to calibrate hardware delay offset of a 
    Tausand Tempico TP1200 device. These offsets are intended to fine tune each
    TP1200 device.
    
    Changing hardware delay offset should only be done by qualified personnel.

    In TP1004, the theoretical hardware delay is 0ns. No delay offset applies.
    In TP1204, the theoretical hardware delay is 250ns. The theoretical delay 
    offset is 0ns.

    This example:
        * opens connection to a Tempico device,
        * launches a menu with the following options,
            1. Read delay offsets
            2. Read default delay offsets
            3. Calibrate delay offset in single channel
            4. Change hardware delay offset
            0. Exit

    You **need** a duplicated signal connected to start and stop to run this routine.

    Instructions:
        1. Ensure `pyTempico` and `pandas' are installed.
        2. Run the script.
        3. Enter the communication port of Tempico device when requested (e.g. 'COM7')

    | @author: David Guzman, Tausand Electronics 
    | dguzman@tausand.com 
    | https://www.tausand.com
"""
import pyTempico
import pandas as pd
from datetime import datetime


def ReadTempicoIdentifiers():
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
    
    
def ReadTempicoDelayOffsets():
    print('\nReading current delay offsets in each channel')    
    delay_offsets = []
    for i in range(1,numch+1):
        msg='CALibrate:CH'+str(i)+':DELay:OFFSet?'
        my_device.writeMessage(msg)
        resul = my_device.readMessage()
        print("\t"+msg+" "+resul)
        delay_offsets.append(float(resul))
    return delay_offsets


def ReadTempicoDelayOffsetDefaults():    
    print('\nReading delay offset deafults in each channel')
    default_delay_offsets = []    
    for i in range(1,numch+1):
        msg='CALibrate:CH'+str(i)+':DELay:OFFSet:DEFault?'
        my_device.writeMessage(msg)
        resul = my_device.readMessage()
        print("\t"+msg+" "+resul)
        default_delay_offsets .append(float(resul))
    return default_delay_offsets
        
        
def ResetAndCalibrateSingleCh(selected_ch):
    try:
        selected_ch = int(selected_ch)
        if (selected_ch < 1) or (selected_ch > numch):
            selected_ch=""
            raise Exception("Invalid input.")
    except ValueError:
        selected_ch=""
        print("Invalid input.")
    
    selected_ch_letter = chr(ord('A')+selected_ch-1)
    print('\nPreparing settings on channel '+selected_ch_letter)
    
    #reset to default settings
    my_device.reset()
    
    #set stopMask to its minimum
    my_device.setStopMask(selected_ch, my_device.getStopMaskMinimum())
    
    #set mode=1 for higher-resolution, TOF up to 250ns
    new_mode = 1
    my_device.setMode(selected_ch, new_mode)
    
    #calibrate inner delays before launching the measurement sequence
    my_device.calibrateDelay()
    
    
def MeasureStartStopSingleCh(selected_ch):
    try:
        selected_ch = int(selected_ch)
        if (selected_ch < 1) or (selected_ch > numch):
            selected_ch=""
            raise Exception("Invalid input.")
    except ValueError:
        selected_ch=""
        print("Invalid input.")
              
    selected_ch_letter = chr(ord('A')+selected_ch-1)
    print('\nMeasure start-stop in channel '+selected_ch_letter)
    print('Connect a duplicated signal into start and stop'+selected_ch_letter+' (e.g. 1kHz pulse)')    
    user_input = input("Are signals connected? (y/n): ")
    data = []
    if ((user_input == 'y') or (user_input == 'Y')):
        #print('yes')
        my_device.setMode(selected_ch, 1)
        for i in range(1,numch+1):
            if i == selected_ch:
                #enable selected channel
                my_device.enableChannel(i)
            else:
                #disable unselected channels
                my_device.disableChannel(i)
        
        my_device.setNumberOfRuns(100)
        print('\nMeasure started. Progress:')
        for k in range(1,50+1):
            #repeat 50 times the measurment
            percentage=100*k/50
            print(f"\r{percentage:4.0f}%",end='')
            this_data = my_device.measure()   #starts a measurement, and saves response in 'data'
            data = data + this_data  #appending
            
        df = pd.DataFrame(data, columns = ["ch", "run", "datetime", "tof_ps"])
        print('\nMeasure completed.')
        
        overflow_constant = my_device.getOverflowParameter()
        df_correct = df[df['tof_ps'] != overflow_constant] #discard OVF values, (-1000000 in TP1204)
        
        print('\nTime-Of-Flight statistics:')
        samples = len(df)
        samples_ok = len(df_correct)
        samples_ovf = samples - samples_ok        
        tof_mean = round(df_correct['tof_ps'].mean(),2)
        tof_median = df_correct['tof_ps'].median()
        tof_mode = df_correct['tof_ps'].mode()[0]
        tof_std = round(df_correct['tof_ps'].std(),2)
        tof_max = df_correct['tof_ps'].max()
        tof_min = df_correct['tof_ps'].min()
        print(f" samples:       \t{samples:4d}")
        print(f" ovf samples:   \t{samples_ovf:4d}")
        print(f" valid samples: \t{samples_ok:4d}")
        print(f" mean (ps):     \t{tof_mean:7.2f}")
        print(f" median (ps):   \t{tof_median:7.2f}")
        print(f" mode (ps):     \t{tof_mode:7.2f}")
        print(f' std (ps):      \t{tof_std:7.2f}')
        print(f' max (ps):      \t{tof_max:7.2f}')
        print(f' min (ps):      \t{tof_min:7.2f}')
        
        
        #Estimate a good delay offset
        print('\nEstimating recommendation for delay offset, based on measured median.')
        try:
            current_offset = delay_offsets[selected_ch-1]
        except:
            msg='CALibrate:CH'+str(selected_ch)+':DELay:OFFSet?'
            my_device.writeMessage(msg)
            current_offset = float(my_device.readMessage())
        recommended_new_offset = current_offset + tof_median
        print(f' current delay offset for channel {selected_ch_letter}:         \t{current_offset:7.2f}')
        print(f' recommended new delay offset for channel {selected_ch_letter}: \t{recommended_new_offset:7.2f}')
        
        #Save measured data in a csv file        
        dt_string=datetime.today().strftime('%Y%m%d%H%M')
        csv_file_name='tempico_tof_ch'+str(selected_ch)+'_'+dt_string+'.csv'
               
        my_header = {
            'Column1': ['Datetime', 'Tempico model', 'Serial number', 'Firmware', ''], #end with blank row
            'Column2': [datetime.today().strftime('%Y-%m-%d %H:%M'), my_device.getModelIdn(), my_device.getSerialNumber(), my_device.getFirmware(),''] #end with blank row
        }
        header_df = pd.DataFrame(my_header)
        header_df.to_csv(csv_file_name,header=False,index=False) #no printing column names or row indexes
        df.to_csv(csv_file_name,mode='a') #mode 'append'
        print('\nData saved in '+csv_file_name)
        
    else:
        print('skip')


def ChangeTempicoDelayOffset():
    print('\nChange hardware delay offset')    
    print("DANGER ZONE: Do you want to change hardware delay offset of a channel? (y/n):")
    user_input = input()

    if ((user_input == 'y') or (user_input == 'Y')):
        #print('yes')
        
        print('Delay Offset: select channel to change (1 to '+str(numch)+')')
        user_input = input()
        try:
            selected_ch=int(user_input)
            if (selected_ch < 1) or (selected_ch > numch):
                selected_ch=""
                raise Exception("Invalid input.")
        except ValueError:
            selected_ch=""
            print("Invalid input.")
        
        print('Delay Offset: enter the NEW desired value, in ps')
        user_input = input()
        try:
            new_offset = float(user_input)
        except ValueError:
            new_offset = ""
            print("Invalid input.")
 
        
        if((new_offset != "") and (selected_ch != "")):
            msg='CALibrate:DELay:OFFSet:PROTect Off'
            my_device.writeMessage(msg)
            resul = my_device.readMessage()
            print(msg+" "+resul)
            
            print('Change delay offset value in device:')
            msg='CALibrate:CH'+str(selected_ch)+':DELay:OFFSet '+str(new_offset)
            my_device.writeMessage(msg)
            resul = my_device.readMessage()
            print(msg+" "+resul)
            
            print('Read new value from device')
            msg='CALibrate:CH'+str(selected_ch)+':DELay:OFFSet?'
            my_device.writeMessage(msg)
            resul = my_device.readMessage()
            print(msg+" "+resul)
            
            msg='CALibrate:DELay:OFFSet:PROTect On'
            my_device.writeMessage(msg)
            resul = my_device.readMessage()
            print(msg+" "+resul)



###############    MAIN       #################

try:
    print("Write the port where the Tempico is connected (e.g. COM5).")
    my_port = input("The port is: ")
    my_device = pyTempico.TempicoDevice(my_port)    #create object
    
    print('\nopening connection with device in port',my_port)
    my_device.open()             #open connection with device
    if my_device.isOpen():
        print(f'connection with device in port {my_port} is open')
    else:
        print('connection with device is close')
        raise Exception("Failed opening a conection in port "+my_port)
        
    delay_offsets = []
    numch = my_device.number_of_channels    
    ReadTempicoIdentifiers()    
    
    while True:
        print("\nSelect the routine to execute:")
        print("1. Read delay offsets")
        print("2. Read default delay offsets")
        print("3. Calibrate delay offset in single channel")
        print("4. Change hardware delay offset")
        print("0. Exit")
        choice = input("Enter option: ")
        
        if choice == "0":
            break 
        
        if choice == "1":
            delay_offsets = ReadTempicoDelayOffsets()
            
        if choice == "2":
            ReadTempicoDelayOffsetDefaults()
            
        if choice == "3":
            print('\nSelect a stop channel to calibrate its offset (1 to '+str(numch)+'):')
            user_input = input()
            
            if (delay_offsets == []):
                delay_offsets = ReadTempicoDelayOffsets()
            
            ResetAndCalibrateSingleCh(user_input)            
            MeasureStartStopSingleCh(user_input) 
        
        if choice == "4":  
            ChangeTempicoDelayOffset()
    
    
    my_device.close()
    if my_device.isOpen():
        print(f'\nconnection with device in port {my_port} is open')
    else:
        print(f'\nconnection with device in port {my_port} is close')
    
except Exception as e:
    print(e)
    
finally:
    if my_device.isOpen():
        my_device.close() #close a connection, if it is still open