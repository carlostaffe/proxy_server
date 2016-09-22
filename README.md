
instalacion:

make clean
make 

cp proxy_server /usr/sbin

copia de script arranque/parada etc/init.d/proxy_server  al /etc/init.d/

modificarcion de ips/puertos en ese archivo ... 
DAEMON_ARGS="0.0.0.0 19999 127.0.0.1 18888 /var/log/proxy_server/proxy_server.log"

crear el directorio /var/log/proxy_server

ponerlo como servicio
update-rc.d proxy_server defaults 20 5


cuando quiera obtener los archivos .csv, ejecutar 

./parser > archivo.csv

Para logrotate, copiar el archivo etc/logrotate.d/proxy_server al /etc/logrotate.d

Si quiero que me mande mails diariamente con el archivo server.log,
copiar el archivo etc/cron.d/proxy_server al /etc/cron.d/

listo !
