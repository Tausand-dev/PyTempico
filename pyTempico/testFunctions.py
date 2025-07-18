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
# tempDevice.setDateTime()
# print(tempDevice.getDateTime())

# tempDevice.setDateTime(1677854900.0)
# print("New time")
# print(tempDevice.getDateTime(True))
# print("Maximun time")
# print(tempDevice.getMaximumDatetime(True))
# print("Minimum time")
# print(tempDevice.getMinimumDatetime(True))



tempDevice= TempicoDevice("COM5")
tempDevice.open()
tempDevice.setAverageCycles(1,64)
tempDevice.setAverageCycles(2,32)
tempDevice.setAverageCycles(3,16)
tempDevice.setAverageCycles(4,2)
print("Average cycles channel A")
print(tempDevice.getAverageCycles(1))
print("Average cycles channel B")
print(tempDevice.getAverageCycles(2))
print("Average cycles channel C")
print(tempDevice.getAverageCycles(3))
print("Average cycles channel D")
print(tempDevice.getAverageCycles(4))
tempDevice.setNumberOfStops(1,5)
tempDevice.setNumberOfStops(2,4)
tempDevice.setNumberOfStops(3,3)
tempDevice.setNumberOfStops(4,2)
print("Number of stops channel A")
print(tempDevice.getNumberOfStops(1))
print("Number of stops channel B")
print(tempDevice.getNumberOfStops(2))
print("Number of stops channel C")
print(tempDevice.getNumberOfStops(3))
print("Number of stops channel D")
print(tempDevice.getNumberOfStops(4))
tempDevice.setMode(1,1)
tempDevice.setMode(2,2)
tempDevice.setMode(3,1)
tempDevice.setMode(4,2)
print("Mode channel A")
print(tempDevice.getMode(1))
print("Mode channel B")
print(tempDevice.getMode(2))
print("Mode channel C")
print(tempDevice.getMode(3))
print("Mode channel D")
print(tempDevice.getMode(4))
tempDevice.setStartEdge(1,"FALL")
tempDevice.setStartEdge(2,"RISE")
tempDevice.setStartEdge(3,"FALL")
tempDevice.setStartEdge(4,"RISE")
print("Start edge channel A")
print(tempDevice.getStartEdge(1))
print("Start edge channel B")
print(tempDevice.getStartEdge(2))
print("Start edge channel C")
print(tempDevice.getStartEdge(3))
print("Start edge channel D")
print(tempDevice.getStartEdge(4))
tempDevice.setStopEdge(1,"FALL")
tempDevice.setStopEdge(2,"RISE")
tempDevice.setStopEdge(3,"FALL")
tempDevice.setStopEdge(4,"RISE")
print("Stop edge channel A")
print(tempDevice.getStopEdge(1))
print("Stop edge channel B")
print(tempDevice.getStopEdge(2))
print("Stop edge channel C")
print(tempDevice.getStopEdge(3))
print("Stop edge channel D")
print(tempDevice.getStopEdge(4))
tempDevice.setStopMask(1,100)
tempDevice.setStopMask(2,200)
tempDevice.setStopMask(3,300)
tempDevice.setStopMask(4,500)
print("Stop Mask channel A")
print(tempDevice.getStopMask(1))
print("Stop Mask channel B")
print(tempDevice.getStopMask(2))
print("Stop Mask channel C")
print(tempDevice.getStopMask(3))
print("Stop Mask channel D")
print(tempDevice.getStopMask(4))

#Test enable functions
tempDevice.disableChannel(1)
tempDevice.disableChannel(3)
print("Enable channel A")
print(tempDevice.isEnabled(1))
print("Enable channel B")
print(tempDevice.isEnabled(2))
print("Enable channel C")
print(tempDevice.isEnabled(3))
print("Enable channel D")
print(tempDevice.isEnabled(4))
tempDevice.enableChannel(1)
tempDevice.enableChannel(3)
print("Enable channel A")
print(tempDevice.isEnabled(1))
print("Enable channel B")
print(tempDevice.isEnabled(2))
print("Enable channel C")
print(tempDevice.isEnabled(3))
print("Enable channel D")
print(tempDevice.isEnabled(4))
print(tempDevice.getSerialNumber())