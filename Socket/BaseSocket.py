#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''
@author: melon
'''
import json
import time #Used to simulate - Remove on production
from math import sin, cos#Used to simulate - Remove on production
from Stat import *
import Utilities

import serial

import struct


from time import sleep
import os

class BaseSocket(object):
    master_control_class = False
    _id = False
    control = []
    #pub_topic = 0
    #pub_procesed_topic = 0
    #pub_qos = 0
    connection = 0
    status = 1
    stats = {}
    parser=False
    parser_array = []
    join = False
    encode = False
    eol_character = False
    iol_character = False
    eol_count = False
    unpack = False
    
    def getId(self):
        return self._id
    
    def __init__(self,control_class,json_data):
        self.master_control_class = control_class
        '''
        Constructor
        Where the magic happend
        '''
        self.stats = {}
        self._id = json_data['id'] if 'id' in json_data else False
        self.reloadConfig(json_data)
 
    def reloadConfig(self,json_data):
        '''
        Reload configuration if there is any changes
        '''
        #Reload normal config
        self.control =  json_data['control'] if 'control' in json_data and json_data['control'] != self.control else self.control
        self.eol_character =  json_data['eol_character'] if 'eol_character' in json_data and json_data['eol_character'] != self.eol_character else self.eol_character
        self.iol_character =  json_data['iol_character'] if 'iol_character' in json_data and json_data['iol_character'] != self.iol_character else self.iol_character

        self.eol_count =  json_data['eol_count'] if 'eol_count' in json_data and json_data['eol_count'] != self.eol_count else self.eol_count
        self.encode =  json_data['encode'] if 'encode' in json_data and json_data['encode'] != self.encode else self.encode
        self.unpack =  json_data['unpack'] if 'unpack' in json_data and json_data['unpack'] != self.unpack else self.unpack
        # Reload al stats

        new_data = json_data['publish'] if 'publish' in json_data else {'topics':[]}
        self.join =  new_data['join'] if 'join' in new_data and new_data['join'] != self.join else  self.join
        if 'parser' in new_data:
            #print("With Parser")
            self.parser = new_data['parser']
            self.parser_array = Utilities.ParseParser(self.parser)
        else:
            self.parser = False
            self.parser_array = {'position': '0', 'start': 0,'prec':'','post':''}

        if 'topics' in new_data:
            #print "tenemos topics"
            topics = new_data['topics']
            if 'parser' not in new_data and '0' not in topics:
                topics = {"0":topics}
            group_to_delete = []
            for group_id in self.stats:
                #si el grupo está en topics -> se actualiza
                if(group_id in topics):
                    to_delete = []
                    #UPDATE GROUP
                    new_data = topics[group_id]
                    for model_id in self.stats[group_id]:  # check for models in the group
                        self.stats[group_id][model_id].reloadConfig(new_data[model_id])
                        if(model_id in new_data):
                            del new_data[model_id]
                        else:
                            to_delete.append(model_id)

                    #Create the remaining models
                    for data_id in new_data:
                        data_json = new_data[data_id]
                        data_json["id"] = data_id
                        stat_class = create_stat_class(self.master_control_class,stat_data)
                        if (stat_class != False):
                            self.stats[group_id][stat_class.getId()] = stat_class
                    #delete the models not present in the new config
                    for delete_id in to_delete:
                        del self.stats[group_id][delete_id] 
                        #remove group from topics we are done with it.
                    del topics[group_id]
                else:
                    #sino, se borra
                    group_to_delete.append(group_id)
            #los grupos que falten se crean
            for group_id in topics:
                new_data = topics[group_id]
                self.stats[group_id] = {}
                for data_id in new_data:
                    data_json = new_data[data_id]
                    data_json["id"] = data_id
                    stat_class = create_stat_class(self.master_control_class,data_json)
                    if (stat_class != False):
                        self.stats[group_id][stat_class.getId()] = stat_class

            for group_id in group_to_delete:
                del self.stats[group_id]
        #print(json.dumps(self.stats, indent=4, sort_keys=True)) 
        #print(self.stats)

    def subscribeToCommand(self):
        '''
        subscribe to commands topics.
        '''
        if(self.control != False):
            for control_topic in self.control:
                qos = control_topic['qos'] if 'qos' in control_topic else 0
                self.master_control_class.client.subscribe(control_topic['topic'],qos)

    def isSubTopic(self,topic):
        '''
        Averigua si el topic dado es uno de los que
        este socket se suscribe
        '''
        res = False
        for control_topic in self.control:
                if(control_topic['topic'] == topic):
                    res = True
        return res

    def isPubTopic(self,topic):
        '''
        Averigua si el topic dado es uno de los que
        este socket publica datos
        '''     
        for stat in self.stats:
            if(stat.isPubTopic(topic)):
                return True
        return False
        
    #def mqttPublishPayload(self,payload,mqtt_client):
    #    @DEPRECATED
    #    '''
    #    funcion que parsea el payload en funcion del topic
    #    dato o lo publica directamente si no es necesario.
    #    '''
    #    if(self.pub_topic != False):
    #        mqtt_client.publish(self.pub_topic,payload,self.pub_qos)

    def getStatus(self):
        return self.status
    def getName(self):
        return str(self.__class__.__name__)+"."+str(id(self))

    def mqttReceiveCommand(self,topic,command):
        '''
        funcion a la que se llama desde el cliente de mqtt
        cuando se recive un comando de control,
        esta funcion debe efectuar la accion necesaria sobre 
        el dispositivo.
        '''
        if(self.isSubTopic(topic)):
            todo_action = 0
            for control_topic in self.control:
                if(control_topic['topic'] == topic):
                    for action in control_topic['actions']:
                        if(action['message'] == command):
                            todo_action = action['action']
                            self.sendCommand(todo_action)
                            return True

    def sendCommand(self,command):
        '''
        Abstract method
        '''
        raise RuntimeError("function Socket::sendCommand() bust be implemented in all children classes")
        return False

        self.status = command #Dummy operation

    def receivePayload(self):
        '''
        Abstract method
        '''
        raise RuntimeError("function Socket::receivePayload() bust be implemented in all children classes")
        return False
    def close(self):
        '''
        Abstract method
        '''
        raise RuntimeError("function Socket::close() bust be implemented in all children classes")
        return False


    def processPayload(self,payload):
        '''
        Main payload processing function.
        '''
        #self.mqttPublishPayload(payload,mqtt_client)
        payload_group = []
        if(self.parser != False):   # tenemos parser "#{0}:{1};"
            payload_group  = self.ParsePayload(payload)
        else:#No hay parser, se asigna el payload como un solo valor al grupo 0
            payload_group = {"0":payload}
        #print(json.dumps(payload_group, indent=4, sort_keys=True))
        self.processStats(payload_group)
        #TODO: add to payload_group the join information ¿? 
        joindata = self.getJoinPayload(payload_group)
        return joindata

    def getJoinPayload(self,payload_group):
        '''
        Prepare the payload in groups for the joiners
        '''
        if(self.join == False):
            return False
        joined_data={}
        for join in self.join:
            frm = join['from'] if 'from' in join else 0
            sync = payload_group[join['sync']] if 'sync' in join else 0
            join_to = join['to']
            if join_to not in joined_data:
                joined_data[join_to] = []
            joined_data[join_to].append( {'pos':join['position'],'payload':payload_group[frm],'sync':sync} )
        #print(json.dumps(joined_data, indent=4, sort_keys=True)) 
        return joined_data


    def ParsePayload(self,payload):
        '''
        Parse the payload using the parser config string
        and split it in groups.
        '''
        #payload = "#22134:643.0605-56234;"

        payload_group = {}
        #print self.parser_array
        for group in self.parser_array:
            if(group['prec'] != ''):
                start = payload.find(group['prec'])+len(group['prec'])
            else:
                start = 0
            if(group['post'] != ''):
                end= payload.find(group['post'],start)
            else:
                end = len(payload)
            #print("positions prec-{}:{} -- post{}:{}".format(group['prec'],start,group['post'],end))    
            result = payload[start:end]
            payload_group[group['position']] = result
            payload = payload[end:]
            #print("Extracted: {} - Remaining: {}".format(result,payload))
        return payload_group

    def processStats(self,payload):
        '''
        Split the payload acording to parser order
        to each corresponding stat group
        '''
        #print(self.stats)
        for stat_group in self.stats:# A cada grupo mandar solo el dato correspondiente.
            #print("Sending payload To {} ".format(stat_group))
            if( stat_group in payload): #Tenemos payload para el grupo
                for stat_id in self.stats[stat_group]:
                    stat=self.stats[stat_group][stat_id]
                    #stat.publishStatIfReady(mqtt_client)
                    stat.addValue(payload[stat_group])
                    stat.publishStatIfReady()
    
    def decode(self,payload):
        '''
        Decode the payload if configured
        Also remove white spaces and line terminations on strings
        '''
        
        if(self.encode != False):
            try:
                payload = payload.decode(self.encode)        
                payload =  payload.replace(" ","").replace('\t', '').replace('\n', '')
            except:
                payload=False
                print("Error: Socket.decode()")
                pass
            #payload =  payload.replace(" ","").replace('\t', '').replace('\n', '')
        return payload

    def doConnect(self):
        pass
    def beforeConnect(self):
        pass
    def afterConnect(self):
        pass
    def connect(self):
        self.beforeConnect()
        if(self.doConnect() != False):
            self.afterConnect()

    def reconect(self):
        self.close()
        self.connect()




























