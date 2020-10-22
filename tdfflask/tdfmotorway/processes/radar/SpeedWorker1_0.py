import serial
from serial.serialutil import SerialException
import json
import time
import pandas as pd
import numpy as np
BASE = "http://0.0.0.0:80/"     # local host
import requests
from datetime import datetime
class SpeedWorker:

    def __init__(self,port,baud_rate,logger ):
        self.baud_rate=baud_rate
        self.port=port
        self.logger=logger
        self.stopflag=True
        self.serial_port=None
        try:
            self.serial_port=serial.Serial(self.port,baudrate=int(self.baud_rate))
            self.serial_port.reset_input_buffer()
            self.serial_port.flushInput()
            self.serial_port.flushOutput()
            self.logger.info("Worker initialized")
            if self.serial_port.isOpen():
                x=self.serial_port .readline().decode()

            #self.serial_port.close()    #print(x)
        except SerialException:
            logger.exception("Serial Exception while initializing worker")

    def process_speed(self):
        range_value=np.zeros(10,dtype=float)
        speed_value=np.zeros(10,dtype=float)
        rangeind=0
        speedind=0
        decreasingflage=False
        self.logger.info("Worker Working")
        self.serial_port.reset_input_buffer()
        self.serial_port.flushInput()
        self.serial_port.flushOutput()
        while self.stopflag:
            try:
                if self.serial_port.isOpen():
                    try:
                        x=self.serial_port.readline().decode('utf8','strict')
                    except UnicodeDecodeError:
                        self.logger.exception("Serial Decoding Error")
                    try:
                        ndata=json.loads(x)
                        if 'range' in ndata.keys():
                            #print("raneg",float(ndata['range']))
                            #print(range_value.shape[0])
                            if rangeind==range_value.shape[0]:
                                if (pd.Series(range_value).is_monotonic_decreasing):
                                    decreasingflage=True
                                    #print("occured")
                                rangeind=0
                            range_value[rangeind]=float(ndata['range'])
                            rangeind+=1
                            #print("range", range_value)

                        elif 'speed' in ndata.keys():
                            #speeddata=np.zeros(len(ndata['speed']))
                            #print("original",ndata['speed'])
                            #try:
                                if speedind==speed_value.shape[0]:
                                    speedind=0
                                speed_value[speedind]=float(ndata['speed'])

                                if decreasingflage:
                                    decreasingflage=False
                                    #print("range", range_value[rangeind-1]) # Here It will send the data to server
                                    #print("speed", speed_value[speedind])
                                    now = datetime.now()
                                    dt_string = now.strftime('%d/%m/%Y %H:%M:%S')
                                    res = requests.post(BASE + 'speed/', json = {"speed": str(range_value[rangeind-1]), "range": str(speed_value[speedind]),"date_time":str(dt_string)})
                                    if res.ok:
                                        print(res.json())
                                speedind+=1;

#                            except TypeError:
#                                speeddata=np.zeros(len(ndata['speed']))
#                                for i in range(len(ndata['speed'])):
#                                    speeddata[i] = float(ndata['speed'][i])
#                                if decreasingflage:
#                                    print("occured")
#                                    decreasingflage=False
                                #print("speed",speed_value)


                    except json.decoder.JSONDecodeError:
                        self.logger.exception("Error while decoding JSON string in worker")


                            #speeddata[i]=float(temp)

                        #speeddata=ndata['speed']

                    #print("Worker process",x)
            except SerialException:
                self.logger.exception("Serial Exception in worker speed process")

            #time.sleep(1)

    def stopworker(self):
        self.stopflag=False
        self.serial_port.close()
        print("False")
