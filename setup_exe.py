#!/usr/bin/env python
#encoding: utf-8
#
#   Programa ViSol: Visor de archivos de resultados de LIDER
#
#   Copyright (C) 2014 Rafael Villar Burke <pachi@rvburke.com>
#
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 2
#   of the License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
#   02110-1301, USA.
"""Configuración de SOL para generar ejecutable en win32 con cx_freeze

$ python setup.py build

http://stackoverflow.com/questions/21002446/bundling-gtk3-with-py2exe
http://stackoverflow.com/questions/20067856/python3-pygobject-gtk3-and-cx-freeze-missing-dlls

Para ver archivos necesarios en la distribución ver:
http://www.tarnyko.net/repo/gtk3_build_system/tutorial/gtk3_tutorial.htm
"""

import os, sys, io
from glob import glob
from cx_Freeze import setup, Executable
from sol import __version__

## Collect the list of missing dll when cx_freeze builds the app
include_dll_path = os.path.abspath(r'C:\msys32\mingw32\bin')
missing_dll = ['libgtk-3-0.dll',
               'libgdk-3-0.dll',
               'libatk-1.0-0.dll',
               'libcairo-gobject-2.dll',
               #'libcroco-0.6-3.dll', #SVG
               'libepoxy-0.dll',
               'libffi-7.dll',
               'libgcrypt-20.dll',
               'libgdk_pixbuf-2.0-0.dll',
               'libgirepository-1.0-1.dll',
               'libgnutls-30.dll',
               'libjpeg-8.dll',
               #'liblzma-5.dll', #SVG
               'libp11-kit-0.dll',
               'libpango-1.0-0.dll',
               'libpangocairo-1.0-0.dll',
               'libpangoft2-1.0-0.dll',
               'libpangowin32-1.0-0.dll',
               'libpyglib-2.0-python2-0.dll',
               #'librsvg-2-2.dll', #SVG
               #'libxml2-2.dll', #SVG
]

## We need to add all the libraries too (for themes, etc..)
gtk_libs = ['etc/gtk-3.0',
            'etc/pango',
            'lib/gdk-pixbuf-2.0', #SVG
            'lib/gtk-3.0',
            'lib/girepository-1.0',
            'share/glib-2.0',
            'share/gtk-3.0',
            'share/icons/hicolor',
            'share/icons/Adwaita/16x16',
            'share/icons/Adwaita/22x22',
            'share/icons/Adwaita/index.theme',
            'share/themes/Default/gtk-3.0']

## Create the list of includes as cx_freeze likes
include_files = []
for dll in missing_dll:
    include_files.append((os.path.join(include_dll_path, dll), dll))

## Let's add ui, res and data dirs from ViSol
pats = ['ui/*.jpg', 'ui/*.png', 'res/pantallazo*.png']
staticfiles = ['ui/sol.ui',
               'ui/visol.cfg',
               'data/test.res',
               'data/test.re2',
               'data/test.bin',
               'README.rst',
               'NEWS.txt',
               'HACKING.txt',
               'COPYING.txt'
]
include_files.extend((ff, ff) for ffpat in pats for ff in glob(ffpat))
for ff in staticfiles:
    include_files.append((ff, ff))

## Let's add gtk libraries folders and files
for lib in gtk_libs:
    include_files.append((os.path.join(r'C:\msys32\mingw32', lib), lib))

base = None

## Lets not open the console while running the app
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable("bin/visol",
               base=base,
               icon='res/visol.ico'
    )
]

buildOptions = dict(
    no_compress=True,
    includes=["gi"],
    excludes=["Tkinter", "tcl", "PyQt5", "_ssl", "doctest", "ssl", "PIL"],
    packages=["gi"],
    include_files=include_files,
    )

README = io.open('README.rst', 'r', encoding="utf-8").read()
NEWS = open('NEWS.txt').read()
setup(
    name="visol",
    author="Rafael Villar Burke",
    author_email='pachi@rvburke.com',
    version=__version__,
    description="Visor de archivos de resultados de LIDER",
    long_description=README + '\n\n' + NEWS,
    options=dict(build_exe=buildOptions),
    executables=executables,
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Natural Language :: Spanish',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Scientific/Engineering'],
    keywords=u"LIDER,energía,edificación,CTE",
    url="http://www.rvburke.com/software.html",
    license="GPL-2.0+"
)
