import serial
from core import TempicoDevicesSearch
from core import TempicoDevice

#Test for abort measure

# tempicoDevice = TempDev('COM12')
# tempicoDevice.openTempico()
# tempicoDevice.close()
# valueIdn=tempicoDevice.getIdn()
# tempicoDevice.measure()
# #tempicoDevice.abort()
# print(tempicoDevice.fetch())
# tempicoDevice.close()
#change
#change2
#Test for selfTest
# tempicoDevice = TempDev('COM12')
# tempicoDevice.openTempico()
# tempicoDevice.selfTest()
# tempicoDevice.close()

#Test tempico devices
# tempicoDevice = TempDev('COM42')
# portsFound=tempicoDevice.findDevices()
# print(portsFound)

#Test new open function
#look up for connected Tempico devices, and connect to it
portsFound = TempicoDevicesSearch().findDevices()
print(portsFound)
if portsFound:
    #connect to the first found device
    tempicoDevice = TempicoDevice(portsFound[0]) 
    tempicoDevice.open()
    tempicoDevice.close()


# DevTemp=TempDevs()
# devices=DevTemp.findDevices()
# print(devices)