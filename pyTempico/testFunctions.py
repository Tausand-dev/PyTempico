import serial
from core import TempicoDevice as TempDev

#Test for abort measure

# tempicoDevice = TempDev('COM12')
# tempicoDevice.openTempico()
# valueIdn=tempicoDevice.getIdn()
# tempicoDevice.measure()
# tempicoDevice.abortMeasure()
# print(tempicoDevice.fetch())
# tempicoDevice.close()
#change
#Test for selfTest
# tempicoDevice = TempDev('COM12')
# tempicoDevice.openTempico()
# tempicoDevice.selfTest()
# tempicoDevice.close()

#Test tempico devices
# tempicoDevice = TempDev('COM12')
# portsFound=tempicoDevice.findDevices()
# print(portsFound)

#Test new open function
tempicoDevice = TempDev('COM42')
tempicoDevice.openTempico()
tempicoDevice.close()
