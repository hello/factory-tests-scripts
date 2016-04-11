#import os
#import sys
import socket
import time

packetSize = 1024
maxSize = 4096

#sock.setblocking(0)
localAddr = ('127.0.0.1',43556)
messages = []
messages.append({"action":"disconnect_serial","purpose":"power_supply"})
messages.append({"action":"disconnect_serial","purpose":"uut"})
messages.append({"action":"disconnect_serial","purpose":"golden"})
messages.append({"action":"disconnect_serial","purpose":"control_board"})
messages.append({"action":"delay","length":5})

messages.append({"action":"connect_serial","port":0,"purpose":"control_board", "baudrate":19200, "parity":'N', "stopbits":1,"bytesize":8})
#messages.append({"action":"enable_recording","purpose":"control_board"})


messages.append({"action":"connect_serial","port":"/dev/cu.usbserial-FTXKC7LC","purpose":"uut", "baudrate":115200, "parity":'N', "stopbits":1,"bytesize":8, "timestamp_enabled":True, "detect_restart":True})
messages.append({"action":"enable_recording","purpose":"uut"})


messages.append({"action":"connect_serial","port":7,"purpose":"golden", "baudrate":115200, "parity":'N', "stopbits":1,"bytesize":8})
messages.append({"action":"enable_recording","purpose":"golden"})


messages.append({"action":"connect_serial","port":2,"purpose":"power_supply", "baudrate":19200, "parity":'N', "stopbits":1,"bytesize":8})
messages.append({"action":"enable_recording","purpose":"power_supply"})


messages.append({"action":"serial_message","purpose":"power_supply","message":"SYST:REM\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"INST FIR\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"VOLT 24.0V\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"CURR 0.5A\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"VOLT:PROT 10V\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"INST SECO\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"VOLT 12.0V\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"CURR 0.5A\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"VOLT:PROT 10V\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"INST THI\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"VOLT 5.25V\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"CURR 2A\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"VOLT:PROT 5V\n"})
messages.append({"action":"serial_message","purpose":"power_supply","message":"OUTP 1\n"})

messages.append({"action":"serial_message","purpose":"control_board","message":"#RKA$\r\n"})
messages.append({"action":"serial_message_re","purpose":"control_board","message":"#HELP$\r\n","delay":0.5,"regular_expression":"Ver\:\d\.\d"})
messages.append({"action":"serial_message_re","purpose":"control_board","message":"#IN1$\r\n","delay":1,"regular_expression":"\d"})
messages.append({"action":"serial_message","purpose":"control_board","message":"#RK0$\r\n"})
messages.append({"action":"serial_message","purpose":"control_board","message":"#SK1$\r\n"})

#messages.append({"action":"serial_message","message":"loglevel 40","purpose":"uut"})
messages.append({"action":"serial_message","message":"boot\r\n","purpose":"uut"})
messages.append({"action":"serial_status","verbose": False})

#messages.append({"action":"serial_message","purpose":"power_supply","message":"OUTP 0\n"})
#messages.append({"action":"disable_recording", "purpose":"power_supply"})
#messages.append({"action":"disconnect_serial","purpose":"power_supply"})
#message = {"action":"connect_serial","port":"/dev/cu.usbserial-FTXKC7LC","purpose":"power_supply"}
#message = {"action":"enable_recording"}
#message = {"action":"add_recording_tag", "tag": "XXXXXXX IM A TAG! YYAYAYAYXXXXX"}
#message = {"action":"serial_message","message":"boot","purpose":"power_supply"}
#message = {"action":"serial_message","message":"led stop","purpose":"power_supply"}
#message = {"action":"serial_message","message":"loglevel 40","purpose":"power_supply"}
#message = {"action":"serial_message_re","message":"temp","purpose":"power_supply", "regular_expression":"\d+"}
#message = {"action":"disable_recording"}
#message = {"action":"disconnect_serial","purpose":"power_supply"}
for message in messages:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(localAddr)
    print message
    sock.sendall(str(message).replace("'",'"').replace("True","true").replace("False","false") + '\0')
    stuff = sock.recv(1024)
    print stuff
    sock.close()
    time.sleep(1)






