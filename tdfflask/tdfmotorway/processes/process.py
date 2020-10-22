# importing the multiprocessing module 
import multiprocessing 
import os 
import subprocess
from radar.SpeedMonitorV1_1 import SpeedMonitor
from radar.SpeedWorker1_0 import SpeedWorker
import logging
import time
from platform import system

logger = logging.getLogger('Speedworker')
hdlr = logging.FileHandler('speedworker.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)
confpath="../../tdfmotorway/config.ini"

if system()=="Linux":
	port="/dev/ttyACM0"
else:
	port= "COM4"

Sp=SpeedMonitor(confpath)
speedworker=SpeedWorker(port,9600,logger)

def worker1(): 
	subprocess.call(['lxterminal -e sudo python3 ofe_new.py file:///home/jetsonuser/Videos/vid301_cropped.264 frames'], cwd='/opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/processes/ofe', shell=True)
	print("ID of process running worker1: {}".format(os.getpid())) 		# printing process id 

def worker2(): 
	# printing process id 
	print("ID of process running worker2: {}".format(os.getpid()))
	subprocess.call(['lxterminal'], cwd='/opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/processes/ofe', shell=True) 

if __name__ == "__main__": 
	# printing main program process id 
	print("ID of main process: {}".format(os.getpid())) 

	# creating processes 
	p1 = multiprocessing.Process(target=worker1) 
	p2 = multiprocessing.Process(target=speedworker.process_speed) 

	# starting processes 
	p1.start() 
	p2.start() 

	# process IDs 
	print("ID of process p1: {}".format(p1.pid)) 
	print("ID of process p2: {}".format(p2.pid)) 

	# wait until processes are finished 
	p1.join() 
	time.sleep(20)
	p2.terminate()
	time.sleep(2)
	p2.join()

	# both processes finished 
	print("Both processes finished execution!") 

	# check if processes are alive 
	print("Process p1 is alive: {}".format(p1.is_alive())) 
	print("Process p2 is alive: {}".format(p2.is_alive())) 
