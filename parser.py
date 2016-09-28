#!/usr/bin/python
import time
import sys
import getopt
from protocolo import *
#                          char<>DLE and char<>ETX
#     _______________________________
#    |    largo = 0 \                \
# ___|__           _|___          ___|__
#/waiting\------->/length\------->/data \
#\______/<-\      \______/     /->\___ _/
#     |     |                |     |   
#     \____/                  \___/        
#     char<>SOF             char<>ESC


###################################################################################
myopts, args = getopt.getopt(sys.argv[1:],"vd:i:")
salida = ' '  
archivo= ' ' 
###############################
# o == option
# a == argument passed to the o
###############################
for o, a in myopts:
    if o == '-v':
       DEBUG=True; 
    elif o == '-d':
        if a != 't' and a !='v' and a !='g' :
            print("Usage: %s -d option support only t(ension) , v(oltaje) or g(graphic) argument" % sys.argv[0])
            exit()
        salida = a 
    elif o == '-i':
       archivo = a
if salida == ' ' or archivo == ' '  :
    print("Usage: %s -d [t|v|g] -v -i file" % sys.argv[0])
    exit()

fd = open(archivo, "r")
#etiqueta
if salida == 't': #datos de temperatura
    print "etiqueta,fecha,hora,temperatura"
if salida == 'v': #datos de tension 
    print "nodo,tension,fecha,hora"
#leo byte x byte
while byte != EOF and len(byte) != 0:
    byte = fd.read(1)
    if ESTADO == "waiting":
        if byte == SOF :
            ESTADO = "length"
    elif ESTADO == "length":
        largo = ord(byte)
        #print largo
        if largo == 0:
            comandos(KEEP_ALI,'', salida)
            # volvemos a leer de a 1 byte ......
            ESTADO = "waiting"
        else:
            ESTADO = "data"
    elif ESTADO == "data":
        datos = byte + fd.read(largo - 2 )
        if datos[0] == DATA_IND : # hasta que arregle el server
            datos = escape(datos) # saca los escapes :-)
        registro = comandos(datos[0], datos[1:],salida) # mando el comando y los datos restantes 
        if registro != None :
            print registro
        if DEBUG == True :
            print [hex(ord(x)) for x in datos]

        # volvemos a leer de a 1 byte ......
        ESTADO = "waiting"

if DEBUG == True:
    print "final"
fd.close()
