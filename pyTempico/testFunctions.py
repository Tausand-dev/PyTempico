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
tempicoDevice = TempicoDevicesSearch()
values=tempicoDevice.findDevices()
print(values)
tempicoDeviceNew = TempicoDevice(values[0])
tempicoDeviceNew.open()


# DevTemp=TempDevs()
# devices=DevTemp.findDevices()
# print(devices)