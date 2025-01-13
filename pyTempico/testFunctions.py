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

#Test for selfTest
tempicoDevice = TempDev('COM12')
tempicoDevice.openTempico()
tempicoDevice.selfTest()
tempicoDevice.close()
