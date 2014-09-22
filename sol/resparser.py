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

def findblocks(resfile):
    """Devuelve diccionario de bloques del archivo de resultados de LIDER"""
    numplantas = 0
    blocks = OrderedDict()
    currentblock = None
    linebuffer = []

    for line in resfile:
        line = line.strip()
        if not line:
            pass
        elif line.startswith(u'Numero de plantas'):
            numplantas = int(next(resfile))
        elif ((line.startswith(u'"P') and ',' not in line) or
              line.startswith(u'RESULTADOS A NIVEL EDIFICIO')):
            blockname = line.strip('"') if line.startswith(u'"P') else u'Edificio'
            if currentblock is not None:
                blocks[currentblock] = linebuffer[:]
                linebuffer = []
            blocks[blockname] = []
            currentblock = blockname
        else:
            linebuffer.append(line)
    if currentblock is not None:
        blocks[currentblock] = linebuffer[:]
    return numplantas, blocks

def parseEdificio(block):
    """Interpreta bloque de datos del edificio de LIDER

    El bloque de edificio devuelve un objeto de tipo edificio y un diccionario
    con datos de las zonas, que se pueden ensamblar luego en el edificio por
    plantas.

    El diccionario de zonas contiene las claves: datos, calefaccion, refrigeracion
    """
    edificio = EdificioLIDER()
    zonas = OrderedDict()

    iblock = iter(block)
    for line in iblock:
        if line.startswith(u'Calefacción, Refrigeración anual'):
            cal, ref = next(iblock).split(',')
            edificio.calefaccion = float(cal)
            edificio.refrigeracion = float(ref)
            assert next(iblock).startswith(u'Calefacción mensual')
            edificio.calefaccion_meses = [float(mes) for mes in next(iblock).split(',')]
            assert next(iblock).startswith(u'Refrigeración mensual')
            edificio.refrigeracion_meses = [float(mes) for mes in next(iblock).split(',')]
        if line.startswith(u'Numero de zonas'):
            edificio.numzonas = int(next(iblock))
            # Linea de encabezados antes de datos por zonas
            if not next(iblock).startswith(u'Nombre, m2'):
                raise
            for line in iblock:
                # El bloque de zonas acaba con los totales
                if line.startswith(u'TOTAL'):
                    # TOTAL, m2, calefacción_total, refrigeracion
                    vals = [float(d) for d in line.lstrip(u'TOTAL,').split(',')]
                    edificio.superficie = vals[0]
                    # Valores redundantes
                    assert (vals[1] == edificio.calefaccion and
                            vals[2] == edificio.refrigeracion)
                    break
                else:
                    # nombrezona, m2, multiplicador, calefaccion, refrigeracion
                    key, (sup, multip, cal, ref) = valores(line)
                    zonas[key] = ZonaLIDER(key, sup, multip, cal, ref)
        if line.startswith(u'Calefacción mensual por zonas'):
            for i, (key, line) in enumerate(zip(zonas.keys(), iblock)):
                if i == edificio.numzonas: break
                zonas[key].calefaccion_meses = [float(d) for d in line.split(',')]
        if line.startswith(u'Refrigeración mensual por zonas'):
            for i, (key, line) in enumerate(zip(zonas.keys(), iblock)):
                if i == edificio.numzonas: break
                zonas[key].refrigeracion_meses = [float(d) for d in line.split(',')]
    return edificio, zonas

def parsePlanta(block, nombreplanta, zonas):
    """Intepreta bloque de planta de LIDER

    Se devuelve un diccionario de zonas por planta.
    Cada zona es un diccionario que incluye:
    - 'superficie':  la superficie de la zona.
    - 'flujos':      flujos térmicos por elementos generales (suelos, paredes,
                     infiltración...) y totales.
                     Es a su vez un diccionario de tuplas indexado por elementos
                     o 'TOTAL'.
    - 'componentes': cargas térmicas indexadas por espacio.

    Las cargas térmicas y los flujos se dan como tuplas con nombres del tipo
    Detalle -> 'Cal_positivo, Cal_negativo, Cal_neto, Ref_positivo, Ref_negativo, Ref_neto'
    """
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

                    # Procesamos los flujos de zona, que finalizan con el TOTAL
                    flujos = OrderedDict()
                    for zline in iblock:
                        if zline.startswith(u'Concepto') or not zline:
                            continue
                        concepto, vals = valores(zline)
                        flujos[concepto] = ComponenteLIDER(concepto, *vals)
                        if zline.startswith(u'TOTAL'):
                            break
                    zona.flujos = flujos

                    # Procesamos los componentes de zona, que están contados
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

                    zonasencontradas += 1
                    planta[nombrezona] = zona
    return planta

def parsefile(resfile):
    """Lee archivo y genera objeto edificio con datos generales y por plantas"""
    numplantas, plantablocks = findblocks(iter(resfile))
    edificio, zonas = parseEdificio(plantablocks.pop(u'Edificio'))
    edificio.numplantas = numplantas
    # Acopla plantas en edificio
    for nombreplanta in plantablocks:
        planta = parsePlanta(plantablocks[nombreplanta], nombreplanta, zonas)
        edificio[nombreplanta] = planta
    return edificio

def loadfile(resfile):
    """Devuelve edificio y texto original del archivo en forma de lista"""
    try:
        data = codecs.open(resfile, "rU", "latin-1" ).readlines()
        edificio = parsefile(data)
        edificio.resdata = ''.join(data)
    except:
        print "Errores procesando archivo", resfile
        raise
    return edificio

def check(edificio):
    """Comprueba que los datos del edificio son coherentes"""
    # TODO: comprobar que el número de plantas del archivo es igual que el
    # calculado, que las zonas están todas asignadas a plantas, que todas las
    # zonas tienen todos los datos, que las sumas dan lo de los totales....
    pass

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
    print zona.flujos
    print zona.calefaccion
    print zona.refrigeracion
