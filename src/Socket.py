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

from MasterObject import masterObject
import struct


from time import sleep
import os

class Socket(masterObject):
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
        masterObject.__init__(self,control_class)
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


class FileSocket(Socket):
    file_name = 0
    file_object = 0
    delay = 0
    last_time = 0
    #def __new__(cls, *p, **k):
    #    inst = Socket.__new__(cls)
    #    return inst
    def __init__(self,control_class,json_data):
        '''
        Constructor
        '''
        Socket.__init__(self,control_class,json_data)
        self.file_name = json_data['file_name']
        self.delay = json_data['delay'] if 'delay' in json_data else 0
        self.connect()
        #Python2
        #super(FileSocket,self).__init__(json_data)
            
    def reloadConfig(self,json_data):
        '''
        Reload configuration if there is any changes
        '''
        #Reload normal config

        Socket.reloadConfig(self,json_data)
        if ('file_name' in json_data and json_data['file_name'] != self.file_name):
            self.file_name =  json_data['file_name']
            self.connect()
        self.delay =  json_data['delay'] if 'delay' in json_data and json_data['delay'] != self.delay else self.delay


    def doConnect(self):
        self.file_object  = open(self.file_name, "r") 
        self.last_time = time.time()    
        return self.file_object != False


    def sendCommand(self,command):
        '''
        change fileSocket status
        '''
        self.status = int(command) #Status = 0 or 1

    def close(self):
        self.file_object.close()

    def receivePayload(self):
        '''
        read a line of the file
        '''        
        ret = False
        if(self.status==1):        
            if(self.delay == 0 or time.time()>(self.delay+self.last_time)):
                payload =  self.file_object.readline().replace(" ","").replace('\t', '').replace('\n', '')
                if(payload == False):
                    self.connect()
                    return False
                ret = self.processPayload(payload)
                self.last_time = time.time()   
        return ret
                





'''
UART = serial.Serial()
UART.port = SerialPort
UART.baudrate = SerialBaudrate
UART.bytesize = serial.EIGHTBITS #number of bits per bytes
UART.parity = serial.PARITY_NONE #set parity check: no parity
UART.stopbits = serial.STOPBITS_ONE #number of stop bits
UART.timeout = 1        #non-block read
UART.xonxoff = False    #disable software flow control
UART.rtscts = False     #disable hardware (RTS/CTS) flow control
UART.dsrdtr = False     #disable hardware (DSR/DTR) flow control
UART.writeTimeout = 2   #timeout for write
'''
class SerialSocket(Socket):
    port = '/dev/ttyAMA0'
    serial = 0
    baudrate = 9600
    parity = 'E'
    stopbits = 2
    delay = 0
    last_time = 0
    #def __new__(cls, *p, **k):
    #    inst = Socket.__new__(cls)
    #    return inst
    def __init__(self,control_class,json_data):        
        '''
        Constructor
        '''
        Socket.__init__(self,control_class,json_data)
        self.port = json_data['port'] if 'port' in json_data else '/dev/ttyAMA0'
        self.delay = json_data['delay'] if 'delay' in json_data else 0
        self.baudrate = json_data['baudrate'] if 'baudrate' in json_data else 9600
        self.parity = json_data['parity'] if 'parity' in json_data else 'E'
        self.stopbits = json_data['stopbits'] if 'stopbits' in json_data else 2
        self.connect()
        #Python2
        #super(FileSocket,self).__init__(json_data)
    def reloadConfig(self,json_data):
        '''
        Reload configuration if there is any changes
        '''
        #Reload normal config
        reconect = False
        Socket.reloadConfig(self,json_data)
        if ('port' in json_data and json_data['port'] != self.port):
            self.port =  json_data['port'] 
            reconect = True
        if ('baudrate' in json_data and json_data['baudrate'] != self.baudrate):
            self.baudrate =  json_data['baudrate']
            reconect = True
        if ('parity' in json_data and json_data['parity'] != self.parity):
            self.parity =  json_data['parity']
            reconect = True
        if ('stopbits' in json_data and json_data['stopbits'] != self.stopbits):
            self.stopbits =  json_data['stopbits']
            reconect = True
        if(reconect):
            self.connect()
        self.delay =  json_data['delay'] if 'delay' in json_data and json_data['delay'] != self.delay else self.delay

    def doConnect(self):
        try:
            self.serial  = serial.Serial(
                port=self.port,
                baudrate=self.baudrate, 
                parity=self.parity, #default: 'E'
                stopbits=self.stopbits #default: 2
                )
            self.serial.flushInput()  #flush input buffer, discarding all its contents
            self.serial.flushOutput()#flush output buffer, aborting current output and discard all that is in buffer
            self.last_time = time.time()
        except:
            self.serial = False
            print("Error: SerialSocket.connect()")
            pass          
        return self.serial != False

    def sendCommand(self,command):
        '''
        Send the command throw serial com
        '''
        self.serial.write(command)

    def close(self):
        self.serial.close()
        
    def testConnection(self):
        if(self.serial == False):
            self.connect()
        if(self.serial == False):
            return False
        return True

    def receivePayload(self):
        '''
        Read a line from serial com
        '''        
        ret = False
        if(self.testConnection() ==False):
            return ret
        
        if(self.delay == 0 or time.time()>(self.delay+self.last_time)):
            try:            
                if(self.eol_character != False): 
                    line = ""
                    while True:
                        c = self.serial.read(1)
                        line+=c
                        decode_format = self.encode if self.encode != False else 'utf-8'
                        if c.decode(decode_format) == self.eol_character:
                            #print("Line: " + line)
                            break
                elif (self.eol_count != False):
                    line = self.serial.read(self.eol_count)
                    
                else:
                    line = self.serial.readline()
                    #print"readline"
                payload =  self.decode(line)
            except:
                payload = ''
                self.serial=False
                print("Error: SerialSocket.ReceivePayload()")
                pass
            #print payload
            if(payload == False):
                return False
            ret = self.processPayload(payload)
            self.last_time = time.time()   
        return ret
                




import paho.mqtt.client as mqtt

class MqttSocket(Socket):
    topic = 'default'
    broker_address = False
    broker_port = False
    delay = 0
    last_time = 0
    client = False
    qos = 0
    last_payload = {}

    def __init__(self,control_class,json_data):        
        '''
        Constructor
        '''
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        Socket.__init__(self,control_class,json_data)
        self.reloadConfig(self,json_data)

        #Python2
        #super(FileSocket,self).__init__(json_data)
    def reloadConfig(self,json_data):
        '''
        Reload configuration if there is any changes
        '''
        #Reload normal config
        reconnect_mqtt = False
        resubscribe = False
        Socket.reloadConfig(self,json_data)
    
        new_broker_address =  new_config['address'] if 'address' in new_config else "localhost"
        if(new_broker_address != self.broker_address):
            self.broker_address = new_broker_address
            reconnect_mqtt = True

        new_broker_port =  new_config['port'] if 'port' in new_config else 1883
        if(new_broker_port != self.broker_port):
            self.broker_port = new_broker_port
            reconnect_mqtt = True

        if ('topic' in json_data and json_data['topic'] != self.topic):
            resubscribe=True
            self.client.unsuscribe(self.topic)
            self.topic =  json_data['topic'] 
        if ('qos' in json_data and json_data['qos'] != self.qos):
            if(resubscribe==False):
                self.client.unsuscribe(self.topic)
            resubscribe=True
            self.qos =  json_data['qos'] 

        if (reconnect_mqtt == True):
            self.connect()
        elif(resubscribe==True): 
            self.subscribe()

    def subscribe(self):
        '''
        Subscribe to command topic
        '''
        self.client.subscribe(self.topic,self.qos)
    def doConnect(self):
        try:        
            self.client.connect(self.broker_address, self.broker_port, 60)
            self.client.loop_start()
        except:
            self.client = False
            print("Error: MqttSocket.connect()")
            pass
        return self.client != False

    def sendCommand(self,command):
        '''
        Send the command throw serial com
        '''
        #TODO: DEFINIR COMO FUNCIONA ESTO
        return False

    def close(self):
        self.client.disconnect()
        self.client.loop_stop()
        print("Error: MqttSocket.Close()")
        pass
        
    def receivePayload(self):
        '''
        Read a line from serial com
        '''        
        #Return all received payloads for joiners
        return self.last_payload

    def on_connect(self,client, userdata, flags, rc):
        '''
        On_connect Mqtt function
        '''
        print("MqttSocket Connected with result code "+str(rc))
        self.subscribe()
    
    
    # when receiving a mqtt message do this;
    def on_message(self,client, userdata, msg):
        '''
        on_message Mqtt function
        '''
        message = str(msg.payload)
        topic = msg.topic
        #TODO: parsear los topics

        ret = False
        try:            
            payload =  self.decode(message)
        except:
            payload = ''
            print("Error: MqttSocket.decode()")
            pass
        #print payload
        if(payload == False):
            return False
        ret = self.processPayload(payload)
        self.last_time = time.time()   
        return ret


















class ByteSerialSocket(SerialSocket):
    iol_character_ord = False
    eol_character_ord = False
    def __init__(self,control_class,json_data):        
        '''
        Constructor
        '''
        SerialSocket.__init__(self,control_class,json_data)
        self.iol_character_ord = ord(self.iol_character)
        self.eol_character_ord = ord(self.eol_character)


    def processPayload(self,payload):
        '''
        Main payload processing function.
        '''
        #self.mqttPublishPayload(payload,mqtt_client)
        payload_group = []
        #start_time = time.time()
        if(self.parser != False):   # tenemos parser "#{0}:{1};"
            payload_group  = self.ParsePayload(payload)
        else:#No hay parser, se asigna el payload como un solo valor al grupo 0
            payload_group = {"0":payload}
        self.processStats(payload_group)
        #print(json.dumps(payload_group, indent=4, sort_keys=True))
        #print("Socket : ParsePayload--- %s seconds ---" % (time.time() - start_time))
        #start_time = time.time()
        #print("Socket : processStats--- %s seconds ---" % (time.time() - start_time))
        #TODO: add to payload_group the join information ¿? 
        #start_time = time.time()
        joindata = self.getJoinPayload(payload_group)
        #print("Socket : getJoinPayload--- %s seconds ---" % (time.time() - start_time))
        return joindata 

    def doUnpack(self,payload):
        if(self.unpack!=False):
            try:
                payload = struct.unpack(self.unpack,payload)[0]  
            except Exception as e:
                payload=False
                print("Error: ByteSerialSocket.unpack()")
                self.serial.flushInput()
                pass
        if(payload == False):
            try:
                payload= payload.decode('utf-8')
            except Exception as e:
                payload=''
                pass
        try:
            payload = float(payload)#TODO Quitar este float y hacer que el tipo de dato sea configurable
        except Exception as e:
            payload = False
            pass
        return payload     

    def receivePayload(self):
        '''
        Read a line from serial com
        '''        
        #start_time = time.time()
        ret = False        
        if(self.testConnection() ==False):
            return ret

        
        #if(self.delay == 0 or time.time()>(self.delay+self.last_time)):

        line = bytes()
        
        while True:
            c= self.serial.read(1)
            #print(c)
            if c[0] == self.iol_character_ord:
                #We found the start:
                line = c
                break
        if(self.eol_character):
            while True:
                c= self.serial.read(1)
                line += c
                if c[0] == self.eol_character_ord:
                    #We found the end:
                    break
        elif(self.eol_count):
            line = self.serial.read(self.eol_count-1)
            line +=c
            #print(line)
            if line[0] != self.eol_character_ord:
                #We didnt read a valid payload
                return False
            
        #self.serial.flushInput()
        print(line)
        #print (''.join(format(x, '02x')+'.' for x in payload))
        inWaiting = self.serial.inWaiting()
        if(inWaiting >= 4090):
            print("buffer: {}".format(inWaiting))
            self.serial.flushInput()
        if(line == False):
            return False
        #print("calling process")
        #print("Socket : receivePayload--- %s seconds ---" % (time.time() - start_time))
        ret = self.processPayload(line)
        #self.last_time = time.time()   
        return ret
                

    def ParsePayload(self,payload):
        '''
        Parse the payload using the parser config string
        and split it in groups.
        '''
        #print(payload)
        #payload = "#22134:643.0605-56234;"
        #print("In Parse")
        payload_group = {}
        #print(self.parser_array)
        for group in self.parser_array:
            start = -1
            end = -1
            group_post = group['post']
            group_prec = group['prec']
            len_group_post = len(group_post)
            len_group_prec = len(group_prec)
            len_payload = len(payload)
            #print(group)
            if(group_prec != ''):
                #print("tenemos prec")
                group_prec_ord = ord(group_prec[0])
                for i in range(0,len_payload):
                    if(start == -1 and payload[i] == group_prec_ord):
                        #Hemos encontrado el primer caracter del principio
                        start = i
                        #print("start found : {}".format( start))
                    elif(start!= -1):
                        if(i-start >= len_group_prec):
                            start += len_group_prec
                            break #Ya hemos buscado todo el grupo
                        elif(payload[i] != ord(group_prec[i-start])):
                            start = False #Error al encontrar start entero
                            break

            if(start == -1):
                start = 0
            if(group_post != ''):
                group_post_ord = ord(group_post[0])
                for i in range(start,len_payload):
                    if(end == -1 and payload[i] == group_post_ord):
                        #Hemos encontrado el primer caracter del final
                        end = i
                        #print("start found : {}".format( start))
                    elif(end != -1):
                        if(i-end >= len_group_post):
                            break #Ya hemos buscado todo el grupo
                        elif(payload[i] != ord(group_post[i-end])):
                            end = -1 #Error al encontrar start entero
                            break

            if(end == -1):
                end = len_payload

            #print("positions prec-{}:{} -- post{}:{}".format(group['prec'],start,group['post'],end))    
            data = self.doUnpack(payload[start:end])
            if(data is None): #Hemos tenido un error en unpack
                data = False
                print("Payload: {} - Dato: {}".format(payload,payload[start:end]))
            payload_group[group['position']] = data
            payload = payload[end:]
            #print("Extracted: {} - Remaining: {}".format(result,payload))
        #print(payload_group)
        return payload_group








class FasometroSerialSocket(ByteSerialSocket):

    def afterConnect(self):
        print('Resetting timestamp. Why is executed twice?')
        os.system('echo 4 > /sys/class/gpio/export')
        os.system('echo high > /sys/class/gpio/gpio4/direction')
        os.system('echo 0 > /sys/class/gpio/gpio4/value')
        sleep(0.1)
        
        os.system('echo 1 > /sys/class/gpio/gpio4/value')
        sleep(0.1)
        os.system('echo 0 > /sys/class/gpio/gpio4/value')


    def doPack(self,payload):
        try:
            payload = struct.pack("<L",payload) 
        except:
            payload=False
            print("Error: ByteSerialSocket.unpack()")
            pass
        return payload  

    def mqttReceiveCommand(self,topic,command):
        '''
        funcion a la que se llama desde el cliente de mqtt
        cuando se recive un comando de control,
        esta funcion debe efectuar la accion necesaria sobre 
        el dispositivo.
        '''
        payload=False        
        if(str(topic) == 'fasometro/control/skip'):
            try:
                frec = int(command)
                print("frec : {}".format(frec))
                skip = int(round(frec/125000.0,0))
                print("skip : {}".format(skip))
                payload = b'\x2A' +self.doPack(skip) + b'\x5f'        
            except:
                payload = False
                pass
        elif(str(topic) == 'fasometro/control/nfft'):
            try:
                nfft = int(command)
                print("nfft : {}".format(nfft))
                payload = b'\x5E' +self.doPack(nfft) + b'\x5f'        
            except:
                payload = False
                pass
        elif(str(topic) == 'fasometro/control/nfftexp'):
            try:
                nfftexp = int(command)
                print("nfft : {}".format(nfftexp))
                payload = b'\x3C' +self.doPack(nfftexp) + b'\x5f'        
            except:
                payload = False
                pass
        if(payload != False):
            print("{}".format(payload))
            self.sendCommand(payload)

    def sendCommand(self,command):
        '''
        Send the command throw serial com
        '''
        self.serial.write(command)

    def doUnpack(self,payload):
        try:
            payload = struct.unpack('<l',payload)[0]  
        except:
            payload=''
            print("Error: ByteSerialSocket.unpack()")
            self.serial.flushInput()
            pass
        return payload  

    def ParsePayload(self,payload):
        '''
        Parse the payload using the parser config string
        and split it in groups.
        '''
        data={"0":0,"1":0,"2":0} #_{4}::{3}||{2}**{1}??{0}#
        sink_mark = self.doUnpack(payload[1:5])
        
        #print(sink_mark)
        
        data3 = self.doUnpack(payload[7:11]) #Img 2
        data2 = self.doUnpack(payload[13:17]) # Real 2
        data1 = self.doUnpack(payload[19:23]) # IMG 1
        data0 = self.doUnpack(payload[25:29]) #Real 1

        
        atan1 = round(math.atan2(float(data3),float(data2))*(180/math.pi),4)
        atan2 = round(math.atan2(float(data1),float(data0))*(180/math.pi),4)
        data['2']=sink_mark
        data['1']=atan1
        data['0']=atan2
        return data

    def getJoinPayload(self,payload_group):
        '''
        Prepare the payload in groups for the joiners
        '''
        if(self.join == False):
            return False
        joined_data={
            "join_1": [
                    {'pos':0,'payload':payload_group['0'],'sync':0},
                    {'pos':1,'payload':payload_group['1'],'sync':0}
                ]
            }
        return joined_data

    def processPayload(self,payload):
        '''
        Main payload processing function.
        '''
        #self.mqttPublishPayload(payload,mqtt_client)
        payload_group = []

        #start_time = time.time()
        payload_group  = self.ParsePayload(payload)
        #print("Socket : ParsePayload--- %s seconds ---" % (time.time() - start_time))
        #print(payload_group)
        #start_time = time.time()
        self.processStats(payload_group)
        #print("Socket : processStats--- %s seconds ---" % (time.time() - start_time))

        #start_time = time.time()
        joindata = self.getJoinPayload(payload_group)
        #print("Socket : getJoinPayload--- %s seconds ---" % (time.time() - start_time))
        return joindata
