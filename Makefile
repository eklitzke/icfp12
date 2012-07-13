all:

CXXFLAGS += -I/usr/local/include
CXXFLAGS += -I/usr/include/python2.7
LDFLAGS += -dylib
LDFLAGS += -L/usr/local/lib
LDFLAGS += -lstdc++
LDFLAGS += -lboost_python-mt
LDFLAGS += -lboost_iostreams-mt
LDFLAGS += -lpython2.7
LDFLAGS += -lc
PYTHON ?= python2.7

CXX ?= g++

%.o: %.cc
	$(CXX) $(CXXFLAGS) -c -o $@ $+

%.so: %.o
	$(LD) $(LDFLAGS) -o $@ $+

all: hello_ext.o hello_ext.so

clean:
	rm -rf hello_ext.o hello_ext.so

test: hello_ext.so
	$(PYTHON) -c 'import hello_ext; print hello_ext.greet()'

