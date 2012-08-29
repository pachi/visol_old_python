#!/usr/bin/env python
#encoding: utf-8
#
#   gtkui.py
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
"""Interfaz de usuario de SOL en GTK+"""

# En zonas muestra histograma de flujos y componentes. Encabezado de totales
# en calef y refrig. También datos por meses (cal y ref)
# En plantas muestra totales por planta e histograma por zonas de cal y ref.

#import gobject
import gtk
import util, resparser
from widgets import HistoMeses, HistoElementos

TESTFILE = util.get_resource('data/test.res')
EDIFICIOICON = gtk.gdk.pixbuf_new_from_file(util.get_resource('ui/edificioicono.png'))
PLANTAICON = gtk.gdk.pixbuf_new_from_file(util.get_resource('ui/plantaicono.png'))
ZONAICON = gtk.gdk.pixbuf_new_from_file(util.get_resource('ui/zonaicono.png'))
COMPONENTEICON = gtk.gdk.pixbuf_new_from_file(util.get_resource('ui/componenteicono.png'))

class VISOLModel(object):
    """Modelo para la aplicación ViSOL"""
    def __init__(self, edificio=None):
        self.edificio = edificio
        self._file = None

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, value):
        if value != self.file:
            self._file = value
            self.edificio = resparser.loadfile(value)


class GtkSol(object):
    """Aplicación Visor de archivos de LIDER"""
    def __init__(self):
        """Inicialización de datos e interfaz"""
        self.model = VISOLModel()

        self.ui = gtk.Builder()
        self.ui.add_from_file(util.get_resource('ui', 'sol.ui'))

        self.window = self.ui.get_object('window')
        self.sb = self.ui.get_object('statusbar')
        self.edificiots = self.ui.get_object('treestore')
        self.edificiotv = self.ui.get_object('treeview')
        self.tb = self.ui.get_object('textbuffer')
        self.nb = self.ui.get_object('notebook')

        self.histomeses = HistoMeses()
        vb = self.ui.get_object('vbmeses')
        vb.pack_start(self.histomeses)

        self.histoelementos = HistoElementos()
        vb = self.ui.get_object('vbelementos') #self.nb.get_nth_page(1)
        vb.pack_start(self.histoelementos)

        # Filtro de archivos
        ffilter = self.ui.get_object('filefilter')
        ffilter.set_name('Archivos *.res')
        ffilter.add_pattern('*.res')

        self.ui.connect_signals(self)
        # Carga datos de materiales, cerramientos y clima
        self.loadfile(TESTFILE)

        self.edificiotv.set_cursor((0,))

    def loadfile(self, path=TESTFILE):
        """Carga archivo en el modelo y actualiza la interfaz"""
        self.model.file = path
        e = self.model.edificio
        self.tb.set_text(e.resdata)
        self.edificiots.clear()
        self.edificiotv.collapse_all()
        # Modelo de plantas y zonas
        ed = e.nombre
        edificioiter = self.edificiots.append(None, (ed, 'edificio', ed, '', '', '', EDIFICIOICON))
        for planta in e:
            plantaiter = self.edificiots.append(edificioiter, (planta, 'planta', ed, planta, '', '', PLANTAICON))
            zonas = e[planta]
            for zona in zonas:
                zonaiter = self.edificiots.append(plantaiter, (zona, 'zona', ed, planta, zona, '', ZONAICON))
                self.edificiotv.expand_to_path(self.edificiots.get_path(zonaiter))
                for componente in zonas[zona]:
                    self.edificiots.append(zonaiter, (componente, 'componente', ed, planta, zona, componente, COMPONENTEICON))
        self.histomeses.edificio = e
        self.histoelementos.edificio = e
        self.sb.push(0, u'Cargado modelo: %s' % path)

    def showtextfile(self, button):
        """Cambia la visibilidad de la pestaña de texto"""
        if not button.props.active:
            self.ui.get_object('scrolledwindowtext').hide()
        else:
            self.ui.get_object('scrolledwindowtext').show()

    def cursorchanged(self, tv):
        """Seleccionada una nueva fila de la vista de árbol"""
        path, col = tv.get_cursor()
        tm = tv.get_model()
        nombre, tipo, ed, pl, zn, comp, icon = tm[path]
        self.histomeses.data = (ed, pl, zn, comp)
        self.histoelementos.data = (ed, pl, zn, comp)
        if tipo == 'edificio':
            self.histomeses.modo = 'edificio'
            self.histoelementos.modo = 'edificio'
            objeto = self.model.edificio
            sup = u'<i>%.2fm²</i>\n' % objeto.superficie
            cal = u'calefacción: %6.1f<i>kWh/m²año</i>, ' % objeto.calefaccion
            ref = u'refrigeración: %6.1f<i>kWh/m²año</i>' % objeto.refrigeracion
        elif tipo == 'planta':
            self.histomeses.modo = 'planta'
            self.histoelementos.modo = 'planta'
            objeto = self.model.edificio[nombre]
            sup = u'<i>%.2fm²</i>\n' % objeto.superficie
            cal = u'calefacción: %6.1f<i>kWh/m²año</i>, ' % objeto.calefaccion
            ref = u'refrigeración: %6.1f<i>kWh/m²año</i>' % objeto.refrigeracion
        elif tipo == 'zona':
            self.histomeses.modo = 'zona'
            self.histoelementos.modo = 'zona'
            objeto = self.model.edificio[pl][zn]
            sup = u'<i>%d x %.2fm²</i>\n' % (objeto.multiplicador, objeto.superficie)
            cal = u'calefacción: %6.1f<i>kWh/m²año</i>, ' % objeto.calefaccion
            ref = u'refrigeración: %6.1f<i>kWh/m²año</i>' % objeto.refrigeracion
        elif tipo == 'componente':
            #self.histomeses.modo = 'componente'
            self.ui.get_object('vbmeses').hide()
            self.histoelementos.modo = 'componente'
            objeto = self.model.edificio[pl][zn][comp]
            sup = '\n'
            cal = u'calefacción: %6.1f<i>kWh/m²año</i>, ' % objeto[2]
            ref = u'refrigeración: %6.1f<i>kWh/m²año</i>' % objeto[5]
        else:
            raise ValueError("Tipo desconocido")
        
        if tipo != 'componente':
            self.ui.get_object('vbmeses').show()

        txt1 = u'<big><b>%s</b></big> (%s)\n' % (nombre, tipo.capitalize())
        txt1 += sup
        txt1 += cal
        txt1 += ref
        self.sb.push(0, u'Seleccionado %s: %s' % (tipo, nombre))
        self.ui.get_object('labelzona').props.label = txt1

    def cbelementos(self, action):
        """Modifica el número de flujos activos en la vista de elementos"""
        he = self.histoelementos
        he.showcalpos = self.ui.get_object('cbcalpos').props.active
        he.showcalneg = self.ui.get_object('cbcalneg').props.active
        he.showrefpos = self.ui.get_object('cbrefpos').props.active
        he.showrefneg = self.ui.get_object('cbrefneg').props.active
        he.dibuja()

    #{ Funciones generales de aplicación
    def openfile(self, toolbutton):
        """Abre archivo de resultados"""
        chooser = self.ui.get_object('filechooserdialog')
        chooser.set_filename(self.model.file)
        response = chooser.run()

        if response == gtk.RESPONSE_ACCEPT:
            self.loadfile(chooser.get_filename())
            self.sb.push(0, u'Seleccionado archivo: %s' % self.model.file)
        elif response == gtk.RESPONSE_CANCEL:
            self.sb.push(0, u'Carga de archivo cancelada')
        chooser.hide()

    def about(self, toolbutton):
        """Diálogo de créditos"""
        about = self.ui.get_object('aboutdialog')
        about.run()
        about.hide()

    def quit(self, w, *args):
        """Salir de la aplicación"""
        gtk.main_quit()

    def main(self):
        """Arranca la aplicación"""
        self.ui.get_object('window').show_all()
        gtk.main()
