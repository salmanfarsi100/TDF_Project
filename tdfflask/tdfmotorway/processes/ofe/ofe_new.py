#!/usr/bin/env python3

################################################################################
# Copyright (c) 2020, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
################################################################################

import os
os.environ.pop("DISPLAY", None)

import shutil
import requests
from datetime import datetime
import sys
sys.path.append('../../../../')
import gi
import configparser
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from gi.repository import GLib
from ctypes import *
import time
import math
import platform
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.FPS import GETFPS
import numpy as np
import pyds
import cv2
# ~ import os
import os.path
from os import path
fps_streams={}
frame_count={}
saved_count={}
global PGIE_CLASS_ID_VEHICLE
PGIE_CLASS_ID_VEHICLE=0
global PGIE_CLASS_ID_PERSON
PGIE_CLASS_ID_PERSON=2

# ~ os.system("unset DISPLAY")

BASE = "http://0.0.0.0:80/"     # local host
    
MAX_DISPLAY_LEN=64
PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3
MUXER_OUTPUT_WIDTH=1920
MUXER_OUTPUT_HEIGHT=1080
MUXER_BATCH_TIMEOUT_USEC=4000000
TILED_OUTPUT_WIDTH=1920
TILED_OUTPUT_HEIGHT=1080
GST_CAPS_FEATURES_NVMM="memory:NVMM"
pgie_classes_str= ["Vehicle", "TwoWheeler", "Person","RoadSign"]

road = []   # list to obtain parameters initialized in 'road.txt'
par = []    # list to split parameters in road[]
# f = open('road.txt', 'r')
f = open('/opt/nvidia/deepstream/deepstream-5.0/sources/deepstream_python_apps/apps/tdfflask/tdfmotorway/road.ini', 'r')
road = f.readlines()
for r in road:
    temp = r.split()
    if len(temp) > 1:
        par.append(temp[1])
    else:
        par.append(int(0))

x11 = int(par[2])    # leftmost 'vertical' segment top; lane is to the left of segment
x12 = int(par[4])    # second lane from the left 'vertical' segment top
x13 = int(par[6])    # third lane from the left 'vertical' segment top
x14 = int(par[8])    # last lane from the left 'vertical' segment top
x21 = int(par[10])    # leftmost 'vertical' segment bottom
x22 = int(par[12])    # second lane from the left 'vertical' segment bottom
x23 = int(par[14])    # third lane from the left 'vertical' segment bottom
x24 = int(par[16])    # rightmost 'vertical' segment bottom
y11 = int(par[18])    # lane top y; for all lanes
y22 = int(par[20])    # lane bottom y; for all lanes
y1 = int(par[24])    # optimal range filter start 
y2 = int(par[26])    # optimal range filter end 

vehicle_list = []   # vehicle bounding box metadata buffer
rgb_frames_list = []    # video stream image metadata buffer
vehicle_count = 0   # total vehicles detected in stream

########## Vehicle Class ##########     # vehicle_list[] object class; described by the vehicle's tracking id, the number of frames it is tracked for, the coordinates of its bounding boxes and the lane it is tracked in

class Vehicle:
    def __init__(self, vehicle_id, frames_list=[], x_list=[], y_list=[], xc_list=[], yc_list=[], width_list=[], height_list=[], lane_list=[]):
        self.vehicle_id = vehicle_id
        self.frames_list = frames_list
        self.x_list = x_list
        self.y_list = y_list
        self.xc_list = xc_list
        self.yc_list = yc_list
        self.width_list = width_list
        self.height_list = height_list
        self.lane_list = lane_list

########## Vehicle Class ##########
        
########## RGB Frame Class ##########       # rgb_frames_list[] object class; described by the frame number and the pixel matrix of the frame

class RGB_Frame:
    def __init__(self, frame_iterator, rgb_image):
        self.frame_iterator = frame_iterator
        self.rgb_image = rgb_image

########## RGB Frame Class ##########

#response = requests.get(BASE + "road/1")
#x11 = int(response.json()['x11'])
#x12 = int(response.json()['x12'])
#x13 = int(response.json()['x13']) 
#x14 = int(response.json()['x14']) 
#x21 = int(response.json()['x21'])   
#x22 = int(response.json()['x22'])   
#x23 = int(response.json()['x23'])
#x24 = int(response.json()['x24'])   
#y11 = int(response.json()['y11'])   
#y22 = int(response.json()['y22'])  
#y1 = int(response.json()['y1'])   
#y2 = int(response.json()['y2'])   

# tiler_sink_pad_buffer_probe  will extract metadata received on tiler src pad
# and update params for drawing rectangle, object information etc.
def tiler_sink_pad_buffer_probe(pad,info,u_data):
    global x11, x12, x13, x14, x21, x22, x23, x24
    global y11, y22, y1, y2
    global vehicle_count
    frame_number=0
    num_rects=0
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return
        
    # Retrieve batch metadata from the gst_buffer
    # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
    # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    
    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
            # The casting is done by pyds.NvDsFrameMeta.cast()
            # The casting also keeps ownership of the underlying memory
            # in the C code, so the Python garbage collector will leave
            # it alone.
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            
        except StopIteration:
            break

        frame_number=frame_meta.frame_num
        l_obj=frame_meta.obj_meta_list
        num_rects = frame_meta.num_obj_meta
        obj_counter = {
        PGIE_CLASS_ID_VEHICLE:0,
        PGIE_CLASS_ID_PERSON:0,
        PGIE_CLASS_ID_BICYCLE:0,
        PGIE_CLASS_ID_ROADSIGN:0
        }
        while l_obj is not None:
            try: 
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta=pyds.NvDsObjectMeta.cast(l_obj.data)
                if obj_meta.class_id == PGIE_CLASS_ID_VEHICLE:  # vehicle detected
                    if obj_meta.rect_params.top >= y1 and obj_meta.rect_params.top <= y2:   # optimal range filter
                        car_found = 0   # vehicle id flag
                        for x in vehicle_list:
                            if x.vehicle_id == obj_meta.object_id:      # vehicle metadata lists are already initialized in vehicle_list
                                x.frames_list.append(frame_number)
                                x.x_list.append(obj_meta.rect_params.left)
                                x.y_list.append(obj_meta.rect_params.top)
                                x.xc_list.append(int(obj_meta.rect_params.left + (obj_meta.rect_params.width / 2)))
                                x.yc_list.append(int(obj_meta.rect_params.top + (obj_meta.rect_params.height / 2)))
                                x.width_list.append(obj_meta.rect_params.width)
                                x.height_list.append(obj_meta.rect_params.height)
                                x_center = int(obj_meta.rect_params.left + (obj_meta.rect_params.width / 2))
                                if x_center > min(x13, x23):
                                    x.lane_list.append('shoulder')
                                elif x_center > min(x12, x22):
                                    x.lane_list.append('slow')
                                elif x_center > min(x11, x21):
                                    x.lane_list.append('medium')
                                else:
                                    x.lane_list.append('fast')
                                car_found = 1   # vehicle metadata lists were already initialized in vehicle_list
                                break
                            
                        if car_found == 0:      # vehicle metadata lists are not initialized in vehicle_list
                            frames_temp_list = []
                            frames_temp_list.append(frame_number)
                            x_temp_list = []
                            x_temp_list.append(obj_meta.rect_params.left)
                            y_temp_list = []
                            y_temp_list.append(obj_meta.rect_params.top)
                            xc_temp_list = []
                            xc_temp_list.append(int(obj_meta.rect_params.left + (obj_meta.rect_params.width / 2)))
                            yc_temp_list = []
                            yc_temp_list.append(int(obj_meta.rect_params.top + (obj_meta.rect_params.height / 2)))
                            width_temp_list = []
                            width_temp_list.append(obj_meta.rect_params.width)
                            height_temp_list = []
                            height_temp_list.append(obj_meta.rect_params.height)
                            x_center = int(obj_meta.rect_params.left + (obj_meta.rect_params.width / 2))
                            lane_temp_list = []
                            if x_center > min(x13, x23):
                                lane_temp_list.append('shoulder')
                            elif x_center > min(x12, x22):
                                lane_temp_list.append('slow')
                            elif x_center > min(x11, x21):
                                lane_temp_list.append('medium')
                            else:
                                lane_temp_list.append('fast')
                                
                            vehicle_list.append(Vehicle(obj_meta.object_id, frames_temp_list, x_temp_list, y_temp_list, xc_temp_list, yc_temp_list, width_temp_list, height_temp_list, lane_temp_list))     # initialize vehicle metadata lists
                        
                    print('Vehicle ID = ', obj_meta.object_id, ', Frame Number = ', frame_number, ', Top X = ', obj_meta.rect_params.left,', Top Y = ', obj_meta.rect_params.top, ', Width = ', obj_meta.rect_params.width, ', Height = ', obj_meta.rect_params.height)     # show metadata of vehicle detection instance

                    for i, o in enumerate(vehicle_list):        
                        frame_lag = abs(int(o.frames_list[-1]) - int(frame_number))     # how far behind is the vehicle object; usually, a difference at least two frames signifies a stop or break in tracking activity
                        if (frame_lag > 20) and int(len(o.frames_list)) <= 6:   # vehicle count rectifier; eliminates false tracking instances, i.e., ones not tracked long enough for conclusive tracking train resolution
                            print('inadequate number of frames in train, deleting...', '\n')
                            del vehicle_list[i]
                            break
                        
                        if frame_lag > 20 and frame_lag < 100:      # optimal frame extractor...the business end
                            vehicle_count += 1
                            midpoint = int((y1 + y2) / 2)       # reference point of optimality
                            my_array = np.array(o.yc_list)
                            pos = (np.abs(my_array - midpoint)).argmin()    # position of frame - in the vehicle object y coordinates list - closest to the midpoint of optimal range
                            temp_frame_number = o.frames_list[pos]
                            temp_id = o.vehicle_id
                            now = datetime.now()
                            dt_string = now.strftime('%d/%m/%Y %H:%M:%S')
                            image_path = folder_name+"/stream_"+str(0)+"/numb_frno_trid="+str(vehicle_count)+'_'+str(temp_frame_number)+'_'+str(temp_id)+".jpg"
                            #response = requests.put(BASE + "vehicle/" + str(o.vehicle_id), {"frame_number": str(o.frames_list[pos]), "lane": str(o.lane_list[pos]), "datetime": str(dt_string), "image_path": str(image_path)})     # add to server database
                            #response = requests.put(BASE + "camera/", {"tracking_id": str(o.vehicle_id), "frame_number": str(o.frames_list[pos]), "lane": str(o.lane_list[pos]), "datetime": str(dt_string), "image_path": str(image_path)})
                            #response = requests.post(BASE + "camera_post/", data = {"tracking_id": str(o.vehicle_id), "frame_number": str(o.frames_list[pos]), "lane": str(o.lane_list[pos]), "datetime": str(dt_string), "image_path": str(image_path)})
                            #print(response.json())
                            # res = requests.post(BASE + 'camera_post/', json = {"tracking_id": str(o.vehicle_id), "frame_number": str(o.frames_list[pos]), "lane": str(o.lane_list[pos]), "datetime": str(dt_string), "image_path": str(image_path)})
                            
                            res = requests.post(BASE + 'camera/', json = {"tracking_id": str(o.vehicle_id), "frame_number": str(o.frames_list[pos]), "lane": str(o.lane_list[pos]), "datetime": str(dt_string), "image_path": str(image_path)})
                            if res.ok:
                                print(res.json())
                            
                            with open('optimal_frame_extraction.txt', 'a') as the_file:
                                the_file.write(str(o.frames_list[pos]))
                                the_file.write(' ')
                                the_file.write(str(o.vehicle_id))
                                the_file.write(' ')
                                the_file.write(str(o.width_list[pos]))
                                the_file.write(' ')
                                the_file.write(str(o.height_list[pos]))
                                the_file.write(' ')
                                the_file.write(str(o.x_list[pos]))
                                the_file.write(' ')
                                the_file.write(str(o.y_list[pos]))
                                the_file.write(' ')
                                the_file.write(str(o.lane_list[pos]))
                                the_file.write(' ')
                                the_file.write(str(dt_string))
                                the_file.write('\n')
                            xx1 = int(o.x_list[pos])
                            xx2 = int(o.x_list[pos]) + int(o.width_list[pos])
                            yy1 = int(o.y_list[pos])
                            yy2 = int(o.y_list[pos]) + int(o.height_list[pos])
                            del vehicle_list[i]
                            finder = 0
                            for f in rgb_frames_list:
                                if f.frame_iterator == temp_frame_number:
                                    break
                                else:
                                    finder += 1
                            crop = (rgb_frames_list[finder].rgb_image)[yy1:yy2, xx1:xx2]    # crop the part of the frame bounding the vehicle
                            cv2.imwrite(folder_name+"/stream_"+str(0)+"/numb_frno_trid="+str(vehicle_count)+'_'+str(temp_frame_number)+'_'+str(temp_id)+".jpg", crop)
                            break
                            
                        if frame_lag > 100:     # vehicle buffer cleaner; eliminates expired tracking instances
                            print('train expired, deleting...', '\n')
                            del vehicle_list[i]
                            break
                                       
            except StopIteration:
                break
            obj_counter[obj_meta.class_id] += 1
            
            try: 
                l_obj=l_obj.next
            except StopIteration:
                break

        print("Frame Number =", frame_number, "Number of Objects in frame =",num_rects,"Vehicles in frame =",obj_counter[PGIE_CLASS_ID_VEHICLE],"Total Vehicles Detected =",vehicle_count)      # metadata overlay
        # Get frame rate through this probe
        fps_streams["stream{0}".format(frame_meta.pad_index)].get_fps()
        #if save_image:
        #    cv2.imwrite(folder_name+"/stream_"+str(frame_meta.pad_index)+"/frame_"+str(frame_number)+".jpg",frame_image)
        #saved_count["stream_"+str(frame_meta.pad_index)]+=1 
        
        # Acquiring a display meta object. The memory ownership remains in
        # the C code so downstream plugins can still access it. Otherwise
        # the garbage collector will claim it when this probe function exits.
        display_meta=pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 1
        py_nvosd_text_params = display_meta.text_params[0]
        # Setting display text to be shown on screen
        # Note that the pyds module allocates a buffer for the string, and the
        # memory will not be claimed by the garbage collector.
        # Reading the display_text field here will return the C address of the
        # allocated string. Use pyds.get_string() to get the string content.
        py_nvosd_text_params.display_text = "Frame Number={} Number of Objects={} Vehicle_count={} Total Vehicles Detected={}".format(frame_number, num_rects, obj_counter[PGIE_CLASS_ID_VEHICLE], vehicle_count)

        # Now set the offsets where the string should appear
        py_nvosd_text_params.x_offset = 10
        py_nvosd_text_params.y_offset = 12

        # Font , font-color and font-size
        py_nvosd_text_params.font_params.font_name = "Serif"
        py_nvosd_text_params.font_params.font_size = 10
        # set(red, green, blue, alpha); set to White
        py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

        # Text background color
        py_nvosd_text_params.set_bg_clr = 1
        # set(red, green, blue, alpha); set to Black
        py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
        # Using pyds.get_string() to get display_text as string
        print(pyds.get_string(py_nvosd_text_params.display_text))
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        
        # Draw x11_x21
        py_nvosd_line_params = display_meta.line_params[0]
        py_nvosd_line_params.x1 = x11
        py_nvosd_line_params.y1 = y11
        py_nvosd_line_params.x2 = x21
        py_nvosd_line_params.y2 = y22
        py_nvosd_line_params.line_width = 5
        py_nvosd_line_params.line_color.set(0.0, 1.0, 0.0, 1.0)
        display_meta.num_lines = display_meta.num_lines + 1
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        x11 = py_nvosd_line_params.x1
        x21 = py_nvosd_line_params.x2

        # Draw x12_x22
        py_nvosd_line_params = display_meta.line_params[1]
        py_nvosd_line_params.x1 = x12
        py_nvosd_line_params.y1 = y11
        py_nvosd_line_params.x2 = x22
        py_nvosd_line_params.y2 = y22
        py_nvosd_line_params.line_width = 5
        py_nvosd_line_params.line_color.set(0.0, 1.0, 0.0, 1.0)
        display_meta.num_lines = display_meta.num_lines + 1
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        x12 = py_nvosd_line_params.x1
        x22 = py_nvosd_line_params.x2

        # Draw x13_x23
        py_nvosd_line_params = display_meta.line_params[2]
        py_nvosd_line_params.x1 = x13
        py_nvosd_line_params.y1 = y11
        py_nvosd_line_params.x2 = x23
        py_nvosd_line_params.y2 = y22
        py_nvosd_line_params.line_width = 5
        py_nvosd_line_params.line_color.set(0.0, 1.0, 0.0, 1.0)
        display_meta.num_lines = display_meta.num_lines + 1
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        x13 = py_nvosd_line_params.x1
        x23 = py_nvosd_line_params.x2

        # Draw x14_x24
        py_nvosd_line_params = display_meta.line_params[3]
        py_nvosd_line_params.x1 = x14
        py_nvosd_line_params.y1 = y11
        py_nvosd_line_params.x2 = x24
        py_nvosd_line_params.y2 = y22
        py_nvosd_line_params.line_width = 5
        py_nvosd_line_params.line_color.set(0.0, 1.0, 0.0, 1.0)
        display_meta.num_lines = display_meta.num_lines + 1
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        x14 = py_nvosd_line_params.x1
        x24 = py_nvosd_line_params.x2
        
        # save current frame to rgb_frames_list
        n_frame=pyds.get_nvds_buf_surface(hash(gst_buffer),frame_meta.batch_id)
        frame_image=np.array(n_frame,copy=True,order='C')
        frame_image=cv2.cvtColor(frame_image,cv2.COLOR_RGBA2BGRA)
        rgb_frames_list.append(RGB_Frame(frame_number, frame_image))
        if len(rgb_frames_list) > 120:      # drop expired frames; extend frame life by increasing this value (may cause Jetson to shutdown)
            for x in range(20):
                del rgb_frames_list[x]
        
        try:
            l_frame=l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK

def draw_bounding_boxes(image,obj_meta,confidence):
    confidence='{0:.2f}'.format(confidence)
    rect_params=obj_meta.rect_params
    top=int(rect_params.top)
    left=int(rect_params.left)
    width=int(rect_params.width)
    height=int(rect_params.height)
    obj_name=pgie_classes_str[obj_meta.class_id]
    image=cv2.rectangle(image,(left,top),(left+width,top+height),(0,0,255,0),2)
    # Note that on some systems cv2.putText erroneously draws horizontal lines across the image
    image=cv2.putText(image,obj_name+',C='+str(confidence),(left-10,top-10),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,255,0),2)
    return image

def cb_newpad(decodebin, decoder_src_pad,data):
    print("In cb_newpad\n")
    caps=decoder_src_pad.get_current_caps()
    gststruct=caps.get_structure(0)
    gstname=gststruct.get_name()
    source_bin=data
    features=caps.get_features(0)

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
    if(gstname.find("video")!=-1):
        # Link the decodebin pad only if decodebin has picked nvidia
        # decoder plugin nvdec_*. We do this by checking if the pad caps contain
        # NVMM memory features.
        if features.contains("memory:NVMM"):
            # Get the source bin ghost pad
            bin_ghost_pad=source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
        else:
            sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")

def decodebin_child_added(child_proxy,Object,name,user_data):
    print("Decodebin child added:", name, "\n")
    if(name.find("decodebin") != -1):
        Object.connect("child-added",decodebin_child_added,user_data)   
    if(is_aarch64() and name.find("nvv4l2decoder") != -1):
        print("Seting bufapi_version\n")
        Object.set_property("bufapi-version",True)

def create_source_bin(index,uri):
    print("Creating source bin")

    # Create a source GstBin to abstract this bin's content from the rest of the
    # pipeline
    bin_name="source-bin-%02d" %index
    print(bin_name)
    nbin=Gst.Bin.new(bin_name)
    if not nbin:
        sys.stderr.write(" Unable to create source bin \n")

    # Source element for reading from the uri.
    # We will use decodebin and let it figure out the container format of the
    # stream and the codec and plug the appropriate demux and decode plugins.
    uri_decode_bin=Gst.ElementFactory.make("uridecodebin", "uri-decode-bin")
    if not uri_decode_bin:
        sys.stderr.write(" Unable to create uri decode bin \n")
    # We set the input uri to the source element
    uri_decode_bin.set_property("uri",uri)
    # Connect to the "pad-added" signal of the decodebin which generates a
    # callback once a new pad for raw data has beed created by the decodebin
    uri_decode_bin.connect("pad-added",cb_newpad,nbin)
    uri_decode_bin.connect("child-added",decodebin_child_added,nbin)

    # We need to create a ghost pad for the source bin which will act as a proxy
    # for the video decoder src pad. The ghost pad will not have a target right
    # now. Once the decode bin creates the video decoder and generates the
    # cb_newpad callback, we will set the ghost pad target to the video decoder
    # src pad.
    Gst.Bin.add(nbin,uri_decode_bin)
    bin_pad=nbin.add_pad(Gst.GhostPad.new_no_target("src",Gst.PadDirection.SRC))
    if not bin_pad:
        sys.stderr.write(" Failed to add ghost pad in source bin \n")
        return None
    return nbin

def main(args):
    f = open('optimal_frame_extraction.txt', 'w')       # erase previous contents
    f.close()
    with open('optimal_frame_extraction.txt', 'a') as the_file:
        the_file.write(str('f-no v-id wid hei x-top y-left lane date time'))
        the_file.write('\n')
    f.close()
    
    # Check input arguments
    if len(args) < 2:
        sys.stderr.write("usage: %s <uri1> [uri2] ... [uriN] <folder to save frames>\n" % args[0])
        sys.exit(1)

    for i in range(0,len(args)-2):
        fps_streams["stream{0}".format(i)]=GETFPS(i)
    number_sources=len(args)-2

    global folder_name
    folder_name=args[-1]
    if path.exists(folder_name):
        sys.stderr.write("The output folder %s already exists. Removing...\n" % folder_name)
        shutil.rmtree(folder_name, ignore_errors=True)
        #sys.exit(1)

    os.mkdir(folder_name)
    print("Frames will be saved in ",folder_name)
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    # Create gstreamer elements */
    # Create Pipeline element that will form a connection of other elements
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()
    is_live = False

    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")
    print("Creating streamux \n ")

    # Create nvstreammux instance to form batches from one or more sources.
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux \n")

    pipeline.add(streammux)
    for i in range(number_sources):
        os.mkdir(folder_name+"/stream_"+str(i))
        frame_count["stream_"+str(i)]=0
        saved_count["stream_"+str(i)]=0
        print("Creating source_bin ",i," \n ")
        uri_name=args[i+1]
        if uri_name.find("rtsp://") == 0 :
            is_live = True
        source_bin=create_source_bin(i, uri_name)
        if not source_bin:
            sys.stderr.write("Unable to create source bin \n")
        pipeline.add(source_bin)
        padname="sink_%u" %i
        sinkpad= streammux.get_request_pad(padname) 
        if not sinkpad:
            sys.stderr.write("Unable to create sink pad bin \n")
        srcpad=source_bin.get_static_pad("src")
        if not srcpad:
            sys.stderr.write("Unable to create src pad bin \n")
        srcpad.link(sinkpad)
    print("Creating Pgie \n ")
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie \n")
        
    tracker = Gst.ElementFactory.make("nvtracker", "tracker")       # tracker to assign unique ids to objects
    if not tracker:
        sys.stderr.write(" Unable to create tracker \n")
    
    # Add nvvidconv1 and filter1 to convert the frames to RGBA
    # which is easier to work with in Python.
    print("Creating nvvidconv1 \n ")
    nvvidconv1 = Gst.ElementFactory.make("nvvideoconvert", "convertor1")
    if not nvvidconv1:
        sys.stderr.write(" Unable to create nvvidconv1 \n")
    print("Creating filter1 \n ")
    caps1 = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA")
    filter1 = Gst.ElementFactory.make("capsfilter", "filter1")
    if not filter1:
        sys.stderr.write(" Unable to get the caps filter1 \n")
    filter1.set_property("caps", caps1)
    print("Creating tiler \n ")
    tiler=Gst.ElementFactory.make("nvmultistreamtiler", "nvtiler")
    if not tiler:
        sys.stderr.write(" Unable to create tiler \n")
    print("Creating nvvidconv \n ")
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not nvvidconv:
        sys.stderr.write(" Unable to create nvvidconv \n")
    print("Creating nvosd \n ")
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    if not nvosd:
        sys.stderr.write(" Unable to create nvosd \n")
    if(is_aarch64()):
        print("Creating transform \n ")
        transform=Gst.ElementFactory.make("nvegltransform", "nvegl-transform")
        if not transform:
            sys.stderr.write(" Unable to create transform \n")

    print("Creating EGLSink \n")
    sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
    if not sink:
        sys.stderr.write(" Unable to create egl sink \n")

    if is_live:
        print("Atleast one of the sources is live")
        streammux.set_property('live-source', 1)

    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('batch-size', number_sources)
    streammux.set_property('batched-push-timeout', 4000000)
    pgie.set_property('config-file-path', "dstest_imagedata_config.txt")
    pgie_batch_size=pgie.get_property("batch-size")
    if(pgie_batch_size != number_sources):
        print("WARNING: Overriding infer-config batch-size",pgie_batch_size," with number of sources ", number_sources," \n")
        pgie.set_property("batch-size",number_sources)
    tiler_rows=int(math.sqrt(number_sources))
    tiler_columns=int(math.ceil((1.0*number_sources)/tiler_rows))
    tiler.set_property("rows",tiler_rows)
    tiler.set_property("columns",tiler_columns)
    tiler.set_property("width", TILED_OUTPUT_WIDTH)
    tiler.set_property("height", TILED_OUTPUT_HEIGHT)

    sink.set_property("sync", 0)

    # Set properties of tracker
    config = configparser.ConfigParser()
    config.read('dstest2_tracker_config.txt')
    config.sections()

    for key in config['tracker']:
        if key == 'tracker-width' :
            tracker_width = config.getint('tracker', key)
            tracker.set_property('tracker-width', tracker_width)
        if key == 'tracker-height' :
            tracker_height = config.getint('tracker', key)
            tracker.set_property('tracker-height', tracker_height)
        if key == 'gpu-id' :
            tracker_gpu_id = config.getint('tracker', key)
            tracker.set_property('gpu_id', tracker_gpu_id)
        if key == 'll-lib-file' :
            tracker_ll_lib_file = config.get('tracker', key)
            tracker.set_property('ll-lib-file', tracker_ll_lib_file)
        if key == 'll-config-file' :
            tracker_ll_config_file = config.get('tracker', key)
            tracker.set_property('ll-config-file', tracker_ll_config_file)
        if key == 'enable-batch-process' :
            tracker_enable_batch_process = config.getint('tracker', key)
            tracker.set_property('enable_batch_process', tracker_enable_batch_process)

    if not is_aarch64():
        # Use CUDA unified memory in the pipeline so frames
        # can be easily accessed on CPU in Python.
        mem_type = int(pyds.NVBUF_MEM_CUDA_UNIFIED)
        streammux.set_property("nvbuf-memory-type", mem_type)
        nvvidconv.set_property("nvbuf-memory-type", mem_type)
        nvvidconv1.set_property("nvbuf-memory-type", mem_type)
        tiler.set_property("nvbuf-memory-type", mem_type)

    print("Adding elements to Pipeline \n")
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(tiler)
    pipeline.add(nvvidconv)
    pipeline.add(filter1)
    pipeline.add(nvvidconv1)
    pipeline.add(nvosd)
    if is_aarch64():
        pipeline.add(transform)
    pipeline.add(sink)

    print("Linking elements in the Pipeline \n")
    streammux.link(pgie)    
    pgie.link(tracker)
    tracker.link(nvvidconv1)
    nvvidconv1.link(filter1)
    filter1.link(tiler)
    tiler.link(nvvidconv)
    nvvidconv.link(nvosd)
    if is_aarch64():
        nvosd.link(transform)
        transform.link(sink)
    else:
        nvosd.link(sink)

    # create an event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)

    tiler_sink_pad=tiler.get_static_pad("sink")
    if not tiler_sink_pad:
        sys.stderr.write(" Unable to get src pad \n")
    else:
        tiler_sink_pad.add_probe(Gst.PadProbeType.BUFFER, tiler_sink_pad_buffer_probe, 0)

    # List the sources
    print("Now playing...")
    for i, source in enumerate(args[:-1]):
        if (i != 0):
            print(i, ": ", source)

    print("Starting pipeline \n")
    # start play back and listed to events		
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except:
        pass

    # cleanup
    print("Exiting app\n")
    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
