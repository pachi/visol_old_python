#!/usr/bin/env python
#encoding: utf-8
#
#   Utilidades varias
#
#   Copyright (C) 2009-2011 Rafael Villar Burke <pachi@rvburke.com>
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
"""Módulo de utilidades varias"""

import os, sys

def get_main_dir():
    """Find main dir even for py2exe frozen modules"""
    if hasattr(sys, "frozen"): #py2exe frozen module
        md = os.path.dirname(sys.executable)
    else:
        # normal run
        md = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        # test run
        if not os.path.isdir(os.path.join(md, 'data')):
            md = os.path.abspath(os.path.join(md, '..'))
            if not os.path.isdir(os.path.join(md, 'data')):
                raise ValueError, 'No se encuentra directorio base'
    return md

APPROOT = get_main_dir()

def get_resource(*path_list):
    "Localiza un recurso del proyecto en base al directorio base del paquete"
    return os.path.abspath(os.path.join(APPROOT, *path_list))

def myround(x, base=5):
    """Redondea al valor más próximo a base"""
    return int(base * round(float(x)/base))
