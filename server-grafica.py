#!/usr/bin/python
from socket import *
from protocolo import *
import os, sys
import signal
HOST = ''
PORT = 5000
BUF = 1024
pasivofd = socket(AF_INET, SOCK_STREAM)
pasivofd.bind((HOST, PORT))
pasivofd.listen(5)
# evito zzzzooooombiessss
signal.signal(signal.SIGCHLD, signal.SIG_IGN)
while 1:
    #print 'fumando espero ...'
    activofd, addr = pasivofd.accept()
    pid = os.fork()
    if pid == 0: # proceso hijo 
        while 1:
            leido = activofd.recv(BUF)
            if not leido:
                break
            ################################################
            if leido[0] == SOF:
                largo = ord(leido[1])
                if largo != 0:
                   salida = comandos(leido[2], leido[3:], 'g') # mando el comando y los datos restantes 
                   i = 0
                   while i < len(salida)/5:
                       if salida[0+(i*5)] != (i*5):
                           sys.stdout = open(salida[0+(i*5)]+'.txt' , "w")
                           print salida[1+(i*5)] 
                           print salida[2+(i*5)] 
                           print salida[3+(i*5)] 
                           print salida[4+(i*5)] 
                       i = i + 1
        ################################################
        activofd.close()
        sys.exit()
    # el padre sigue escuchando 
pasivofd.close()

