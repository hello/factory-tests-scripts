import Queue
import subprocess
import threading
import re
import json
import sys
import os
import shlex
import time

class AsynchronousFileReader(threading.Thread):
    '''
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    '''

    def __init__(self, fd, queue):
        assert isinstance(queue, Queue.Queue)
        assert callable(fd.readline)
        threading.Thread.__init__(self)
        self._fd = fd
        self._queue = queue

    def run(self):
        '''The body of the tread: read lines and put them on the queue.'''
        for line in iter(self._fd.readline, ''):
            self._queue.put(line)

    def eof(self):
        '''Check whether there is no more content to expect.'''
        return not self.is_alive() and self._queue.empty()

def main(logPath,args):
    result = ""
    try:
        with open(logPath,'w') as f:
            try:
                try:
                    action = args[1+args.index("-a")]
                    print "Action: %s" % action
                except ValueError:
                    f.write("FAIL: Couldn't find action")
                    sys.exit(-1)
                command = subprocess.Popen(args, stdout=subprocess.PIPE)
                process = subprocess.Popen(["adb","logcat","-s","TestOutput"], stdout=subprocess.PIPE)

# Launch the asynchronous readers of the process' stdout.
                stdout_queue = Queue.Queue()
                stdout_reader = AsynchronousFileReader(process.stdout, stdout_queue)
                stdout_reader.start()

                done = False
                fail = False
                linePattern = "([IDE])\s+TestOutput\:\s+(\{.*\})\s*$"
                while not stdout_reader.eof() and not done:
                    while not stdout_queue.empty():
                        time.sleep(.1)
                        line = stdout_queue.get().strip()
                        if line.startswith("----"):
                            continue
                        reObj = re.search(linePattern,line)
                        if (not reObj) or reObj.group(2) == "":
                            done = True
                            fail = True
                            newStuff = line
                            print newStuff
                            result = result + newStuff + os.linesep
                            continue
                        else:
                            try:
                                jsonObj = json.loads(reObj.group(2))
                            except ValueError:
                                done = True
                                fail = True
                                newStuff = "Not JSON: %s" % reObj.group(2)
                                print newstuff
                                result = result + newStuff + os.linesep
                                continue
                            if reObj.group(1).upper() == "E":
                                done = True
                                fail = True
                                try:
                                    newStuff = jsonObj['message'] + os.linesep + line
                                    print newStuff
                                    result = result + newStuff + os.linesep
                                except KeyError:
                                    newStuff = "Key Error: %s" % str(reObj.group(0))
                                    print newStuff
                                    result = result + newStuff + os.linesep
                                continue
                            try:
                                if jsonObj['event'] == "begin_command" and jsonObj['action'] == action:
                                    done = True
                                    newStuff = "Action started: %s" % action
                                    print newStuff
                                    result = result + newStuff + os.linesep
                                elif jsonObj['action'] != action:
                                    done = True
                                    fail = True
                                    newStuff = "Action doesn't match: %s" % jsonObj['action']
                                    result = result + newStuff + os.linesep
                                    continue
                            except KeyError:
                                done = True
                                fail = True
                                newStuff = "Key Error: %s" % str(jsonObj)
                                result = result + newStuff + os.linesep
                                continue

                process.terminate()
                if fail:
                    f.write("FAIL: %s" % result.rstrip())
                    sys.exit(-1)
                else:
                    f.write("PASS: %s" % result.rstrip())
                    sys.exit(0)
            except Exception as e:
                #clearCode = subprocess.Popen(["adb","logcat","-c"])
                f.write("FAIL: Unhandled Exception %s\n%s" % (repr(e),result.rstrip()))
                sys.exit(-1)
    except IOError:
        print "FAIL: Couldn't open log out"
        sys.exit(-1)

if __name__ == "__main__":
    clearCode = subprocess.Popen(["adb","logcat","-c"])
    time.sleep(.5)
    clearCode.terminate()
    if len(sys.argv) == 1:
        logPath = "androidLog.txt"
        args = ["adb","shell","am","broadcast","-p","\"is.hello.puppet\"","-a","\"is.hello.puppet.ACTION_DISCOVER\"","--es","sense_id","\"A66B6BC4EB9CC237\""]
    elif len(sys.argv) == 2:
        logPath = "androidLog.txt"
        args = shlex.split(sys.argv[1])
    elif len(sys.argv) == 3:
        logPath = sys.argv[1]
        args = shlex.split(sys.argv[2])
    else:
        print sys.argv
        logPath = sys.argv[1]
        args = sys.argv[2:]
    main(logPath,args)
