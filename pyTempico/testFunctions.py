import serial
from core import TempicoDevicesSearch
from core import TempicoDevice
from datetime import datetime
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
# portsFound = TempicoDevicesSearch().findDevices()
# print(portsFound)
# if portsFound:
#     #connect to the first found device
#     tempicoDevice = TempicoDevice(portsFound[0]) 
#     tempicoDevice.open()
#     tempicoDevice.close()


# DevTemp=TempDevs()
# devices=DevTemp.findDevices()
# print(devices)

# tempDevice= TempicoDevice("COM5")
# tempDevice.open()
# print("Old time")
# print(tempDevice.getDateTime(True))
# currentDate= datetime.now().timestamp()

# tempDevice.setDateTime(1677854900.0)
# print("New time")
# print(tempDevice.getDateTime(True))
# print("Maximun time")
# print(tempDevice.getMaximumDatetime(True))
# print("Minimum time")
# print(tempDevice.getMinimumDatetime(True))



tempDevice= TempicoDevice("COM5")
tempDevice.open()
print("Last sync")
print(tempDevice.getLastSync())

