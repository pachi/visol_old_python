#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   visor.py
#   Visor de archivos de LIDER
#
#   Copyright (C) 2011 Rafael Villar Burke <pachi@ietcc.csic.es>
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
"""Script de arranque de la aplicación sin necesidad de instalarla"""

import os, sys
import warnings

if not hasattr(sys, 'frozen'):
    currpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(currpath)
else:
    warnings.simplefilter('ignore')

from sol.gtkui import GtkSol

app = GtkSol()
app.main()