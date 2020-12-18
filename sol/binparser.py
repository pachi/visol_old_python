#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   pybinlider.py
#   Lectura de archivos BIN de LIDER
#
#   Copyright (C) 2015 Rafael Villar Burke <pachi@rvburke.com>
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
#   02110-1301, USA.#!/usr/bin/env python

import numpy as np
import pandas as pd

"""Estructura de datos de zonas LIDER

La estructura del formato está documentada en el archivo "esto2_nucleo.jar",
en el archivo LeeZonasLIDER_2.h

El primer entero (4bytes) del archivo contiene el número de zonas y
luego datos con información de cada zona según esta estructura (566206 bytes):

    const int nHoras=8760;
    struct zonaLIDER
    {
      char nombreZona[50];
      float Area;
      float Volumen;
      int multiplicador;
      float p[2];
      float g[24];
      int numLocalesAdyacentes;
      float UAext;
      float UAint[100];
      char localAdyacente[100][50];
      int daCal[nHoras];
      int daRef[nHoras];
      float QS[nHoras];
      float QL[nHoras];
      float Treal[nHoras];
      float Tmax[nHoras];
      float Tmin[nHoras];
      float Vventinf[nHoras];
    };

nombreZona: Nombre de la zona
Area: Superficie de la zona [m2]
Volumen: Volumen de la zona []m3]
multiplicador: Multiplicador de la zona
p: Factores de respuesta de la zona (p)
   ante ganancia térmica
   (cálculo de la carga sensible sobre los equipos con RTS)
g: Factores de respuesta (g) de la zona
   ante cambio de la temperatura
   (cálculo de la carga sensible sobre los equipos con RTS)
numLocalesAdyacentes: Número de zonas adyacentes (de 0 a numLocalesAdyacentes)
UAext: UA con el exterior [W/K]
UAint: UA con las zonas adyacentes [W/K]
localAdyacente: Nombres de las zonas adyacentes
daCal: 1|0 para on|off de demanda de calefacción
daRef: 1|0 para on|off de demanda de refrigeración
QS: Carga sensible de la zona [W?]
QL: Carga latente de la zona [W?]
Treal: Temperatura del local [ºC]
Tmax: Temperatura de consigna alta [ºC]
Tmin: Temperatura de consigna baja [ºC]
Vventinf: Caudal másico de ventilación e infiltración [kg/s?]

Ver descripción de los factores p y g en:
    IDAE, "Guía técnica. Procedimientos y aspectos de la simulación de instalaciones
    térmicas en edificios", pp.50-51 y Anexo 6.
"""

# _ZONASTRUCT.itemsize == 566206 # bytes
_ZONASTRUCT = np.dtype({'names': ['nombreZona', 'Area', 'Volumen', 'multiplicador',
                                  'p', 'g',
                                  'numLocalesAdyacentes', 'UAext',
                                  'UAint', 'localAdyacente',
                                  'daCal', 'daRef',
                                  'QS', 'QL',
                                  'Treal', 'Tmax', 'Tmin',
                                  'Vventinf'],
                        'formats': ['a50', 'f4', 'f4', 'i4',
                                    ('f4', 2), ('f4', 24),
                                    'i4', 'f4',
                                    ('f4', 100), ('a50', 100),
                                    ('i4', 8760), ('i4', 8760),
                                    ('f4', 8760), ('f4', 8760),
                                    ('f4', 8760), ('f4', 8760), ('f4', 8760),
                                    ('f4', 8760)]},
                       align=True)

def readBIN(filename='ResumenRCC.bin'):
    """Genera dataframes a partir de archivo LIDER con información de zonas"""
    with open(filename, "rb") as f:
        f.seek(4) #No necesitamos leer explícitamente el número de zonas
        resto = f.read()
        rawdata = np.fromstring(resto, dtype=_ZONASTRUCT)

    # Información general de zonas
    zidata = [dict(Nombre=zona['nombreZona'].strip('"'),
                   Area=zona['Area'],
                   Volumen=zona['Volumen'],
                   Multiplicador=zona['multiplicador'],
                   **dict({'p%i' % i: p for (i, p) in enumerate(zona['p'])},
                          **{'g%i' % i: g for (i, g) in enumerate(zona['g'])})
                  ) for zona in rawdata]
    zidf = pd.DataFrame(zidata)
    zidf.set_index('Nombre', drop=True, inplace=True)

    # Conectividades (UA con exterior y con zonas adyacentes)
    zcdata = [dict(Nombre=zona['nombreZona'].strip('"'),
                   Ext=zona['UAext'],
                   **{local.strip('"'): zona['UAint'][i] for (i, local) in enumerate(zona['localAdyacente']) if local})
              for zona in rawdata]
    zcdf = pd.DataFrame(zcdata)
    zcdf.set_index('Nombre', drop=True, inplace=True)

    # Datos horarios de las zonas
    zddata = [pd.DataFrame(dict(Nombre=zona['nombreZona'].strip('"'),
                                HasCal=zona['daCal'],
                                HasRef=zona['daRef'],
                                QSen=zona['QS'],
                                QLat=zona['QL'],
                                Temp=zona['Treal'],
                                Tmax=zona['Tmax'],
                                Tmin=zona['Tmin'],
                                Vventinf=zona['Vventinf']))
              for zona in rawdata]
    zddf = pd.concat(zddata)

    return zidf, zcdf, zddf

def saveBINdata(zi, zc, zd):
    "Guarda en disco datos de zonas de LIDER"

    with open('Zonas_Info.csv', 'w') as zif:
        zif.write("#Datos generales de zona:\n#Nombre, Área (m2), "
                    "Multiplicador, Volumen (m3), y factores de respuesta (p, g) de la zona\n")
        zi.to_csv(zif,
                    columns=('Area Multiplicador Volumen p0 p1 '
                            'g0 g1 g2 g3 g4 g5 g6 g7 g8 g9 g10 g11 g12 g13 g14 g15 g16 g17 g18 '
                            'g19 g20 g21 g22 g23').split())
    with open('Zonas_Conectividades.csv', 'w') as zcf:
        zcf.write("#Datos de conectividades de zona:\n#Nombre, Valores UA con el exterior "
                    "con los y locales adyacentes (W/K)\n")
        zc.to_csv(zcf,
                    columns=sorted(zc.columns))
    with open('Zonas_Datos.csv', 'w') as zdf:
        zdf.write("#Datos horarios de zonas:\n#Nombre, demanda de calefacción (on=1/off=0), "
                    "demanda de refrigeración (on=1/off=0), Carga latente (W), Carga sensible (W), "
                    "Temperatura real (ºC), Consigna alta (ºC), Consigna baja (ºC), "
                    "Caudal másico de ventilación e infiltraciones (kg/s)\n")
        zd.to_csv(zdf,
                    columns=('HasCal HasRef QLat QSen Temp Tmax Tmin Vventinf').split())

if __name__ == '__main__':
    import os
    import argparse

    usage = """%(prog)s [opciones] archivo.bin

    Lectura de archivos .BIN de LIDER
    (C) 2015 Rafael Villar Burke <pachi@rvburke.com>"""
    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument('binpath', nargs='?', default='ResumenRCC.bin', action='store',
                        help='Archivo .BIN de LIDER con datos de zonas')
    parser.add_argument('-s', '--save', action='store_true', help=u"Guarda resultados en disco")
    parser.add_argument('-i', '--info', action='store_true', help=u"Muestra información general de zonas")
    parser.add_argument('-c', '--conectividades', action='store_true', help=u"Muestra conectividades de zonas")
    parser.add_argument('-d', '--datoshorarios', action='store_true', help=u"Muestra datos horarios de zonas")

    args = parser.parse_args()

    binpath = args.binpath
    if os.path.exists(binpath):
        zi, zc, zd = readBIN(binpath)
        print(u"Leído archivo %s (%i zonas, %i vínculos, %i datos)" % (binpath, len(zi), len(zc), len(zd)))
        if args.save:
            saveBINdata(zi, zc, zd)
        if args.info:
            print("* Información general de zonas (%i zonas): " % len(zi))
            print(zi)
        if args.conectividades:
            print("* Conectividades entre zonas y con el exterior (UA W/K)")
            print(zc)
        if args.datoshorarios:
            print("* Datos horarios (iniciales) de las zonas (valores iniciales)")
            print(zd.head())
        # renh = suma de ventilación por zonas (kg/s * s/h * m3/kg) / Volumen zonas
    else:
        parser.print_help()
