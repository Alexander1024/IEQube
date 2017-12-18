#!/usr/bin/python
import config
import math
import json
import serial
import os.path
import time
import Queue
from collections import defaultdict
from xbee import ZigBee
import thingspeak
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
config.intPM10 = 0
config.intPM2_5 = 0
config.intCO2 = 400
config.intLight = 0
config.floatTVOC = 0
config.floatHum = 50
config.floatTemp = 20.0
config.intNO2 = 0

PORT = '/dev/ttyAMA0'
BAUD_RATE = 9600

packetQueue = Queue.Queue()

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
    sensorID_dict = thingspeak.checkLocalChannels()
    print "sensorID_dict from file is", sensorID_dict
else:
    print "No saved channel list...downloading remote list"
    try :
         sensorID_dict = thingspeak.downloadChannels();
	 print "downloaded existing channel IDs!"
    except Exception:
         print "error downloading channel list"
         pass

if os.path.isfile("/home/pi/zigb2net/writeKeys.json"):
    print "Writekey list exists"
    writeKey_dict = thingspeak.checkLocalKeyList()
    print "writeKey_dict from file is", writeKey_dict
else:
    print "No saved writekey list"

# Open serial port
xbeeSerial = serial.Serial(PORT, BAUD_RATE)

# read calibration files
Calib_CSV=csv.DictReader(open('Calib_CSV.csv','rb'))

#receives packet data and places it into the queue
def packet_received(data):
    packetQueue.put(data, block = False)

# Create API object, which spawns a new thread
xbee = ZigBee(xbeeSerial, callback=packet_received)

# main thread
xbeeSerial.flushInput()            #clear serial buffer

while True:
    try:
        time.sleep(0.1)
        if packetQueue.qsize() > 0:
            newPacket = packetQueue.get_nowait()
            print 'Packet received'
            print 'queue length is now', packetQueue.qsize()
            source = newPacket['source_addr_long'].encode('hex')
            incoming = newPacket['rf_data']
            Calib_CSV=csv.DictReader(open('Calib_CSV.csv','rb'))
            ######################
            print incoming[0]
            ######################
            if incoming[0] == "0":
                print "PM and VOC Data"
                sensortype,RsRo,PM2_5,PM10 = incoming.split(",")       #split data (comma separated values)
                tvoc = packethandler.TVOCcalc(RsRo)
                config.floatTVOC = float(tvoc)
                config.intPM10 = int(PM10)
                config.intPM2_5 = int(PM2_5)
                config.floatTVOC,config.intPM10,config.intPM2_5=calibration.Calibration(source, sensortype, config.floatTemp, config.floatHum, config.intLight, config.intCO2, config.floatTVOC, config.intPM10, config.intPM2_5)
            elif incoming[0] == "1":
                print "Temp,Hum & Lux Data"
                sensortype,hum,temp,light = incoming.split(",")        #split data (comma separated values)
                tempReplace = temp.replace(' ', '')
                lightReplace = light.replace('\n','')
                config.floatTemp = float(tempReplace)
                config.floatHum = float(hum)
                nanLight = packethandler.is_number(lightReplace)
                config.intLight = int(nanLight)
                print "Pre-calibration values are: ",config.floatTemp, config.floatHum, config.intLight                                                         #print to verify
                config.floatTemp, config.floatHum, config.intLight=calibration.Calibration(source, sensortype, config.floatTemp, config.floatHum, config.intLight, config.intCO2, config.floatTVOC, config.intPM10, config.intPM2_5) #send to calibration function
                print "Post-calibration values are: ",config.floatTemp, config.floatHum, config.intLight                                                        #print to verify
            elif incoming[0] == "2":
                print "TVOC & Lux Data"
                sensortype,RsRo,light = incoming.split(",")            #add light to this once sensor hooked up
                lightReplace = light.replace('\n','')
                tvoc = packethandler.TVOCcalc(RsRo)                                      #not used!
                config.floatTVOC = float(tvoc)
                print source,sensortype,RsRo,light
                config.floatTVOC,config.intLight=calibration.Calibration(source,sensortype,config.floatTemp,config.floatHum,config.intLight,config.intCO2,config.floatTVOC,config.intPM10,config.intPM2_5)
                elif incoming[0] == "3":
                print "CO2 Data"
                sensortype,CO2 = incoming.split(",")                       #split data (comma separated values)
                config.intCO2 = int(CO2)
                print source,sensortype,CO2                            #print to verify
                config.intCO2=calibration.Calibration(source,sensortype,config.floatTemp,config.floatHum,config.intLight,config.intCO2,config.floatTVOC,config.intPM10,config.intPM2_5)
            elif incoming[0] == "4":
                print "PM, VOC & CO2 Data"
                sensortype,RsRo,PM2_5,PM10,CO2 = incoming.split(",")   #split data (comma separated values)
                tvoc = packethandler.TVOCcalc(RsRo)
                config.intCO2 = int(CO2)
                config.floatTVOC = float(tvoc)
                config.intPM10 = int(PM10)
                config.intPM2_5 = int(PM2_5)
                print "Pre-calibration values are: ",config.intCO2,config.floatTVOC,config.intPM10,config.intPM2_5             #print to verify
                config.intCO2,config.floatTVOC,config.intPM10,config.intPM2_5=calibration.Calibration(source,sensortype,config.floatTemp,config.floatHum,config.intLight,config.intCO2,config.floatTVOC,config.intPM10,config.intPM2_5)
                print "Post-calibration values are: ",config.intCO2,config.floatTVOC,config.intPM10,config.intPM2_5
            elif incoming[0] == "5":
                print "NO2,Temp & Hum Data"
                config.sensortype,config.intNO2,config.floatTemp,config.floatHum = incoming.split(",")                          #split data (comma separated values)
                print source,sensortype,config.intNO2,config.floatTemp,config.floatHum                                   #print to verify
            else:
                print "Non-recognised sensor type in Gateway Routine, Ed needs to fix this!"
            try:
                print timestamp()
                sensorID_dict = thingspeak.checkChannel(source, sensorID_dict)
            except Exception:
                sensorID_dict = {}
            thingspeak.ThingspeakProcess(source,sensortype,sensorID_dict,writeKey_dict)
            thingspeak.storeWriteKeys(writeKey_dict)
    except KeyboardInterrupt:
        break

# halt() must be called before closing the serial port to ensure proper thread shutdown
xbee.halt()
xbeeSerial.close()