#!/usr/bin/python

#                          char<>DLE and char<>ETX
#     _______________________________
#    |    largo = 0 \                \
# ___|__           _|___          ___|__
#/espera\------->/largo \------->/datos \
#\______/<-\     \______/     /->\____ _/
#     |     |                |     |   
#     \____/                  \___/        
#     char<>SOF             char<>ESC

# algunas secuencias de escape
SOF = '0x7e'
ESC = '0x03'
EOF = '0xa'
ESTADO = "espera"
datos = ''
byte = '0'
fd = open("/tmp/proxy_server.log","r")

#leo byte x byte
while byte != '':
    byte = ord(fd.read(1))
    if ESTADO == "espera":
        if hex(byte) == SOF :
            ESTADO = "largo"
        if hex(byte) == EOF:
            break
    elif ESTADO == "largo":
        largo = byte
        if largo == 0:
            ESTADO = "espera"
            print "ACK"
        else:
            ESTADO = "datos"
    elif ESTADO == "datos":
        datos = fd.read(largo - 2 )
        print datos
       # ESTADO = "check"
        ESTADO = "espera"

#    elif ESTADO == "check":
#        print "calculo checksum "
#        
#        ESTADO = "espera"
#
#
#    elif ESTADO == "datos":
#        if byte == ESC :
#            ESTADO == "escape"
#        elif  
#        
#
print "final"
fd.close()
