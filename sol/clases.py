#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy
from collections import OrderedDict

class EdificioLIDER(object):
    """Edificio en LIDER

    El edificio está organizado por plantas y contiene los siguientes datos:

    nombre - Nombre del edificio
    numplantas - Número de plantas del edificio
    numzonas - Número de zonas en el edificio
    superficie - Superficie del edificio [m²]
    calefaccion   - Demanda anual de calefacción del edificio [kWh/m²/año]
    refrigeracion - Demanda anual de refrigeración del edificio  [kWh/m²/año]
    calefaccion_meses   - Demandas mensuales de calefacción del edificio [kWh/m²/mes]
    refrigeracion_meses - Demandas mensuales de refrigeración del edificio [kWh/m²/mes]
    plantas - Diccionario de zonas por planta
    """
    def __init__(self, nombre='Edificio1'):
        self.nombre = nombre
        self.numplantas = 0
        self.numzonas = 0
        self.superficie = 0.0
        self.calefaccion = 0.0
        self.refrigeracion = 0.0
        self.calefaccion_meses = []
        self.refrigeracion_meses = []
        self.plantas = OrderedDict()

    @property
    def zonas(self):
        """Devuelve las zonas del edificio"""
        return [self.plantas[planta][zona] for planta in self.plantas for zona in self.plantas[planta]]

    def zona(self, nombrezona):
        #BUG: esto falla si hay varias zonas con el mismo nombre
        """Devuelve zona a partir del nombre"""
        for planta in self.plantas:
            if nombrezona in self.plantas[planta]:
                return self.plantas[planta][nombrezona]
        return None

class PlantaLIDER(OrderedDict):
    """Planta de LIDER

    Es un diccionario ordenado de zonas.

    nombre - Nombre de la planta
    superficie - Superficie de la planta [m²]
    calefaccion - Demanda anual de calefacción de la planta [kWh/m²año]
    refrigeracion - Demanda anual de refrigeración de la planta [kWh/m²año]
    calefaccion_meses   - Demandas mensuales de calefacción de la planta [kWh/m²/mes]
    refrigeracion_meses - Demandas mensuales de refrigeración de la planta [kWh/m²/mes]

    flujos - Flujos de calor por grupo (Paredes exteriores, Cubiertas...) [kWh/m²año]
    componentes - Flujos de calor por componente (Hueco H1, muro M1...) [kWh/m²año]
    """
    def __init__(self, nombre=''):
        OrderedDict.__init__(self)
        self.nombre = nombre

    @property
    def superficie(self):
        """Superficie de la planta en m²"""
        return sum(self[zona].superficie * self[zona].multiplicador for zona in self.keys())

    @property
    def calefaccion(self):
        """Demanda anual de calefacción por m²"""
        return sum(self.calefaccion_meses)

    @property
    def calefaccion_meses(self):
        """Demandas de calefacción mensuales por m²"""
        cal_planta = numpy.array([0.0] * 12)
        for nzona in self:
            zona = self[nzona]
            cal_planta += numpy.array(zona.calefaccion_meses) * zona.superficie
        return cal_planta / self.superficie

    @property
    def refrigeracion(self):
        """Demanda anual de refrigeración por m²"""
        return sum(self.refrigeracion_meses)

    @property
    def refrigeracion_meses(self):
        """Demandas de refrigeración mensuales por m²"""
        ref_planta = numpy.array([0.0] * 12)
        for nzona in self:
            zona = self[nzona]
            ref_planta += numpy.array(zona.refrigeracion_meses) * zona.superficie
        return ref_planta / self.superficie

    @property
    def flujos(self):
        """Flujos de calor de los grupos, para la planta"""
        dic = OrderedDict()
        flujoskeys = self[self.keys()[0]].flujos.keys()
        for grupo in flujoskeys:
            params = [self[object].superficie *
                      self[object].multiplicador *
                      numpy.array(self[object].flujos[grupo]) for object in self]
            plist = [sum(lst) for lst in zip(*params)]
            dic[grupo] = tuple(numpy.array(plist) / self.superficie)
        return dic

class ZonaLIDER(object):
    """Zona de edificio de LIDER

    Las zonas incluyen los siguientes datos:

    nombre - Nombre de la zona
    numero - Número identificativo de la zona
    planta - Nombre de la planta a la que pertenece la zona
    superficie - Superficie de la zona [m²]
    multiplicador - Número de zonas iguales
    calefaccion - Demanda anual de calefacción de la zona [kWh/m²/año]
    refrigeracion - Demanda anual de refrigeración de la zona [kWh/m²/año]
    calefaccion_meses - Demanda mensual de calefacción de la zona [kWh/m²/mes]
    refrigeración_meses - Demanda mensual de refrigeración de la zona [kWh/m²/mes]
    flujos - Flujos de calor por grupo (Paredes exteriores, Cubiertas...) [kWh/año]
    componentes - Flujos de calor por componente (Hueco H1, muro M1...) [kWh/año]
    """
    def __init__(self, nombre=None, superficie=0.0, multiplicador=1.0,
                 calefaccion=0.0, refrigeracion=0.0):
        self.nombre = nombre
        self.numero = None
        self.planta = None
        self.superficie = superficie
        self.multiplicador = multiplicador
        self.calefaccion = calefaccion
        self.refrigeracion = refrigeracion
        self.calefaccion_meses = []
        self.refrigeracion_meses = []
        # Elementos: incluyen información desglosada de flujos:
        # Calef. positivo, Calef. negativo, Calef. neto
        # Ref. poisitivo, Ref. negativo, Ref. neto
        self.flujos = None
        self.componentes = None
