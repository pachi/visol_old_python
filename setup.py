#!/usr/bin/env python
#encoding: utf-8
#
#   gtkui.py
#   Programa Visor para el Sistema de Observación de LIDER
#
#   Copyright (C) 2011 Rafael Villar Burke <pachi@rvburke.com>
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
"""Configuración de SOL"""

from setuptools import setup, find_packages
import py2exe
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


#gtk file inclusion
import gtk
# The runtime dir is in the same directory as the module:
GTK_RUNTIME_DIR = os.path.join(
    os.path.split(os.path.dirname(gtk.__file__))[0], "runtime")
assert os.path.exists(GTK_RUNTIME_DIR), "Cannot find GTK runtime data"
GTK_THEME_DEFAULT = os.path.join("share", "themes", "Default")
GTK_THEME_WINDOWS = os.path.join("share", "themes", "MS-Windows")
GTK_GTKRC_DIR = os.path.join("etc", "gtk-2.0")
GTK_GTKRC = "gtkrc"
GTK_WIMP_DIR = os.path.join("lib", "gtk-2.0", "2.10.0", "engines")
GTK_WIMP_DLL = "libwimp.dll"
# For tango icons
GTK_ICONS = os.path.join("share", "icons")
# Localisation data
GTK_LOCALE_DATA = os.path.join("share", "locale")

# Receta sacada de http://stackoverflow.com/questions/7884959/bundling-gtk-resources-with-py2exe
def generate_data_files(prefix, tree, file_filter=None):
    """
    Walk the filesystem starting at "prefix" + "tree", producing a list of files
    suitable for the data_files option to setup(). The prefix will be omitted
    from the path given to setup(). For example, if you have

        C:\Python26\Lib\site-packages\gtk-2.0\runtime\etc\...

    ...and you want your "dist\" dir to contain "etc\..." as a subdirectory,
    invoke the function as

        generate_data_files(
            r"C:\Python26\Lib\site-packages\gtk-2.0\runtime",
            r"etc")

    If, instead, you want it to contain "runtime\etc\..." use:

        generate_data_files(
            r"C:\Python26\Lib\site-packages\gtk-2.0",
            r"runtime\etc")

    Empty directories are omitted.

    file_filter(root, fl) is an optional function called with a containing
    directory and filename of each file. If it returns False, the file is
    omitted from the results.
    """
    data_files = []
    for root, dirs, files in os.walk(os.path.join(prefix, tree)):
        to_dir = os.path.relpath(root, prefix)

        if file_filter is not None:
            file_iter = (fl for fl in files if file_filter(root, fl))
        else:
            file_iter = files

        data_files.append((to_dir, [os.path.join(root, fl) for fl in file_iter]))

    non_empties = [(to, fro) for (to, fro) in data_files if fro]

    return non_empties

data_files = (
    # Use the function above...
    generate_data_files(GTK_RUNTIME_DIR, GTK_THEME_DEFAULT) +
    generate_data_files(GTK_RUNTIME_DIR, GTK_THEME_WINDOWS) +
    generate_data_files(GTK_RUNTIME_DIR, GTK_ICONS) +
    # ...or include single files manually
    [
        (GTK_GTKRC_DIR, [
            os.path.join(GTK_RUNTIME_DIR,
                         GTK_GTKRC_DIR,
                         GTK_GTKRC)
        ]),
        
        (GTK_WIMP_DIR, [
            os.path.join(
                GTK_RUNTIME_DIR,
                GTK_WIMP_DIR,
                GTK_WIMP_DLL)
        ]),
        ('ui', ['*jpg', '*.png', 'sol.ui']),
        ('.', ['README.rst', 'NEWS.txt', 'HACKING.txt'])
    ]
)

#data_files = [ 'ui/logo.jpg', 'ui/sol.ui', 'README.rst', 'NEWS.txt', 'HACKING.txt'
               # If using GTK+'s built in SVG support, uncomment these
               #os.path.join(GTK_RUNTIME_DIR, 'bin', 'gdk-pixbuf-query-loaders.exe'),
               #os.path.join(GTK_RUNTIME_DIR, 'bin', 'libxml2-2.dll'),
#           ]

# you'll need to copy the etc, lib and share directories from your GTK+ install
# from lib/ only all the *.dlls in the subtree are needed, and from
# share/ only themes/ and locale/. saves lots of space 

version = '1.0'

install_requires = ['matplotlib', 'numpy', 'pygtk', 'pygobject'
                    # List your project dependencies here.
                    # For more details, see:
                    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
                ]

#entry_points = {'console_scripts': ['visol=bin/visol']}

windows = [{'script': 'bin/visol',
            #'icon_resources': [(1, "visol.ico")],
}]

options = {'py2exe': { 'packages':'encodings',
                       # Optionally omit gio, gtk.keysyms, and/or rsvg if you're not using them
                       #'includes': 'cairo, pango, pangocairo, atk, gobject, gio, gtk.keysyms, rsvg',
                       'includes': 'cairo, pango, pangocairo, atk, gobject, gio',
                   }
       }

setup(name='visol',
    version=version,
    description="Visor de archivos de resultados de LIDER",
    long_description=README + '\n\n' + NEWS,
    classifiers=[
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    'Development Status :: 5 - Production/Stable',
    'Environment :: MacOS X',
    'Environment :: Win32 (MS Windows)',
    'Environment :: X11 Applications :: GTK',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
    'Natural Language :: Spanish',
    'Programming Language :: Python :: 2.7'
    'Programming Language :: Python :: Implementation :: CPython',
    'Topic :: Scientific/Engineering'
    ],
    keywords='LIDER,energía,edificación,CTE',
    author='Rafael Villar Burke',
    author_email='pachi@rvburke.com',
    url='http://www.rvburke.com/software.html',
    license='GPL-2.0+',
    packages=find_packages('sol'),
    package_dir = {'': 'sol'},
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    #entry_points=entry_points, # Esta es la alternativa a 'scripts' de setuptools
    windows=windows,
    options=options,
    data_files=data_files
)
