'''
    Modified from https://github.com/Circuit-Digest/rpi-pico-micropython-esp8266-lib/tree/main
    using README.md, esp8266.py, and httpParser.py
    
    Original Author: Noyel Seth
    Email: noyelseth@gmail.com
    
    Modified by: Andrew Macpherson
    Email: macphersona@spu.edu
    
    MicroPython Version: 3.4
'''

# -----------------------------------
#           httpParser
# -----------------------------------
class HttpParser:
    """
    This is a class for parse HTTP response, coming from ESP8266 after complete the Post/Get operation
    Using this class, you parse the HTTP Post/Get operation's response and get HTTP status code, Response.
    """
    
    __httpErrorCode=None
    __httpHeader=None
    __httpResponseLength=None
    __httpResponse=None
    
    def __init__(self):
        """
        The constaructor for HttpParser class
        """
        self.__httpErrCode=None
        self.__httpHeader=None
        self.__httpResponseLength=None
        self.__httpResponse=None
        
    def parseHTTP(self, httpRes):
        """
        This funtion use to parse the HTTP response and return back the HTTP status code
        
        Return:
            HTTP status code.
        """
        #print(">>>>",httpRes)
        if(httpRes != None):
            retParseResponse=str(httpRes).partition("+IPD,")[2]
            #print(">>>>>>>>>>>>>>>>>",retParseResponse)
            retParseResponse=retParseResponse.split(r"\r\n\r\n");
            #print(">>>>>>>>>>>>>>>>>",retParseResponse[0])
            self.__httpResponse = retParseResponse[1]
            #print(">>>>>>>>>>>>>>>>>???",retParseResponse[1])  
            self.__httpHeader=str(retParseResponse[0]).partition(":")[2]
            #print("--",self.__httpHeader)
            for code in str(self.__httpHeader.partition(r"\r\n")[0]).split():
                if code.isdigit():
                    self.__httpErrCode=int(code)
                    
            if(self.__httpErrCode != 200):
                self.__httpResponse=None
                
            return self.__httpErrCode
        else:
            return 0
    
    def getHTTPErrCode(self):
        """
        This funtion use to get latest parsed HTTP response's status code
        
        Return:
            HTTP status code.
        """
        return self.__httpErrCode
    
    def getHTTPResponse(self):
        """
        This funtion use to get latest parsed HTTP response's response massage.
        
        Return:
            HTTP response message.
        """
        return self.__httpResponse
    
    def __del__(self):
        """
        The distaructor for HttpParser class
        """
        pass
    



# -----------------------------------
#           esp8266.py
# -----------------------------------

from machine import UART, Pin
import time

ESP8266_OK_STATUS = "OK\r\n"
ESP8266_ERROR_STATUS = "ERROR\r\n"
ESP8266_FAIL_STATUS = "FAIL\r\n"
ESP8266_WIFI_CONNECTED="WIFI CONNECTED\r\n"
ESP8266_WIFI_GOT_IP_CONNECTED="WIFI GOT IP\r\n"
ESP8266_WIFI_DISCONNECTED="WIFI DISCONNECT\r\n"
ESP8266_WIFI_AP_NOT_PRESENT="WIFI AP NOT FOUND\r\n"
ESP8266_WIFI_AP_WRONG_PWD="WIFI AP WRONG PASSWORD\r\n"
ESP8266_BUSY_STATUS="busy p...\r\n"
UART_Tx_BUFFER_LENGTH = 1024
UART_Rx_BUFFER_LENGTH = 1024*2


class ESP8266:
    """
    This is a class for access ESP8266 using AT commands
    Using this class, you access WiFi and do HTTP Post/Get operations.
    
    Attributes:
        uartPort (int): The Uart port numbet of the RPI Pico's UART BUS [Default UART0]
        baudRate (int): UART Baud-Rate for communncating between RPI Pico's & ESP8266 [Default 115200]
        txPin (init): RPI Pico's Tx pin [Default Pin 0]
        rxPin (init): RPI Pico's Rx pin [Default Pin 1]
    """
    
    __rxData=None
    __txData=None
    __httpResponse=None
    
    def __init__(self, uartPort=0, baudRate=115200, txPin=(16), rxPin=(17)):
        """
        The constaructor for ESP8266 class
        
        Parameters:
            uartPort (int): The Uart port numbet of the RPI Pico's UART BUS [Default UART0]
            baudRate (int): UART Baud-Rate for communncating between RPI Pico's & ESP8266 [Default 115200]
            txPin (init): RPI Pico's Tx pin [Default Pin 0]
            rxPin (init): RPI Pico's Rx pin [Default Pin 1]
        """
        self.__uartPort=uartPort
        self.__baudRate=baudRate
        self.__txPin=txPin
        self.__rxPin=rxPin
        #print(self.__uartPort,       self.__baudRate,        self.__txPin,        self.__rxPin)
        self.__uartObj = UART(self.__uartPort, baudrate=self.__baudRate, tx=Pin(self.__txPin), rx=Pin(self.__rxPin), txbuf=UART_Tx_BUFFER_LENGTH, rxbuf=UART_Rx_BUFFER_LENGTH)
        #print(self.__uartObj)
        
    def _createHTTPParseObj(self):
        """
        This is private function for create HTTP response every time
        before doing the HTTP Post/Get operation
        
        """
        if(self.__httpResponse != None):
            del self.__httpResponse
            self.__httpResponse=HttpParser()
        else:
            #del self.__httpResponse
            self.__httpResponse=HttpParser()
        
    def _sendToESP8266(self, atCMD, delay=1):
        """
        This is private function for complete ESP8266 AT command Send/Receive operation.
        """
        self.__rxData=str()
        self.__txData=atCMD
        #print("---------------------------"+self.__txData)
        self.__uartObj.write(self.__txData)
        self.__rxData=bytes()
        
        time.sleep(delay)
        
        #while self.__uartObj.any()>0:
        #    self.__rxData += self.__uartObj.read(1)
        
        while True:
            #print(".")
            if self.__uartObj.any()>0:
                #print(self.__uartObj.any())
                break
        
        while self.__uartObj.any()>0:
            self.__rxData += self.__uartObj.read(UART_Rx_BUFFER_LENGTH)
            
        #print(self.__rxData)
        if ESP8266_OK_STATUS in self.__rxData:
            return self.__rxData
        elif ESP8266_ERROR_STATUS in self.__rxData:
            return self.__rxData
        elif ESP8266_FAIL_STATUS in self.__rxData:
            return self.__rxData
        elif ESP8266_BUSY_STATUS in self.__rxData:
            return "ESP BUSY\r\n"
        else:
            return None
        
    def startUP(self):
        """
        This funtion use to check the communication between ESP8266 & RPI Pico
        
        Return:
            True if communication success with the ESP8266
            False if unable to communication with the ESP8266
        """
        retData = self._sendToESP8266("AT\r\n")
        if(retData != None):
            if ESP8266_OK_STATUS in retData:
                return True
            else:
                return False
        else:
            return False
    
    def reStart(self):
        """
        This funtion use to Reset the ESP8266
        
        Return:
            True if Reset successfully done with the ESP8266
            False if unable to reset the ESP8266
        """
        retData = self._sendToESP8266("AT+RST\r\n")
        if(retData != None):
            if ESP8266_OK_STATUS in retData:
                time.sleep(5)
                #self.startUP()
                return self.startUP()
            else:
                return False
        else:
            False        
        
    
    def echoING(self, enable=False):
        """
        This function use to enable/diable AT command echo [Default set as false for diable Echo]
        
        Return:
            True if echo off/on command succefully initiate with the ESP8266
            False if echo off/on command failed to initiate with the ESP8266
        
        """
        if enable==False:
            retData = self._sendToESP8266("ATE0\r\n")
            if(retData != None):
                if ESP8266_OK_STATUS in retData:
                    return True
                else:
                    return False
            else:
                return False
        else:
            retData = self._sendToESP8266("ATE1\r\n")
            if(retData != None):
                if ESP8266_OK_STATUS in retData:
                    return True
                else:
                    return False
            else:
                return False
        
        
    def getVersion(self):
        """
        This function use to get AT command Version details
        
        Return:
            Version details on success else None
        """
        retData = self._sendToESP8266("AT+GMR\r\n")
        if(retData != None):
            if ESP8266_OK_STATUS in retData:
                #print(str(retData,"utf-8"))
                retData = str(retData).partition(r"OK")[0]
                #print(str(retData,"utf-8"))
                retData = retData.split(r"\r\n")
                retData[0] = retData[0].replace("b'","")
                retData=str(retData[0]+"\r\n"+retData[1]+"\r\n"+retData[2])
                return retData
            else:
                return None
        else:
            return None
        
    def reStore(self):
        """
        This function use to reset the ESP8266 into the Factory reset mode & delete previous configurations
        Return:
            True on ESP8266 restore succesfully
            False on failed to restore ESP8266
        """
        retData = self._sendToESP8266("AT+RESTORE\r\n")
        if(retData != None):
            if ESP8266_OK_STATUS in retData:   
                return True
            else:
                return False
        else:
            return None
    """    
    def chcekSYSRAM(self):
        #retData = self._sendToESP8266("AT+SYSRAM?\r\n")   
        self.__rxData=b''
        self.__txData="AT+SYSRAM?\r\n"
        self.__uartObj.write(self.__txData)
        self.__rxData=bytes()
        
        time.sleep(2)
        
        while self.__uartObj.any()>0:
            self.__rxData += self.__uartObj.read(1)
            
        print(self.__rxData.decode())
        if ESP8266_OK_STATUS in self.__rxData:
            return self.__rxData
        else:
            return 1
    """
        
    def getCurrentWiFiMode(self):
        """
        This fucntion use to query ESP8266 WiFi's current mode [STA: Station, SoftAP: Software AccessPoint, or Both]
        
        Return:
            STA if ESP8266's wifi's current mode pre-config as Station
            SoftAP if ESP8266's wifi's current mode pre-config as SoftAP
            SoftAP+STA if ESP8266's wifi's current mode set pre-config Station & SoftAP
            None failed to detect the wifi's current pre-config mode
        """
        retData = self._sendToESP8266("AT+CWMODE_CUR?\r\n")
        if(retData != None):
            if "1" in retData:
                return "STA"
            elif "2" in retData:
                return "SoftAP"
            elif "3" in retData:
                return "SoftAP+STA"
            else:
                return None
        else:
            return None
        
        
    def setCurrentWiFiMode(self, mode=3):
        """
        This fucntion use to set ESP8266 WiFi's current mode [STA: Station, SoftAP: Software AccessPoint, or Both]
        
        Parameter:
            mode (int): ESP8266 WiFi's [ 1: STA, 2: SoftAP, 3: SoftAP+STA(default)]
        
        Return:
            True on successfully set the current wifi mode
            False on failed set the current wifi mode
        
        """
        txData="AT+CWMODE_CUR="+str(mode)+"\r\n"
        retData = self._sendToESP8266(txData)
        if(retData!=None):
            if ESP8266_OK_STATUS in retData:   
                return True
            else:
                return False
        else:
            return False
        
    def getDefaultWiFiMode(self):
        """
        This fucntion use to query ESP8266 WiFi's default mode [STA: Station, SoftAP: Software AccessPoint, or Both]
        
        Return:
            STA if ESP8266's wifi's default mode pre-config as Station
            SoftAP if ESP8266's wifi's default mode pre-config as SoftAP
            SoftAP+STA if ESP8266's wifi's default mode set pre-config Station & SoftAP
            None failed to detect the wifi's default pre-config mode
        
        """
        retData = self._sendToESP8266("AT+CWMODE_DEF?\r\n")
        if(retData!=None):
            if "1" in retData:
                return "STA"
            elif "2" in retData:
                return "SoftAP"
            elif "3" in retData:
                return "SoftAP+STA"
            else:
                return None
        else:
            return None
        
    def setDefaultWiFiMode(self, mode=3):
        """
        This fucntion use to set ESP8266 WiFi's default mode [STA: Station, SoftAP: Software AccessPoint, or Both]
        
        Parameter:
            mode (int): ESP8266 WiFi's [ 1: STA, 2: SoftAP, 3: SoftAP+STA(default)]
            
        Return:
            True on successfully set the default wifi mode
            False on failed set the default wifi mode
            
        """
        txData="AT+CWMODE_DEF="+str(mode)+"\r\n"
        retData = self._sendToESP8266(txData)
        if(retData!=None):
            if ESP8266_OK_STATUS in retData:   
                return True
            else:
                return False
        else:
            return False
        
    def getAvailableAPs(self):
        """
        This fucntion use to query ESP8266 for available WiFi AccessPoins
        
        Retuns:
            List of Available APs or None
        """
        retData = str(self._sendToESP8266("AT+CWLAP\r\n", delay=10))
        if(retData != None):
            retData = retData.replace("+CWLAP:", "")
            retData = retData.replace(r"\r\n\r\nOK\r\n", "")
            retData = retData.replace(r"\r\n","@")
            retData = retData.replace("b'(","(").replace("'","")
            retData = retData.split("@")
            retData =list(retData)
            apLists=list()
            
            for items in retData:
                data=str(items).replace("(","").replace(")","").split(",")
                data=tuple(data)
                apLists.append(data)

            return apLists
        else:
            return None
        
    def connectWiFi(self,ssid,pwd):
        """
        This fucntion use to connect ESP8266 with a WiFi AccessPoins
        
        Parameters:
            ssid : WiFi AP's SSID
            pwd : WiFi AP's Password
        
        Retuns:
            WIFI DISCONNECT when ESP8266 failed connect with target AP's credential
            WIFI AP WRONG PASSWORD when ESP8266 tried connect with taget AP with wrong password
            WIFI AP NOT FOUND when ESP8266 cann't find the target AP
            WIFI CONNECTED when ESP8266 successfully connect with the target AP
        """
        txData="AT+CWJAP_CUR="+'"'+ssid+'"'+','+'"'+pwd+'"'+"\r\n"
        #print(txData)
        retData = self._sendToESP8266(txData, delay=15)
        #print(".....")
        #print(retData)
        if(retData!=None):
            if "+CWJAP" in retData:
                if "1" in retData:
                    return ESP8266_WIFI_DISCONNECTED
                elif "2" in retData:
                    return ESP8266_WIFI_AP_WRONG_PWD
                elif "3" in retData:
                    return ESP8266_WIFI_AP_NOT_PRESENT
                elif "4" in retData:
                    return ESP8266_WIFI_DISCONNECTED
                else:
                    return None
            elif ESP8266_WIFI_CONNECTED in retData:
                if ESP8266_WIFI_GOT_IP_CONNECTED in retData:
                    return ESP8266_WIFI_CONNECTED
                else:
                    return ESP8266_WIFI_DISCONNECTED
            else:
                return ESP8266_WIFI_DISCONNECTED
        else:
                return ESP8266_WIFI_DISCONNECTED
            
        
        
    def disconnectWiFi(self):
        """
        This fucntion use to disconnect ESP8266 with a connected WiFi AccessPoins
        
        Return:
            False on failed to disconnect the WiFi
            True on successfully disconnected
        """
        retData = self._sendToESP8266("AT+CWQAP\r\n")
        if(retData!=None):
            if ESP8266_OK_STATUS in retData:
                return True
            else:
                return False
        else:
            return False

    def _createTCPConnection(self, link, port=80):
        """
        This fucntion use to create connect between ESP8266 and Host.
        Just like create a socket before complete the HTTP Get/Post operation.
        
        Return:
            False on failed to create a socket connection
            True on successfully create and establish a socket connection.
        """
        #self._sendToESP8266("AT+CIPMUX=0")
        txData="AT+CIPSTART="+'"'+"TCP"+'"'+','+'"'+link+'"'+','+str(port)+"\r\n"
        #print(txData)
        retData = self._sendToESP8266(txData)
        #print(".....")
        #print(retData)
        if(retData != None):
            if ESP8266_OK_STATUS in retData:
                return True
            else:
                return False
        else:
            False
    
    def doHttpGet(self,host,path,user_agent="RPi-Pico", port=80):
        """
        This fucntion use to complete a HTTP Get operation
        
        Parameter:
            host (str): Host URL [ex: get operation URL: www.httpbin.org/ip. so, Host URL only "www.httpbin.org"]
            path (str): Get operation's URL path [ex: get operation URL: www.httpbin.org/ip. so, the path "/ip"]
            user-agent (str): User Agent Name [Default "RPi-Pico"]
            post (int): HTTP post number [Default port number 80]
        
        Return:
            HTTP error code & HTTP response[If error not equal to 200 then the response is None]
            On failed return 0 and None
        
        """
        if(self._createTCPConnection(host, port) == True):
            self._createHTTPParseObj()
            #getHeader="GET "+path+" HTTP/1.1\r\n"+"Host: "+host+":"+str(port)+"\r\n"+"User-Agent: "+user_agent+"\r\n"+"\r\n";
            getHeader="GET "+path+" HTTP/1.1\r\n"+"Host: "+host+"\r\n"+"User-Agent: "+user_agent+"\r\n"+"\r\n";
            #print(getHeader,len(getHeader))
            txData="AT+CIPSEND="+str(len(getHeader))+"\r\n"
            retData = self._sendToESP8266(txData)
            if(retData != None):
                if ">" in retData:
                    retData = self._sendToESP8266(getHeader, delay=2)
                    self._sendToESP8266("AT+CIPCLOSE\r\n")
                    retData=self.__httpResponse.parseHTTP(retData)
                    return retData, self.__httpResponse.getHTTPResponse()
                else:
                    return 0, None
            else:
                return 0, None
        else:
            self._sendToESP8266("AT+CIPCLOSE\r\n")
            return 0, None
            
        
    def doHttpPost(self,host,path,content_type,content,user_agent="RPi-Pico",port=80):
        """
        This fucntion use to complete a HTTP Post operation
        
        Parameter:
            host (str): Host URL [ex: get operation URL: www.httpbin.org/ip. so, Host URL only "www.httpbin.org"]
            path (str): Get operation's URL path [ex: get operation URL: www.httpbin.org/ip. so, the path "/ip"]
            user-agent (str): User Agent Name [Default "RPi-Pico"]
            content_type (str): Post operation's upload content type [ex. "application/json", "application/x-www-form-urlencoded", "text/plain"
            content (str): Post operation's upload content 
            post (int): HTTP post number [Default port number 80]
        
        Return:
            HTTP error code & HTTP response[If error not equal to 200 then the response is None]
            On failed return 0 and None
        
        """
        if(self._createTCPConnection(host, port) == True):
            self._createHTTPParseObj()
            postHeader="POST "+path+" HTTP/1.1\r\n"+"Host: "+host+"\r\n"+"User-Agent: "+user_agent+"\r\n"+"Content-Type: "+content_type+"\r\n"+"Content-Length: "+str(len(content))+"\r\n"+"\r\n"+content+"\r\n";
            #print(postHeader,len(postHeader))
            txData="AT+CIPSEND="+str(len(postHeader))+"\r\n"
            retData = self._sendToESP8266(txData)
            if(retData != None):
                if ">" in retData:
                    retData = self._sendToESP8266(postHeader, delay=2)
                    #print(".......@@",retData)            
                    self._sendToESP8266("AT+CIPCLOSE\r\n")
                    #print(self.__httpResponse)
                    retData=self.__httpResponse.parseHTTP(retData)
                    return retData, self.__httpResponse.getHTTPResponse()
                else:
                    return 0, None
            else:
                return 0, None
        else:
            self._sendToESP8266("AT+CIPCLOSE\r\n")
            return 0, None
        
    def __del__(self):
        """
        The distaructor for ESP8266 class
        """
        print('Destructor called, ESP8266 deleted.')
        pass
        





# -----------------------------------
#           MAIN PROGRAM
# -----------------------------------

def httpTestSequence():
    print("\r\n\r\n")
    print("Now it's time to start HTTP Get/Post Operation.......\r\n")

    while(1):    
        led.toggle()
        time.sleep(1)
        
        '''
        Going to do HTTP Get Operation with www.httpbin.org/ip, It return the IP address of the connected device
        '''
        httpCode, httpRes = esp01.doHttpGet("www.httpbin.org","/ip","RaspberryPi-Pico", port=80)
        print("------------- www.httpbin.org/ip Get Operation Result -----------------------")
        print("HTTP Code:",httpCode)
        print("HTTP Response:",httpRes)
        print("-----------------------------------------------------------------------------\r\n\r\n")
        
        
        '''
        Going to do HTTP Post Operation with www.httpbin.org/post
        '''
        post_json="{\"name\":\"Noyel\"}"
        httpCode, httpRes = esp01.doHttpPost("www.httpbin.org","/post","RPi-Pico", "application/json",post_json,port=80)
        print("------------- www.httpbin.org/post Post Operation Result -----------------------")
        print("HTTP Code:",httpCode)
        print("HTTP Response:",httpRes)
        print("--------------------------------------------------------------------------------\r\n\r\n")

#Redundant Imports
#from machine import Pin
#from esp8266 import ESP8266
#import time, sys
# import sys
# import utime
# 
# #-----STARTUP SEQUENCE-----#
# 
# WIFI_NAME = "SPU-Wireless"
# WIFI_PASSWORD = "SPU-Wireless"
# 
# print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
# print("RPi-Pico MicroPython Ver:", sys.version)
# print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
# 
# ## Create an ESP8266 Object
# #Default args: uartPort=0, baudRate=115200, txPin=(0), rxPin=(1)
# esp01 = ESP8266()
# esp8266_at_ver = None
# 
# print("StartUP",esp01.startUP())
# print("Echo-Off",esp01.echoING())
# print("\r\n")
# 
# #Print ESP8266 AT comand version and SDK details
# esp8266_at_ver = esp01.getVersion()
# if(esp8266_at_ver != None):
#     print(esp8266_at_ver)
#     
# #-----WIFI CONFIGURATION-----#
# 
# #Set the current WiFi in SoftAP+STA
# print("WiFi Current Mode:",esp01.setCurrentWiFiMode())
# print("\r\n\r\n")
# 
# #Connect with the WiFi
# print("Try to connect with the WiFi..")
# while (1):
#     if "WIFI CONNECTED" in esp01.connectWiFi(WIFI_NAME, WIFI_PASSWORD): ###CHANGE WIFI SETTINGS
#         print("ESP8266 connect with the WiFi..")
#         break;
#     else:
#         print(".")
#         time.sleep(2)
# 
# #-----FUNCTIONALITY-----#
#         
# #Sample HTTP Sequence
# #httpTestSequence()
# 
# # Get the current timestamp in seconds since epoch
# timestamp = utime.time()
# 
# # Convert the timestamp to a tuple representing local time
# local_time = utime.localtime(timestamp)
# 
# # Extract individual components from the local time tuple
# year, month, day, hour, minute, second, _, _ = local_time
# 
# # Print the current date and time
# print("Date: {:04d}-{:02d}-{:02d}".format(year, month, day))
# print("Time: {:02d}:{:02d}:{:02d}".format(hour, minute, second))


