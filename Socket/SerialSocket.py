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
from .BaseSocket import BaseSocket
class SerialSocket(BaseSocket):
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
        BaseSocket.__init__(self,control_class,json_data)
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
        BaseSocket.reloadConfig(self,json_data)
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
