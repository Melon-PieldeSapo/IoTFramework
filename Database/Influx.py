#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''
@author: melon
'''

from Database import Database
from influxdb import InfluxDBClient
import datetime
class Influx(Database):

    def getDefaultPort(self):
        return 8086

    def setDefaults(self):
        if(self.port == 'default'):
            self.port = self.getDefaultPort()
        self.runNo = 33 # ¿? es necesario ¿?


    def connect(self):
        try:
            self.db_client = InfluxDBClient(self.address, self.port, self.user, self.password, self.dbname)
            print("connected to Influx")
        except Exception as e:
            self.db_client = False
            print("Error connecting to Influx DB")
            #print(e.message)
            pass
    
    def save(self,table,column,value,sync_mark):
        if(self.db_client == False):
            #print("No client, reconecting")
            self.connect()
        if(self.db_client == False):
            return False
        iso = datetime.datetime.utcnow()
        json_body = [
        {
          "measurement": table,
          "tags": {
             "run": self.runNo,
              },
          "time": iso,
          "fields": {
              column : value
          }
          }
        ]        
        if(sync_mark != 0):
            json_body[0]['fields']['sync'] = sync_mark

        #print("Write points: {0}".format(json_body))
        # Write JSON to InfluxDB
        try:
            self.db_client.write_points(json_body)
        except Exception as e:
            print("Error writing to Influx DB")
            #print(e.message)
            pass 
