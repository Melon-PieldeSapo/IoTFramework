import paho.mqtt.client as mqtt
from .BaseSocket import BaseSocket
class MqttSocket(BaseSocket):
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

        BaseSocket.__init__(self,control_class,json_data)
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
        BaseSocket.reloadConfig(self,json_data)
    
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
