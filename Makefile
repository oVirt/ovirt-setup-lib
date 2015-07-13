
.PHONY: build dist install
all: build

build:
	python setup.py build

clean:
	python setup.py clean

dist:
	python setup.py sdist --dist-dir .


install: build
	python setup.py install -O1 --root="$(DESTDIR)" --record=INSTALLED_FILES
