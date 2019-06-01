.PHONY: all test clean

all:
	sudo pip3 install -e .

test:
	curseradio-improved

clean:
	sudo rm -rf curseradio_improved.egg-info build/ dist/ $(shell which curseradio-improved)
