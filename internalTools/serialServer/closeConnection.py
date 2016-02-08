import os
import sys
import socket

packetSize = 1024
maxSize = 4096

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#sock.setblocking(0)
localAddr = ('localhost',43556)
sock.connect(localAddr)
message = {"action":"close_service"}
sock.sendall(str(message).replace("'",'"'))
sock.send("\0")
sock.close()

print "Done"





