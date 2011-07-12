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
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo
from matplotlib.font_manager import FontProperties
from util import myround

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
         'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

class HistoCanvas(FigureCanvasGTKCairo):
    """Histograma de demandas mensuales

    Dibuja un histograma de demandas de una zona por meses
    """
    __gtype_name__ = 'HistoCanvas'

    def __init__(self, edificio=None, zona=None):
        """Constructor

        zona - Zona analizada
        """
        self.edificio = edificio
        self._zona = zona
        self._modo = 'edificio'
        self.fig = Figure()
        FigureCanvasGTKCairo.__init__(self, self.fig)
        self.fig.set_facecolor('w')
        self.ax1 = self.fig.add_subplot(111)

    @property
    def modo(self):
        return self._modo

    @modo.setter
    def modo(self, val):
        if self._modo != val:
            self._modo = val
            self.dibuja()

    @property
    def zona(self):
        return self._zona

    @zona.setter
    def zona(self, val):
        self._zona = val
        self.dibuja()

    def dibuja(self, width=400, height=200):
        """Representa histograma de demanda mensual para una zona

        Se incluye la demanda de calefacción y refrigeración.

        El eje horizontal representa los periodos [meses] y el eje vertical la
        demanda existente [kWh/m²mes]
        """

        def autolabel(ax, rects):
            """Etiquetar valores fuera de las barras"""
            #TODO: usar altura de texto en lugar de displacement
            # ver http://matplotlib.sourceforge.net/faq/howto_faq.html
            # Automatically make room for tick labels
#            text = ax.text(0,0, "1", size='small')
#            text.draw()
#            bb = text.get_window_extent()
#            print bb.width, bb.height
            texth = 2.0
            for rect in rects:
                height = rect.get_height()
                if height:
                    # rect.get_y() es la base del rectángulo y es 0 si es positivo
                    _h = -(height + texth + 0.5) if rect.get_y() else (height + 0.5)
                    ax.text(rect.get_x() + rect.get_width() / 2.0,
                            _h, '%.1f' % round(height, 1),
                            ha='center', va='bottom', size='small')

        def barras(min, max, seriec, serier):
            w = 1.0
            rects1 = ax1.bar(ind, seriec, w, align='center', fc='r', ec='k')
            rects2 = ax1.bar(ind, serier, w, align='center', fc='b', ec='k')
            ax1.legend((rects1[0], rects2[0]), ('Calefacción', 'Refrigeración'),
                       loc='lower right', prop=FontProperties(size='small'))
            ax1.set_ylim(min - 10, max + 10)
            autolabel(ax1, rects1)
            autolabel(ax1, rects2)

        # Elementos generales
        ax1 = self.ax1
        ax1.clear() # Limpia imagen de datos anteriores
        ax1.set_title(u"Demanda mensual", size='large')
        ax1.set_xlabel(u"Periodo")
        ax1.set_ylabel(u"Demanda [kWh/m²mes]", fontdict=dict(color='b'))
        ind = numpy.arange(12)
        x_names = [mes[:3] for mes in MESES]
        ax1.set_xticks(ind)
        ax1.set_xticklabels(x_names, size='small', rotation=90)

        # Demandas
        if self.modo == 'zona' and self.zona:
            """Dibuja las barras correspondientes a la demanda de una zona"""
            _min = myround(min(min(zona.calefaccion_meses) for zona in self.edificio.zonas), 5)
            _max = myround(max(max(zona.refrigeracion_meses) for zona in self.edificio.zonas), 5)
            barras(_min, _max,
                   self.zona.calefaccion_meses,
                   self.zona.refrigeracion_meses)
        elif self.modo == 'edificio' and self.edificio:
            """Dibuja las barras correspondientes a la demanda global del edificio"""
            _min = myround(min(self.edificio.calefaccion_meses), 5)
            _max = myround(max(self.edificio.refrigeracion_meses), 5)
            barras(_min, _max,
                   self.edificio.calefaccion_meses,
                   self.edificio.refrigeracion_meses)
        elif self.modo == 'planta':
            # ¿representa la suma de los espacios de las planta?
            pass

        # Tamaño
        self.set_size_request(width, height)
        self.draw()

    def pixbuf(self, destwidth=600):
        """Obtén un pixbuf a partir del canvas actual"""
        return get_pixbuf_from_canvas(self, destwidth)

    def save(self, filename='condensacionesplot.png'):
        """Guardar y mostrar gráfica"""
        self.fig.savefig(filename)


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