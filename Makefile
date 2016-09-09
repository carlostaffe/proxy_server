CFLAGS=-g -Wall $(COPTS)
TARGETS=proxy_server
LDLIBS=-lpthread

all: $(TARGETS) 

clean:  
	rm -f *.o *~ $(TARGETS) $(LIBS) core
