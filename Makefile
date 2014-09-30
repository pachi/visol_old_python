# Makefile para la gestión del proyecto ViSol: Visor de archivos de LIDER
# Rafael Villar Burke, 2014

EXEBASE ?= /e/winp2
PYTHON = python

# Escapamos / con \/ para sed y \ con \\ para make
UPXPATH='E:\\/winp2\\/UPX\\/upx.exe'
DISTDIR='build\\/exe.mingw-2.7'

VERSION=$(shell python -c"from sol import __version__;print __version__")
MAKENSIS:=$(EXEBASE)/NSIS/makensis

PAGEANT:=$(EXEBASE)/PuTTY/pageant.exe
KEYFILE:=$(EXEBASE)/PuTTY/keys/pachi-key-putty.PPK

PYRSTEXISTS:=$(findstring .py, $(shell which rst2html.py))
ifeq ($(PYRSTEXISTS), .py)
$(info Encontrado rst2html.py)
RST2HTML=rst2html.py
else
$(info Encontrado rst2html)
RST2HTML=rst2html
endif

#make windows installer by default

winbuild: py2exe nsiinstaller

py2exe: setup_exe.py
	$(PYTHON) setup_exe.py py2exe
	sleep 5s

nsiinstaller: README.html setup.nsi splash
	$(MAKENSIS) setup.nsi

build: setup.py splash
	$(PYTHON) setup.py build

install: setup.py
	$(PYTHON) setup.py install

README.html: README.rst res/style.css
	$(RST2HTML) --stylesheet=res/style.css README.rst > $@

setup.nsi: setup.nsi.in
	sed 's/@VERSION@/$(VERSION)/g; s/@UPXPATH@/$(UPXPATH)/g; s/@DISTDIR@/$(DISTDIR)/g' setup.nsi.in > setup.nsi

splash:
	$(PYTHON) ./res/makesplash.py -b ./res/background.png -o ./res/splash.jpg $(VERSION)
	cp ./res/splash.jpg ./ui/splash.jpg

test check tests:
	unit2 discover

testall:
#	python2.5 setup_exe.py test
	python2.7 setup_exe.py test
#	python3.1 setup_exe.py test
#	make checkdocs

#docs:
#	$(MAKE) -C docs html

clean:
	rm -rf build dist MANIFEST setup.nsi README.html res/splash.jpg ui/splash.jpg
	find . -name *.pyc -exec rm {} \;
	find . -name *.swp -exec rm {} \;
#	$(PYTHON) setup.py clean

# push changes to hg
push:
	$(PAGEANT) $(KEYFILE) &
	hg push ssh://hg@bitbucket.org/pachi/visol/

# commit to hg
commit:
	hg commit

#upload to pypi
upload:
	make clean
	$(PYTHON) setup.py sdist upload --sign --identity="Rafael Villar Burke <pachid@rvburke.com>"

sdist: splash
	make clean
#	make testall
	$(PYTHON) setup.py sdist

checkdocs:
	$(PYTHON) setup.py checkdocs -setuptools

showdocs:
	$(PYTHON) setup.py showdocs -setuptools

coverage:
	coverage run run_tests.py
	coverage report -m

profile:
# http://blog.brianbeck.com/post/22199891/the-state-of-python-profilers-in-two-words
# http://www.doughellmann.com/PyMOTW/profile/
	$(PYTHON) -m cProfile bin/visol > profile.stats
	echo "Profiling data saved in profile.stats"

# Los phony son los que hay que considerar siempre no actualizados (rebuild)
.PHONY = winbuild build sdist clean testall test check tests
