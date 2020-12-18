#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   widgets.py
#   Programa Visor para el Sistema de Observación de LIDER
#
#   Copyright (C) 2014-15 Rafael Villar Burke <pachi@rvburke.com>
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
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('GTK3Cairo')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo
from matplotlib.transforms import offset_copy
from .observer import Observer

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
         'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


def myround(x, base=5):
    """Redondea al valor más próximo a base"""
    return int(base * round(float(x)/base))


class PieGlobal(FigureCanvasGTK3Cairo, Observer):
    """Gráfico circular de Matplotlib

    Representa el balance neto de energía para cada componente del edificio.
    Se representan ganancias o pérdidas de calor para las temporadas de
    calefacción o refrigeración.
    """
    __gtype_name__ = 'PieChart'

    def __init__(self, tipodemanda='cal+', modelo=None):
        """Constructor

        edificio - Edificio analizado (EdificioLIDER)
        planta - Nombre de la planta "actual" analizada en el edificio (str)
        zona - Nombre de la Zona "actual" analizada en la planta (str)
        """
        Observer.__init__(self, modelo)

        self.tipodemanda = tipodemanda
        self.needsredraw = False

        self._titles = {'cal+': u'Periodo de calefacción. Ganancias térmicas',
                        'cal-': u'Periodo de calefacción. Pérdidas térmicas',
                        'ref+': u'Periodo de refrigeración. Ganancias térmicas',
                        'ref-': u'Periodo de refrigeración. Pérdidas térmicas'}

        self.fig = Figure()
        self.fig.add_subplot(aspect='equal')
        FigureCanvasGTK3Cairo.__init__(self, self.fig)

    def colors(self, nelems):
        """Devuelve lista de colores en un rango"""
        sign = -1 if self.tipodemanda.endswith('-') else 1
        step = int(255 / nelems) * sign
        aa, bb, cc = (255, 0, 0) if self.tipodemanda.startswith('cal') else (0, 0, 255)
        colorlist = ['#%02x%02x%02x' % (aa, (bb + i*step) % 256, cc) for i in range(nelems)]
        return colorlist

    def dibujaseries(self):
        """Dibuja series de datos"""

        # demandas y grupos, excluido el grupo 'TOTAL'
        demandas = self.model.activo.demandas[self.tipodemanda][:-1]
        grupos = self.model.edificio.gruposlider[:-1] # Quitamos TOTAL
        self.fig.clear()
        ax = self.fig.gca(aspect='equal')
        self.fig.text(0.5, 0.98,
                      (self._titles[self.tipodemanda] +
                       u'\nTotal: %4.1f kWh/m²año' % sum(demandas)),
                      size='medium', ha='center', va='top')

        # No damos esta información en modo componente
        if self.model.modo == 'componente':
            ax.axis('off')
            ax.annotate(u"Información no disponible para componentes",
                        (0.5, 0.5), xycoords='axes fraction', ha='center')
            return

        # Genera etiquetas y valores (absolutos) de demanda
        labels, values = [], []
        for demanda, grupo in sorted(zip(demandas, grupos)):
            demanda = demanda if demanda else 0.0
            labels.append(u"\n".join(grupo.split()) + u"\n(%4.1f kWh/m²año)" % demanda)
            values.append(abs(demanda))

        # Genera colores de sectores (cuenta valores significativos)
        colors = self.colors(sum(1 for value in values if value >= 0.1))

        if not any(values):
            ax.axis('off')
            ax.annotate(u"La demanda es nula",
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

    def do_draw(self, cr):
        if not self.needsredraw:
            return False
        self.needsredraw = False
        self.dibujaseries()
        self.draw()
        return False

    def update(self, subject, **kwargs):
        if kwargs.get('label', None) in ['index']:
            self.needsredraw = True
        else:
            self.needsredraw = False
        self.queue_draw()

    def save(self, filename='piechart.png', dpi=100):
        """Guardar y mostrar gráfica"""
        self.fig.canvas.print_figure(filename,
                                     format='png',
                                     facecolor='w',
                                     dpi=dpi)

class HistoBase(FigureCanvasGTK3Cairo, Observer):
    """Histograma de Matplotlib"""
    __gtype_name__ = 'HistoBase'

    def __init__(self, modelo=None):
        """Constructor

        edificio - Edificio analizado (EdificioLIDER)
        planta - Nombre de la planta "actual" analizada en el edificio (str)
        zona - Nombre de la Zona "actual" analizada en la planta (str)
        """
        Observer.__init__(self, modelo)

        self.fig = Figure()
        FigureCanvasGTK3Cairo.__init__(self, self.fig)
        self.ax1 = self.fig.add_subplot(111)
        self.title = ''
        self.xlabel = ''
        self.ylabel = ''
        self.needsredraw = False

        # Tamaños de letra y transformaciones para etiquetas de barras
        fontsize = matplotlib.rcParams['font.size']
        labelscale = 0.7
        self.labelfs = fontsize * labelscale
        labeloffset = fontsize * (1.0 - labelscale)

        self.trneg = offset_copy(self.ax1.transData, fig=self.fig,
                                 x=0, y=-fontsize, units='points')
        self.trpos = offset_copy(self.ax1.transData, fig=self.fig,
                                 x=0, y=labeloffset, units='points')

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

    def do_draw(self, cr):
        if not self.needsredraw:
            return False
        self.needsredraw = False
        ax1 = self.ax1
        ax1.clear() # Limpia imagen de datos anteriores
        ax1.grid(True)
        ax1.set_title(self.title, size='large')
        ax1.set_xlabel(self.xlabel, fontdict=dict(color='0.5'))
        ax1.set_ylabel(self.ylabel, fontdict=dict(color='0.5'))
        self.dibujaseries(ax1)
        self.draw()
        return False

    # ver si dibuja pasa a ser esto
    def update(self, subject, **kwargs):
        if kwargs.get('label', None) in ['grupos', 'index']:
            self.needsredraw = True
        else:
            self.needsredraw = False
        self.queue_draw()

    def dibujaseries(self, ax):
        """Dibuja series de datos"""
        pass

    def save(self, filename='histobase.png', dpi=100):
        """Guardar y mostrar gráfica"""
        self.fig.canvas.print_figure(filename,
                                     format='png',
                                     facecolor='w',
                                     dpi=dpi)

class HistoMeses(HistoBase):
    """Histograma de demandas mensuales

    Dibuja un histograma de demandas de una zona por meses
    """
    __gtype_name__ = 'HistoMeses'

    def __init__(self, modelo=None):
        """Constructor

        zona - Zona analizada
        """
        HistoBase.__init__(self, modelo)

        self.title = u"Demanda neta mensual"
        self.xlabel = u"Periodo"
        self.ylabel = u"Demanda [kWh/m²mes]"

    def dibujaseries(self, ax1):
        """Representa histograma de demanda mensual para una zona

        Se incluye la demanda de calefacción y refrigeración.

        El eje horizontal representa los periodos [meses] y el eje vertical la
        demanda existente [kWh/m²mes]
        """
        # No damos esta información en modo componente
        if self.model.modo == 'componente':
            ax1.axis('off')
            ax1.annotate(u"Información no disponible para componentes",
                         (0.5, 0.5), xycoords='axes fraction', ha='center')
            return
        # Meses como etiquetas y localizamos los valores límite
        ind = np.arange(12)
        x_names = [mes[:3] for mes in MESES]
        ax1.set_xticks(ind)
        ax1.set_xticklabels(x_names, size='small', rotation=90)
        # Seleccionamos las demandas y dibujamos los rectángulos
        obj = self.model.activo
        rects1 = ax1.bar(ind, obj.calefaccion_meses, 1.0, align='center', fc='r', ec='k')
        rects2 = ax1.bar(ind, obj.refrigeracion_meses, 1.0, align='center', fc='b', ec='k')
        leg = ax1.legend((rects1[0], rects2[0]),
                         (u'Calefacción', u'Refrigeración'),
                         loc='lower left', prop={"size":'small'}, fancybox=True)
        leg.draw_frame(False)
        leg.get_frame().set_alpha(0.5)
        _min, _max = self.model.edificio.minmaxmeses()
        _min, _max = myround(_min, 5), myround(_max, 5)
        ax1.set_ylim(_min - 10, _max + 10)
        self.autolabel(ax1, rects1)
        self.autolabel(ax1, rects2)

    def save(self, filename='meseschart.png', dpi=100):
        """Guardar y mostrar gráfica"""
        self.fig.canvas.print_figure(filename,
                                     format='png',
                                     facecolor='w',
                                     dpi=dpi)

class HistoElementos(HistoBase):
    """Histograma de demandas netas o separadas por componentes de la demanda

    Dibuja un histograma de demandas de una zona por componentes
    """
    __gtype_name__ = 'HistoElementos'

    def __init__(self, modelo=None):
        """Constructor

        zona - Zona analizada
        """
        HistoBase.__init__(self, modelo)

        self.title = u"Demandas por componente"
        self.xlabel = u"Componente"
        self.ylabel = u"Demanda [kWh/m²·año]"
        # Muestra o no los distintos desgloses de calefacción y refrigeración
        self._showelems = (False, False, False, False)

    @property
    def showelems(self):
        return self._showelems

    @showelems.setter
    def showelems(self, value):
        if value != self._showelems:
            self._showelems = value
            self.model.notify(label='grupos')

    def dibujaseries(self, ax1):
        """Representa histograma de demanda por elemento

        El eje horizontal representa los elementos y el eje vertical la
        demanda existente [kWh/m²año]
        """
        def barras(demandas):
            """Dibuja las barras de demanda para las series activas"""
            showcalpos, showcalneg, showrefpos, showrefneg = self.showelems
            seriesall = []
            if showcalpos:
                seriesall.append((demandas.get('cal+', []), '#FFBBFF', '0.5', u'Calefacción +'))
            if showcalneg:
                seriesall.append((demandas.get('cal-', []), '#FF6666', '0.5', u'Calefacción -'))
            seriesall.append((demandas.get('cal', []), '#FF0000', 'k', u'Calefacción'))
            if showrefpos:
                seriesall.append((demandas.get('ref+', []), '#6666FF', '0.5', u'Refrigeración +'))
            if showrefneg:
                seriesall.append((demandas.get('ref-', []), '#B3FFB3', '0.5', u'Refrigeración -'))
            seriesall.append((demandas.get('ref', []), '#0000FF', 'k', u'Refrigeración'))

            active = len(seriesall) # total active series
            w = 1.0 / active # width of each active serie

            seriesd = []
            labelsd = []

            for ii, (serie, fc, ec, label) in enumerate(seriesall):
                rects = ax1.bar(ind+(ii+0.5)*w, serie, w, align='center', fc=fc, ec=ec)
                seriesd.append(rects[0])
                labelsd.append(label)
                if label == u'Calefacción' or label == u'Refrigeración':
                    self.autolabel(ax1, rects)

            leg = ax1.legend(seriesd, labelsd, loc='lower left',
                             prop={"size":'small'}, fancybox=True)
            leg.draw_frame(False)
            leg.get_frame().set_alpha(0.5) # transparencia de la leyenda
            if self.model.config['autolimits']:
                mind, maxd = self.model.edificio.minmaxgrupos()
                mind, maxd = myround(mind, 10) - 10, myround(maxd, 10) + 10
            else:
                mind = self.model.config['minlimit']
                maxd = self.model.config['maxlimit']
            ax1.set_ylim(mind, maxd)
            ax1.set_xlim(0, ind[-1] + active * w) # mismo ancho aunque los extremos valgan cero

        # Flujos por elementos
        obj = self.model.activo
        demandas = obj.demandas
        x_labels = [u"\n".join(name.split()) for name in obj.demandas['grupos']]
        labelrotation = 0 if self.model.modo == 'componente' else 90
        ind = np.arange(len(x_labels))
        barras(demandas)
        ax1.set_xticks(ind + 0.5)
        ax1.set_xticklabels(x_labels, size='small',
                            rotation=labelrotation, ha='center')
        ymin, ymax = ax1.get_ylim()
        ax1.vlines(ind, ymin, ymax, color='gray')
        ax1.grid(False)
        self.fig.subplots_adjust(bottom=0.17, left=.15)

class ZonasGraph(FigureCanvasGTK3Cairo, Observer):
    """Gráficas de zonas con Matplotlib"""
    __gtype_name__ = 'ZonasGraph'

    def __init__(self, modelo=None):
        """Constructor

        edificio - Edificio analizado (EdificioLIDER)
        planta - Nombre de la planta "actual" analizada en el edificio (str)
        zona - Nombre de la Zona "actual" analizada en la planta (str)
        """
        Observer.__init__(self, modelo)

        self.fig = Figure()
        FigureCanvasGTK3Cairo.__init__(self, self.fig)
        self.ax1 = self.fig.add_subplot(311)
        self.ax2 = self.fig.add_subplot(312, sharex=self.ax1)
        self.ax3 = self.fig.add_subplot(313, sharex=self.ax1)
        self.ax4 = self.ax3.twinx()
        self.ax4.patch.set_visible(False)

        self.fig.suptitle(u'Valores diarios de zona', size='large')
        self.fig.subplots_adjust(left=0.15,
                                 #right=0.9,
                                 top=0.9, bottom=0.1,
                                 wspace=0.2, hspace=0.4)
        self.needsredraw = False

    def do_draw(self, cr):
        if not self.needsredraw:
            return False
        self.needsredraw = False
        self.dibujaseries()
        self.draw()
        return False

    # ver si dibuja pasa a ser esto
    def update(self, subject, **kwargs):
        if kwargs.get('label', None) in ['grupos', 'index']:
            self.needsredraw = True
        else:
            self.needsredraw = False
        self.queue_draw()

    def dibujaseries(self):
        """Dibuja series de datos"""
        ax1 = self.ax1
        ax2 = self.ax2
        ax3 = self.ax3
        ax4 = self.ax4

        #Limpia datos anteriores
        ax1.clear()
        ax2.clear()
        ax3.clear()
        ax4.clear()

        # No damos esta información en modo componente
        if self.model.modo in ['componente', 'planta', 'edificio']:
            for ax in [ax1, ax2, ax3]:
                ax.axis('off')
                ax.annotate(u"Información solo disponible para zonas",
                            (0.5, 0.5), xycoords='axes fraction', ha='center')
            ax4.axis('off')
            return

        ax1.axis('on')
        ax2.axis('on')
        ax3.axis('on')
        ax4.axis('on')
        ax4.patch.set_visible(False)

        ax1.set_title(u'Temperatura diaria (máxima, media, mínima)', size='medium')
        ax2.set_title(u'Carga térmica diaria (sensible, latente, total)', size='medium')
        ax3.set_title(u'Caudal diario de ventilación e infiltraciones', size='medium')
        ax1.set_ylabel(u'Temperatura\n$T$, $T_{min}$, $T_{max}$\n[ºC]', fontdict=dict(alpha=0.75, size='small'))
        ax2.set_ylabel(u'Carga térmica\n$Q_S$, $Q_S + Q_L$\n[W]', fontdict=dict(alpha=0.75, size='small'))
        ax3.set_ylabel(u'Ventilación e infiltraciones\n[m3/h]', fontdict=dict(alpha=0.75, size='small'))
        ax4.set_ylabel(u'[ren/h]', fontdict=dict(alpha=0.75, size='small'))

        zidf, zcdf, zddf = self.model.bindata
        zonedf = zddf[zddf.Nombre == self.model.activo.nombre]
        zonedf.index = pd.date_range('1/1/2007', periods=8760,
                                     freq='H')
        tdmed = zonedf.Temp.resample('D').mean()
        tdmin = zonedf.Temp.resample('D').min()
        tdmax = zonedf.Temp.resample('D').max()

        #tdmed.plot(ax=ax1, color='black', lw=0.5)
        ax1.plot(tdmed.index, tdmed, color='black', lw=0.5)
        ax1.fill_between(tdmed.index, tdmed, tdmax, facecolor='red', alpha=.2)
        ax1.fill_between(tdmed.index, tdmin, tdmed, facecolor='blue', alpha=.2)
        mintemp = np.ceil(zddf.Temp.min()) -3
        maxtemp = np.floor(zddf.Temp.max()) + 3
        ax1.set_ylim(mintemp, maxtemp)

        #TODO: Ver cómo indicar zonas sobre y bajo consigna
        #TODO: o poner bandas de verano e invierno

        qldtot = zonedf.QLat.resample('D').sum() / 24.0
        qsdtot = zonedf.QSen.resample('D').sum() / 24.0
        qtot = (qldtot + qsdtot)

        #qsdtot.plot(ax=ax2, color='blue', lw=0.5)
        ax2.plot(qsdtot.index, qsdtot, color='blue', lw=0.5, alpha=0.5)

        #qtot.plot(ax=ax2, color='black', lw=0.5)
        ax2.plot(qtot.index, qtot, color='black', lw=0.5)
        ax2.fill_between(qsdtot.index, 0, qsdtot, facecolor='blue', alpha=.2)
        ax2.fill_between(qtot.index, qsdtot, qtot, facecolor='red', alpha=.2)

        ax1.get_xaxis().set_major_formatter(matplotlib.dates.DateFormatter('%b'))

        # 3600 s/h * 1.2922 kg/m3
        veninftot = zonedf.Vventinf.resample('D').mean() * 3600.0 / 1.225
        #veninftot = zonedf.Vventinf * 3600.0 / 1.225
        ax3.plot(veninftot.index, veninftot, color='black', lw=0.5)
        ax3.fill_between(veninftot.index, 0, veninftot, facecolor='cyan', alpha=.2)

        zoneinfo = zidf.loc[self.model.activo.nombre]
        zonevolume = zoneinfo.Volumen
        ax3.text(.05, .85,
                 u'Vol. zona = %.2f m3\n%.2f[ren/h]' % (zonevolume,
                                               zonedf.Vventinf.mean() * 3600.0 / 1.225 / zonevolume),
                 transform=ax3.transAxes, size='small', va='top')
        ymin, ymax = ax3.get_ylim()
        ax4.set_ylim(ymin/zonevolume, ymax/zonevolume)

    def save(self, filename='histobase.png', dpi=100):
        """Guardar y mostrar gráfica"""
        self.fig.canvas.print_figure(filename,
                                     format='png',
                                     facecolor='w',
                                     dpi=dpi)

