#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''
@author: melon
'''
import math
import numpy as np
from time import sleep
import time
import os
import os.path
import sys
import datetime
import string
from math import sin, cos

from Socket import *

from Join import *
from Database import *


#import time
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json

class Control(object):

    status = False
    broker_address = False
    broker_port = False
    sockets = {}
    db_clients = {}
    client = False
    control_topic = False
    control_qos = False
    control_messages = False
    keep_runing = True
    reloading=False
    config = False
    joiners = {}
    config_file_name= False
    ready_to_reload =False
    def __init__(self,file_name):
        '''
        contructor
        '''
        self.config_file_name = file_name if file_name != False else 'data.json'
        #self.load_json_data()
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def loadJsonConfigFile(self):
        '''
        Read configuration file
        '''
        error = {'error':'Unknown error'}
        try:
            with open(self.config_file_name) as data_file:    
                temp_conf = json.load(data_file)
                return temp_conf

        except Exception as e:
            print("Error parsing Json file. Ignoring changes")
            print(e.message)
            error = {'error':"Error parsing Config file. Ignoring changes. {}".format(e.message)}
            pass
        return error

    def loadConfig(self):
        '''
        Load and update controler configuration
        and all needed components
        '''
        new_config = self.loadJsonConfigFile()
        if('error' in new_config):
            self.client.publish("{}/error".format(self.control_topic),new_config['error'])
            return False


        new_sockets = new_config['sockets'] if 'sockets' in new_config else {}
        self.loadSockets(new_sockets)

        new_joiners = new_config['joiners'] if 'joiners' in new_config else {}
        self.loadJoiners(new_joiners)

        new_databases = new_config['dbs'] if 'dbs' in new_config else {}
        self.loadDatabases(new_databases)

        new_control = new_config['control'] if 'control' in new_config else {}
        self.loadControlConfig(new_config)

        return True

    def loadSockets(self,new_data):
        '''
        Load Sockets from config json. 
        Update existing ones, remove old one
        And create the missing ones.
        '''

        to_delete = []
        for model_id in self.sockets: 
            model = self.sockets[model_id]
            if(model_id in new_data):
                model.reloadConfig(new_data[model_id])
                del new_data[model_id]
            else:
                to_delete.append(model_id)

        for data_id in new_data:
            data_json = new_data[data_id]
            data_json["id"] = data_id
            class_name = globals()[data_json['class_name']]
            class_instance = (class_name(self,data_json))
            self.sockets[class_instance.getId()] = class_instance
        for delete_id in to_delete:
            del self.sockets[delete_id]       

    def loadJoiners(self,new_data):
        '''
        Load Joiners from config json. 
        Update existing ones, remove old one
        And create the missing ones.
        '''
        to_delete = []
        for model_id in self.joiners: 
            model = self.joiners[model_id]
            if(model_id in new_data):
                model.reloadConfig(new_data[model_id])
                del new_data[model_id]
            else:
                to_delete.append(model_id)

        for data_id in new_data:
            data_json = new_data[data_id]
            data_json["id"] = data_id
            class_instance = globals()[data_json['class_name']](self,data_json)
            self.joiners[class_instance.getId()] = class_instance
        for delete_id in to_delete:
            del self.joiners[delete_id]   

    def loadDatabases(self,new_data):
        '''
        Load Databases from config json. 
        Update existing ones, remove old one
        And create the missing ones.
        '''
        to_delete = []
        for model_id in self.db_clients: 
            model = self.db_clients[model_id]
            if(model_id in new_data):
                model.reloadConfig(new_data[model_id])
                del new_data[model_id]
            else:
                to_delete.append(model_id)

        for data_id in new_data:
            data_json = new_data[data_id]
            data_json["id"] = data_id
            class_name = globals()[data_json['class_name']]
            class_instance = (class_name(self,data_json))
            self.db_clients[class_instance.getId()] = class_instance
        for delete_id in to_delete:
            del self.db_clients[delete_id] 

    def loadControlConfig(self,new_config):
        '''
        Configure basic control parameters
        '''
        reconnect_mqtt = False
        resubscribe = False

        new_broker_address =  new_config['address'] if 'address' in new_config else "localhost"
        if(new_broker_address != self.broker_address):
            self.broker_address = new_broker_address
            reconnect_mqtt = True

        new_broker_port =  new_config['port'] if 'port' in new_config else 1883
        if(new_broker_port != self.broker_port):
            self.broker_port = new_broker_port
            reconnect_mqtt = True


        new_control_qos =  new_config['qos'] if 'qos' in new_config else 2
        if(new_control_qos != self.control_qos):
            if(reconnect_mqtt == False):
                print(self.broker_address)
                self.client.unsubscribe(self.control_topic)#TODO: esto rebienta si control_topic==""
                resubscribe = True
            self.control_qos = new_control_qos

        new_control_topic =  new_config['topic'] if 'topic' in new_config else "master/control"
        if(new_control_topic != self.control_topic):
            if(reconnect_mqtt == False and resubscribe == False):
                self.client.unsubscribe(self.control_topic)
                resubscribe = True
            self.control_topic = new_control_topic
        
        self.control_messages = new_config['control_messages'] if 'control_messages' in new_config else {"reload": "reload","shutdown": "shutdown","status": "status"}

        if(reconnect_mqtt==True):
            self.connectMQTTClient()
        if(resubscribe==True):
            self.subscribeCommand()


    def subscribeCommand(self):
        '''
        Subscribe to command topic
        '''
        self.client.subscribe(self.control_topic,self.control_qos)

    def on_connect(self,client, userdata, flags, rc):
        '''
        On_connect Mqtt function
        '''
        print("Connected with result code "+str(rc))
        self.subscribeCommand()
        for socket_id in self.sockets:
            self.sockets[socket_id].subscribeToCommand()
    
    
    # when receiving a mqtt message do this;
    def on_message(self,client, userdata, msg):
        '''
        on_message Mqtt function
        '''

        global status,sockets
        message =msg.payload.decode('utf-8')
        topic = msg.topic
        print("Topic: '{}' with msg: '{}' with type: {}".format(topic,message,type(message)))
        if(str(topic)==self.control_topic):
            print("We have a control message")
            if(message == self.control_messages['reload']):
                #reload config file and re-create sockets
                print ("Reloading configuration files.")
                self.reloading=True
                while(self.ready_to_reload == False):
                    sleep(0.1)
                self.loadConfig()
                print("Configuration Re-Loaded.")
                self.ready_to_reload = False
                self.reloading=False

            elif(message == self.control_messages['shutdown']):
                print ("Shutdown now.")
                self.keep_runing = False
            elif(message == self.control_messages['status']):
                data = {}
                data['Controll Status'] = self.keep_runing
                data['Sockets']={}
                for socket in self.sockets:
                    data['Sockets'][socket.getName()] = socket.getStatus()
                client.publish(self.control_topic,json.dumps(data))
            elif(os.path.isfile(message)):
                #TODO check if is json file
                print ("Changing configuration file.")
                self.config_file_name = message
                
        
        for socket_id in self.sockets:
            self.sockets[socket_id].mqttReceiveCommand(topic,message)

    def connectMQTTClient(self):
        '''
        Connect to MQTT client with current configuration
        '''
        self.client.connect(self.broker_address, self.broker_port, 60)
        self.client.loop_start()

    def run(self):
        if(self.keep_runing==False):        
            return False

        if(self.loadConfig() == False):
            print("Stoping execution")
            return False
        print ("Loaded and Runing") #TODO: esto va a una función poara poder llamarlo en caso de cambiar la conf.


        #delta_time = 0.0001 #velocidad real
        #delta_time = 0.1 # velocidad reducida para node-red (mas rapido de esto no tira)
        #self.connectMQTTClient()
        

        tiempos = []
        while self.keep_runing:
            try:
                #start_time = time.time()
                if(self.reloading == False):
                    for socket_id in self.sockets:
                      #TODO: Cada socket se ejecuta en una hebra independiente
                        #Comunicacion entre hebras ¿? <- hacer pruebas
                        #start3_time = time.time()
                        data = self.sockets[socket_id].receivePayload()
                        #print("Socket --- %s seconds ---" % (time.time() - start3_time))
                        if(data!=False):
                            #start2_time = time.time()
                            #print(json.dumps(data, indent=4, sort_keys=True))
                            for key, value in data.items():
                                #print(key)
                                #print(value)
                                self.joiners[key].addValues(value)
                            #print("Joiners --- %s seconds ---" % (time.time() - start2_time))

                else:
                    self.ready_to_reload = True
                    sleep(1)
                #print("--- %s seconds ---" % (time.time() - start_time))
                #sleep(delta_time)
                #tiempos.append(time.time() - start_time)
            #Program is closing
            except KeyboardInterrupt:
                self.keep_runing = False
                pass
        
        for socket_id in self.sockets:
            self.sockets[socket_id].close()
        self.client.loop_stop()
        self.client.disconnect()
        '''
        print("Muestras tomadas: {}".format(len(tiempos)))
        print("\033[92m == EFICIENCIA MEDIA == \033[0m")
        value_total = sum(tiempos)/len(tiempos)
        print("Media de tiempo : --- {} ---".format(value_total))
        instrucciones = value_total*1200000
        print("Instrucciones de media : --- {} ---".format(instrucciones))

        print("\033[92m == EFICIENCIA MEJOR CASO == \033[0m")
        value_total = min(tiempos)
        print("Tiempo mejor caso : --- {} ---".format(value_total))
        instrucciones = value_total*1200000
        print("Instrucciones de mejor caso : --- {} ---".format(instrucciones))


        print("\033[92m == EFICIENCIA PEOR CASO == \033[0m")
        value_total = max(tiempos)
        print("Tiempo peor caso : --- {} ---".format(value_total))
        instrucciones = value_total*1200000
        print("Instrucciones de peor caso : --- {} ---".format(instrucciones))
        '''
