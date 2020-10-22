from SpeedMonitorV1_1 import SpeedMonitor
import time

confpath="../../../tdfmotorway/config.ini"

Sp=SpeedMonitor(confpath)
time.sleep(20)
Sp.stopserial()
