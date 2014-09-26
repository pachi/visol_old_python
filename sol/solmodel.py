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
"""Modelo de datos de la herramienta ViSol"""

from collections import namedtuple
from observer import Subject
import resparser
from config import config

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
            self._file = value
            self.edificio = resparser.loadfile(value)
