instalacion:

make clean
make 

cp proxy_server /usr/sbin

copia de script arranque/parada etc/init.d/proxy_server  al /etc/init.d/

modificarcion de ips/puertos en ese archivo. La linea de DAEMON_ARGS , por ejemplo
DAEMON_ARGS="0.0.0.0 19999 127.0.0.1 18888 /var/log/proxy_server/proxy_server.log ip_graficador puerto_graficador"

crear el directorio /var/log/proxy_server

ponerlo como servicio con update-rc.d proxy_server defaults 20 5

cuando quiera obtener los archivos .csv, ejecutar 

./parser -d t|v -i archivo.log > archivo.csv

Para logrotate, copiar el archivo etc/logrotate.d/proxy_server al /etc/logrotate.d

en la configuracion, antes de hacer el logrotate, genera los archivos .cvs de tension y 
temperatura y los envia por correo

Si quiero que me mande mails diariamente con el archivo server.log,
copiar el archivo etc/cron.d/proxy_server al /etc/cron.d/

en el graficador, instalar apache, mrtg y copiar la configuracion desde /etc/mtrg.conf
tambien copiar protocolo.py y server_grafica.py

listo !

