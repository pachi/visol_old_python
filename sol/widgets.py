#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   widgets.py
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

import gtk
import numpy
import matplotlib
matplotlib.use('GTKCairo')
#import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo
from matplotlib.font_manager import FontProperties
from matplotlib.transforms import offset_copy
from util import myround
from collections import OrderedDict

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
         'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

class HistoBase(FigureCanvasGTKCairo):
    """Histograma de Matplotlib"""
    __gtype_name__ = 'HistoBase'

    def __init__(self, edificio=None, planta=None, zona=None, componente=None):
        """Constructor

        edificio - Edificio analizado (EdificioLIDER)
        planta - Nombre de la planta "actual" analizada en el edificio (str)
        zona - Nombre de la Zona "actual" analizada en la planta (str)
        """
        self.edificio = edificio
        self.planta = planta
        self.zona = zona
        self.componente = componente

        self.fig = Figure()
        FigureCanvasGTKCairo.__init__(self, self.fig)
        self.fig.set_facecolor('w')
        self.ax1 = self.fig.add_subplot(111)
        self.ax1.set_axis_bgcolor('#f6f6f6')
        
        # Tamaños de letra y transformaciones para etiquetas de barras
        fontsize = matplotlib.rcParams['font.size']
        labelscale = 0.7
        self.labelfs = fontsize * labelscale
        labeloffset = fontsize * (1.0 - labelscale)
        
        self.trneg = offset_copy(self.ax1.transData, fig=self.fig,
                                 x=0, y=-fontsize, units='points')
        self.trpos = offset_copy(self.ax1.transData, fig=self.fig,
                                 x=0, y=labeloffset, units='points')
    
    @property
    def modo(self):
        return self._modo

    @modo.setter
    def modo(self, val):
        self._modo = val
        self.dibuja()

    @property
    def data(self):
        return self.edificio, self.planta, self.zona, self.componente

    @data.setter
    def data(self, value):
        edificio, planta, zona, componente = value
        #self.edificio = edificio # Es el nombre, no el objeto edificio
        self.planta = planta
        self.zona = zona
        self.componente = componente

    def autolabel(self, ax, rects):
        """Etiquetar valores fuera de las barras"""
        for rect in rects:
            height = rect.get_height()
            if height:
                # rect.get_y() es la base del rectángulo y es 0 si es positivo
                rectbasey = rect.get_y()
                if rectbasey == 0:  # rectángulo en la parte positiva
                    tr = self.trpos
                    rectbasey = height
                    k = 1.0
                else:               # rectángulo en la parte negativa
                    tr = self.trneg
                    k = -1.0
                ax.text(rect.get_x() + rect.get_width() / 2.0, rectbasey,
                        '%.1f' % (k*round(height, 1)), ha='center', va='bottom',
                        size=self.labelfs, transform=tr)

    def dibujaseries(self, ax):
        pass

    def dibuja(self, width=400, height=200):
        # Elementos generales
        ax1 = self.ax1
        ax1.clear() # Limpia imagen de datos anteriores
        ax1.grid(True)
        ax1.set_title(self.title, size='large')
        ax1.set_xlabel(self.xlabel,  fontdict=dict(color='0.5'))
        ax1.set_ylabel(self.ylabel, fontdict=dict(color='0.5'))

        self.dibujaseries(ax1)

        # Tamaño
        self.set_size_request(width, height)
        self.draw()

    def pixbuf(self, destwidth=600):
        """Obtén un pixbuf a partir del canvas actual"""
        return get_pixbuf_from_canvas(self, destwidth)

    def save(self, filename='condensacionesplot.png'):
        """Guardar y mostrar gráfica"""
        self.fig.savefig(filename)


class HistoMeses(HistoBase):
    """Histograma de demandas mensuales

    Dibuja un histograma de demandas de una zona por meses
    """
    __gtype_name__ = 'HistoMeses'

    def __init__(self, edificio=None, planta=None, zona=None, componente=None):
        """Constructor

        zona - Zona analizada
        """
        HistoBase.__init__(self, edificio, planta, zona, componente)
        self._modo = 'edificio'

        self.title = u"Demanda mensual"
        self.xlabel = u"Periodo"
        self.ylabel = u"Demanda [kWh/m²mes]"

    def minmax(self):
        """Mínimo y máximo en demanda por m2 del edificio.

        Corresponde al mínimo y máximo de las zonas, ya que las plantas y edificio
        solamente tienen que tener valores más bajos por m2
        """
        _min = min(min(zona.calefaccion_meses) for zona in self.edificio.zonas)
        _max = max(max(zona.refrigeracion_meses) for zona in self.edificio.zonas)
        return myround(_min, 5), myround(_max, 5)

    def dibujaseries(self, ax1):
        """Representa histograma de demanda mensual para una zona

        Se incluye la demanda de calefacción y refrigeración.

        El eje horizontal representa los periodos [meses] y el eje vertical la
        demanda existente [kWh/m²mes]
        """

        def barras(min, max, seriec, serier):
            w = 1.0
            rects1 = ax1.bar(ind, seriec, w, align='center', fc='r', ec='k')
            rects2 = ax1.bar(ind, serier, w, align='center', fc='b', ec='k')
            leg = ax1.legend((rects1[0], rects2[0]), ('Calefacción', 'Refrigeración'),
                             loc='lower left', prop={"size":'small'}, fancybox=True)
            leg.draw_frame(False)
            leg.get_frame().set_alpha(0.5) # transparencia de la leyenda
            ax1.set_ylim(min - 10, max + 10)
            self.autolabel(ax1, rects1)
            self.autolabel(ax1, rects2)

        # Datos meses
        ind = numpy.arange(12)
        x_names = [mes[:3] for mes in MESES]
        ax1.set_xticks(ind)
        ax1.set_xticklabels(x_names, size='small', rotation=90)
        _min, _max = self.minmax()

        # Demandas
        if self.modo == 'edificio' and self.edificio is not None:
            e = self.edificio
            barras(_min, _max, e.calefaccion_meses, e.refrigeracion_meses)
        elif self.modo == 'planta':
            pl = self.edificio[self.planta]
            barras(_min, _max, pl.calefaccion_meses, pl.refrigeracion_meses)
        elif self.modo == 'zona' and self.zona:
            zona = self.edificio[self.planta][self.zona]
            barras(_min, _max,zona.calefaccion_meses, zona.refrigeracion_meses)

class HistoElementos(HistoBase):
    """Histograma de demandas por elementos

    Dibuja un histograma de demandas de una zona por elementos
    """
    __gtype_name__ = 'HistoElementos'

    def __init__(self, edificio=None, planta=None, zona=None, componente=None):
        """Constructor

        zona - Zona analizada
        """
        HistoBase.__init__(self, edificio, planta, zona, componente)
        self._modo = 'edificio'

        self.title = u"Demandas por elemento"
        self.xlabel = u"Elemento"
        self.ylabel = u"Demanda [kWh/m²·año]"
        # Muestra o no los distintos desgloses de calefacción y refrigeración
        self.showcalpos = False
        self.showcalneg = False
        self.showrefpos = False
        self.showrefneg = False

    def minmaxplanta(self):
        """Mínimo y máximo de la escala vertical para todas las zonas de una planta"""
        pmin, pmax = [], []
        zonas = self.edificio[self.planta]
        for nzona in zonas:
            zona = zonas[nzona]
            x_names = zona.flujos.keys()
            pmin.append(myround(min(min(zona.flujos[name]) for zona in self.edificio.zonas for name in x_names), 10))
            pmax.append(myround(max(max(zona.flujos[name]) for zona in self.edificio.zonas for name in x_names), 10))
        return min(pmin), max(pmax)

    def dibujaseries(self, ax1):
        """Representa histograma de demanda por elemento

        El eje horizontal representa los elementos y el eje vertical la
        demanda existente [kWh/m²año]
        """
        def barras(demandas):
            """Dibuja las barras de demanda para las series activas"""
            calpos = demandas.get('cal+', [])
            calneg = demandas.get('cal-', [])
            calnet = demandas.get('cal', [])
            refpos = demandas.get('ref+', [])
            refneg = demandas.get('ref-', [])
            refnet = demandas.get('ref', [])
            if self.modo == 'edificio':
                mind = min(calneg + refneg)
                maxd = max(calpos + refpos + calnet + refnet)
            else:
                mind, maxd = self.minmaxplanta()
            
            seriesall = []
            
            if self.showcalpos:
                seriesall.append((calpos, '#FFBBFF', '0.5', 'Calefacción +'))
            if self.showcalneg:
                seriesall.append((calneg, '#FF6666', '0.5', 'Calefacción -'))
            seriesall.append((calnet, '#FF0000', 'k', 'Calefacción'))
            if self.showrefpos:
                seriesall.append((refpos, '#6666FF', '0.5', 'Refrigeración +'))
            if self.showrefneg:
                seriesall.append((refneg, '#B3FFB3', '0.5', 'Refrigeración -'))
            seriesall.append((refnet, '#0000FF', 'k', 'Refrigeración'))
            
            active = len(seriesall) # total active series
            w = 1.0 / active # width of each active serie
            
            seriesd = []
            labelsd = []
            
            for ii, (serie, fc, ec, label) in enumerate(seriesall):
                rects = ax1.bar(ind+(ii+0.5)*w, serie, w, align='center', fc=fc, ec=ec)
                seriesd.append(rects[0])
                labelsd.append(label)
                if label == 'Calefacción' or label == 'Refrigeración':
                    self.autolabel(ax1, rects)
            
            leg = ax1.legend(seriesd, labelsd, loc='lower left',
                             prop={"size":'small'}, fancybox=True)
            leg.draw_frame(False)
            leg.get_frame().set_alpha(0.5) # transparencia de la leyenda
            ax1.set_ylim(mind - 10, maxd + 10)
            ax1.set_xlim(0, ind[-1] + active * w) # mismo ancho aunque los extremos valgan cero

        # Demandas
        edificio = self.edificio
        labelrotation = 90
        if self.modo == 'edificio' and edificio is not None:
            #TODO: demandas por elementos para edificio
            x_labels = ["\n".join(name.split()) for name in edificio.flujos]
            demandas = edificio.demandas
        elif self.modo == 'planta':
            # Demandas por elementos para planta
            planta = edificio[self.planta]
            x_labels = ["\n".join(name.split()) for name in planta.flujos]
            demandas = planta.demandas
        elif self.modo == 'zona' and self.zona is not None:
            # Datos por elementos para una zona
            zona = edificio[self.planta][self.zona]
            x_labels = ["\n".join(name.split()) for name in zona.flujos]
            demandas = zona.demandas
        elif self.modo == 'componente':
            labelrotation = 0
            flujos = edificio[self.planta][self.zona][self.componente]
            demandas = OrderedDict()
            x_labels = [self.componente,]
            (demandas['cal+'], demandas['cal-'], demandas['cal'],
             demandas['ref+'], demandas['ref-'], demandas['ref']) = flujos
        else:
            raise NameError("Modo de operación inesperado: %s (%s, %s, %s, %s)" % 
                        (self.modo, self.edificio, self.planta, self.zona, self.componente))
        
        ind = numpy.arange(len(x_labels))
        barras(demandas)
        ax1.set_xticks(ind + 0.5)
        ax1.set_xticklabels(x_labels, size='small',
                            rotation=labelrotation, ha='center')
        ymin, ymax = ax1.get_ylim()
        ax1.vlines(ind, ymin, ymax, color='gray')
        ax1.grid(False)
        self.fig.subplots_adjust(bottom=0.17, left=.15)


def get_pixbuf_from_canvas(canvas, destwidth=None):
    """Devuelve un pixbuf a partir de un canvas de Matplotlib

    destwidth - ancho del pixbuf de destino
    """
    w, h = canvas.get_width_height()
    destwidth = destwidth if destwidth else w
    destheight = h * destwidth / w
    #Antes de mostrarse la gráfica en una de las pestañas no existe el _pixmap
    #pero al generar el informe queremos que se dibuje en uno fuera de pantalla
    oldpixmap = canvas._pixmap if hasattr(canvas, '_pixmap') else None
    pixmap = gtk.gdk.Pixmap(None, w, h, depth=24)
    canvas._renderer.set_pixmap(pixmap) # mpl backend_gtkcairo
    canvas._render_figure(pixmap, w, h) # mpl backend_gtk
    if oldpixmap:
        canvas._renderer.set_pixmap(oldpixmap)
    cm = pixmap.get_colormap()
    pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
    pixbuf.get_from_drawable(pixmap, cm, 0, 0, 0, 0, -1, -1)
    scaledpixbuf = pixbuf.scale_simple(destwidth, destheight,
                                       gtk.gdk.INTERP_HYPER)
    return scaledpixbuf