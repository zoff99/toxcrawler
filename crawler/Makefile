LIBS = libtoxcore
CFLAGS = -std=gnu99 -O3 -fPIC -Wall -ggdb $(shell pkg-config --cflags $(LIBS)) -fstack-protector-all -pthread
OBJ = main.o util.o
LDFLAGS = -fPIC $(shell pkg-config --libs $(LIBS)) $(shell pkg-config --libs libsodium)
SRC_DIR = ./src

all: $(OBJ)
	@echo "  LD    $@"
	@$(CC) $(CFLAGS) -o crawler $(OBJ) $(LDFLAGS)

%.o: $(SRC_DIR)/%.c
	@echo "  CC    $@"
	@$(CC) $(CFLAGS) -o $*.o -c $(SRC_DIR)/$*.c
	@$(CC) -MM $(CFLAGS) $(SRC_DIR)/$*.c > $*.d

clean:
	rm -f *.d *.o crawler

.PHONY: clean all
