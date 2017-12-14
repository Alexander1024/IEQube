#! /usr/bin/python

import math
import urllib, httplib
import json

headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}  #standard headers for all Thspeak communications
conn = httplib.HTTPConnection("api.thingspeak.com:80")    #standard conn to main Thspeak server - update for personal server
user_ID = 'cundall'         #User ID used to create Thingspeak account - VITAL
user_key = 'P13RYTD0TZ2RVA1P'      #write API key - found at https://thingspeak.com/account, allows read & write operations - VITAL

def newchannelParams(sensorID,sensortype):

    try:
        if sensortype == "0": #TVOC,PM2.5,PM10
            print "TVOC, PM2.5, PM10 Sensor"
            params = urllib.urlencode({'name': sensorID,'field1': field4name, 'field2':field5name, 'field3':field6name, 'api_key':user_key})
            return params
        elif sensortype == "1": #Temp,Hum,Lux sensor
            print "New Temp, Hum, Lux Sensor"
            params = urllib.urlencode({'name': sensorID,'field1': field1name, 'field2':field2name, 'field3':field3name, 'api_key':user_key})
            return params
        elif sensortype == "2": #TVOC,Lux sensor
            print "New TVOC, Lux Sensor"
            params = urllib.urlencode({'name': sensorID,'field1': field4name, 'field2':field3name, 'api_key':user_key})
            return params
        elif sensortype == "3": #CO2 Sensor
            print "New CO2 Sensor"
            params = urllib.urlencode({'name': sensorID,'field1': field7name, 'api_key':user_key})
            return params
        elif sensortype == "4": #TVOC,PM2.5,PM10,CO2 Sensor
            print "TVOC, PM2.5, PM10, CO2 Sensor"
            params = urllib.urlencode({'name': sensorID,'field1': field4name, 'field2':field5name, 'field3':field6name, 'field4':field7name,'api_key':user_key})
            return params
        elif sensortype == "5": #NO2 Sensor
            print "NO2, Temp, Humidity sensor"
            params = urllib.urlencode({'name': sensorID,'field1': field1name, 'field2':field2name,'field3':field3name,'api_key':user_key})
            return params
        else:
            print "Sensor type is not defined!"
    except:
            print "This shouldn't happen!"

#Defines upload parameters like field names and write key for each type of sensor

def uploadParams(sensortype,WriteKey):

    try:
        if sensortype == "0": #TVOC,PM10,PM2.5
            params = urllib.urlencode({'field1':floatTVOC, 'field2':intPM2_5, 'field3':intPM10, 'api_key': WriteKey})
            return params
        elif sensortype == "1": #Temp,Hum,Lux sensor
            params = urllib.urlencode({'field1':floatTemp, 'field2':floatHum, 'field3':intLight, 'api_key':WriteKey})
            return params
        elif sensortype == "2": #TVOC,Lux sensor
            params = urllib.urlencode({'field1':floatTVOC, 'field2':intLight, 'api_key':WriteKey})
            return params
        elif sensortype == "3": #CO2 sensor
            params = urllib.urlencode({'field1':intCO2, 'api_key':WriteKey})
            return params
        elif sensortype == "4": #TVOC,PM2.5,PM10,CO2 Sensor
            params = urllib.urlencode({'field1':floatTVOC, 'field2':intPM2_5, 'field3':intPM10, 'field4':intCO2, 'api_key': WriteKey})
            return params
        elif sensortype == "5": #NO2,Temp,Hum Sensor
            params = urllib.urlencode({'field1':intNO2, 'field2':floatTemp, 'field3':floatHum, 'api_key': WriteKey})
            return params
        else:
            print "Sensor type is not defined!"
    except Exception:
            print "This shouldn't happen!"

#Create New Thingspeak Channel

def createChannel(sensorID,sensortype):

    try:
        print "creating channel..."
        params = newchannelParams(sensorID,sensortype)
        conn.request("POST", "/channels.json", params, headers)
        response = conn.getresponse()
        print "got response"
        print response.status, response.reason
        if response.status == 200:
            data = response.read()
            json_data = json.loads(data)
            print "Channel created"
            newkey = json_data['id']
            return newkey
        else:
            print "Channel creation failed"
            print response.status
            conn.close()
    except:
        print "Create channel failed - connection probably failed"
        conn.close()

#reads local channel infomation file and returns dictionary of names & ids

def checkLocalChannels():

    with open ('channelList.json') as infile:
        json_data_from_file = json.load(infile)
    list_length = len(json_data_from_file['channels'])
    name_list = [0]*list_length
    id_list = [0]*list_length

    for i in range(0,list_length):
        name_list[i] = json_data_from_file['channels'][i]['name']
        id_list[i] = json_data_from_file['channels'][i]['id']
        i+1

    names_ids = dict(zip(name_list,id_list))
    return names_ids

# parses local Thingspeak write key list

def checkLocalKeyList():

    with open ('writeKeys.json') as infile:
        json_data_from_file = json.load(infile)
    return json_data_from_file

# Downloads existing channel info from Thingspeak on startup

def downloadChannels():

    try:
         params = urllib.urlencode({'api_key': user_key})
         conn.request("GET", "/users/" + user_ID + "/channels.json/", params, headers)
         response =  conn.getresponse()
         print response.status, response.reason
         if response.status == 200:
             print "Got response OK"
             data = response.read()
             #print data
             json_data = json.loads(data)
             conn.close()
             print "writing channel list to local file"
             with open ('channelList.json', 'w') as outfile:
                 json.dump(json_data, outfile, sort_keys = True, indent = 4)
             with open ('channelList.json') as infile:
                 json_data_from_file = json.load(infile)
                 #print json_data_from_file
             list_length = len(json_data_from_file['channels'])
             name_list = [0]*list_length
             id_list = [0]*list_length
             for i in range(0,list_length):
                 name_list[i] = json_data_from_file['channels'][i]['name']
                 id_list[i] = json_data_from_file["channels"][i]["id"]
                 i+1
             print "created ID list"
         else:
             print response.status, response.reason
             conn.close()
    except Exception:
         print "No response - had difficulty communicating with Thingspeak"
         print "Check network connection"
         conn.close()
         pass
    else:
         names_ids = dict(zip(name_list,id_list))
         print "returned list of existing sensors"
         return names_ids

# checks which channels already exist on Thingspeak using userID
# If in localDB (local, non-persistent dictionary), returns the existing dictionary without download
# otherwise contacts Thingspeak and downloads list of all existing channels

def checkChannel(sensorID, sensorID_dict):

    print sensorID
    if sensorID in sensorID_dict:
        print "Already have sensorID in local DB"
        return sensorID_dict
    else:
         print "Downloading existing channel information"
    try:
        params = urllib.urlencode({'api_key': user_key})
        conn.request("GET", "/users/" + user_ID + "/channels.json/", params, headers)
        response =  conn.getresponse()
        print response.status, response.reason
        if response.status == 200:
            print "Got response OK"
            data = response.read()
            print data
            json_data = json.loads(data)
            conn.close()
            print "writing channel list to local file"
            with open ('channelList.json', 'w') as outfile:
                json.dump(json_data, outfile, sort_keys = True, indent = 4)
            with open ('channelList.json') as infile:
                json_data_from_file = json.load(infile)
                print json_data_from_file
            list_length = len(json_data_from_file['channels'])
            name_list = [0]*list_length
            id_list = [0]*list_length
            for i in range(0,list_length):
                name_list[i] = json_data_from_file['channels'][i]['name']
                id_list[i] = json_data_from_file["channels"][i]["id"]
                i+1
            print "created ID list"
        else:
            print response.status, response.reason
            conn.close()
    except Exception:
        print "No response - had difficulty communicating with Thingspeak"
        print "Check network connection"
        conn.close()
        pass
    else:
        names_ids = dict(zip(name_list,id_list))
        print "returned list of existing sensors"
        return names_ids

#does a false update of the channel to retrieve the writekey as a single string

def getWriteKey(CHANNEL_ID):

    uploadID = str(CHANNEL_ID)
    try:
        print "getting write key"
        params = urllib.urlencode({'api_key': user_key})
        conn.request("PUT", "/channels/" + uploadID + ".json", params, headers)
        response = conn.getresponse()
        print response.status, response.reason
        if response.status == 200:
            print "got key!"
            data = response.read()
            json_data = json.loads(data)
            apikeys = json_data['api_keys']
            return apikeys
        else:
            print response.status, response.reason
            conn.close()
    except:
        print "Get write key failed - connection probably timed-out"
        conn.close()

def storeWriteKeys(writeKey_dict):

    print "appending write key to local file..."
    json_data = writeKey_dict
    #print "json key data is", json_data
    with open ('writeKeys.json', 'w') as f:
        json.dump(json_data,f, indent=4)
    print "Done"
    return

#uploads sensor data using writekey

def uploadData(WriteKey,sensortype):

    params = uploadParams(sensortype,WriteKey)
    try:
        print "Uploading data..."
        conn.request("POST", "/update", params, headers)
        response = conn.getresponse()
        print response.status, response.reason
        if response.status == 200:
            print "UPLOADED!"
            print "**********"
            conn.close()
        else:
            print response.status, response.reason
            conn.close()
    except:
        print "connection probably timed-out"
        conn.close()

###################################### Main Subroutine #############################################

def ThingspeakProcess(source,sensortype,sensorID_dict,writeKey_dict):

    if source in sensorID_dict:
        print "1 Source in sensorID_dict"
        if source in writeKey_dict:
            print "1-1 source in writeKey_dict"
            if len(writeKey_dict[source]) == 2:
                print "1-1-1 source in both db"
                uploadData(writeKey_dict[source][1],sensortype)       #upload
            else:
                print "1-1-2 source in both db, no write key?"
                channelID = sensorID_dict[source]
                readwritekey = getWriteKey(channelID)    #get key object from thingspeak json response
                writekey = readwritekey[0]['api_key']    #get writekey from object
                writeKey_dict[source].append(writekey)   #write key into DB
                uploadData(writekey,sensortype)          #upload
        else:
            print "1-2 source not in writeKey_dict"
            channelID = sensorID_dict[source]            #create new channel with source_addr as name - returns ID of new channel
            writeKey_dict[source] = [channelID,0]        #insert channelID and empty list item for writekey
            readwritekey = getWriteKey(channelID)
            writekey = readwritekey[0]['api_key']
            writeKey_dict[source][1] = writekey          #write key into DB
            uploadData(writekey,sensortype)              #upload

    elif source not in sensorID_dict:                    # = new sensor = create a channel, add the write API key to memory
        print "2 Source not in sensorID_dict"
        if source not in writeKey_dict:
            print "2-1 source not in writeKey_dict"
            channelID = createChannel(source,sensortype) #create new channel with source_addr as name - returns ID of new channel
            sensorID_dict[source] = [channelID]          #add new channelID to sensorIDlist
            writeKey_dict[source] = [channelID,0]        #insert channelID and empty list item for writekey
            readwritekey = getWriteKey(channelID)        #get key object from thingspeak json response
            writekey = readwritekey[0]['api_key']        #get writekey from object
            writeKey_dict[source][1] = writekey          #write key int DB
            uploadData(writekey,sensortype)              #upload
        else:
            print "2-2 source already in writeKey_dict"
            writeKey_dict[source][1] = writekey          #write key into DB
            uploadData(writekey,sensortype)              #upload
    else:
        print "this shouldn't happen"
        conn.close()
    return writeKey_dict, sensorID_dict