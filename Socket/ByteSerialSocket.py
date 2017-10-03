from .SerialSocket import SerialSocket
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





