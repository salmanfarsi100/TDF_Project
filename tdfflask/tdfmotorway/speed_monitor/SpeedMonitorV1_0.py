# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 00:11:35 2020

@author: nabeel.tahir
"""
#!/usr/bin/env python3
from argparse import ArgumentParser
from configparser import ConfigParser
from time import time
from datetime import datetime
import serial
import serial.tools.list_ports
from serial.serialutil import SerialException
import json
import sys
import select
from platform import system

class SpeedMonitor:
    def __init__(self, confgpath):
        self.confgpath=confgpath
        config = ConfigParser()
        config.read(self.confgpath)

        self.SpeedConfg =   config.options('SpeedSensorConfig')
        self.confsect  = config['SpeedSensorConfig']
        if system()=="Linux":
            self.port="/dev/ttyACM0"
        else:
            self.port= "COM4"
        self.buad_rate      =   self.confsect['brate']
        self.sample_freq    =   self.confsect['samplefreq']
        self.speed_unit     =   self.confsect['speedunit'] #Set speed unit
        self.v_direction    =   self.confsect['direction']
        self.fft_mode   =   self.confsect['FFTMode']
        self.Js_mode    =   self.confsect['JSMode']
        self.n_reports  =   self.confsect['NReports']
        self.s_reports  =   self.confsect['SReports']
        self.r_reports  =   self.confsect['RReports']
        self.u_reports   =   self.confsect['uReports']
        self.save_conf  =   self.confsect['SConf']  # Set unit report off
        #try:
        self.serial_port = serial.Serial(self.port, baudrate=int(self.buad_rate))
        #self.serial_port.open()
        #except serial.serialutil.SerialException:
        #    print ("Unable to connect port",self.port)

        if self.serial_port.isOpen():

            self.serial_port.timeout=5
            self.serial_port.reset_input_buffer()
            self.serial_port.flushInput()
            self.serial_port.flushOutput()
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
            self.serial_port.close()
            print("serial closed")
        else:
            print("Unable to initialize serial connection")
        self.stopserial()

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

                    baudrate=int(self.buad_rate)
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

        return str(data)

    def stopserial(self):
        self.serial_port.close()
