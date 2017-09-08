#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''
@author: melon
'''
from influxdb import InfluxDBClient
import datetime
import json

from MasterObject import masterObject

class Database(masterObject):
    address = ''
    port = ''
    dbname = ''
    user = ''
    password =''
    db_client = 0
    _id = 0
    def __init__(self,control_class,json_data):
        masterObject.__init__(self,control_class)
        self.address = json_data['address'] if 'address' in json_data else "localhost"
        self.port = json_data['port'] if 'port' in json_data else False
        self.dbname = json_data['db_name'] if 'db_name' in json_data else "db_name"
        self.user = json_data['user'] if 'user' in json_data else False
        self.password = json_data['password'] if 'password' in json_data else False
        self._id = json_data['id'] if 'id' in json_data else 0
        self.setDefaults()
        self.connect()

    def getDefaultPort(self):
        '''
        Abstract method
        '''
        raise RuntimeError("function Database::getDefaultPort() bust be implemented in all children classes")
        return False

    def reloadConfig(self,json_data):
        reconnect = False

        new_address =  json_data['address'] if 'address' in json_data else "localhost"
        if(new_address != self.address):
            reconnect =True
            self.address = new_address 

        new_port =  json_data['port'] if 'port' in json_data else self.getDefaultPort()
        if(new_port != self.port and new_port != False):
            reconnect =True
            self.port = new_port 

        new_dbname =  json_data['db_name'] if 'db_name' in json_data else "db_name"
        if(new_dbname != self.dbname):
            reconnect =True
            self.dbname = new_dbname 

        new_user =  json_data['user'] if 'user' in json_data else False
        if(new_user != self.user):
            reconnect =True
            self.user = new_user

        new_password =  json_data['password'] if 'password' in json_data else False
        if(new_password!= self.password):
            reconnect =True
            self.password = new_password
        self.setDefaults()
        if(reconnect):
            self.connect()
    
    def getId(self):
        return self._id

    
    def save(self,table,column,value,sync_mark):
        '''
        Abstract method
        '''
        raise RuntimeError("function Database::save(self,table,column,value,sync_mark) bust be implemented in all children classes")
        return 0

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

        
