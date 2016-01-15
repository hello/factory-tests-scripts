import socket
import datetime
import argparse
import json
import sys
import errno

def setupParser():
    """Command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--message",      help="json formatted message to send to the serial server")
    parser.add_argument("-w", "--wait_time",    help="how long to wait for response in seconds",
        default=3, type=float)
    parser.add_argument("-l", "--log_path",     help="output path of file for received JSON. JabilTest reads from this file")
    return parser.parse_args()

def mainFunc():
    """Do things here"""
    arguments = setupParser()

    if not arguments.log_path:
        print "Must provide log path"
        sys.exit(-1)

    try:
        logFile = open(arguments.log_path, 'w')
    except:
        print "Couldn't open log file"
        sys.exit(-1)

    try:
        if not arguments.message:
            raise ValueError("Must provide message")

        try:
            json.loads(arguments.message)
        except ValueError as e:
            raise ValueError("Must provide valid JSON as message")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(1)
        localAddr = ('localhost',43556)

        sock.connect(localAddr)
        sock.setblocking(0)
        sock.sendall(arguments.message + '\0')

        done = False
        returnText = []
        startTime = datetime.datetime.now()
        while not done and (datetime.datetime.now() - startTime) <= datetime.timedelta(seconds=arguments.wait_time):
            try:
                thisRun = sock.recv(1024)
            except socket.error as e:
                if e.errno == errno.EAGAIN or e.errno == 10035:#bullshit mac stuff
                    continue
                else:
                    raise
            returnText.append(thisRun)
            if '\0' in thisRun or len(thisRun) == 0:
                done = True

        if not done:
            raise ValueError("Full message not received in time")

        message = "".join(returnText)
        print message
        logFile.write(message)

    except Exception as e:
        message = '{"status":"fail","response":"%s"}' % str(e)
        print message
        logFile.write(message)
    finally:
        logFile.close()

    sock.close()

if __name__ == '__main__':
    mainFunc()

