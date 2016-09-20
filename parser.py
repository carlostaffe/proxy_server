#!/usr/bin/python
import datetime
import time
#                          char<>DLE and char<>ETX
#     _______________________________
#    |    largo = 0 \                \
# ___|__           _|___          ___|__
#/waiting\------->/length\------->/data \
#\______/<-\      \______/     /->\___ _/
#     |     |                |     |   
#     \____/                  \___/        
#     char<>SOF             char<>ESC

# algunas secuencias de escape
SOF = '\x7e'
ESC = '\x7d'
EOF = '\x0a'
XOR = '\x20'
#Comandos
DATA_IND ='\x03' 
COMM_IND ='\x06' 
KEEP_ALI ='\x00' 
TIME_PRX ='\xaa' 
#Algunas configs iniciales
#DEBUG = True
DEBUG = False
ESTADO = "waiting"
datos = ''
byte = '0'
#tabla de calibracion de motes
# http://proyectos.gridtics.frm.utn.edu.ar/projects/livres-dog/wiki/Planilla_de_direcciones
K1 = {"a" : 1.0042 , "b" : 1.0215 , "U" : 1.0184 , "V" : 1.0301,
      "G" : 1.0152 , "K" : 1.0109 , "L" : 1.0043 , "O" : 1.0160 }
K2 = {"a" :-0.3493 , "b" :-0.8110 , "U" : 0.0110 , "V" : 0.5783,
      "G" :-0.4679 , "K" :-0.7132 , "L" :-0.6028 , "O" :-0.1544 }

#http://proyectos.gridtics.frm.utn.edu.ar/projects/livres-dog/wiki/Nueva_calibraci%C3%B3n_Modelo_B2
#Temp[C]=[(2,5*CRUDO/16383-0,5)*100]*K1+K2

##################### funciones #################################
def escape (datos):
    'Busca bytes escapados en la data'
    escape = datos.find(ESC)
    while (escape  > 0 ):
        #cuando aparece 0x7D en la trama, se elimina y al caracter siguiente se le vuelve a hacer una XOR con 0x20
        datos = datos[:escape] + chr( ord(datos[escape+1]) ^ ord(XOR)) + datos[escape+2:]
        escape = datos.find(ESC)
    return datos

def lectura_fecha(datos):
    'algoritmo de impresion de fecha'
    # reagrupo los 4 bytes
    timestamp = ord(datos[0]) * 16777216 + ord(datos[1]) * 65536 + ord(datos[2]) * 256 + ord(datos[3])
    fecha = (datetime.datetime.fromtimestamp(timestamp))
    return fecha

def calibracion(sonda,temp):
    'se calcula con la siguiente formula Temp[c] = [(2,5*CRUDO/16383-0,5)*100]*K1+K2 '
    grados = (((2.5 * ((ord(temp[0]) * 256) + ord (temp[1])) / 16383 - 0.5)* 100 ) * K1[sonda]) + K2[sonda]
    return grados

def comandos (comando , datos):
    'parseo de los distintos comandos'
    registro = ''
    if comando == DATA_IND:
        if DEBUG == True:
            print "data indication"
        print  ord(datos[1]) , ',' ,
        # para ordenar las columnas 
        if ord(datos[1]) == 2:
            print "," , "," , "," , "," , "," , "," , "," , "," , 
        i = 0
        while i < ord (datos[3]):
            print datos[4+3*i],  ',' ,
            temp = calibracion(datos[4+3*i], datos[5+3*i:7+3*i])
            print temp , ',' ,
            i = i + 1
        # para ordenar las columnas 
        if ord(datos[1]) == 1:
            print "," , "," , "," , "," , "," , "," , "," , "," , 
        fecha  = lectura_fecha(datos[-5:-1]) #el ultimo es lqi .. el timestamp los 4 anteriores al ultimo
        print fecha , "," ,
	print ord(datos[-1:])	# valor de LQI
        
    elif comando == KEEP_ALI:
        if DEBUG == True:
            print "keep alive"
    elif comando == TIME_PRX:
        if DEBUG == True:
            print "timestamp proxy"
    elif comando == COMM_IND:
        if DEBUG == True:
            print "command indication"
    return



fd = open("proxy_server.log","r")

#leo byte x byte
while byte != EOF:
    byte = fd.read(1)
    if ESTADO == "waiting":
        if byte == SOF :
            ESTADO = "length"
    elif ESTADO == "length":
        largo = ord(byte)
#        print largo
        if largo == 0:
            comandos(KEEP_ALI,'')
            # volvemos a leer de a 1 byte ......
            ESTADO = "waiting"
        else:
            ESTADO = "data"
    elif ESTADO == "data":
        datos = byte + fd.read(largo - 2 )
        if datos[0] == DATA_IND : # hasta que arregle el server
            datos = escape(datos) # saca los escapes :-)
        comandos(datos[0], datos[1:]) # mando el comando y los datos restantes 
        if DEBUG == True :
            print [hex(ord(x)) for x in datos]

        # volvemos a leer de a 1 byte ......
        ESTADO = "waiting"

if DEBUG == True:
    print "final"
fd.close()
