#!/usr/bin/env python
#encoding: utf-8
#
#   gtkui.py
#   Programa Visor para el Sistema de Observación de LIDER
#
#   Copyright (C) 2011-2014 Rafael Villar Burke <pachi@rvburke.com>
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
"""Configuración la herramienta ViSol"""

from util import get_resource

config = {}

validkeys = ['autolimits', # Límite automático de demanda
             'maxlimit',   # Límite superior
             'minlimit'    # Límite inferior
]

keys = []
for line in open(get_resource('ui/visol.cfg')):
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    else:
        key, value = line.split('=')
        key, value = key.strip(), value.strip()
        if key in validkeys:
            if key == 'autolimits':
                config[key] = bool(value)
            else:
                config[key] = int(value)
