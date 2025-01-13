import serial
from core import TempicoDevice as TempDev

tempicoDevice = TempDev('COM12')
tempicoDevice.openTempico()
valueIdn=tempicoDevice.getIdn()
tempicoDevice.measure()
tempicoDevice.abortMeasure()
print(tempicoDevice.fetch())
tempicoDevice.close()
