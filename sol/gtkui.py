#!/usr/bin/env python
#encoding: utf-8
#
#   gtkui.py
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
"""Interfaz de usuario de SOL en GTK+"""

# En zonas muestra histograma de flujos y componentes. Encabezado de totales
# en calef y refrig. También datos por meses (cal y ref)
# En plantas muestra totales por planta e histograma por zonas de cal y ref.

import os
import datetime
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
from widgets import HistoMeses, HistoElementos, PieGlobal, ZonasGraph
import sol
from solmodel import VISOLModel
import util

TESTFILE = util.get_resource('data/test.res')

if hasattr(GdkPixbuf.Pixbuf, 'new_from_file_utf8'):
    pixfromfile = GdkPixbuf.Pixbuf.new_from_file_utf8
else:
    pixfromfile = GdkPixbuf.Pixbuf.new_from_file

EDIFICIOICON = pixfromfile(util.get_resource('ui/edificioicono.png'))
PLANTAICON = pixfromfile(util.get_resource('ui/plantaicono.png'))
ZONAICON = pixfromfile(util.get_resource('ui/zonaicono.png'))
COMPONENTEICON = pixfromfile(util.get_resource('ui/componenteicono.png'))

class GtkSol(object):
    """Aplicación Visor de archivos de LIDER"""
    def __init__(self):
        """Inicialización de datos e interfaz"""
        self.model = VISOLModel()

        self.ui = Gtk.Builder()
        self.ui.add_from_file(util.get_resource('ui', 'sol.ui'))

        self.window = self.ui.get_object('window')
        self.sb = self.ui.get_object('statusbar')
        self.edificiots = self.ui.get_object('treestore')
        self.edificiotv = self.ui.get_object('treeview')
        self.tb = self.ui.get_object('textbuffer')
        self.nb = self.ui.get_object('notebook')
        self.ui.get_object('aboutdialog').set_version(sol.__version__)

        self.histoelementos = HistoElementos(modelo=self.model)
        vb = self.ui.get_object('belementos') #self.nb.get_nth_page(1)
        vb.pack_start(self.histoelementos, expand=True, fill=True, padding=0)

        self.histomeses = HistoMeses(modelo=self.model)
        vb = self.ui.get_object('bmeses')
        vb.pack_start(self.histomeses, expand=True, fill=True, padding=0)

        self.calposchart = PieGlobal(tipodemanda='cal+',
                                     modelo=self.model)
        vb = self.ui.get_object('bcalpos')
        vb.pack_start(self.calposchart, expand=True, fill=True, padding=0)

        self.calnegchart = PieGlobal(tipodemanda='cal-',
                                     modelo=self.model)
        vb = self.ui.get_object('bcalneg')
        vb.pack_start(self.calnegchart, expand=True, fill=True, padding=0)

        self.refposchart = PieGlobal(tipodemanda='ref+',
                                     modelo=self.model)
        vb = self.ui.get_object('brefpos')
        vb.pack_start(self.refposchart, expand=True, fill=True, padding=0)

        self.refnegchart = PieGlobal(tipodemanda='ref-',
                                     modelo=self.model)
        vb = self.ui.get_object('brefneg')
        vb.pack_start(self.refnegchart, expand=True, fill=True, padding=0)

        self.zonaschart = ZonasGraph(modelo=self.model)
        vb = self.ui.get_object('bzonas')
        vb.pack_start(self.zonaschart, expand=True, fill=True, padding=0)

        # Filtro de archivos
        ffilter = self.ui.get_object('filefilter')
        ffilter.set_name('Archivos *.res, *.re2')
        ffilter.add_pattern('*.re[s|2]')

        self.ui.connect_signals(self)
        self.loadfile(TESTFILE)

    def loadfile(self, path=TESTFILE):
        """Carga archivo en el modelo y actualiza la interfaz"""
        try:
            self.model.file = path
            self.sb.push(0, u'Seleccionado archivo: %s' % self.model.file)

            e = self.model.edificio
            self.window.props.title = u"ViSOL [... %s]" % self.model.file[-40:]

            self.tb.set_text(e.resdata)
            ts = self.edificiots
            tv = self.edificiotv
            ts.clear()
            tv.collapse_all()
            # Modelo de plantas y zonas
            ed = e.nombre
            edificioiter = ts.append(None, (ed, 'edificio', ed, '', '', '', EDIFICIOICON))
            for planta in e:
                plantaiter = ts.append(edificioiter, (planta, 'planta', ed, planta, '', '', PLANTAICON))
                zonas = e[planta]
                for zona in zonas:
                    zonaiter = ts.append(plantaiter, (zona, 'zona', ed, planta, zona, '', ZONAICON))
                    tv.expand_to_path(ts.get_path(zonaiter))
                    for componente in zonas[zona]:
                        ts.append(zonaiter, (componente, 'componente', ed, planta, zona, componente, COMPONENTEICON))
            tv.set_cursor((0,)) # Seleccionar edificio

            self.sb.push(0, u'Cargado modelo: %s' % path)
        except:
            self.sb.push(0, u'Error al leer archivo: %s' % self.model.file)

    def showtextfile(self, button):
        """Cambia la visibilidad de la pestaña de texto"""
        if not button.props.active:
            self.ui.get_object('scrolledwindowtext').hide()
        else:
            self.ui.get_object('scrolledwindowtext').show()

    def guardarbutton(self, button):
        """Guarda imagen de la gráfica actual"""
        idx = self.nb.get_current_page()
        container = self.nb.get_nth_page(idx)
        out_dpi = self.model.config.get('out_dpi', 100)
        out_fmt = self.model.config.get('out_fmt', '%Y%m%d_%H%M%S')
        out_basename = self.model.config.get('out_basename', 'ViSol')
        for child in container.get_children():
            if child.__gtype_name__ in ['PieChart', 'HistoMeses', 'HistoElementos']:
                timestamp = datetime.datetime.now().strftime(out_fmt)
                filename = "%s-%s-%s.png" % (timestamp, out_basename, self.model.filename)
                pathname = os.path.join(self.model.dirname, filename)
                child.save(pathname, dpi=out_dpi)
                self.sb.push(0, u'Guardando captura de pantalla: %s' % pathname)
                break

    def cursorchanged(self, tv):
        """Seleccionada una nueva fila de la vista de árbol"""
        path, col = tv.get_cursor()
        if not path: # Al cargar archivos en un momento path es None
            return
        tm = tv.get_model()
        nombre, tipo, ed, pl, zn, comp = tuple(tm[path])[:6]
        self.model.index = (ed, pl, zn, comp)
        objeto = self.model.activo
        mul = getattr(objeto, 'multiplicador', 1)
        sup = getattr(objeto, 'superficie', None)
        cal = getattr(objeto, 'calefaccion', None)
        ref = getattr(objeto, 'refrigeracion', None)

        txt1 = u'<big><b>%s</b></big> (%s)\n' % (nombre, tipo.capitalize())
        if self.model.modo != 'componente':
            txt1 += u'<i>%d x %.2fm²</i>\n' % (mul, sup)
            txt1 += u'calefacción: %6.1f<i>kWh/m²año</i>, ' % cal
            txt1 += u'refrigeración: %6.1f<i>kWh/m²año</i>' % ref
        else:
            txt1 += u'\n'
        self.sb.push(0, u'Seleccionado %s: %s' % (tipo, nombre))
        self.ui.get_object('labelzona').props.label = txt1

    def cbelementos(self, action):
        """Modifica el número de flujos activos en la vista de elementos"""
        he = self.histoelementos
        he.showelems = (self.ui.get_object('cbcalpos').props.active,
                        self.ui.get_object('cbcalneg').props.active,
                        self.ui.get_object('cbrefpos').props.active,
                        self.ui.get_object('cbrefneg').props.active)

    #{ Funciones generales de aplicación
    def openfile(self, toolbutton):
        """Abre archivo de resultados"""
        chooser = self.ui.get_object('filechooserdialog')
        chooser.set_filename(self.model.file)
        response = chooser.run()

        if response == Gtk.ResponseType.ACCEPT:
            self.loadfile(chooser.get_filename().decode('utf8'))
        elif response == Gtk.ResponseType.CANCEL:
            self.sb.push(0, u'Carga de archivo cancelada')
        chooser.hide()

    def about(self, toolbutton):
        """Diálogo de créditos"""
        about = self.ui.get_object('aboutdialog')
        about.run()
        about.hide()

    def quit(self, w, *args):
        """Salir de la aplicación"""
        Gtk.main_quit()

    def main(self):
        """Arranca la aplicación"""
        self.ui.get_object('window').show_all()
        Gtk.main()
