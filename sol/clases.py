#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import OrderedDict

class EdificioLIDER(object):
    """Edificio en LIDER

    El edificio está organizado por plantas y contiene los siguientes datos:

    numplantas - Número de plantas del edificio
    numzonas - Número de zonas en el edificio
    superficie - Superficie del edificio [m²]
    calefaccion   - Demanda anual de calefacción del edificio [kWh/m²/año]
    refrigeracion - Demanda anual de refrigeración del edificio  [kWh/m²/año]
    calefaccion_meses   - Demandas mensuales de calefacción del edificio [kWh/m²/mes]
    refrigeracion_meses - Demandas mensuales de refrigeración del edificio [kWh/m²/mes]
    plantas - Diccionario de zonas por planta
    """
    def __init__(self):
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
    flujos - Flujos de calor por grupo (Paredes exteriores, Cubiertas...) [kWh/año]??
    componentes - Flujos de calor por componente (Hueco H1, muro M1...) [kWh/año]???

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
        self.flujos = None
        self.componentes = None

class DetalleLIDER(object):
    def __init__(self, nombre='',
                 calpos=0.0, calneg=0.0, calnet=0.0,
                 refpos=0.0, refneg=0.0, refnet=0.0):
        """Detalle de flujo de LIDER

        nombre - Nombre del elemento
        calpos - Flujo positivo en calefacción
        calneg - Flujo negativo en calefacción
        calnet - Flujo neto en calefacción
        refpos - Flujo positivo en refrigeración
        refneg - Flujo negativo en refrigeración
        refnet - Flujo neto en refrigeración
        """
        self.nombre = nombre
        self.calpos = calpos
        self.calneg = calneg
        self.calnet = calnet
        self.refpos = refpos
        self.refneg = refneg
        self.refnet = refnet

    def __repr__(self):
        t = "DetalleLIDER(%s, %f, %f, %f, %f, %f, %f)"
        return t % (self.nombre, self.calpos, self.calneg, self.calnet,
                    self.refpos, self.refneg, self.refnet)

