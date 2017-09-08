#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''
@author: melon
'''
import json
import math


from MasterObject import masterObject

class Stat(masterObject):
    _id = 0
    values=[]
    total_values=100
    topic=False
    qos=0
    retain = False
    to_db = False
    db_data = False
    to_file = False
    file_data = False
    sync_mark = 0
    file_obj = False
    file_name = False
    file_flags = False
    file_saved=0

    def getId(self):
        return self._id

    def __init__(self,control_class,json_data):
        '''
        Constructor
        '''        
        masterObject.__init__(self,control_class)
        self._id = json_data['id'] if 'id' in json_data else 0
        self.reloadConfig(json_data)
    
    def reloadConfig(self,json_data):
        '''
        Reload configuration if there is any changes
        '''
        #Reload normal config
        self.values = []
        self.total_values =  json_data['samples'] if 'samples' in json_data and json_data['samples'] != self.total_values else self.total_values
        self.topic =  json_data['topic'] if 'topic' in json_data and json_data['topic'] != self.topic else self.topic

        self.qos =  json_data['qos'] if 'qos' in json_data and json_data['qos'] != self.qos else self.qos
        self.retain =  True if ('retain' in json_data and str(json_data['retain']) != str('0')) else False
        self.to_db =  True if 'to_db' in json_data else False
        self.db_data =  json_data['to_db'] if 'to_db' in json_data and json_data['to_db'] != self.db_data else self.db_data
        self.to_file =  True if 'to_file' in json_data else False
        self.file_data =  json_data['to_file'] if 'to_file' in json_data and json_data['to_file'] != self.file_data else self.file_data
        if(self.to_file == True):
            self.file_name =  self.file_data['file_name'] if 'file_name' in self.file_data and self.file_data['file_name'] != self.file_name else self.file_name
            self.file_flags =  self.file_data['file_flags'] if 'file_flags' in self.file_data and self.file_data['file_flags'] != self.file_flags else self.file_flags


    def addValue(self,value):
        #print "adding {}".format(value)
        self.values.append(value)

    def clearValues(self):
        self.values = []

    def setSyncMark(self,mark):
        self.sync_mark = mark

    def getStat(self):
        '''
        Abstract method
        '''
        raise RuntimeError("function Stat::getStat() bust be implemented in all children classes")
        return False

    def isPubTopic(self,topic):
        '''
        Averigua si el topic dado es uno de los que
        este socket publica datos
        '''     
        return self.topic == topic

    def saveToDb(self,stat):
        if(self.to_db == True):
            self.master_control_class.db_clients[self.db_data["db_id"]].save(self.db_data["table"],self.db_data["column"],stat,self.sync_mark)
        return True

    def saveToFile(self,stat):
        if(self.to_file== True):
            if(self.file_obj == False):
                self.file_obj = open(self.file_name,self.file_flags)
            self.file_obj.write(str(stat)+'\n')
            self.file_saved+=1
            if(self.file_saved >= 5000):
                self.file_obj.close()
                self.file_obj = False
            #with open(self.file_name,self.file_flags) as fileobj:
            #    fileobj.write(str(self.getStat())+'\n')
        return True

    def publishStat(self,stat): 
        if(self.topic != False):          
            self.master_control_class.client.publish(self.topic,stat,self.qos,self.retain)

    def publishStatIfReady(self):
        #print("Stat {} : len {} with total {}.".format(self.__class__.__name__,len(self.values),self.total_values))
        if(len(self.values) == self.total_values):
            stat = self.getStat()
            self.publishStat(stat)
            self.saveToDb(stat)
            self.saveToFile(stat)
            self.clearValues()

class RawStat(Stat):
    def getStat(self):
        return self.values[self.total_values-1]

class MeanStat(Stat):
    def getStat(self):
        return sum(self.values)/len(self.values)
    def addValue(self,value):        
        try:
            self.values.append(float(value))        
        except Exception as e:
            print("Error adding value -{}- to Mean".format(value))
            #print(e.message)

class VarianceStat(Stat):
    def getStat(self):
        mean = sum(self.values)/len(self.values)
        squared_sum = 0
        for value in self.values:
            squared_sum += pow(mean-value,2)
        return (squared_sum / len(self.values))
    def addValue(self,value):
        try:
            self.values.append(float(value))        
        except Exception as e:
            print("Error adding value -{}- to Variance".format(value))
            #print(e.message)
    
class StandardDeviationStat(Stat):
    def getStat(self):
        mean = sum(self.values)/len(self.values)
        squared_sum = 0
        for value in self.values:
            squared_sum += pow(mean-value,2)
        return math.sqrt(squared_sum / len(self.values))
    def addValue(self,value):        
        try:
            self.values.append(float(value))        
        except Exception as e:
            print("Error adding value -{}- to Std".format(value))
            #print(e.message)

class DiferenceStat(Stat):
    epsilon = 0.000

    def __init__(self,control_class,json_data):    
        '''
        Constructor
        '''
        Stat.__init__(self,control_class,json_data)
        self.values=[0,0]

    def getStat(self):
        return self.values[1]
    def addValue(self,value):        
        try:
            self.values[1] = float(value)      
        except Exception as e:
            print("Error adding value -{}- to Std".format(value))
            #print(e.message)

    def publishStatIfReady(self):
        if(self.values[1] < (self.values[0] - self.epsilon) or self.values[1] > (self.values[0] + self.epsilon)):
            self.publishStat()
            self.saveToDb()
            self.clearValues()

    def clearValues(self):
        self.values[0] = self.values[1]

dispatch_dict = {"Stat": Stat, "Raw": RawStat, "Mean":MeanStat,"Variance":VarianceStat,"StandardDeviation":StandardDeviationStat,"Diference": DiferenceStat}

def create_stat_class(control_class,json_data):
        #print(json_data)
        function_name = json_data['function']
        #           stat_class = globals()[class_name] #Todo: si la clase no existe no se hace nada
        #        return stat_class(json_data)# Revisar: no se estan creando
        return dispatch_dict[function_name](control_class,json_data)

