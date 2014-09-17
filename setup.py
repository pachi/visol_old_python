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
"""Configuración de SOL"""

from setuptools import setup, find_packages
import sys, os
from sol import __version__

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()

data_files = ([('ui', glob.glob('ui/*.png')),
               ('ui', glob.glob('ui/*.jpg')),
               ('ui', ['ui/sol.ui', 'ui/visol.cfg']),
               ('data', ['data/test.res', 'data/test.re2']),
               ('res', glob.glob('res/pantallazo*.png')),
               ('.', ['COPYING.txt', 'README.rst', 'NEWS.txt', 'HACKING.txt', 'TODO.txt']),
])

install_requires = ['matplotlib', 'numpy', 'pygtk', 'gobject', 'cairo', 'pangocairo', 'atk', 'gio',
                    'dateutils', 'six', 'pytz'
                    # List your project dependencies here.
                    # For more details, see:
                    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
                ]

entry_points = {'gui_scripts': ['visol=bin/visol:main']}

setup(name='visol',
    version=__version__,
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
    entry_points=entry_points,
    data_files=data_files
)
