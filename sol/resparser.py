#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   resparser.py
#   Analizador de archivos de resultados de LIDER
#
#   Copyright (C) 2013-2014 Rafael Villar Burke <pachi@ietcc.csic.es>
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

"""Parser de  archivos de resultados de LIDER"""

import codecs
from collections import OrderedDict
import numpy as np
from .clases import EdificioLIDER, PlantaLIDER, ZonaLIDER, ComponenteLIDER

def nextblock(linesiter, startswith):
    """Avanza el iterador y devuelve la primera línea que empiece por startswith"""
    for line in linesiter:
        if line.startswith(startswith):
            return line

def valores(linea):
    """Devuelve concepto y valores de líneas de detalle

    >>> valores(u"Paredes Exteriores, 0.000000, -116.455211, 2.686940")
    (u'Paredes Exteriores', [0.000000, -116.455211, 2.686940])
    """
    elems = linea.split(u',')
    return elems[0].strip(u'"\' '), [float(elem) for elem in elems[1:]]

def loadfile(resfile):
    """Devuelve un objeto de tipo EdificioLIDER a partir del archivo resfile"""
    try:
        data = codecs.open(resfile, "rU", "latin-1").readlines()
    except IOError:
        print "Errores procesando archivo", resfile
        raise
    lines = iter(data)

    edificio = EdificioLIDER()
    edificio.resdata = ''.join(data)

    zonasstore = OrderedDict()

    # Plantas del edificio
    nextblock(lines, u'Numero de plantas')
    numplantas = int(next(lines))
    edificio.numplantas = numplantas

    for iplanta in range(numplantas):
        line = nextblock(lines, u'"P')
        nombreplanta = line.strip(u'" \t\r\n')
        planta = PlantaLIDER(nombreplanta)
        edificio[nombreplanta] = planta

        # Zonas de la planta
        nextblock(lines, u'Numero de zonas')
        numzonas = int(next(lines))
        zonasplantanames = []
        for izona in range(numzonas):
            numzona, nombrezona = nextblock(lines, u'Zona ').split(u',')
            nombrezona = nombrezona.strip(u'" \t\r\n')
            zonasplantanames.append(nombrezona)
            supzona = float(next(lines))

            zona = ZonaLIDER(nombrezona)
            zona.numero =  int(numzona[4:])
            zona.planta = nombreplanta
            zona.superficie = supzona

            # Grupos de demanda de la zona
            nextblock(lines, u'Concepto')
            grupos = OrderedDict()
            for igrupos in range(9): # 9 grupos de demanda
                gline = next(lines).strip()
                grupo, vals = valores(gline)
                grupos[grupo] = ComponenteLIDER(grupo, *vals)
            zona.grupos = grupos

            # Componentes de demanda de la zona
            nextblock(lines, u'Numero de Componentes')
            numcomponentes = int(next(lines))
            nextblock(lines, u'Componente,')
            for icomponente in range(numcomponentes):
                cline = next(lines).strip()
                componente, vals = valores(cline)
                zona[componente] = ComponenteLIDER(componente, *vals)

            planta[nombrezona] = zona
            zonasstore[nombrezona] = zona
        edificio[nombreplanta] = planta

    # Datos generales del edificio
    nextblock(lines, u'RESULTADOS A NIVEL EDIFICIO')

    # Datos generales de demandas del edificio
    nextblock(lines, u'Calefacción, Refrigeración anual')
    cal, ref = next(lines).split(u',')
    edificio.calefaccion = float(cal)
    edificio.refrigeracion = float(ref)
    nextblock(lines, u'Calefacción mensual')
    edificio.calefaccion_meses = [float(x) for x in next(lines).split(u',')]
    nextblock(lines, u'Refrigeración mensual')
    edificio.refrigeracion_meses = [float(x) for x in next(lines).split(u',')]

    # Datos generales de las zonas del edificio
    nextblock(lines, u'Numero de zonas')
    numzonasedificio = int(next(lines))
    edificio.numzonas = numzonasedificio
    nextblock(lines, u'Nombre, m2, multiplicador')
    zonasnames = []
    for izona in range(numzonasedificio):
        zline = next(lines)
        nombrezona, (sup, multip, cal, ref) = valores(zline)
        zonasnames.append(nombrezona)
        zona = zonasstore[nombrezona]
        # zona.superficie = sup # ya se almacenó antes
        zona.multiplicador = multip
        zona.calefaccion = cal
        zona.refrigeracion = ref

    supedificio, _, _ = next(lines).split(u',')[1:]
    edificio.superficie = float(supedificio)

    # Demandas mensuales por zonas
    nextblock(lines, u'Calefacción mensual por zonas')
    for nombrezona in zonasnames:
        vals = [float(x) for x in next(lines).split(u',')]
        zonasstore[nombrezona].calefaccion_meses = vals
    nextblock(lines, u'Refrigeración mensual por zonas')
    for nombrezona in zonasnames:
        vals = [float(x) for x in next(lines).split(u',')]
        zonasstore[nombrezona].refrigeracion_meses = vals

    return edificio

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=u'Visor de archivos de resultados de LIDER')
    parser.add_argument('file1', action="store", default='data/test.res')
    try:
        params = parser.parse_args()
        file1 = codecs.open(params.file1, "rU", "latin-1")
    except IOError, msg:
        parser.error(str(msg))

    ed = loadfile(file1)

    print ed.numzonas
    print ed.calefaccion, ed.refrigeracion
    print ed.calefaccion_meses
    print ed.refrigeracion_meses
    pl = ed.plantas[u'P02']
    print pl
    zn = pl[u'P02_E01']
    print zn.nombre
    print zn.numero
    print zn.planta
    print zn.superficie
    print zn.multiplicador
    print zn.keys()
    print zn.grupos
    print zn.calefaccion
    print zn.refrigeracion
