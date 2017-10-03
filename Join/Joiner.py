#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''
@author: melon
'''
import json
import math
from Stat import *
import Utilities
import re
import time

from MasterObject import masterObject


class Joiner(masterObject): #Puede ser un socket ?
    _id = 0
    connection = 0
    stats = {}
    function=0
    parsed_function = 0
    values = {}
    n_values = 0
    synchronous = 0
    def getId(self):
        return self._id
    
    def __init__(self,control_class,json_data):
        masterObject.__init__(self,control_class)
        '''
        Constructor
        '''        
        self._id = json_data['id'] if 'id' in json_data else 0
        self.reloadConfig(json_data)

    def reloadConfig(self,json_data):
        '''
        Reload configuration if there is any changes
        '''
        #Reload normal config
        self.function =  json_data['function'] if 'function' in json_data and json_data['function'] != self.function else  self.function
        if(self.function != 0):
            self.n_values = len(Utilities.ParseFunction(self.function))
        self.synchronous =  json_data['synchronous'] if 'synchronous' in json_data and json_data['synchronous'] != self.synchronous else  self.synchronous       
        # Reload al stats
        to_delete = []

        new_data = json_data['topics'] if 'topics' in json_data else []
        for model_id in self.stats: 
            model = self.stats[model_id]
            if(model_id in new_data):
                model.reloadConfig(new_data[model_id])
                del new_data[model_id]
            else:
                to_delete.append(model_id)

        for data_id in new_data:
            data_json = new_data[data_id]
            data_json["id"] = data_id
            stat_class = create_stat_class(self.master_control_class,data_json)
            if (stat_class != False):
                self.stats[stat_class.getId()] = stat_class
        for delete_id in to_delete:
            del self.stats[delete_id] 

    def addValues(self,values):
        '''
        Add the value to the joiner in it's corresponding time-spot
        '''
        for group in values:
            group_sync = group['sync']
            group_pos = group['pos']
            if group_sync not in self.values:
                self.values[group_sync] = {}
            try:
                self.values[group_sync][group_pos] = float(group['payload'])
            except:
                self.values[group_sync][group_pos] = 1
                print("Error: Joiner.addValue()")
                pass
        return self.processIfReady()


    def processPayload(self,sync_mark): 
        '''
        Replace the values on the formula to evaluate it and send to stats
        '''

        #start_time = time.time()
        #print ("FUNCTION {} :".format(self.function))
        function_with_data = self.function
        for i in range(0,self.n_values): 
            #TODO: hacer un filtro de values para evitar insertar caracteres extraños
            #TODO: hacer un filtro de la función para evitar insertar caracteres extraños
            #ESOS filtros se implementan en las funciones de entrada addValue e __init__
            pattern = r'[{]'+str(i)+'[}]'
            function_with_data =  re.sub(pattern, "({})".format(str(float(self.values[sync_mark][i]))), function_with_data)
        #print(function_with_data)
        payload = False
        try:
            payload = eval(function_with_data) 
        except:               
            print("Error: Joiner.processPayload()")
            pass
        self.values[sync_mark]={}

        #print("Joiner::processPayload --- %s seconds ---" % (time.time() - start_time))
        return self.processStats(sync_mark,payload)

    def isReady(self,sync_mark):
        '''
        Check if there is enought data to evaluate the formula
        '''
        return len(self.values[sync_mark])==self.n_values

    def processIfReady(self):
        '''
        Evaluate the formula if we have all necesary data
        '''
        for sync_mark in self.values:
            if self.isReady(sync_mark):
                self.processPayload(sync_mark) 
        return True

    def processStats(self,sync_mark,payload):
        '''
        Send the payload to stats
        '''
        for stat_id in self.stats:
            stat = self.stats[stat_id]
            #print("Sending payload To {} ".format(stat_group))
            stat.addValue(payload) 
            stat.setSyncMark(sync_mark)
            stat.publishStatIfReady()
        return True

class FasometroJoiner(Joiner):
    def processPayload(self,sync_mark): 
        '''
        Replace the values on the formula to evaluate it and send to stats
        '''

        #start_time = time.time()
        payload = False
        try:
            #atan1 = round(math.atan2(float(self.values[sync_mark][3]),float(self.values[sync_mark][2]))*(180/math.pi),4)
            #atan2 = round(math.atan2(float(self.values[sync_mark][1]),float(self.values[sync_mark][0]))*(180/math.pi),4)
            payload= self.values[sync_mark][0]-self.values[sync_mark][1]
        except:               
            print("Error: Joiner.processPayload()")
            pass
        self.values[sync_mark]={}

        #print("Joiner::processPayload --- %s seconds ---" % (time.time() - start_time))
        return self.processStats(sync_mark,payload)
        
