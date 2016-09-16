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
SOF = '\x7e'
ESC = '\x03'
EOF = '\x0a'
ESTADO = "espera"
datos = ''
byte = '0'
fd = open("test_bed.log","r")

#leo byte x byte
while byte != '':
    byte = fd.read(1)
    if ESTADO == "espera":
        if byte == SOF :
            ESTADO = "largo"
        if byte == EOF:
            break
    elif ESTADO == "largo":
        largo = ord(byte)
        if largo == 0:
            ESTADO = "espera"
            print "KEEP ALIVE"
        else:
	    print largo
            ESTADO = "datos"
    elif ESTADO == "datos":
        datos = byte + fd.read(largo - 2 )
	print [hex(ord(x)) for x in datos]
        ESTADO = "espera"

#
#    elif ESTADO == "datos":
#        if byte == ESC :
#            ESTADO == "escape"
#        elif  
#        
#

######### impresion de la hora 
#python -c "import datetime; print(datetime.datetime.fromtimestamp(0x57d9d79c))"


print "final"
fd.close()
