#Readme
#Primary dev: Brandon Clarke
#How to use: python serialServer [install|start|stop|restart|remove|debug]
#Note: Unless run on windows, willl default to debug. This code is
#designed to be run as a windows service. It runs in the background and
#manages the direct serial connections to support systems that otherwise
#don't multitask or do anything at all very well. This will also be very
#helpful if Jabil ever drops us and we need to use the existing testers
#at another manufacturer. This code shouldn't crash. If it does and you
#were running it as a windows service, to get to the error log:
#Start->event viewer->windows logs->applications and look for the Error
#at the top (you need to refresh that window for the next one to appear)

#Other stuff: to install as a windows service, google pywin32 and install
#the appropriate version. You might also need some serial class for osx
import os
import socket
import json
import logging
import time
import datetime
from logging.handlers import RotatingFileHandler
import re
import serial
import errno
import sys

class SerialPort:
    """ Higher level serial port class to contain port and status info."""
    disconnected, connected = range(2)
    defaultReceiveTimeSec = 3
    def __init__(self, purpose, port=None, baudrate=115200, parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, connectionTimeout=2):
#defaults work with sense
        self.purpose = purpose
        self.status = self.disconnected
        self.ser = None
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.connectionTimeout = connectionTimeout
        self.isRecording = False
        self.recordingPath = None
        self.recRef = None
        self.otherData = ""

    def __repr__(self):
        return "%r(status=%r, ser=%r, port=%r, baudrate=%r, parity=%r, " \
        "stopbits=%r, bytesize=%r, connectionTimeout=%r, isRecording=%r, " \
        "recordingPath=%r, recRef=%r, otherData=%r)" % (self.purpose,
            self.status, self.ser, self.port, self.baudrate, self.parity,
            self.stopbits, self.bytesize, self.connectionTimeout,
            self.isRecording, self.recordingPath, self.recRef, self.otherData)

    def __str__(self):
        return "%r(status=%r, port=%r, baudrate=%r, parity=%r, " \
        "stopbits=%r, bytesize=%r, isRecording=%r, " \
        "recordingPath=%r)" % (self.purpose,
            self.status, self.port, self.baudrate, self.parity,
            self.stopbits, self.bytesize,
            self.isRecording, self.recordingPath)

    def connect(self, port=None, baudrate=None, parity=None,
        stopbits=None, bytesize=None, connectionTimeout=None):
        if not self.status is self.disconnected:
            raise HelloSerialException("Can't connect when already connected")
        if port:
            self.port = port
        if baudrate:
            self.baudrate = baudrate
        if parity:
            self.parity = parity
        if stopbits:
            self.stopbits = stopbits
        if bytesize:
            self.bytesize = bytesize
        if connectionTimeout:
            self.connectionTimeout = connectionTimeout
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=self.connectionTimeout
                )
        except OSError as e:
            raise HelloSerialException("Could not open serial port", str(e))
        self.status = self.connected

    def clearReadBuffer(self, timeoutSec=None):
        if not self.status is self.connected:
            raise HelloSerialException("Can't clear buffer when not connected")
        if not timeoutSec:
            timeoutSec = self.defaultReceiveTimeSec
        done = False
        data = []
        startTime = datetime.datetime.now()
        while not done and (datetime.datetime.now() - startTime) <= datetime.timedelta(seconds=timeoutSec):
            bytesToRead = self.ser.inWaiting()
            if not bytesToRead:
                done = True
            else:
                newData = self.ser.read(bytesToRead)
                data.append(newData)
        if not done:
            raise HelloSerialException("Could not clearReadBuffer in %d seconds" % timeoutSec)
        dataString = "".join(data)
        return re.sub("^\r","", re.sub("\r\r+", '\r', dataString))

    def send(self, message):
        if not self.status is self.connected:
            raise HelloSerialException("Can't send when not connected")
        self.ser.write((message).encode())

    def receiveRe(self, expression, receiveTime=None):
        if not self.status is self.connected:
            raise HelloSerialException("Can't receive when not connected")
        if not receiveTime:
            receiveTime = self.defaultReceiveTimeSec
        done = False
        data = ""#concatenating this can be slow. should really do append and a join at the end,
# but can't do that with a regular_expression that needs to be constantly checked :-/
        startTime = datetime.datetime.now()
        reObj = None
        while not done and (datetime.datetime.now() - startTime) <= datetime.timedelta(seconds=receiveTime):
            time.sleep(0.1)
            bytesToRead = self.ser.inWaiting()
            if not bytesToRead:
                continue
            newData = self.ser.read(bytesToRead)
            data += newData
            reObj = re.search(expression, data)
            if reObj:
                done = True

        self.otherData = data
        if reObj:
            return reObj.group(0), data#let the client get sub matches if they want, don't bother pickling here
        else:
            return "", data

    def sendAndReceiveRE(self, message, expression, receiveTime=None):
        data = self.clearReadBuffer()
        self.send(message)
        matchedExpresion, otherData = self.receiveRe(expression, receiveTime)
        self.otherData = data + otherData
        return matchedExpresion, self.otherData

    def disconnect(self):
        if not self.status is self.connected:
            raise HelloSerialException("Can't disconnect when not connected")
        self.ser.close()
        self.ser = None
        self.status = self.disconnected

class HelloSerialException(Exception):
    """Error class to differentiate expected vs unexpected errors."""
    def __init__(self, message, errors=None):
        super(HelloSerialException, self).__init__(message)
        self.errors = errors
        self.message = message

    def __str__(self):
        return "Error Message: \"%s\" Other info: \"%s\"" % (self.message, self.errors)

class StructuredMessage(object):
    """Class to make logging look pretty"""
    def __init__(self, state, **kwargs):
        self.state = state
        self.kwargs = kwargs

    def __str__(self):
        totalDict = {"event": self.kwargs, "state": self.state}
        totalDict["event"]["time"] = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        return json.dumps(totalDict)

_ = StructuredMessage #easier to read

def returnDone():
    """Returns the correct value of done for usage type"""
    if runningAsService:
        return win32event.WAIT_OBJECT_0
    else:
        return True

runningAsService = os.name == 'nt' and not (len(sys.argv) == 2 and sys.argv[1] == "debug")

if os.name == 'nt':#windows
    rootLogDir = r'C:\helloLogs'
else:
    rootLogDir = r'/Users/brandon/tmp/helloLogs'

rootLogPath = os.path.join(rootLogDir,"serviceLog.txt")
try:
    os.makedirs(rootLogDir)
except:
    pass

fileHandler = RotatingFileHandler(rootLogPath, mode='a', maxBytes=100000000, backupCount=20)#avoids super giant log files
formatter = logging.Formatter('{"%(levelname)s": %(message)s}')
fileHandler.setFormatter(formatter)
logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)#suggest info for regular usage, debug for ...
logger.addHandler(fileHandler)
logger.propagate = False

state = {#this is what gets sent when logging. in my original plan there would be more stuff
        "rootLogPath": rootLogPath,
        "caller": None,
        "action": "idle",
        "restarted": False
        }

if runningAsService:#windows service stuff, don't touch
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager

    logger.critical(_(state, message="Service command issued"))

    class AppServerSvc (win32serviceutil.ServiceFramework):
        _svc_name_ = "HelloSerialServer"
        _svc_display_name_ = "Hello Serial Server"
        _svc_description_  = "Server to manage serial connections for tester backend"

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

        def SvcStop(self):
            logger.info(_(state, message="Main loop stopped from service command"))
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_,''))

        def SvcDoRun(self):
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_,''))
            self.main()

        def main(self):
            logger.info(_(state, message="Main loop started from service command"))
            mainLoop(self.hWaitStop)


def mainLoop(hWaitStop):
    packetSize = 1024#this is awful and should be changed
    maxSize = 4096

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(0)
    sock.settimeout(.1)
    localAddr = ('0.0.0.0', 43556)
    sock.bind(localAddr)

    sock.listen(1)

    logger.debug(_(state, message="Service started"))

    serialPorts = {}

    if runningAsService:
        isDone = None
    else:
        isDone = False

    while isDone != returnDone():
        connection = None
        state['caller'] = None
        state['action'] = "idle"
        state['status'] = "none"
        if runningAsService:
            isDone = win32event.WaitForSingleObject(hWaitStop, 5)#without this you can't stop the service without restarting
        try:
            connection, clientAddr = sock.accept()
            state['caller'] = clientAddr
            totalData = 0
            dataList = []
            totalErrs = 0
            while True:
                try:
                    data = connection.recv(packetSize)
                except socket.timeout:
                    raise HelloSerialException("Socket timed out during receive", totalData)
                except socket.error as e:
                    if (e.errno == errno.EAGAIN or e.errno == 10035) and totalErrs < 100:#bullshit mac stuff, and picked 100 randomly
                        time.sleep(.1)
                        totalErrs += 1
                        continue
                    elif e.errno == errno.EAGAIN or e.errno == 10035:
                        raise HelloSerialException("Lotsa socket errors", totalData)
                    else:
                        raise e
                if data:
                    if len(data) + totalData > maxSize:
                        raise HelloSerialException("Message too big, max size is %d" % maxSize)
                    dataList.append(data)
                    totalData += len(data)
                    if '\0' in data:
                        break
                else:
                    break

            finalData = ''.join(dataList).split('\0')[0]#python string join instead of += , lmgtfy
            try:
                jsonObj = json.loads(finalData)
                logger.info(_(state, message="message received", jsonMessage=json.dumps(jsonObj)))
            except:
                raise HelloSerialException("Message isn't valid json", data)

            try:
                state['action'] = jsonObj['action']
            except KeyError as e:
                raise HelloSerialException("Message must have 'action'", jsonObj)

            response = ""
            if state['action'] == "connect_serial":
                """connect to a serial port"""
                try:
                    serialPorts[jsonObj['purpose']] = SerialPort(
                        purpose=jsonObj['purpose'],
                        port=jsonObj['port'],
                        baudrate=jsonObj['baudrate'],
                        parity=jsonObj['parity'],
                        stopbits=jsonObj['stopbits'],
                        bytesize=jsonObj['bytesize'])
                    serialPorts[jsonObj['purpose']].connect()
                except KeyError as e:
                    raise HelloSerialException("connect_serial must have fields: purpose, port, baudrate, parity, stopbits, bytesize", jsonObj)
                logger.debug(_(state, message="serial connected", purpose=jsonObj['purpose'],
                    port=jsonObj['port']))
            elif state['action'] == "serial_message":
                """send a message bug don't worry about response"""
                try:
                    serialPorts[jsonObj['purpose']].send(jsonObj['message'])
                except KeyError as e:
                    raise HelloSerialException("serial_message must have purpose and message fields", jsonObj)
                logger.debug(_(state, message="sent serial message", purpose=jsonObj['purpose'],
                    sentMessage=jsonObj['message']))
            elif state['action'] == "serial_message_re":
                """send a message and get the response"""
                try:
                    try:
                        delay = jsonObj['delay']
                    except KeyError as e:
                        delay = SerialPort.defaultReceiveTimeSec
                    response = serialPorts[jsonObj['purpose']].sendAndReceiveRE(jsonObj['message'], jsonObj['regular_expression'], delay)[0]
                except KeyError as e:
                    raise HelloSerialException("serial_message_re must have purpose, message, and regular_expression fields", jsonObj)
                logger.debug(_(state, message="sent serial message and received re",
                    purpose=jsonObj['purpose'], sentMessage=jsonObj['message'],
                    receivedRe=response))
            elif state['action'] == "disconnect_serial":
                """disconnect serial port"""
                try:
                    serialPorts[jsonObj['purpose']].isRecording = False
                    serialPorts[jsonObj['purpose']].disconnect()
                except KeyError as e:
                    raise HelloSerialException("disconnect_serial must have purpose field", jsonObj)
                logger.debug(_(state, message="disconnected serial",
                    purpose=jsonObj['purpose']))
            elif state['action'] == "disconnect_all_serials":
                """disconnect all, don't return errors"""
                for key, ser in serialPorts:
                    ser.isRecording = False
                    try:
                        ser.disconnect()
                        logger.debug(_(state, message="Serial port %s cleared" % key))
                    except HelloSerialException:#catch everything?
                        pass
                try:#great to run at end of test to get everything clean
                    if jsonObj['clear']:
                        serialPorts = {}
                        logger.debug(_(state, message="Serial ports cleared"))
                except KeyError:
                    pass
            elif state['action'] == "enable_recording":
                """record everything that comes out of the serial port.
                This is great for debugging and is kind of the whole
                point of this, so you should probably have it on for uut
                """
                try:
                    if serialPorts[jsonObj['purpose']].status != SerialPort.connected:
                        raise HelloSerialException("Serial Port not connected", serialPorts[jsonObj['purpose']])
                    if serialPorts[jsonObj['purpose']].isRecording:
                        raise HelloSerialException("Serial port already recording", serialPorts[jsonObj['purpose']])
                except KeyError as e:
                    raise HelloSerialException("enable recording requires specifying a serial purpose", jsonObj)
                try:
                    filePath = os.path.join(rootLogDir, jsonObj['file_path'])
                    if not os.path.abspath(filePath).startswith(rootLogDir):
                        raise HelloSerialException("no relative paths outside the current directory", filePath)
                    if os.path.isdir(filePath):
                        raise HelloSerialException("directory with that name, try something else", filePath)
                    serialPorts[jsonObj['purpose']].recordingPath = filePath
                    os.makedirs(os.path.split(filePath)[0])
                except KeyError as e:
                    serialPorts[jsonObj['purpose']].recordingPath = os.path.join(rootLogDir, "recordingFile_%s.txt" % jsonObj['purpose'])
                except OSError as e:
                    pass#dirs exist
                try:
                    serialPorts[jsonObj['purpose']].recRef = open(serialPorts[jsonObj['purpose']].recordingPath,'w', 0)#0 means no buffer
                except IOError as e:
                    raise HelloSerialException("Can't open recording file", serialPorts[jsonObj['purpose']].recordingPath)
                serialPorts[jsonObj['purpose']].isRecording = True
                logger.debug(_(state, message="recording enabled",
                    recordingPath=serialPorts[jsonObj['purpose']].recordingPath))
            elif state['action'] == "add_recording_tag":
                """Want to make debugging easier?
                Ask me how to make a take in the recording log
                so you can easily see what you did when!
                """
                try:
                    if not serialPorts[jsonObj['purpose']].isRecording:
                        raise HelloSerialException("Not currently recording", serialPorts[jsonObj['purpose']])
                    if not serialPorts[jsonObj['purpose']].recRef:
                        raise HelloSerialException("Something bad happened, no recording reference", serialPorts[jsonObj['purpose']])
                    serialPorts[jsonObj['purpose']].recRef.write(jsonObj['tag']+'\r\n')
                except KeyError as e:
                    raise HelloSerialException("add_recording_tag needs purpose and tag fields", jsonObj)
                except IOError as e:
                    raise HelloSerialException("Something went wrong writing", str(e))
                logger.debug(_(state, message="added recording tag", tag=jsonObj['tag']))
            elif state['action'] == "disable_recording":
                """you'll never guess what this does"""
                try:
                    if not serialPorts[jsonObj['purpose']].isRecording:
                        raise HelloSerialException("Not currently recording", serialPorts[jsonObj['purpose']])
                    if not serialPorts[jsonObj['purpose']].recRef:
                        raise HelloSerialException("Something bad happened, no recording reference", serialPorts[jsonObj['purpose']])
                    serialPorts[jsonObj['purpose']].recRef.close()
                except KeyError as e:
                    raise HelloSerialException("disable recording must have purpose field", jsonObj)
                except IOError as e:
                    serialPorts[jsonObj['purpose']].isRecording = False
                    raise HelloSerialException("Something went wrong closing", str(e))
                serialPorts[jsonObj['purpose']].isRecording = False
                logger.debug(_(state, message="disabled recording"))
            elif state['action'] == "add_logging_tag":
                """Like a recording tag, but not as sexy"""
                try:
                    logger.info(_(state, message="adding logging tag", tag=jsonObj['tag']))
                except KeyError as e:
                    raise HelloSerialException("add_logging_tag needs tag field", jsonObj)
            elif state['action'] == "close_service":
                """You probably don't want to do this"""
                isDone = returnDone()
                logger.critical(_(state, message="closing service"))
            elif state['action'] == "serial_status":
                """see what's going on with the serial ports"""
                response = ""
                for key, ser in serialPorts.iteritems():
                    if response:
                        response += ", "
                    response += str(ser)
                try:
                    if jsonObj['verbose']:
                        response = repr(serialPorts)
                except KeyError:
                    pass
            else:
                """Add your own fun here!"""
                raise HelloSerialException("Unknown action", state['action'])

            state['status'] = "pass"
            logger.debug(_(state, message="action passed"))

        except socket.timeout as e:
            pass#a real pass!
        except HelloSerialException as e:
            state['status'] = "error"
            response = str(e)
            logger.error(_(state, message="known error thrown", errorMessage=str(e)))
        except:#don't crash!
            state['status'] = "error"
            response = sys.exc_info()[1].message
            logger.error(_(state, message="UNKNOWN error thrown", errorMessage=str(sys.exc_info()[1])))

        if not state['action'] == "idle":#if you got a message, reply
            reply = {'action': state['action'],
                    'status': state['status'],
                    'response': response}
            try:
                connection.sendall(json.dumps(reply) + "\0")
                logger.info(_(state, message="reply sent", reply=json.dumps(reply)))
            except:
                logger.error(_(state, message="Error sending reply", reply=json.dumps(reply)))

        if connection:
            try:
                connection.close()
                logger.debug(_(state, message="connection closed"))
            except Exception as e:
                logger.error(_(state, message="error closing connection",
                    errorMessage=e.message))

        for key, ser in serialPorts.iteritems():
            if ser.isRecording:
                if ser.otherData:
                    ser.recRef.write(ser.otherData)#stuff captured waiting for regular expression
                moreData = ser.clearReadBuffer()
                if moreData:
                    ser.recRef.write(moreData)

    for key, ser in serialPorts.iteritems():
        try:
            ser.disconnect()
        except:
            pass
        try:
            ser.recRef.close()
        except:
            pass


    try:
        sock.close()
    except:
        pass


if __name__ == '__main__':
    if runningAsService:#don't screw with this
        if len(sys.argv) == 2 and sys.argv[1] == "install":
            sys.argv = [sys.argv[0],"--startup","delayed", sys.argv[1]]

        win32serviceutil.HandleCommandLine(AppServerSvc, argv=sys.argv)
    else:
        mainLoop(None)
