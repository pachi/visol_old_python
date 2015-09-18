# Makefile para la gestión del proyecto ViSol: Visor de archivos de LIDER
# Rafael Villar Burke, 2014

# Para la generación del instalador para Win32 es necesaria la instalación de:
# - NSIS installer (makensis)
# - Plugin NewAdvSplash de NSIS
# - Compresor UPX
# - Docutils (para rst2html)
# La creación del instalador para Win32 se puede hacer en Windows o Linux
# La versión para win32 se hace con MSYS2

PYTHON = python

# Not used yet. Ideas from gedit's installer
_thisdir="$(dirname $0)"
_arch=$(uname -m)
_date=$(date +'%Y%m%d')
_version=@VERSION@
_filename=visol-${_arch}-${_version}.exe

if [ "${_arch}" = "x86_64" ]; then
  _bitness=64
else
  _bitness=32
fi
#

VERSION=$(shell python -c"from sol import __version__;print __version__")
UPXPATH?=$(subst /,\/,$(shell which upx))
DISTDIR?=$(subst /,\/,build/exe.mingw-2.7)
MAKENSIS?=$(shell which makensis)

PYRSTEXISTS:=$(findstring .py, $(shell which rst2html.py))
ifeq ($(PYRSTEXISTS), .py)
$(info Encontrado rst2html.py)
RST2HTML=rst2html.py
else
$(info Encontrado rst2html)
RST2HTML=rst2html
endif

#make windows installer by default

winbuild: freeze installer

freeze: setup_exe.py
	$(PYTHON) setup_exe.py build
	sleep 5s

installer: README.html setup.nsi splash
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
EXEBASE ?= /e/winp2
PAGEANT:=$(EXEBASE)/PuTTY/pageant.exe
KEYFILE:=$(EXEBASE)/PuTTY/keys/pachi-key-putty.PPK
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
.PHONY = setup.nsi winbuild build sdist clean testall test check tests
