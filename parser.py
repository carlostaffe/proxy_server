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
STATUS_IND ='\x05' 
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
      "G" : 1.0152 , "K" : 1.0109 , "L" : 1.0043 , "O" : 1.0160,
      "d" : 1.0084 , "f" : 1.0182 , "k" : 1.0053 , "q" : 1.0016, 
      "g" : 1.0285 , "h" : 1.0051 , "i" : 1.0061 , "j" : 1.0209, 
      "l" : 1.0091 , "m" : 1.0204 , "o" : 1.0178 , "p" : 1.0256, 
      "r" : 1.0129 , "s" : 1.0191 , "t" : 1.0055 , "u" : 1.0245, 
      "x" : 1.0098 , "H" : 1.0239 , "Y" : 1.0120 , "Z" : 1.0172}
K2 = {"a" :-0.3493 , "b" :-0.8110 , "U" : 0.0110 , "V" : 0.5783,
      "G" :-0.4679 , "K" :-0.7132 , "L" :-0.6028 , "O" :-0.1544,
      "d" :-0.8952 , "f" :-0.5356 , "k" :-0.2316 , "q" : 0.4382, 
      "g" : 0.1082 , "h" :-0.6018 , "i" : 0.9133 , "j" : 0.8511, 
      "l" :-0.5771 , "m" : 0.3928 , "o" :-0.3676 , "p" :-0.5513, 
      "r" : 0.0670 , "s" :-0.4663 , "t" :-0.0928 , "u" :-0.3644, 
      "x" : 0.2324 , "H" : 0.6421 , "Y" :-0.3274 , "Z" : 0.0523}

#http://proyectos.gridtics.frm.utn.edu.ar/projects/livres-dog/wiki/Nueva_calibraci%C3%B3n_Modelo_B2
#Temp[C]=[(2,5*CRUDO/16383-0,5)*100]*K1+K2

##################### funciones #################################
def escape (datos):
    'Busca bytes escapados en la data'
    escape = datos.find(ESC)
    while (escape  > 0 ):
        #cuando aparece 0x7D en la trama, se elimina y al caracter siguiente se le vuelve a hacer una XOR con 0x20
        datos = datos[:escape] + chr( ord(datos[escape+1]) ^ ord(XOR)) + datos[escape+2:]
        escape = datos.find(ESC,escape+1)
    return datos

def lectura_fecha(datos):
    'algoritmo de impresion de fecha'
    # reagrupo los 4 bytes
    timestamp = ord(datos[0]) * 16777216 + ord(datos[1]) * 65536 + ord(datos[2]) * 256 + ord(datos[3])
    return  (datetime.datetime.fromtimestamp(timestamp))

def calibracion(sonda,temp):
    'se calcula con la siguiente formula Temp[c] = [(2,5*CRUDO/16383-0,5)*100]*K1+K2 '
    return (((2.5 * ((ord(temp[0]) * 256) + ord (temp[1])) / 16383 - 0.5)* 100 ) * K1[sonda]) + K2[sonda]

#################################################################

def comandos (comando , datos):
    'parseo de los distintos comandos'
    if comando == DATA_IND:
        if DEBUG == True:
            print "data indication"
#        print  ord(datos[1]) , ',' , # el nro de mote
        i = 0
        while i < ord (datos[3]):
            registro = datos[4+3*i] + ',' 
            temp = calibracion(datos[4+3*i], datos[5+3*i:7+3*i])
            fecha =  lectura_fecha(datos[-5:-1]) 
            registro = registro + fecha.strftime('%d-%m-%Y') + ','  
            registro = registro + fecha.strftime('%H:%M:%S') +  ',' 
            registro = registro + str (temp)
            print registro 
            i = i + 1
#           print ord(datos[-1:])	# valor de LQI

    elif comando == STATUS_IND:
        if DEBUG == True:
            print "status indicaalive"
        
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
#etiqueta
print "etiqueta,fecha,hora,temperatura"
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
