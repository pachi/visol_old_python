#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   resparser.py
#   Analizador de archivos de resultados de LIDER
#
#   Copyright (C) 2013 Rafael Villar Burke <pachi@ietcc.csic.es>
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

"""
Parser de  archivos de resultados de LIDER
==========================================
"""
import codecs
from collections import OrderedDict
from clases import EdificioLIDER, PlantaLIDER, ZonaLIDER, ComponenteLIDER

def nextblock(linesiter, startswith):
    """Avanza el iterador hasta el siguiente bloque que empieza por startswith"""
    linebuffer = []
    for line in linesiter:
        linebuffer.append(line)
        if line.startswith(startswith):
            break
    return linebuffer

def valores(linea):
    """Devuelve concepto y valores de líneas de detalle

    Las líneas de detalle son las que tienen un primer elemento de concepto
    y una serie de valores en coma flotante separados por comas.

    >>> valores(u"Paredes Exteriores, 0.000000, -116.455211, 2.686940")
    (u'Paredes Exteriores', [0.000000, -116.455211, 2.686940])
    """
    elems = linea.split(u',')
    concepto = elems[0].strip(u'"\'')
    valores = [float(elem) for elem in elems[1:]]
    return concepto, valores

def parseEdificio(block):
    """Interpreta bloque de resultados a nivel edificio de LIDER

    Devuelve un objeto de tipo EdificioLIDER y un diccionario ordenado
    con datos de las zonas, que se pueden ensamblar luego en el edificio por
    plantas.

    El diccionario de zonas contiene como claves los nombres de zona y
    y valores un objeto zona con los atributos calefaccion_meses y
    refrigeracion_meses.
    """
    edificio = EdificioLIDER()
    iblock = iter(block)

    # Bloque de resultados a nivel de edificio
    nextblock(iblock, u'Calefacción, Refrigeración anual')
    cal, ref = next(iblock).split(',')
    edificio.calefaccion = float(cal)
    edificio.refrigeracion = float(ref)
    next(iblock) # Línea de 'Calefacción mensual'
    edificio.calefaccion_meses = [float(mes) for mes in next(iblock).split(',')]
    next(iblock) # Línea de 'Refrigeración mensual'
    edificio.refrigeracion_meses = [float(mes) for mes in next(iblock).split(',')]

    # Encuentra bloque de número de zonas
    nextblock(iblock, u'Numero de zonas')
    numerozonas = int(next(iblock))

    # Encuentra bloque de datos generales
    nextblock(iblock, u'Nombre, m2')
    zonas = OrderedDict()
    superficietotalzonas = 0
    for line in iblock:
        if line.startswith(u'TOTAL'):
            # TOTAL, m2, calefacción_total, refrigeracion_total
            # Aprovechamos solo la superficie total
            superficietotalzonas = float(line.split(',')[1])
            break
        else:
            # Nombre, m2, multiplicador, Calefacción, Refrigeración
            key, (sup, multip, cal, ref) = valores(line)
            zonas[key] = ZonaLIDER(key, sup, multip, cal, ref)

    # Encuentra bloque de calefacción por meses de zonas
    nextblock(iblock, u'Calefacción mensual por zonas')
    for key, line in zip(zonas.keys(), iblock):
        zonas[key].calefaccion_meses = [float(d) for d in line.split(',')]

    # Encuentra bloque de refrigeración por meses de zonas
    nextblock(iblock, u'Refrigeración mensual por zonas')
    for key, line in zip(zonas.keys(), iblock):
        zonas[key].refrigeracion_meses = [float(d) for d in line.split(',')]

    edificio.numzonas = numerozonas
    edificio.superficie = superficietotalzonas

    return edificio, zonas

def parsePlanta(block, nombreplanta, zonas):
    """Intepreta bloque de planta de LIDER

    Se devuelve un diccionario de zonas por planta.
    Cada zona es un diccionario que incluye:
    - 'superficie':  la superficie de la zona.
    - 'grupos':      flujos térmicos por elementos generales (suelos, paredes,
                     infiltración...) y totales.
                     Es a su vez un diccionario de tuplas indexado por elementos
                     o 'TOTAL'.
    - 'componentes': cargas térmicas indexadas por espacio.

    Las cargas térmicas y los flujos se dan como tuplas con nombres del tipo
    Detalle -> 'Cal_positivo, Cal_negativo, Cal_neto, Ref_positivo, Ref_negativo, Ref_neto'
    """

    def _parsegruposzona(iblock):
        """Procesa flujos por grupo de la zona"""
        grupos = OrderedDict()
        for zline in iblock:
            if zline.startswith(u'Concepto') or not zline:
                continue
            concepto, vals = valores(zline)
            grupos[concepto] = ComponenteLIDER(concepto, *vals)
            if zline.startswith(u'TOTAL'):
                break
        return grupos

    def _parsecomponenteszona(iblock, zona):
        """Procesa los componentes de la zona"""
        for zline in iblock:
            if zline.startswith(u'Numero de Componentes'):
                numcomponentes = int(next(iblock))
                next(iblock) # títulos
                if numcomponentes: # Si hay más de 0 componentes...
                    for j, zline in enumerate(iblock):
                        componente, vals = valores(zline)
                        zona[componente] = ComponenteLIDER(componente, *vals)
                        if j == numcomponentes - 1:
                            break
                break

    iblock = iter(block)
    planta = PlantaLIDER(nombreplanta)

    for line in iblock:
        if line.startswith(u'Numero de zonas'):
            numzonas = int(next(iblock))
            zonasencontradas = 0
            for line in iblock:
                if zonasencontradas > numzonas:
                    break
                elif line.startswith(u'Zona '):
                    numzona, nombrezona = line[4:].split(',')
                    nombrezona = nombrezona.strip(u' "')
                    zona = zonas[nombrezona]
                    zona.numero = int(numzona)
                    zona.planta = nombreplanta
                    zona.superficie = float(next(iblock))
                    zona.grupos = _parsegruposzona(iblock)
                    _parsecomponenteszona(iblock, zona)
                    zonasencontradas += 1
                    planta[nombrezona] = zona
    return planta

def loadfile(resfile):
    """Devuelve edificio y texto original del archivo en forma de lista"""
    try:
        data = codecs.open(resfile, "rU", "latin-1" ).readlines()
    except:
        print "Errores procesando archivo", resfile
        raise

    lines = iter(data)

    nextblock(lines, u'Numero de plantas')
    numplantas = int(next(lines))

    # Localiza bloques de plantas y de edificio
    blocks = OrderedDict()
    currentblock = None
    linebuffer = []

    for line in lines:
        line = line.strip()
        if ((line.startswith(u'"P') and ',' not in line) or
              line.startswith(u'RESULTADOS A NIVEL EDIFICIO')):
            blockname = line.strip().strip('"') if line.startswith(u'"P') else u'Edificio'
            if currentblock is not None:
                blocks[currentblock] = linebuffer[:]
                linebuffer = []
            blocks[blockname] = []
            currentblock = blockname
        elif line:
            linebuffer.append(line)
    if currentblock is not None:
        blocks[currentblock] = linebuffer[:]


    edificio, zonas = parseEdificio(blocks.pop(u'Edificio'))
    edificio.numplantas = numplantas

    # Acopla plantas en edificio y zonas en plantas
    for nombreplanta in blocks:
        planta = parsePlanta(blocks[nombreplanta], nombreplanta, zonas)
        edificio[nombreplanta] = planta
    edificio.resdata = ''.join(data)

    return edificio

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=u'Visor de archivos de resultados de LIDER')
    parser.add_argument('file1',  action="store", default='data/test.res')
    try:
        params = parser.parse_args()
        file1 = codecs.open(params.file1, "rU", "latin-1" )
    except IOError, msg:
        parser.error(str(msg))

    edificio = parsefile(file1)

    print edificio.numzonas
    print edificio.calefaccion, edificio.refrigeracion
    print edificio.calefaccion_meses
    print edificio.refrigeracion_meses
    planta = edificio.plantas[u'P02']
    print planta
    zona = planta[u'P02_E01']
    print zona.nombre
    print zona.numero
    print zona.planta
    print zona.superficie
    print zona.multiplicador
    print zona.keys()
    print zona.grupos
    print zona.calefaccion
    print zona.refrigeracion
