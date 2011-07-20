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
from util import myround

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
         'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

class HistoBase(FigureCanvasGTKCairo):
    """Histograma de Matplotlib"""
    __gtype_name__ = 'HistoBase'

    def __init__(self, edificio=None, planta=None, zona=None):
        """Constructor

        edificio - Edificio analizado (EdificioLIDER)
        planta - Nombre de la planta analizada en el edificio (str)
        zona - Nombre de la Zona analizada en la planta (str)
        """
        self.edificio = edificio # Objeto EdificioLIDER
        self.planta = planta # Nombre de planta
        self.zona = zona # Nombre de zona

        self.fig = Figure()
        FigureCanvasGTKCairo.__init__(self, self.fig)
        self.fig.set_facecolor('w')
        self.ax1 = self.fig.add_subplot(111)
        self.ax1.set_axis_bgcolor('#f6f6f6')

    @property
    def modo(self):
        return self._modo

    @modo.setter
    def modo(self, val):
        self._modo = val
        self.dibuja()

    @property
    def data(self):
        return self.edificio, self.planta, self.zona

    @data.setter
    def data(self, value):
        edificio, planta, zona = value
        #self.edificio = edificio # Es el nombre, no el objeto edificio
        self.planta = planta
        self.zona = zona

    def autolabel(self, ax, rects):
        """Etiquetar valores fuera de las barras"""
        #TODO: usar altura de texto en lugar de displacement
        # ver http://matplotlib.sourceforge.net/faq/howto_faq.html
        # Automatically make room for tick labels
        texth = 2.0
        for rect in rects:
            height = rect.get_height()
            if height:
                # rect.get_y() es la base del rectángulo y es 0 si es positivo
                _h = -(height + texth + 0.5) if rect.get_y() else (height + 0.5)
                ax.text(rect.get_x() + rect.get_width() / 2.0,
                        _h, '%.1f' % round(height, 1),
                        ha='center', va='bottom', size='small')

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

    def __init__(self, edificio=None, planta=None, zona=None):
        """Constructor

        zona - Zona analizada
        """
        HistoBase.__init__(self, edificio, planta, zona)
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
        if self.modo == 'zona' and self.zona:
            barras(_min, _max,
                   self.edificio.plantas[self.planta][self.zona].calefaccion_meses,
                   self.edificio.plantas[self.planta][self.zona].refrigeracion_meses)
        elif self.modo == 'edificio' and self.edificio:
            barras(_min, _max,
                   self.edificio.calefaccion_meses,
                   self.edificio.refrigeracion_meses)
        elif self.modo == 'planta':
            #TODO: mover lógica de plantas a clases base (EdificioLIDER)
            #cal_planta = numpy.array([0.0] * 12)
            ref_planta = numpy.array([0.0] * 12)
            planta = self.edificio.plantas[self.planta]
            cal_planta = planta.calefaccion_meses
            supplanta = planta.superficie
            for nzona in planta:
                zona = planta[nzona]
                #cal_planta += numpy.array(zona.calefaccion_meses) * zona.superficie
                ref_planta += numpy.array(zona.refrigeracion_meses) * zona.superficie
            #cal_planta /= supplanta
            ref_planta /= supplanta
            barras(_min, _max, cal_planta, ref_planta)

class HistoElementos(HistoBase):
    """Histograma de demandas por elementos

    Dibuja un histograma de demandas de una zona por elementos
    """
    __gtype_name__ = 'HistoElementos'

    def __init__(self, edificio=None, planta=None, zona=None):
        """Constructor

        zona - Zona analizada
        """
        HistoBase.__init__(self, edificio, planta, zona)
        self._modo = 'edificio'

        self.title = u"Demandas por elemento"
        self.xlabel = u"Elemento"
        self.ylabel = u"Demanda [kWh/m²mes]"

    def minmaxplanta(self):
        """Mínimo y máximo de la escala vertical para todas las zonas de una planta"""
        pmin, pmax = [], []
        zonas = self.edificio.plantas[self.planta]
        for nzona in zonas:
            zona = zonas[nzona]
            x_names = zona.flujos.keys()
            pmin.append(myround(min(min(zona.flujos[name].values()) for zona in self.edificio.zonas for name in x_names), 10))
            pmax.append(myround(max(max(zona.flujos[name].values()) for zona in self.edificio.zonas for name in x_names), 10))
        return min(pmin), max(pmax)

    def dibujaseries(self, ax1):
        """Representa histograma de demanda por elemento

        El eje horizontal representa los elementos y el eje vertical la
        demanda existente [kWh/m²año]
        """
        #TODO: Comprobar si la demanda es anual

        def barras(min, max, calpos, calneg, calnet, refpos, refneg, refnet):
            w = 1.0 / 6
            rectsc1 = ax1.bar(ind + 0.5*w, calpos, w, align='center', fc='#FFBBFF', ec='0.5')
            rectsc2 = ax1.bar(ind + 1.5*w, calneg, w, align='center', fc='#FF6666', ec='0.5')
            rectsc3 = ax1.bar(ind + 2.5*w, calnet, w, align='center', fc='#FF0000', ec='k')
            rectsr1 = ax1.bar(ind + 3.5*w, refpos, w, align='center', fc='#6666FF', ec='0.5')
            rectsr2 = ax1.bar(ind + 4.5*w, refneg, w, align='center', fc='#B3FFB3', ec='0.5')
            rectsr3 = ax1.bar(ind + 5.5*w, refnet, w, align='center', fc='#0000FF', ec='k')
            leg = ax1.legend((rectsc1[0], rectsc2[0], rectsc3[0], rectsr1[0], rectsr2[0], rectsr3[0]),
                             ('Calefacción +', 'Calefacción -', 'Calefacción', 'Refrigeración +', 'Refrigeración -', 'Refrigeración'),
                             loc='lower left', prop={"size":'small'}, fancybox=True)
            leg.draw_frame(False)
            leg.get_frame().set_alpha(0.5) # transparencia de la leyenda
            ax1.set_ylim(min - 10, max + 10)
            ax1.set_xlim(0, ind[-1] + 6 * w) # mismo ancho aunque los extremos valgan cero
#            self.autolabel(ax1, rectsc1)
#            self.autolabel(ax1, rectsc2)
            self.autolabel(ax1, rectsc3)
#            self.autolabel(ax1, rectsr1)
#            self.autolabel(ax1, rectsr2)
            self.autolabel(ax1, rectsr3)

        # Demandas
        if self.modo == 'zona' and self.zona:
            # Datos meses
            zona = self.edificio.plantas[self.planta][self.zona]
            x_names = zona.flujos.keys()
            x_labels = ["\n".join(name.split()) for name in x_names]
            ind = numpy.arange(len(x_names))
            ax1.set_xticks(ind)
            #plt.xticks(ind + 0.5, ind)
            ax1.set_xticklabels(x_labels, size='small', rotation=45, ha='right')
            _min, _max = self.minmaxplanta()
            values = [zona.flujos[name].values() for name in x_names]
            calpos, calneg, calnet, refpos, refneg, refnet = zip(*values)
            barras(_min, _max, calpos, calneg, calnet, refpos, refneg, refnet)
            self.fig.subplots_adjust(bottom=0.17, left=.15)
        elif self.modo == 'edificio' and self.edificio:
            #TODO: demandas por elementos para edificio
            pass
        elif self.modo == 'planta':
            #TODO: demandas por elementos para planta
            pass


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