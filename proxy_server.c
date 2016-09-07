#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <signal.h>
#include <time.h>


#define MAX_SIZE 4096

int main(int argc, const char *argv[]) {
	int sockfd, connfd, fdlog, clientefd;	/* descriptores */
	struct sockaddr_in addr_escucha;	/* donde voy a escuchar */
	struct sockaddr_in addr_remoto;		/* el que se conecta */
	struct sockaddr_in addr_reenvio;	/* donde voy a reenviar */
	socklen_t addr_len;			/* longitud de addr_escucha */
	int opt, nread;				/* para setsockopt */
	pid_t hijo; 				/* pid del hijo */
	char buf[MAX_SIZE];			/* Buffer para la lectura */
	unsigned short port_escucha, port_reenvio;
	time_t current_time;
	char hora_actual[11];
	
	/* Verifico el nro de argumentos */
	if (argc != 6) {
		fprintf(stderr, "Uso: %s <ip_escucha> <puerto_escucha> <ip_reenvio> <puerto_reenvio> <archivo_log>\n",
				argv[0]);
		return 1;
	}
 	/* Crea el socket de escucha */	
	if ((sockfd = socket(PF_INET, SOCK_STREAM, 0))<0) {
		perror("socket");
		return 1;		
	}

	/* Se desea reutilizar la direccion local */
	opt=1;
	setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof opt);

	/* Inicializa y configura la estructura de socket del servidor */ 
	inet_pton(AF_INET,argv[1], &addr_escucha.sin_addr);
	
	addr_escucha.sin_family = AF_INET;

	port_escucha = atoi(argv[2]);
	if (port_escucha <=0) {
		fprintf(stderr, "port=%d invalido\n", port_escucha);
		return 255;
	}
	addr_escucha.sin_port = htons(port_escucha);
		
	/* Liga el socket a una direccion */
	addr_len = sizeof(addr_escucha);
	if ( (bind(sockfd, (struct sockaddr *)&addr_escucha, addr_len)) < 0 ) {
		perror("bind");
		return 2;		
	}
	
	/* Aguarda a q arriben conexiones */
	if ( (listen(sockfd, 5)) < 0 ) {
		perror("listen");
		return 3;
	}


	/* no me interesa el exit_value de mis hijos (evito zombies) */
	signal(SIGCHLD, SIG_IGN);

	printf("\nSOCKET  ESCUCHANDO ...\n");
	printf("\tPuerto: %d\n", ntohs(addr_escucha.sin_port));
	printf("\tDireccion IP: %s\n", inet_ntoa(addr_escucha.sin_addr));
	
	/* Ejecuta indefinidamente la aceptacion de conexiones */
	while ((connfd = accept(sockfd, (struct sockaddr *)&addr_remoto, &addr_len))>=0) {
		
		switch(hijo=fork()) {
		case -1: /* Hubo un problema con la creacion del hijo */ 
			break;
		case 0: /* Codigo del hijo, futuros ZOMBIES ... */

			close(sockfd); /* hijo cierra el socket de LISTEN */
			/* no me interesa el exit_value de mis hijos (evito zombies) */
			signal(SIGCHLD, SIG_IGN);
			/* Crea el socket de cliente */	
			if ((clientefd = socket(PF_INET, SOCK_STREAM, 0))<0) {
				perror("socket remoto");
				return 1;		
			}
			addr_reenvio.sin_family = AF_INET;
			/* IP remoto */
			if ( !(inet_aton(argv[3], &addr_reenvio.sin_addr))) {
				perror("inet_aton");
				return 255;
			}
			port_reenvio = atoi(argv[4]);
			addr_reenvio.sin_port = htons(port_reenvio);
			
			/* Conecta al peer remoto */
			if (connect(clientefd, (struct sockaddr *)&addr_reenvio, sizeof(addr_reenvio))) {
				perror("connect");
				return 4;
			}
			/* otro hijo lee del server y lo reenvía al gateway */
			if (( hijo=fork()) == 0 ) {
			/* voy leyendo TOOOOOOODO lo que me llega del server*/	
			while ((nread=read(clientefd, buf, MAX_SIZE))>0) {
				/* lo reenvio al gateway  */
				write(connfd, buf, nread);
				/* Abre el archivo de log */
				/* mmmmmmmmmmm feo, feo .... abro y cierro el archivo cada vez que llegan datos
 				 ... pero es para arreglar problemas de concurrencia de los dos procesos */
				if ((fdlog = open(argv[5], O_RDWR| O_APPEND|O_CREAT , 0660)) < 0 ) {
					perror("open");
					return 1;		
				}
		   		 /* Obtener current time. */
				current_time = time(NULL);
    				if (current_time == ((time_t)-1)) {
					perror ("time");
					return -1;
    				}
   				snprintf(hora_actual, 11, "%ld", current_time);
				write(fdlog, "\n<", 2); /* agrego un indicador de comienzo de trama ... y sentido */
				write(fdlog, hora_actual, sizeof hora_actual); /* agrego un indicador de comienzo de trama ... y sentido .... y hora */
				/*	lo guardo en el archivo de log */
				write(fdlog, buf, nread);     
				close (fdlog);
				}
				return 0;
			}
			/* voy leyendo TOOOOOOODO lo que me llega del gateway*/	
			while ((nread=read(connfd, buf, MAX_SIZE))>0) {
				/* lo reenvio al server de verdad ¿? */
				write(clientefd, buf, nread);
				/* Abre el archivo de log */
				/* mmmmmmmmmmm feo, feo .... abro y cierro el archivo cada vez que llegan datos
 * 				 ... pero es para arreglar problemas de concurrencia de los dos procesos */
				if ((fdlog = open(argv[5], O_RDWR| O_APPEND|O_CREAT , 0660)) < 0 ) {
					perror("open");
					return 1;		
				}
		   		 /* Obtener current time. */
				current_time = time(NULL);
    				if (current_time == ((time_t)-1)) {
					perror ("time");
					return -1;
    				}
   				snprintf(hora_actual, 11, "%ld", current_time);
				write(fdlog, "\n>", 2); /* agrego un indicador de comienzo de trama ... y sentido */
				write(fdlog, hora_actual, sizeof hora_actual); /* agrego un indicador de comienzo de trama ... y sentido .... y hora */
				/*	lo guardo en el archivo de log */
				write(fdlog, buf, nread);
				close (fdlog);
			}
			close (clientefd);
			return 0;
			break;
			
		default: /* Codigo del padre */			
			close(connfd);
			printf("\nNueva conexion pid=%i IP remoto=%s, PORT remoto=%d\n", 
					hijo,
					inet_ntoa(addr_remoto.sin_addr),
					ntohs(addr_remoto.sin_port));
			break;
		}
	}
	close(sockfd);
	return EXIT_SUCCESS;
}
