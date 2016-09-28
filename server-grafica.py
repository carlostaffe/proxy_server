#!/usr/bin/python
from socket import *
from protocolo import *
import os, sys
HOST = ''
PORT = 5000
BUF = 1024
pasivofd = socket(AF_INET, SOCK_STREAM)
pasivofd.bind((HOST, PORT))
pasivofd.listen(5)
while 1:
    print 'fumando espero ...'
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
                    comandos(leido[2], datos[3:], 'g') # mando el comando y los datos restantes 

        ################################################
        # padre .... sigue escuchando
        activofd.close()
        sys.exit()
    else: # el padre
        print '...Cliente desde:', addr
pasivofd.close()

