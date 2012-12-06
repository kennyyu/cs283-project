CPPC = g++
CPPFLAGS = `pkg-config --cflags opencv` -ggdb -std=c++0x
CPPLIBS = `pkg-config --libs opencv`

all: detect optical_flow

objectDetection.o: objectDetection.cpp
	$(CPPC) $(CPPFLAGS) $^ -c -o $@

detect: objectDetection.o
	$(CPPC) $(CPPFLAGS) $^ -o $@ $(CPPLIBS)

optical_flow.o: optical_flow.cpp
	$(CPPC) $(CPPFLAGS) $^ -c -o $@

optical_flow: optical_flow.o
	$(CPPC) $(CPPFLAGS) $^ -o $@ $(CPPLIBS)

clean:
	rm *.o detect optical_flow
