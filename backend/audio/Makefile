# Compiler
CC = gcc

# Compiler flags
CFLAGS = -Wall -fPIC

# The target shared library file
TARGET = audiolib.so

# Source files
SRC = audio.c

# Libraries
LIBS := -lasound

# Rule to build the shared library (.so file)
$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -shared -o $(TARGET) $(SRC) $(LIBS)

# Clean rule to remove generated files
clean:
	rm -f $(TARGET)