#!/usr/bin/env python
#encoding: utf-8
#
#   gtkui.py
#   Programa Visor para el Sistema de Observación de LIDER
#
#   Copyright (C) 2014-15 Rafael Villar Burke <pachi@rvburke.com>
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
"""Modelo de datos de la herramienta ViSol"""

import os
from collections import namedtuple
from .observer import Subject
from . import resparser
from . import binparser
from .config import config

Index = namedtuple('Index', ['edificio', 'planta', 'zona', 'componente'])

class VISOLModel(Subject):
    """Modelo para la aplicación ViSOL"""
    modos = ('edificio', 'planta', 'zona', 'componente')
    def __init__(self, edificio=None):
        Subject.__init__(self)
        self.edificio = edificio
        self.activo = None # Objeto activo
        self.config = config
        self._modo = None  # Tipo del objeto activo
        self._index = None # Índice del objeto activo
        self._file = None

    @property
    def modo(self):
        return self._modo

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, val):
        """Guarda índice, modo y objeto activo"""
        self._index = Index(*val)

        # Actualiza el tipo del objeto activo
        # TODO: Mirar si esto lo puede dar el propio objeto
        ii = sum(1 for i in val if i != '') - 1
        _modo = self.modos[ii]
        self._modo = _modo

        #TODO: mover a método de edificio, que devuelve objeto según ruta
        edf = self.edificio
        idx = self._index
        if _modo == 'edificio':
            self.activo = edf
        elif _modo == 'planta':
            self.activo = edf[idx.planta]
        elif _modo == 'zona':
            self.activo = edf[idx.planta][idx.zona]
        elif _modo == 'componente':
            self.activo = edf[idx.planta][idx.zona][idx.componente]

        self.notify(label='index')

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, value):
        if value != self.file:
            if not os.path.exists(value):
                return
            self._file = value
            self.edificio = resparser.loadfile(value)
            # Probamos primero a ver si hay un bin con el mismo nombre que el res,
            # luego uno con ResumenRCC_nombrearchivores.bin y
            # finalmente el primero que encuentre.
            respathdir = self.dirname
            binfiles = [ff for ff in os.listdir(respathdir) if ff.lower().endswith('.bin')]
            if binfiles:
                samename = self.filename + '.bin'
                resumenrccname = 'ResumenRCC_' + self.filename + '.bin'
                if samename in binfiles:
                    binfile = samename
                elif resumenrccname in binfiles:
                    binfile = resumenrccname
                else:
                    binfile = binfiles[0]
                self._binfile = os.path.join(respathdir, binfile)
                self.bindata = binparser.readBIN(self._binfile)
            else:
                self._binfile = None
                self.bindata = None

    @property
    def filename(self):
        root, ext = os.path.splitext(os.path.basename(self._file))
        return root

    @property
    def dirname(self):
        return os.path.dirname(self._file)
