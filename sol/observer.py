#!/usr/bin/env python
#encoding: utf-8
#
#   ViSoL - Visor de resultados
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
"""Clases base del patrón Modelo-Observador"""

class Subject(object):
    """Clase para implementar el patrón Observer
    
    Tomado en parte de la receta:
        http://code.activestate.com/recipes/131499-observer-pattern/
    Se ha añadido la posibilidad de pasar parámetros arbitrarios en notify,
    para poder filtrar en update.
    
    Los observadores deben implementar el método update.
    """
    def __init__(self):
        self._observers = []
        self._block = False

    def attach(self, observer):
        """Añade un nuevo observador al que notificar"""
        if not observer in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        """Elimina un observador al que notificar"""
        try:
            self._observers.remove(observer)
        except ValueError:
            pass
    
    def block(self):
        """Bloquea notificaciones"""
        self._block = True
    
    def unblock(self, **kwargs):
        """Desbloquea notificaciones
        
        Si se pasa notify=True se realiza una notificación al desbloquear
        """
        self._block = False
        if 'notify' in kwargs and kwargs['notify']:
            self.notify(**kwargs)

    def notify(self, **kwargs):
        """Notificar a todos los observadores
        
        Permite enviar parámetros con nombre arbitrarios y excluir un
        observador usando el parámetro con nombre 'modifier' para evitar su
        actualización.
        
        P.e: model.notify(modifier=sujeto1, label='cambiamodelo')
        
        hace que no se notifique al sujeto1 y el resto recibe en su diccionario
        de parámetros {'modifier':sujeto1, 'label':'cambiamodelo'}
        """
        if not self._block:
            for observer in self._observers:
                if kwargs.get('modifier', None) != observer:
                    observer.update(self, **kwargs)

class Observer(object):
    """Clase de la que heredarán los observadores
    
    model hace referencia al objeto de la clase Subject que es observado.
    """
    def __init__(self, model=None):
        self._model = model
        if isinstance(model, Subject):
            self._model.attach(self)
    
    def update(self, subject, **kwargs):
        """Método que deben sobrecargar los observadores
        
        Puede recibir parámetros con nombre en el diccionario kwargs.
        """
        pass
    
    @property
    def model(self):
        return self._model
    
    @model.setter
    def model(self, newmodel):
        """Cambiar el modelo observado, dejando de observar el antiguo"""
        if self._model:
            self._model.detach(self)
        self._model = newmodel
        self._model.attach(self)
