#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   clases.py
#   Clases para la representación de archivos de resultados de LIDER
#
#   Copyright (C) 2014-15 Rafael Villar Burke <pachi@ietcc.csic.es>
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
#   

from collections import OrderedDict
import numpy


def cached_property(function):
    """Propiedad cacheada

    Receta de: http://code.activestate.com/recipes/576563-cached-property/
    """
    def get(self):
        try:
            return self._property_cache[function]
        except AttributeError:
            self._property_cache = {}
            x = self._property_cache[function] = function(self)
            return x
        except KeyError:
            x = self._property_cache[function] = function(self)
            return x
    return property(get)

GRUPOSLIDER = [u'Paredes Exteriores', u'Cubiertas', u'Suelos',
               u'Puentes Térmicos', u'Solar Ventanas',
               u'Transmisión Ventanas', u'Fuentes Internas',
               u'Ventilación más Infiltración', u'TOTAL']

class EdificioLIDER(OrderedDict):
    """Edificio en LIDER

    El edificio es un diccionario de plantas y tiene las siguientes propiedades

    nombre - Nombre del edificio
    numplantas - Número de plantas del edificio
    numzonas - Número de zonas en el edificio
    superficie - Superficie del edificio [m²]
    calefaccion   - Demanda anual de calefacción del edificio [kWh/m²/año]
    refrigeracion - Demanda anual de refrigeración del edificio  [kWh/m²/año]
    calefaccion_meses   - Demandas mensuales de calefacción del edificio [kWh/m²/mes]
    refrigeracion_meses - Demandas mensuales de refrigeración del edificio [kWh/m²/mes]
    resdata - Contenido del archivo .RES del edificio
    """
    gruposlider = GRUPOSLIDER

    def __init__(self, nombre='Edificio1'):
        OrderedDict.__init__(self)
        self.nombre = nombre
        self.numplantas = 0
        self.numzonas = 0
        self.superficie = 0.0
        self.calefaccion = 0.0
        self.refrigeracion = 0.0
        self.calefaccion_meses = []
        self.refrigeracion_meses = []
        self.resdata = ''

    @property
    def zonas(self):
        """Devuelve las zonas del edificio"""
        return [self[planta][zona] for planta in self for zona in self[planta]]

    @cached_property
    def grupos(self):
        """Flujos de calor de los grupos, para el edificio [kW/m²·año]

        Devuelve un diccionario indexado por grupo (p.e. u'Paredes exteriores')
        que contiene una tupla con las demandas de cada grupo:
            (calefacción +, calefacción -, calefacción neta,
             refrigeración +, refrigeración -, refrigeración neta)
        """
        dic = OrderedDict()
        for grupo in self.gruposlider:
            params = [self[planta].superficie *
                      numpy.array(self[planta].grupos[grupo])
                      for planta in self]
            plist = [sum(lst) for lst in zip(*params)]
            dic[grupo] = numpy.array(plist) / self.superficie
        return dic

    @cached_property
    def demandas(self):
        """Demandas del edificio por grupos [kW/m²·año]

        Devuelve un diccionario con seis tuplas de calefacción +, calefacción -,
        calefacción neta, refrigeración +, refrigeración -, refrigeración neta
        que contienen el valor correspondiente para cada grupo del edificio.

        El orden de los valores corresponde al de los grupos en el diccionario
        self.grupos.keys().
        """
        d = OrderedDict()
        (d['cal+'], d['cal-'], d['cal'],
         d['ref+'], d['ref-'], d['ref']) = zip(*self.grupos.values())
        d['grupos'] = self.grupos.keys() # mismos elementos que self.gruposlider
        return d

    def minmaxgrupos(self):
        """Flujo máximo y mínimo de grupos en todas las zonas del edificio  [kW/m²·año]"""
        zonas = self.zonas
        names = self.gruposlider
        pmin = min(min(zona.grupos[name].values) for zona in zonas for name in names)
        pmax = max(max(zona.grupos[name].values) for zona in zonas for name in names)
        return pmin, pmax

    def minmaxmeses(self):
        """Mínimo y máximo en demanda del edificio [kW/m²·año]

        Corresponde al mínimo y máximo de las zonas, ya que las plantas y edificio
        solamente tienen que tener valores más bajos por m².
        """
        zonas = self.zonas
        _min = min(min(zona.calefaccion_meses) for zona in zonas)
        _max = max(max(zona.refrigeracion_meses) for zona in zonas)
        return _min, _max


class PlantaLIDER(OrderedDict):
    """Planta de LIDER

    Es un diccionario ordenado de zonas.

    nombre - Nombre de la planta
    superficie - Superficie de la planta [m²]
    calefaccion - Demanda anual de calefacción de la planta [kWh/m²año]
    refrigeracion - Demanda anual de refrigeración de la planta [kWh/m²año]
    calefaccion_meses   - Demandas mensuales de calefacción de la planta [kWh/m²/mes]
    refrigeracion_meses - Demandas mensuales de refrigeración de la planta [kWh/m²/mes]

    grupos - Flujos de calor por grupo (Paredes exteriores, Cubiertas...) [kWh/m²año]
    demanda - Flujos de calor por grupo (Paredes exteriores, Cubiertas...) [kWh/m²año]
    componentes - Flujos de calor por componente (Hueco H1, muro M1...) [kWh/m²año]
    """
    gruposlider = GRUPOSLIDER

    def __init__(self, nombre=''):
        OrderedDict.__init__(self)
        self.nombre = nombre

    @property
    def superficie(self):
        """Superficie de la planta en m² [m²]"""
        return sum(self[zona].superficie * self[zona].multiplicador for zona in self)

    @property
    def calefaccion(self):
        """Demanda anual de calefacción por m² [kWh/m²·año]"""
        return sum(self.calefaccion_meses)

    @cached_property
    def calefaccion_meses(self):
        """Demandas de calefacción mensuales por m² [kWh/m²·mes]"""
        cal_planta = numpy.zeros(12)
        for nzona in self:
            zona = self[nzona]
            cal_planta += numpy.array(zona.calefaccion_meses) * zona.superficie
        return cal_planta / self.superficie

    @property
    def refrigeracion(self):
        """Demanda anual de refrigeración por m² [kWh/m²·año]"""
        return sum(self.refrigeracion_meses)

    @cached_property
    def refrigeracion_meses(self):
        """Demandas de refrigeración mensuales por m² [kWh/m²·mes]"""
        ref_planta = numpy.zeros(12)
        for nzona in self:
            zona = self[nzona]
            ref_planta += numpy.array(zona.refrigeracion_meses) * zona.superficie
        return ref_planta / self.superficie

    @cached_property
    def grupos(self):
        """Flujos de calor de los grupos, para la planta [kW/m²·año]

        Devuelve un diccionario indexado por grupo (p.e. u'Paredes exteriores')
        que contiene una tupla con las demandas de cada grupo:
            (calefacción +, calefacción -, calefacción neta,
             refrigeración +, refrigeración -, refrigeración neta)
        """
        #TODO: El rendimiento de esta parte es crítico, y depende mucho
        #TODO: de la creación de numpy.arrays y la suma de valores
        superficieplanta = self.superficie
        dic = OrderedDict()
        for grupo in self.gruposlider:
            params = [self[zona].superficie *
                      self[zona].multiplicador *
                      numpy.array(self[zona].grupos[grupo].values)
                      for zona in self]
            # XXX: Se podría hacer con numpy sumando arrays (que lo hace columna a columna)
            plist = [sum(lst) for lst in zip(*params)]
            dic[grupo] = numpy.array(plist) / superficieplanta
        return dic

    @cached_property
    def demandas(self):
        """Demandas de la planta por grupos [kW/m²·año]

        Devuelve un diccionario con seis tuplas de calefacción +, calefacción -,
        calefacción neta, refrigeración +, refrigeración -, refrigeración neta
        que contienen el valor correspondiente para cada grupo de la planta.

        El orden de los valores corresponde al de los grupos en el diccionario
        self.grupos.keys().
        """
        d = OrderedDict()
        (d['cal+'], d['cal-'], d['cal'],
         d['ref+'], d['ref-'], d['ref']) = zip(*self.grupos.values())
        d['grupos'] = self.grupos.keys()
        return d


class ZonaLIDER(OrderedDict):
    """Zona de edificio de LIDER

    Diccionario ordenado de componentes, con los siguientes atributos:
    Los componentes incluyen flujos de calor por componente
        (Hueco H1, muro M1...) [kWh/año]

    nombre - Nombre de la zona
    numero - Número identificativo de la zona
    planta - Nombre de la planta a la que pertenece la zona
    superficie - Superficie de la zona [m²]
    multiplicador - Número de zonas iguales en la planta
    calefaccion - Demanda anual de calefacción de la zona [kWh/m²/año]
    refrigeracion - Demanda anual de refrigeración de la zona [kWh/m²/año]
    calefaccion_meses - Demanda mensual de calefacción de la zona [kWh/m²/mes]
    refrigeración_meses - Demanda mensual de refrigeración de la zona [kWh/m²/mes]
    grupos - Flujos de calor por grupo (Paredes exteriores, Cubiertas...) [kWh/año]
             (e.g. "'Paredes Exteriores': (0.0, 1.2, 1.2, 0.0, -1.0, -1.0)")
    """
    gruposlider = GRUPOSLIDER

    def __init__(self, nombre=None, superficie=0.0, multiplicador=1.0,
                 calefaccion=0.0, refrigeracion=0.0):
        OrderedDict.__init__(self)
        self.nombre = nombre
        self.numero = None
        self.planta = None
        self.superficie = superficie
        self.multiplicador = multiplicador
        self.calefaccion = calefaccion
        self.refrigeracion = refrigeracion
        self.calefaccion_meses = numpy.zeros(12)
        self.refrigeracion_meses = numpy.zeros(12)
        # Elementos/componentes: incluyen información desglosada de flujos:
        # Calef. positivo, Calef. negativo, Calef. neto
        # Ref. poisitivo, Ref. negativo, Ref. neto
        self.grupos = None

    @cached_property
    def demandas(self):
        """Demanda de la zona por elementos"""
        d = OrderedDict()
        data = [[cc.nombre] + list(cc.values)
                for cc in self.grupos.values()]
        (d['grupos'], d['cal+'], d['cal-'], d['cal'],
         d['ref+'], d['ref-'], d['ref']) = zip(*data)
        return d

class ComponenteLIDER(object):
    """Componente del edificio en LIDER

    nombre - Nombre del componente
    calpos - Flujo positivo de energía en temporada de calefacción [kWh/año]
    calneg - Flujo negativo de energía en temporada de calefacción [kWh/año]
    calnet - Flujo neto de energía en temporada de calefacción [kWh/año]
    refpos - Flujo positivo de energía en temporada de refrigeración [kWh/año]
    refneg - Flujo negativo de energía en temporada de refrigeración [kWh/año]
    refnet - Flujo neto de energía en temporada de refrigeración [kWh/año]
    demandas - diccionario con un elemento con clave el nombre y valor
               los flujos de calor del componente [kWh/año]
    """
    def __init__(self, nombre, calpos, calneg, calnet, refpos, refneg, refnet):
        # Cmabio de formato en HULC
        nombre = u'Ventilación más Infiltración' if nombre == u'Infiltración' else nombre
        self.nombre = nombre
        self.values = (calpos, calneg, calnet, refpos, refneg, refnet)
        self.demandas = OrderedDict([('grupos', [self.nombre]),
                                     ('cal+', [calpos]),
                                     ('cal-', [calneg]),
                                     ('cal', [calnet]),
                                     ('ref+', [refpos]),
                                     ('ref-', [refneg]),
                                     ('ref', [refnet])])
