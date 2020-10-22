# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 00:11:35 2020

@author: nabeel.tahir
"""
#!/usr/bin/env python3
#from multiprocessing import Process

from configparser import ConfigParser
import time
from datetime import datetime
import serial
import serial.tools.list_ports
from serial.serialutil import SerialException
import json
import sys
import select
from platform import system
import logging
#from SpeedWorker1_0 import SpeedWorker
Messages = ["Sensor Configured Successfully", "Serial Port Error"]
class SpeedMonitor:
    def __init__(self, configpath):
        self.configpath=configpath
        self.logger = logging.getLogger('SpeedMonitor')
        hdlr = logging.FileHandler('speedlog.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.DEBUG)

        if system()=="Linux":
            self.port="/dev/ttyACM0"
        else:
            self.port= "COM4"

        self.serial_port=None
        self.baud_rate=9600
        message = self.config_sensor(self.configpath)
        #print(self.baud_rate)
        #self.worker=SpeedWorker(self.port,self.baud_rate,self.logger)
        #self.proc1= Process(target=self.worker.process_speed)
        #self.proc1.start()

        #proc1.terminate()

        #self.worker.process_speed()
        #self.worker.stopworker()
        #print("stop")

        #try:

        #self.stopserial()

            #return "unable to connect to port"
        #print(self.confsect['brate'])
        #baudrate_int = int(config.get)
        #if baudrate_int <= 0:
        #baudrate_int = 57600

    def getspeed_range(self):

        if not self.serial_port.is_open:
            print("test1")
            try:

                self.serial_port = serial.Serial(self.port,
                #timeout=0.1,

                    baudrate=int(self.baud_rate)
                    )
                x=self.serial_port.readline()
                data=x.decode('utf8','strict')
                ndata=json.loads(data)
                while(list(ndata)[0]!='speed'):
                  x1=self.serial_port.readline()
                  data=x1.decode('utf8','strict')
                  ndata=json.loads(data)
                data = [json.loads(x.decode('utf8','strict')), ndata]
            except:
                return ("Unable to connect portn",self.port)
        elif self.serial_port.is_open:
            now=datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print("Before",current_time)
            x=self.serial_port.readline()
            data=x.decode('utf8','strict')
            ndata=json.loads(data)
            while(list(ndata)[0]!='speed'):
               x1=self.serial_port.readline()
               data=x1.decode('utf8','strict')
               ndata=json.loads(data)

            data = [json.loads(x.decode('utf8','strict')), ndata]
            now=datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print("After",current_time)
            #self.serial_port.close()
        else:
            print("Serial port Error")

        print(data)
        return str(data)

    def stopserial(self):

        self.proc1.terminate()
        self.worker.stopworker()
        #self.worker.process_speed()
        #self.serial_port.close()

    def config_sensor(self,configpath):
        config = ConfigParser()
        config.read(configpath)

        self.SpeedConfg =   config.options('SpeedSensorConfig')
        self.confsect   =   config['SpeedSensorConfig']
        self.baud_rate      =   self.confsect['brate']
        self.sample_freq    =   self.confsect['samplefreq']
        self.speed_unit     =   self.confsect['speedunit'] #Set speed unit
        self.v_direction    =   self.confsect['direction']
        self.fft_mode   =   self.confsect['FFTMode']
        self.Js_mode    =   self.confsect['JSMode']
        self.n_reports  =   self.confsect['NReports']
        self.s_reports  =   self.confsect['SReports']
        self.r_reports  =   self.confsect['RReports']
        self.u_reports  =   self.confsect['uReports']
        self.save_conf  =   self.confsect['SConf']  # Set unit report off

        #Open a serial connection for configurations

        #self.serial_port.open()
        #except serial.serialutil.SerialException:
        #    print ("Unable to connect port",self.port)
        try:
            self.serial_port = serial.Serial(self.port, baudrate=int(self.baud_rate))
            self.serial_port.reset_input_buffer()
            self.serial_port.flushInput()
            self.serial_port.flushOutput()
            if self.serial_port.isOpen():



                self.serial_port.write(self.sample_freq.encode('utf-8'))
                self.serial_port.write(self.speed_unit.encode('utf-8'))
                self.serial_port.write(self.v_direction.encode('utf-8'))
                self.serial_port.write(self.fft_mode.encode('utf-8'))
                self.serial_port.write(self.Js_mode.encode('utf-8'))
                self.serial_port.write(self.n_reports.encode('utf-8'))
                self.serial_port.write(self.r_reports.encode('utf-8'))
                self.serial_port.write(self.s_reports.encode('utf-8'))
                self.serial_port.write(self.u_reports.encode('utf-8'))
                self.serial_port .write(self.save_conf.encode('utf-8'))

                for i in range(10):
                    x=self.serial_port .readline().decode()
                    #print(x)
                self.serial_port.close()
                message = 0
                self.logger.info(Messages[message])

                #print("serial closed")
            else:
                message = "Unable to open serial port"#print("Unable to initialize serial connection")
        except SerialException as e:
            self.logger.exception("Serial Exception in sensor config")

            message = 1
            #sys.exit(1)
        return message
