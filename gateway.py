#!/usr/bin/python

import math
import json
import serial
import os.path
import time
import queue
from collections import defaultdict
import calibration
import packethandler

#constants

zbport = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=1.0)                        #Open serial port connected to XBEE
zb = ZigBee(zbport)                                                                       #instantiate a Zigbee on the port above

#global variables with initial values

hum = 50
temp = 20.0
light = 0
RsRo = 1.00
tvoc = 0.9
CO2 = 400
PM2_5 = 0
PM10 = 0
intPM10 = 0
intPM2_5 = 0
intCO2 = 400
intLight = 0
floatTVOC = 0
floatHum = 50
floatTemp = 20.0
intNO2 = 0

def timestamp():
    stamp = time.strftime("%a, %d %b %Y %H:%M:%S ",time.localtime(time.time()))
    return stamp

##################### MAIN GATEWAY ROUTINE #######################
# Routine waits until a packet is received from a remote sensors #
#    checks source and sensor type then calls main sub-routine   #
##################################################################

list = [0,0]
sensorID_dict = {}                                      #global dictionary for storing checkChannel results
writeKey_dict = dict.fromkeys(range(1),list)            #global dictionary for storing writekeys,
print timestamp()
print "Starting Thingspeak processes"
time.sleep(3)
print "Checking for saved channel list"

if os.path.isfile("/home/pi/zigb2net/channelList.json"):
    print "Channel list exists"
    sensorID_dict = checkLocalChannels()
    print "sensorID_dict from file is", sensorID_dict
else:
    print "No saved channel list...downloading remote list"
    try :
         sensorID_dict = downloadChannels();
    except Exception:
         print "error downloading channel list"
         pass

if os.path.isfile("/home/pi/zigb2net/writeKeys.json"):
    print "Writekey list exists"
    writeKey_dict = checkLocalKeyList()
    print "writeKey_dict from file is", writeKey_dict
else:
    print "No saved writekey list"

while True:
    try:
        zbport.flushInput()                                        #clear serial buffer
        print "Waiting for packet..."
        packet = zb.wait_read_frame()                              #wait for incoming packet
        source = packet['source_addr_long'].encode('hex')          #read sending address
        incoming = packet['rf_data']                               #read incoming packet data
        print incoming                                             #show what's coming in
        if incoming[0] == "0":
            print "PM and VOC Data"
            sensortype,RsRo,PM2_5,PM10 = incoming.split(",")       #split data (comma separated values)
            print source,sensortype,RsRo,PM2_5,PM10                #print to verify
        tvoc = packethandler.TVOCcalc(RsRo)
        floatTVOC = float(tvoc)
            intPM10 = int(PM10)
            intPM2_5 = int(PM2_5)
        floatTVOC,intPM10,intPM2_5=calibration.Calibration(source, sensortype, floatTemp, floatHum, intLight, intCO2, floatTVOC, intPM10, intPM2_5)
        elif incoming[0] == "1":
            print "Temp,Hum & Lux Data"
            sensortype,hum,temp,light = incoming.split(",")        #split data (comma separated values)
            tempReplace = temp.replace(' ', '')
            lightReplace = light.replace('\n','')
            floatTemp = float(tempReplace)
            floatHum = float(hum)
            nanLight = packethandler.is_number(lightReplace)
            intLight = int(nanLight)
            print "Pre-calibration values are: " ,floatTemp, floatHum, intLight                                                         #print to verify
            floatTemp, floatHum, intLight=calibration.Calibration(source, sensortype, floatTemp, floatHum, intLight, intCO2, floatTVOC, intPM10, intPM2_5) #send to calibration function
            print "Post-calibration values are: ",floatTemp, floatHum, intLight                                                        #print to verify
        elif incoming[0] == "2":
            print "TVOC & Lux Data"
            sensortype,RsRo,light = incoming.split(",")            #add light to this once sensor hooked up
            lightReplace = light.replace('\n','')
        tvoc = packethandler.TVOCcalc(RsRo)                                      #not used!
        floatTVOC = float(tvoc)
            print source,sensortype,RsRo,light
            floatTVOC,intLight=calibration.Calibration(source,sensortype,floatTemp,floatHum,intLight,intCO2,floatTVOC,intPM10,intPM2_5)
        elif incoming[0] == "3":
        print "CO2 Data"
        sensortype,CO2 = incoming.split(",")                       #split data (comma separated values)
        intCO2 = int(CO2)
            print source,sensortype,CO2                            #print to verify
            intCO2=calibration.Calibration(source,sensortype,floatTemp,floatHum,intLight,intCO2,floatTVOC,intPM10,intPM2_5)
        elif incoming[0] == "4":
            print "PM, VOC & CO2 Data"
            sensortype,RsRo,PM2_5,PM10,CO2 = incoming.split(",")   #split data (comma separated values)
            tvoc = packethandler.TVOCcalc(RsRo)
            intCO2 = int(CO2)
            floatTVOC = float(tvoc)
            intPM10 = int(PM10)
            intPM2_5 = int(PM2_5)
            print "Pre-calibration values are: ",intCO2,floatTVOC,intPM10,intPM2_5             #print to verify
            intCO2,floatTVOC,intPM10,intPM2_5=calibration.Calibration(source,sensortype,floatTemp,floatHum,intLight,intCO2,floatTVOC,intPM10,intPM2_5)
            print "Post-calibration values are: ",intCO2,floatTVOC,intPM10,intPM2_5
        elif incoming[0] == "5":
            print "NO2,Temp & Hum Data"
            sensortype,intNO2,floatTemp,floatHum = incoming.split(",")                          #split data (comma separated values)
            print source,sensortype,intNO2,floatTemp,floatHum                                   #print to verify
        else:
            print "Non-recognised sensor type in Gateway Routine, Ed needs to fix this!"
        try:
            print timestamp()
            sensorID_dict = checkChannel(source, sensorID_dict)
        except Exception:
            sensorID_dict = {}
        ThingspeakProcess(source,sensortype,sensorID_dict,writeKey_dict)
        storeWriteKeys(writeKey_dict)
    except Exception:
       print "error is preventing upload, please check logs"
       pass

zbport.close()