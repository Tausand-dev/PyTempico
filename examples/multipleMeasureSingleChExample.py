# -*- coding: utf-8 -*-
"""
multipleMeasureSingleChExample

    Created on Mon Feb 16 10:35:56 2026
    
    Connects to a Tausand Tempico device, starts a sequence of multiple 
    measurements on a single channel, and reads the results. Results are 
    written in a csv file.
    
    Instructions: 
        * before running this example, pandas and pyTempico packages must be installed.
        * change 'my_port' to your corresponding port.
        * (optional) change parameters 'mode', 'number_of_measurements' 
        and 'number_of_runs'.
        * connect signals to your Tempico Device. If no signals are measured, 
        this example will return an empty data array.
        * run.
    
    | @author: David Guzman, Tausand Electronics 
    | dguzman@tausand.com 
    | https://www.tausand.com

"""
import pyTempico
import pandas as pd
from datetime import datetime

my_port = 'COM7' #change this port to your Tempico device's port
my_device = pyTempico.TempicoDevice(my_port)    #create object
mode = 1 #valid modes: 1 or 2. (TOF up to 250ns, or TOF from 125ns up to 4ms)
number_of_measurements = 50
number_of_runs = 100 #valid values: 1 to 1000

    
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
    print('\nPreparing to measure start-stop TOF in channel '+selected_ch_letter+'.')
    print('Connect signals into start and stop'+selected_ch_letter+'.')
    print("Are signals connected (y/n):")
    user_input = input()
    data = []
    if ((user_input == 'y') or (user_input == 'Y')):
        for i in range(1,numch+1):
            if i == selected_ch:
                #enable selected channel
                my_device.enableChannel(i)
            else:
                #disable unselected channels
                my_device.disableChannel(i)
                
        my_device.setMode(selected_ch, mode)
        my_device.setNumberOfRuns(number_of_runs)
        print('Measure started. Running '+str(number_of_measurements),end='')
        print(' measurements, each of '+str(number_of_runs)+' runs.')
        
        #synchronize Tempico's datetime with PC's datetime
        my_device.setDateTime()
        
        #calibrate before starting a measurement
        my_device.calibrateDelay()
        
        print('Progress:')
        for k in range(1,number_of_measurements+1):
            #repeat number_of_measurements times the measurment
            percentage=100.0*k/number_of_measurements
            print(f"\r{percentage:4.0f}%",end='')
            this_data = my_device.measure()   #starts a measurement, and saves response in 'data'
            data = data + this_data  #appending
            
        df = pd.DataFrame(data, columns = ["ch", "run", "datetime", "tof_ps"])
        print('\nMeasure completed.')
        
        print('\nTime-Of-Flight statistics:')
        samples = len(df)
        tof_mean = round(df['tof_ps'].mean(),2)
        tof_median = df['tof_ps'].median()
        tof_std = round(df['tof_ps'].std(),2)
        tof_max = df['tof_ps'].max()
        tof_min = df['tof_ps'].min()
        print(f" samples:    \t{samples:14d}")
        print(f" mean (ps):  \t{tof_mean:17.2f}")
        print(f" median (ps):\t{tof_median:14.0f}")
        print(f' std (ps):   \t{tof_std:17.2f}')
        print(f' max (ps):   \t{tof_max:14.0f}')
        print(f' min (ps):   \t{tof_min:14.0f}')
        
        #build csv file name
        dt_string=datetime.today().strftime('%Y%m%d%H%M')
        csv_file_name='tempico_tof_ch'+str(selected_ch)+'_'+dt_string+'.csv'
           
        #write header with device details into csv file
        my_header = {
            'label': ['Datetime', 'Tempico model', 'Serial number', 'Firmware', 'mode'],
            'value': [datetime.today().strftime('%Y-%m-%d %H:%M'), my_device.getModelIdn(), my_device.getSerialNumber(), my_device.getFirmware(), my_device.getMode(selected_ch)]
            }
        header_df = pd.DataFrame(my_header)
        header_df.to_csv(csv_file_name,header=False,index=False) #no printing column names or row indexes
        
        #write data statistics into csv file
        my_stats = {
            'label': ['samples','tof_ps mean','tof_ps median','tof_ps standard deviation','tof_ps maximum','tof_ps minimum'],
            'value' : [samples, tof_mean, tof_median, tof_std, tof_max, tof_min]
            }
        stats_df = pd.DataFrame(my_stats)
        stats_df.to_csv(csv_file_name,header=False,index=False,mode='a') #no printing column names or row indexes, mode 'append'
        
        #write dataset into file
        df.to_csv(csv_file_name,mode='a') #mode 'append'
        print('\nData saved in '+csv_file_name)
        
    else:
        print('Measurement cancelled.')



###############    MAIN    #################

try:
    print('opening connection with device in port',my_port)
    my_device.open()             #open connection with device
    if my_device.isOpen():
        print('connection with my_device is open')
    else:
        print('connection with my_device is close')
        raise Exception("Failed opening a conection in port "+my_port)
        
    numch = my_device.number_of_channels
    
    print('\nSelect a stop channel to measure (1 to '+str(numch)+'):')
    user_input = input()  
    
    MeasureStartStopSingleCh(user_input) #call measurement routine
    
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