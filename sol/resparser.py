#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visor de archivos de resultados de LIDER
========================================
"""
import os
import codecs
from collections import OrderedDict, namedtuple

TESTFILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'datos/test.res'))

Zonasdata = namedtuple('Zonasdata', 'm2 multiplicador calefaccion refrigeracion')
TZonasdata = namedtuple('TZonasdata', 'm2 calefaccion refrigeracion')
Detalle = namedtuple('Detalle', 'Cal_positivo, Cal_negativo, Cal_neto, Ref_positivo, Ref_negativo, Ref_neto')

class EdificioLIDER(object):
    """Edificio en LIDER

    El edificio está organizado por plantas
    """
    def __init__(self):
        self.numzonas = 0
        self.totales = {}
        self.totales[u'calefaccion'] = None
        self.totales[u'refrigeracion'] = None
        self.totales[u'zonas'] = None
        self.meses = {}
        self.meses[u'calefaccion'] = []
        self.meses[u'refrigeracion'] = []
        self.plantas = OrderedDict()

def valores(linea):
    """Devuelve concepto y valores de líneas de detalle

    Las líneas de detalle son las que tienen un primer elemento de concepto
    y una serie de valores en coma flotante separados por comas.

    >>> valores(u"Paredes Exteriores, 0.000000, -116.455211, 2.686940")
    (u'Paredes Exteriores', [0.000000, -116.455211, 2.686940])
    """
    elems = linea.split(u',')
    concepto = elems[0].strip()
    valores = [float(elem) for elem in elems[1:]]
    return concepto, valores

def findblocks(file):
    """Devuelve diccionario de bloques del archivo de resultados de LIDER"""
    blocks = OrderedDict()
    currentblock = None
    linebuffer = []

    for line in file:
        line = line.strip()
        if not line:
            pass
        elif line.startswith(u'Numero de plantas'):
            blocks[u'numplantas'] = int(next(file))
        elif line.startswith(u'"P') and ',' not in line:
            line = line.strip('"')
            # Creabloque
            if currentblock is not None:
                blocks[currentblock] = linebuffer[:]
                linebuffer = []
            blocks[line] = list()
            currentblock = line
            # Fin creabloque
        elif line.startswith(u'RESULTADOS A NIVEL EDIFICIO'):
            line = u'Edificio'
            # Creabloque
            if currentblock is not None:
                blocks[currentblock] = linebuffer[:]
                linebuffer = []
            blocks[line] = list()
            currentblock = line
            # Fin creabloque
        else:
            linebuffer.append(line)
    if currentblock is not None:
        blocks[currentblock] = linebuffer[:]
    #print currentblock
    return blocks

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
            edificio.totales[u'calefaccion'] = float(cal)
            edificio.totales[u'refrigeracion'] = float(ref)
        if line.startswith(u'Calefacción mensual'):
            edificio.meses[u'calefaccion'] = [float(mes) for mes in next(iblock).split(',')]
        if line.startswith(u'Refrigeración mensual'):
            edificio.meses[u'refrigeracion'] = [float(mes) for mes in next(iblock).split(',')]
        # XXX: Los datos de zonas son redundantes con el bloque de zonas,
        # XXX: ¿salvo el valor de mutiplicador?
        # XXX: se podrían eliminar o usarlos para comprobaciones
        if line.startswith(u'Numero de zonas'):
            edificio.numzonas = int(next(iblock))
            # Linea de encabezados antes de datos por zonas
            if not next(iblock).startswith(u'Nombre, m2'):
                raise
            for line in iblock:
                # El bloque de zonas acaba con los totales
                if line.startswith(u'TOTAL'):
                    line = line.lstrip(u'TOTAL,')
                    vals = [float(d) for d in line.split(',')]
                    edificio.totales[u'zonas'] = TZonasdata(*vals)
                    break
                else:
                    t = line.split(',')
                    key, values = t[0].strip('"'), [float(d) for d in t[1:]]
                    zonas[key] = {}
                    zonas[key][u'datos'] = Zonasdata(*values)
        if line.startswith(u'Calefacción mensual por zonas'):
            for i, (key, line) in enumerate(zip(zonas.keys(), iblock)):
                if not line or i == edificio.numzonas - 1: break
                zonas[key][u'calefaccion'] = [float(d) for d in line.split(',')]
        if line.startswith(u'Refrigeración mensual por zonas'):
            for i, (key, line) in enumerate(zip(zonas.keys(), iblock)):
                if not line or i == edificio.numzonas - 1: break
                zonas[key][u'refrigeracion'] = [float(d) for d in line.split(',')]
    return edificio, zonas

def parsePlanta(block):
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
    planta = OrderedDict()

    for line in iblock:
        if line.startswith(u'Numero de zonas'):
            numzonas = int(next(iblock))
            zonasencontradas = 0
            for line in iblock:
                if zonasencontradas > numzonas:
                    break
                elif line.startswith(u'Zona '):
                    numzona, nombrezona = line[4:].split(',')
                    # XXX: ¿Se usa en algún lado o vale con nombrezona?
                    numzona = int(numzona)
                    nombrezona = nombrezona.strip(u' "')
                    superficie = float(next(iblock))
                    flujos = OrderedDict()
                    # Procesamos los flujos de zona, que finalizan con el TOTAL
                    for zline in iblock:
                        if zline.startswith(u'Concepto') or not zline:
                            continue
                        concepto, vals = valores(zline)
                        flujos[concepto] = Detalle(*vals)
                        if zline.startswith(u'TOTAL'):
                            break
                    # Procesamos los componentes de zona, que están contados
                    for zline in iblock:
                        if zline.startswith(u'Numero de Componentes'):
                            numcomponentes = int(next(iblock))
                            next(iblock) # títulos
                            componentes = OrderedDict()
                            for j, zline in enumerate(iblock):
                                concepto, vals = valores(zline)
                                componentes[concepto] = Detalle(*vals)
                                if j == numcomponentes - 1:
                                    break
                    zonasencontradas += 1

                    planta[nombrezona] = {}
                    planta[nombrezona][u'numero'] = numzona
                    planta[nombrezona][u'superficie'] = superficie
                    planta[nombrezona][u'flujos'] = flujos
                    planta[nombrezona][u'componentes'] = componentes

    return planta

def parsefile(file):
    """Lee archivo y genera objeto de edificio con datos generales y por plantas"""
    blocks = findblocks(file)
    edificio, zonas = parseEdificio(blocks[u'Edificio'])
    # Acopla plantas en edificio
    for block in blocks.keys():
        if block in (u'numplantas', u'Edificio'):
            continue
        planta = parsePlanta(blocks[block])
        edificio.plantas[block] = planta
    # Acopla zonas en plantas de edificio
    for planta in edificio.plantas:
        for zona in edificio.plantas[planta]:
            destzona = edificio.plantas[planta][zona]
            origzona = zonas[zona]
            destzona[u'datos'] = origzona[u'datos']
            destzona[u'calefaccion'] = origzona[u'calefaccion']
            destzona[u'refrigeracion'] = origzona[u'refrigeracion']
    return edificio

def check(edificio):
    """Comprueba que los datos del edificio son coherentes"""
    # TODO: comprobar que el número de plantas del archivo es igual que el calculado
    # que las zonas están todas asignadas a plantas, que todas las zonas tienen todos
    # los datos, que las sumas dan lo de los totales....
    pass

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=u'Visor de archivos de resultados de LIDER')
    parser.add_argument('file1',  action="store", default='datos/test')
    try:
        params = parser.parse_args()
        file1 = codecs.open(params.file1, "rU", "latin-1" )
    except IOError, msg:
        parser.error(str(msg))

    edificio = parsefile(file1)

    print edificio.totales[u'calefaccion'], edificio.totales[u'refrigeracion']
    print edificio.numzonas
    print edificio.totales[u'zonas']
    print edificio.plantas[u'P02']
    print edificio.plantas[u'P02'][u'P02_E01'][u'datos']
    print edificio.plantas[u'P02'][u'P02_E01'][u'componentes']#zonas.datos
    print edificio.plantas[u'P02'][u'P02_E01'][u'flujos']
    print edificio.plantas[u'P02'][u'P02_E01'][u'calefaccion']
    print edificio.plantas[u'P02'][u'P02_E01'][u'refrigeracion']


