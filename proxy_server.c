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
#include <pthread.h>


#define MAX_SIZE 4096
int clientefd, connfd;	/* descriptores */
int ipc[2];

void *lee_server(void *unused) {
	char buf[MAX_SIZE];			/* Buffer para la lectura */
	int nread;				/* para leer en el socket */
	
	/* voy leyendo TOOOOOOODO lo que me llega del server*/	
	while ((nread=read(clientefd, buf, MAX_SIZE))>0) {
		/* lo reenvio al gateway  */
		write(connfd, buf, nread);
		/* Envia al pipe de log */
		//write(ipc[1], "<", 1); /* agrego un indicador de sentido */
		write(ipc[1], buf ,nread); 
	}
	exit(0);
	//close(ipc[1]);
	//close (clientefd);
	//close (connfd);
	//pthread_exit(NULL);
}


int main(int argc, const char *argv[]) {
	int sockfd,fdlog;			/* descriptores */
	struct sockaddr_in addr_escucha;	/* donde voy a escuchar */
	struct sockaddr_in addr_remoto;		/* el que se conecta */
	struct sockaddr_in addr_reenvio;	/* donde voy a reenviar */
	socklen_t addr_len;			/* longitud de addr_escucha */
	int opt, nread;				/* para setsockopt */
	pid_t hijo; 				/* pid del hijo */
	char buf[MAX_SIZE];			/* Buffer para la lectura */
	unsigned short port_escucha, port_reenvio;
	time_t current_time;
	
	/* Verifico el nro de argumentos */
	if (argc != 6) {
		fprintf(stderr, "Uso: %s <ip_escucha> <puerto_escucha> <ip_reenvio> <puerto_reenvio> <archivo_log>\n",
				argv[0]);
		return 1;
	}
 	/* Crea el socket de escucha */	
	if ((sockfd = socket(PF_INET, SOCK_STREAM, 0))<0) {
		perror("socket"); return 1;		
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
		return -1;
	}
	addr_escucha.sin_port = htons(port_escucha);
		
	/* Liga el socket a una direccion */
	addr_len = sizeof(addr_escucha);
	if ( (bind(sockfd, (struct sockaddr *)&addr_escucha, addr_len)) < 0 ) {
		perror("bind"); return -1;		
	}
	
	/* Aguarda a q arriben conexiones */
	if ( (listen(sockfd, 5)) < 0 ) {
		perror("listen"); return -1;
	}


	/* no me interesa el exit_value de mis hijos (evito zombies) */
	signal(SIGCHLD, SIG_IGN);

	printf("\nSOCKET  ESCUCHANDO ...\n");
	printf("\tPuerto: %d\n", ntohs(addr_escucha.sin_port));
	printf("\tDireccion IP: %s\n", inet_ntoa(addr_escucha.sin_addr));
	
	/* Ejecuta indefinidamente la aceptacion de conexiones */
	while ((connfd = accept(sockfd, (struct sockaddr *)&addr_remoto, &addr_len))>=0) {
		// Uso pipes para sincronizar 
		if (pipe(ipc) < 0) {
			perror("pipe");return -1;
		}

		/* hijo lee del pipe para asegurar atomicidad en la escritura del archivo */
		if (( hijo=fork()) == 0 ) {
			close(sockfd); /* hijo cierra el socket de LISTEN */
			close(connfd); /* hijo cierra el socket CONECTADO */
			close(ipc[1]); // no escribira nada en el pipe
			char trama[7] ; //creo un nuevo tipo de trama con el timestamp del proxy 

			/* Abre el archivo de log */
			if ((fdlog = open(argv[5], O_RDWR| O_APPEND|O_CREAT , 0660)) < 0 ) {
				perror("open"); return -1;		
			}
			//comienzo de la trama ... no cambia nunca
			trama[0] = 0x7e; // start of frame
			trama[1] = 0x06; // length ...10 bytes
			trama[2] = 0xaa; // comando aa

			// Me quedo esperando que alguien mande los datos al pipe
			while ((nread=read(ipc[0], buf, MAX_SIZE))>0) {
				 /* Obtener current time. */
				current_time = time(NULL);
				if (current_time == ((time_t)-1)) {
					perror ("time"); return -1;
				}
				//reordeno big endian ......	
				trama[3] = (uint8_t)(current_time >> 24);
				trama[4] = (uint8_t)(current_time >> 16);
				trama[5] = (uint8_t)(current_time >> 8);
				trama[6] = (uint8_t)current_time;
				//write(fdlog, "\n", 1); //arego un enter ... para ver mejor     
				write(fdlog, trama, (sizeof (trama) - 1)); /* agrego un enter.... y hora */
				/* lo guardo en el archivo de log */
				write(fdlog, buf, nread);     
				
			}
			close(ipc[0]);
			close (fdlog); // cierro el archivo de log, una vez que cierren las escrituras en los pipes 
			return 0;
		} // termina el hijo que lee del pipe ....

		// cierro las lecturas en los hijos que escriben en el pipe
		close(ipc[0]);
		// crea hijo para conectarse al server y proxear ....	
		if (( hijo=fork()) == 0 ) {
			close(sockfd); /* hijo cierra el socket de LISTEN */
			/* Crea el socket de cliente */	
			if ((clientefd = socket(PF_INET, SOCK_STREAM, 0))<0) {
				perror("socket remoto"); return 1;		
			}
			addr_reenvio.sin_family = AF_INET;
			/* IP remoto */
			if ( !(inet_aton(argv[3], &addr_reenvio.sin_addr))) {
				perror("inet_aton"); return -1;
			}
			port_reenvio = atoi(argv[4]);
			addr_reenvio.sin_port = htons(port_reenvio);
			
			/* Conecta al peer remoto */
			if (connect(clientefd, (struct sockaddr *)&addr_reenvio, sizeof(addr_reenvio))) {
				perror("connect"); return -1;
			}
			pthread_t hilo; 
			int rc;
			/* Creo otro hilo, uno para que lea en cada lado del proxy */
			rc = pthread_create(&hilo, NULL, lee_server , NULL );
			if (rc){
				printf("ERROR; pthread_create() = %d\n", rc);
				exit(-1);
                               }

			/* voy leyendo TOOOOOOODO lo que me llega del gateway*/	
			while ((nread=read(connfd, buf, MAX_SIZE))>0) {
				/* lo reenvio al server de verdad ¿? */
				write(clientefd, buf, nread);
				/* Envia al pipe de log */
			//	write(ipc[1], ">", 1); /* agrego un indicador de comienzo de sentido */
				write(ipc[1], buf, nread);
			}
			close(ipc[1]);
			close (clientefd);
			close (connfd);
			return 0;
		} // termina el hijo + el hilo que hace el proxeo	

		// codigo del padre	
		// no usa el pipe, ni el socket conectado
		close(ipc[1]);
		close(connfd);
		printf("\nNueva conexion pid=%i IP remoto=%s, PORT remoto=%d\n", 
				hijo,
				inet_ntoa(addr_remoto.sin_addr),
				ntohs(addr_remoto.sin_port));
	} // vuelve al accept de nuevos clientes
	close(sockfd);
	return EXIT_SUCCESS;
}
