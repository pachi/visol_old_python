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

import math
import gtk
import numpy
import matplotlib
matplotlib.use('GTKCairo')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo
from matplotlib.transforms import offset_copy
from util import myround

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
         'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

class PieGlobal(FigureCanvasGTKCairo):
    """Gráfico circular de Matplotlib

    Representa el balance neto de energía para cada componente del edificio.
    Se representan ganancias o pérdidas de calor para las temporadas de
    calefacción o refrigeración.
    """
    __gtype_name__ = 'PieChart'

    def __init__(self, edificio=None, planta=None, zona=None, componente=None,
                 tipodemanda='cal+'):
        """Constructor

        edificio - Edificio analizado (EdificioLIDER)
        planta - Nombre de la planta "actual" analizada en el edificio (str)
        zona - Nombre de la Zona "actual" analizada en la planta (str)
        """
        self.edificio = edificio
        self.planta = planta
        self.zona = zona
        self.componente = componente
        self._modo = 'edificio'
        self.tipodemanda = tipodemanda

        self._titles = {'cal+': 'Periodo de calefacción. Ganancias térmicas',
                        'cal-': 'Periodo de calefacción. Pérdidas térmicas',
                        'ref+': 'Periodo de refrigeración. Ganancias térmicas',
                        'ref-': 'Periodo de refrigeración. Pérdidas térmicas'}

        #self.title = self._titles[tipodemanda]
        self.fig, _axes = plt.subplots(1, 1,
                                           subplot_kw={'aspect':'equal'},
                                           facecolor='w')
        FigureCanvasGTKCairo.__init__(self, self.fig)

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

    @property
    def demandas(self):
        """Demandas según el modo activo"""
        edificio = self.edificio
        if self.modo == 'edificio' and edificio is not None:
            demandas = edificio.demandas
        elif self.modo == 'planta':
            demandas = edificio[self.planta].demandas
        elif self.modo == 'zona' and self.zona is not None:
            demandas = edificio[self.planta][self.zona].demandas
        elif self.modo == 'componente':
            componente = edificio[self.planta][self.zona][self.componente]
            demandas = {'cal':[componente.calnet, ''],
                        'ref':[componente.refnet, ''],
                        'cal+':[componente.calpos, ''],
                        'cal-':[componente.calneg, ''],
                        'ref+':[componente.refpos, ''],
                        'ref-':[componente.refneg, '']}
        else:
            raise NameError("Modo de operación inesperado: %s" % self.modo)
        return demandas

    def colors(self, nelems, base=(255, 0, 0), reverse=False):
        """Devuelve lista de colores en un rango"""
        step = int(255 / nelems)
        step = -step if reverse else step
        aa, bb, cc = base
        colorlist = ['#%02x%02x%02x' % (aa, (bb + i*step) % 256, cc) for i in range(nelems)]
        return colorlist

    def dibujaseries(self):
        """Dibuja series de datos"""

        # demandas y grupos, excluido el grupo 'TOTAL'
        demandas = self.demandas[self.tipodemanda][:-1]
        grupos = self.edificio.grupos[:-1]
        total = sum(demandas)
        titletext = (self._titles[self.tipodemanda] +
                     u'\nTotal: %4.1f kWh/m²año' % total)

        self.fig.clear()
        ax = self.fig.gca(aspect='equal')
        self.fig.text(0.5, 0.98, titletext,
                      size='medium', ha='center', va='top')

        # No damos esta información en modo componente
        if self.modo == 'componente':
            ax.axis('off')
            ax.annotate("Información no disponible para componentes",
                        (0.5, 0.5), xycoords='axes fraction', ha='center')
            return

        # Genera etiquetas y valores (absolutos) de demanda
        labels, values = [], []
        for demanda, grupo in sorted(zip(demandas, grupos)):
            demanda = demanda if demanda else 0.0
            labels.append("\n".join(grupo.split()) + "\n(%4.1f kWh/m²año)" % demanda)
            values.append(abs(demanda))

        # Genera colores de sectores (cuenta valores significativos)
        ncolors = sum(1 for value in values if value>=0.1)
        base = (255, 0, 0) if self.tipodemanda.startswith('cal') else (0, 0, 255)
        reverse = self.tipodemanda.endswith('-')
        colors = self.colors(ncolors, base, reverse)

        if not any(values):
            ax.axis('off')
            ax.annotate("La demanda es nula",
                        (0.5, 0.5), xycoords='axes fraction', ha='center')
            return

        patches, _texts, autotexts = ax.pie(values, colors=colors,
                                            autopct="%1.1f%%", shadow =False)
        # Reduce algo la escala de las etiquetas
        for text in autotexts:
            size = text.get_size()
            text.set_fontsize(size*0.8)

        # Posicionado inicial de textos y flechas
        data = []
        for patch, label, value in zip(patches, labels, values):
            #Dibuja etiquetas para el conjunto de sectores circulares
            rr = patch.r # radio del sector
            dr = rr*0.1  # separación con el sector
            t1, t2 = patch.theta1, patch.theta2 # ángulos inicial y final del sector
            theta = (t1+t2)/2.

            # Coordenadas inciales del texto, usando un círculo concéntrico
            x1, y1 = (rr+dr)*math.cos(theta/180.*math.pi), (rr+dr)*math.sin(theta/180.*math.pi)
            # Revisión de la posición x y alineación del texto, fijos para cada lado
            if x1 > 0 : # etiquetas a la derecha
                x1 = rr + 2*dr
                ha = "left"
            else: # etiquetas a la izquierda
                x1 = -(rr + 2*dr)
                ha = "right"

            # Coordenadas de la punta de la flecha apuntando al patch
            # En los elementos de arriba y abajo bajamos las flechas un poco
            if 30 < theta < 90:
                ang = t1 + (t2 - t1) / 5.0
            elif 90 < theta < 150:
                ang = t1 + 4.0 * (t2 - t1) / 5.0
            elif 210 < theta < 270:
                ang = t1 + (t2 - t1) / 5.0
            elif 270 < theta < 330:
                ang = t1 + 4.0 * (t2 - t1) / 5.0
            else:
                ang = theta
            xc, yc = 1.02 * rr/1.*math.cos(ang/180.*math.pi), 1.02 * rr/1.*math.sin(ang/180.*math.pi)

            # Omitimos las demandas muy pequeñas (abs(demanda) < 0.1)
            if value >= 0.1:
                data.append([label, (xc, yc), [x1, y1], ha, patch])

        # Recálculo de posición y de los textos de las anotaciones para evitar solapes.
        # Posición y de los textos a la izquierda
        leftdata = [[datum[2][1], datum] for datum in data if datum[3] == 'right']
        lnl = len(leftdata)
        lstep = min(1.8 / (lnl - 1), 0.5) if lnl > 1 else 0.5
        ylmin = 0 - lstep * int(lnl / 2)
        for i, (yval, datum) in enumerate(sorted(leftdata)):
            datum[2][1] = ylmin + i*lstep
        # Posición y de los textos a la derecha
        rightdata = [[datum[2][1], datum] for datum in data if datum[3] == 'left']
        lnr = len(rightdata)
        rstep = min(1.8 / (lnr - 1), 0.5) if lnr > 1 else 0.5
        yrmin = 0 - rstep * int(lnr / 2)
        for i, (yval, datum) in enumerate(sorted(rightdata)):
            datum[2][1] = yrmin + i*rstep

        # Finalmente dibujamos las anotaciones: textos y flechas
        # Origen en el texto (A) y destino en el patch (B)
        for (label, xypatch, xytext, ha, patch) in data:
            ax.annotate(label,
                        xypatch, xycoords="data", size='small',
                        xytext=xytext, textcoords="data", ha=ha, va='center',
                        arrowprops=dict(arrowstyle="-",
                                        facecolor='0.7',
                                        edgecolor='0.7',
                                        relpos=(0.0 if ha=='left' else 1.0, 0.5),
                                        patchB=patch))

    def dibuja(self, width=400, height=200):
        """Dibuja elementos generales de la gráfica"""
        self.dibujaseries()
        self.set_size_request(width, height)
        self.draw()

    def pixbuf(self, destwidth=600):
        """Obtén un pixbuf a partir del canvas actual"""
        return get_pixbuf_from_canvas(self, destwidth)

    def save(self, filename='condensacionesplot.png'):
        """Guardar y mostrar gráfica"""
        self.fig.savefig(filename)

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
        self.title = ''
        self.xlabel = ''
        self.ylabel = ''

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
        """Dibuja series de datos"""
        pass

    def dibuja(self, width=400, height=200):
        """Dibuja elementos generales de la gráfica"""
        ax1 = self.ax1
        ax1.clear() # Limpia imagen de datos anteriores
        ax1.grid(True)
        ax1.set_title(self.title, size='large')
        ax1.set_xlabel(self.xlabel, fontdict=dict(color='0.5'))
        ax1.set_ylabel(self.ylabel, fontdict=dict(color='0.5'))

        self.dibujaseries(ax1)

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

        self.title = u"Demanda neta mensual"
        self.xlabel = u"Periodo"
        self.ylabel = u"Demanda [kWh/m²mes]"

    def dibujaseries(self, ax1):
        """Representa histograma de demanda mensual para una zona

        Se incluye la demanda de calefacción y refrigeración.

        El eje horizontal representa los periodos [meses] y el eje vertical la
        demanda existente [kWh/m²mes]
        """
        # Meses como etiquetas y localizamos los valores límite
        ind = numpy.arange(12)
        x_names = [mes[:3] for mes in MESES]
        ax1.set_xticks(ind)
        ax1.set_xticklabels(x_names, size='small', rotation=90)
        # Seleccionamos las demandas
        if self.modo == 'edificio' and self.edificio is not None:
            e = self.edificio
            seriecal, serieref = e.calefaccion_meses, e.refrigeracion_meses
        elif self.modo == 'planta':
            pl = self.edificio[self.planta]
            seriecal, serieref = pl.calefaccion_meses, pl.refrigeracion_meses
        elif self.modo == 'zona' and self.zona:
            zona = self.edificio[self.planta][self.zona]
            seriecal, serieref = zona.calefaccion_meses, zona.refrigeracion_meses
        else:
            seriecal, serieref = [], []
        # Dibujamos los rectángulos
        rects1 = ax1.bar(ind, seriecal, 1.0, align='center', fc='r', ec='k')
        rects2 = ax1.bar(ind, serieref, 1.0, align='center', fc='b', ec='k')
        leg = ax1.legend((rects1[0], rects2[0]),
                         ('Calefacción', 'Refrigeración'),
                         loc='lower left', prop={"size":'small'}, fancybox=True)
        leg.draw_frame(False)
        leg.get_frame().set_alpha(0.5)
        _min, _max = self.edificio.minmaxdemandas()
        _min, _max = myround(_min, 5), myround(_max, 5)
        ax1.set_ylim(_min - 10, _max + 10)
        self.autolabel(ax1, rects1)
        self.autolabel(ax1, rects2)


class HistoElementos(HistoBase):
    """Histograma de demandas netas o separadas por elementos

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

    def dibujaseries(self, ax1):
        """Representa histograma de demanda por elemento

        El eje horizontal representa los elementos y el eje vertical la
        demanda existente [kWh/m²año]
        """
        def barras(demandas):
            """Dibuja las barras de demanda para las series activas"""
            seriesall = []
            if self.showcalpos:
                seriesall.append((demandas.get('cal+', []), '#FFBBFF', '0.5', 'Calefacción +'))
            if self.showcalneg:
                seriesall.append((demandas.get('cal-', []), '#FF6666', '0.5', 'Calefacción -'))
            seriesall.append((demandas.get('cal', []), '#FF0000', 'k', 'Calefacción'))
            if self.showrefpos:
                seriesall.append((demandas.get('ref+', []), '#6666FF', '0.5', 'Refrigeración +'))
            if self.showrefneg:
                seriesall.append((demandas.get('ref-', []), '#B3FFB3', '0.5', 'Refrigeración -'))
            seriesall.append((demandas.get('ref', []), '#0000FF', 'k', 'Refrigeración'))

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
            mind, maxd = self.edificio.minmaxflujoszonas()
            mind, maxd = myround(mind, 10), myround(maxd, 10)
            ax1.set_ylim(mind - 10, maxd + 10)
            ax1.set_xlim(0, ind[-1] + active * w) # mismo ancho aunque los extremos valgan cero

        # Flujos por elementos
        edificio = self.edificio
        labelrotation = 90
        if self.modo == 'edificio' and edificio is not None:
            x_labels = ["\n".join(name.split()) for name in edificio.flujos]
            demandas = edificio.demandas
        elif self.modo == 'planta':
            planta = edificio[self.planta]
            x_labels = ["\n".join(name.split()) for name in planta.flujos]
            demandas = planta.demandas
        elif self.modo == 'zona' and self.zona is not None:
            zona = edificio[self.planta][self.zona]
            x_labels = ["\n".join(name.split()) for name in zona.flujos]
            demandas = zona.demandas
        elif self.modo == 'componente':
            labelrotation = 0
            flujos = edificio[self.planta][self.zona][self.componente]
            x_labels = [self.componente,]
            demandas = dict(zip(('cal+', 'cal-', 'cal', 'ref+', 'ref-', 'ref'), flujos))
        else:
            raise NameError("Modo de operación inesperado: %s" % self.modo)

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
