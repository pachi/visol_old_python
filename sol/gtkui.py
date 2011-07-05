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
import codecs
import util, resparser, clases

TESTFILE = util.get_resource('data/test.res')


class GtkSol(object):
    """Aplicación Visor de archivos de LIDER"""
    def __init__(self):
        """Inicialización de datos e interfaz"""
        self.ui = gtk.Builder()
        self.ui.add_from_file(util.get_resource('ui', 'sol.ui'))

        self.window = self.ui.get_object('window')
        self.sb = self.ui.get_object('statusbar')
        self.edificiots = self.ui.get_object('treestore')
        self.edificiotv = self.ui.get_object('treeview')
        self.tb = self.ui.get_object('textbuffer')
        # Filtro de archivos
        filter = self.ui.get_object('filefilter')
        filter.set_name('Archivos *.res')
        filter.add_pattern('*.res')

        self.ui.connect_signals(self)
        # Carga datos de materiales, cerramientos y clima
        self.file = TESTFILE
        self.edificio = self.loadfile(self.file)

    def loadfile(self, file=TESTFILE):
        try:
            edificio = resparser.parsefile(codecs.open(file, "rU", "latin-1" ))
        except:
            raise
        self.edificio = edificio
        self.edificiots.clear()
        # Modelo de plantas y zonas
        topiter = self.edificiots.append(None, ('Edificio1', self.edificio))
        for planta in self.edificio.plantas:
            parentiter = self.edificiots.append(topiter, (planta, self.edificio.plantas[planta]))
            for zona in self.edificio.plantas[planta]:
                iter= self.edificiots.append(parentiter, (zona, self.edificio.plantas[planta][zona]))
        self.edificiotv.expand_all()
        # Modelo de
        self.sb.push(0, u'Cargado modelo: %s' % file)
        return edificio

    def cursorchanged(self, tv):
        """Seleccionada una nueva fila de la vista de árbol"""
        def zona2txt(zona):
            txt = 'Zona del Edificio\n==============\n\n'
            txt += '%s (Zona %i)\n\n' % (zona.nombre, zona.numero)
            txt += 'Superficie: %f m2\n' % zona.superficie
            txt += 'Planta %s\n\n' % zona.planta
            txt += 'Flujos por elementos:\n------------\n\n'
            for elemento in zona.flujos:
                txt += '%s: %s\n' % (elemento, zona.flujos[elemento])
            txt += '\nFlujos por componentes:\n------------\n\n'
            for elemento in zona.componentes:
                txt += '%s: %s\n' % (elemento, zona.componentes[elemento])
            txt += '\nDemandas globales de zona:\n---------------\n\n'
            txt += 'Calefaccion: %s\n' % zona.calefaccion
            txt += 'Refrigeracion: %s' % zona.refrigeracion
            return txt

        path, col = tv.get_cursor()
        tm = tv.get_model()
        nombre, objeto = tm[path]
        if isinstance(objeto, clases.ZonaLIDER):
            self.sb.push(0, u'Seleccionada zona: %s' % objeto.nombre)
            txt = zona2txt(objeto)
            self.tb.set_text(txt)

    #{ Funciones generales de aplicación
    def openfile(self, toolbutton):
        chooser = self.ui.get_object('filechooserdialog')
        chooser.set_filename(self.file)
        response = chooser.run()

        if response == gtk.RESPONSE_ACCEPT:
            self.file = chooser.get_filename()
            self.sb.push(0, u'Seleccionado archivo: %s' % self.file)
            self.edificio = self.loadfile(self.file)
        elif response == gtk.RESPONSE_CANCEL:
            self.sb.push(0, u'Carga de archivo cancelada')
        chooser.hide()

    def about(self, toolbutton):
        about = self.ui.get_object('aboutdialog')
        about.run()
        about.destroy()

    def quit(self, w, *args):
        """Salir de la aplicación"""
        gtk.main_quit()

    def main(self):
        """Arranca la aplicación"""
        self.ui.get_object('window').show_all()
        gtk.main()
