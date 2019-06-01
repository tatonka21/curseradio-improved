# Install `curseradio-improved' locally.
.PHONY: all test update_pypi clean

all:
	flake8 curseradio_improved/curseradio_improved.py
	sudo pip3 install -e .
	sudo python3 setup.py sdist bdist_wheel

test:
	curseradio-improved

# update the installed pypi distribution
update_pypi:
	sudo pip3 install --upgrade curseradio-improved

clean:
	sudo rm -rf curseradio_improved.egg-info build/ dist/ $(shell which curseradio-improved)
