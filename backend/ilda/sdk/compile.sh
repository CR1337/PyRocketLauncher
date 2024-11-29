#!/bin/sh

cp /usr/lib/arm-linux-gnueabihf/libusb-1.0.so ./build/libusb-1.0.so

g++ -Wall -std=c++14 -fPIC -O2 -c -o build/HeliosDacAPI.o shared_library/HeliosDacAPI.cpp
g++ -Wall -std=c++14 -fPIC -O2 -c -o build/HeliosDac.o HeliosDac.cpp
g++ -Wall -std=c++14 -fPIC -O2 -c -o build/idn.o idn/idn.cpp
g++ -Wall -std=c++14 -fPIC -O2 -c -o build/idnServerList.o idn/idnServerList.cpp
g++ -Wall -std=c++14 -fPIC -O2 -c -o build/plt-posix.o idn/plt-posix.c

g++ -shared -o build/libHeliosDacAPI_arm.so build/HeliosDacAPI.o build/HeliosDac.o build/plt-posix.o build/idn.o build/idnServerList.o build/libusb-1.0.so

cp ./build/libHeliosDacAPI_arm.so ../libHeliosDacAPI_arm.so
