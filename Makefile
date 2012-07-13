# debian packages:
# libboost-dbg libboost-all-dev python2.7-dev
# libstdc++-dev (?)
#


all:

UNAME = $(shell uname)
PYTHON ?= python2.7
CXX ?= g++

CXXFLAGS += -I/usr/include/python2.7
LDFLAGS += -lstdc++
LDFLAGS += -lpython2.7

ifeq ($(UNAME), Darwin)
CXXFLAGS += -I/usr/local/include
LDFLAGS += -L/usr/local/lib
LDFLAGS += -lboost_python-mt
endif
ifeq ($(UNAME), Linux)
LDFLAGS += -lboost_python-mt-py27
endif

%.o: %.cc
	$(CXX) $(CXXFLAGS) -c -o $@ $+

%.so: %.o
	$(CXX) -shared -o $@ $+ $(LDFLAGS)

all: hello_ext.o hello_ext.so

clean:
	rm -rf hello_ext.o hello_ext.so

test: hello_ext.so
	$(PYTHON) -c 'import hello_ext; print hello_ext.greet(); print hello_ext.Hello().hi()'

