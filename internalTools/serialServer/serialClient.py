#import os
#import sys
import socket

packetSize = 1024
maxSize = 4096

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#sock.setblocking(0)
localAddr = ('localhost',43556)
sock.connect(localAddr)
message = {"action":"connect_serial","port":"/dev/cu.usbserial-FTXKC7LC","purpose":"uut"}
message = {"action":"enable_recording"}
#message = {"action":"add_recording_tag", "tag": "XXXXXXX IM A TAG! YYAYAYAYXXXXX"}
#message = {"action":"serial_message","message":"boot","purpose":"uut"}
#message = {"action":"serial_message","message":"led stop","purpose":"uut"}
#message = {"action":"serial_message","message":"loglevel 40","purpose":"uut"}
#message = {"action":"serial_message_re","message":"temp","purpose":"uut", "regular_expression":"\d+"}
message = {"action":"disable_recording"}
#message = {"action":"disconnect_serial","purpose":"uut"}
sock.sendall(str(message).replace("'",'"'))
sock.send("\0")
stuff = sock.recv(1024)
print stuff
sock.close()

print "Done"





