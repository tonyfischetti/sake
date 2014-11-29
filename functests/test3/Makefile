

CC=gcc
# CFLAGS used for development
# CFLAGS=-Wall -Wextra -Werror -Wwrite-strings -Wundef -Wmissing-noreturn -Wstrict-prototypes -std=c89 -pedantic -O2 -I../include
CFLAGS=-Wall -O2 -I./include
LDFLAGS=-lm
DEPS = statfuncs.h infuncs.h graphfuncs.h qstats.h

all: qstats

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS) $(LDFLAGS)

qstats: qstats.o statfuncs.o infuncs.o graphfuncs.o
	$(CC) -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o $(CFLAGS) $(LDFLAGS)

clean:
	rm -f ./*.o
	rm -f qstats
