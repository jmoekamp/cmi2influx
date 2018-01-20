#!/usr/bin/python3

import json
import requests
from influxdb import InfluxDBClient 
import configparser
import sys
import paho.mqtt.client as mqtt

configfilename=sys.argv[1]
config = configparser.ConfigParser()
config.read(configfilename)

ip=config.get('main','ip')
can_node=config.get('main','can_node')
username=config.get('main','username')
password=config.get('main','password')
influxip=config.get('main','influxip')
influxdb=config.get('main','influxdb')
influxusername=config.get('main','influxusername')
influxpassword=config.get('main','influxusername')
influxtaghost=config.get('main','influxtaghost')
influxtagregion=config.get('main','influxtagregion')
mqttip = config.get('main','mqttip')
mqtttopicprefix = config.get('main','mqtttopicprefix')
mqtttopicprefix_assembled = mqtttopicprefix+"/"+influxtagregion+"/"+influxtaghost

mqttclient =mqtt.Client("cmi2influx")
mqttclient.connect(mqttip)

url = "http://"+ip+"/INCLUDE/api.cgi?jsonnode="+can_node+"&jsonparam=I,O,Na";

result = requests.get(url, auth=(username, password)).text
data = json.loads(result) 

input_data = data["Data"]["Inputs"]
output_data = data["Data"]["Outputs"]
networkanalog_data = data["Data"]["Network Analog"]

inputs={}
for key in input_data:
 mqttclient.publish(mqtttopicprefix_assembled+"/input/"+str(key["Number"]),str(key["Value"]["Value"]))
 inputs[key["Number"]]=key["Value"]["Value"]

networkanalog={}
for key in networkanalog_data:
 mqttclient.publish(mqtttopicprefix_assembled+"/networkanalog/"+str(key["Number"]),str(key["Value"]["Value"]))
 networkanalog[key["Number"]]=key["Value"]["Value"] 

outputs={}
for key in output_data:
 mqttclient.publish(mqtttopicprefix_assembled+"/output/"+str(key["Number"]),str(key["Value"]["Value"]))
 outputs[key["Number"]]=key["Value"]["Value"]


#
# Adapt things below this for your own UVR1611 installation
# 

heisswasserspeicher=inputs[5] # Temperature Hot water buffer
vorlauf=inputs[10] # Temperature of Inlet Flow
heizungsaussentemperatur=inputs[11] # Outside temperature
speicherunten=networkanalog[2] # Main buffer top
speicheroben=networkanalog[3] # Main buffer bottom
ladepumpewarmwasser=outputs[3] # Pump to charge the hot water buffer
anforderungkessel=outputs[5] # Signal to burner
heizkreispumpe=outputs[4] # Main Heating pump

client = InfluxDBClient(influxip,8086, influxusername, influxpassword, influxdb)
json_body = [
		{
            "measurement": "heating",
            "tags": {
                "host": influxtaghost,
                "region": influxtagregion
            },
            "fields": {
                "warmwasserspeicher": heisswasserspeicher, 
				"vorlauftemperatur": vorlauf,
				"heizungsaussentemperatur": heizungsaussentemperatur,
				"pufferspeicheroben": speicheroben,
				"pufferspeicherunten": speicherunten,
				"ladepumpewarmwasser": ladepumpewarmwasser,
				"anforderungkessel": anforderungkessel,
				"heizkreispumpe": heizkreispumpe
            }
        }
    ]
    
#
# Adapt things above this for your own UVR1611 installation
#

client.write_points(json_body)
