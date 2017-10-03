
from .BaseSocket import BaseSocket

class FileSocket(BaseSocket):
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
        BaseSocket.__init__(self,control_class,json_data)
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

        BaseSocket.reloadConfig(self,json_data)
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
