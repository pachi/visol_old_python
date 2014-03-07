#!/usr/bin/env python
# encoding: utf-8
#
#   makesplash.py
#   Script to generate application splash image using a png background
#
#   Copyright (C) 2009-2010 Rafael Villar Burke <pachi@rvburke.com>
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
"""Overlay application and version information on background image

This script overlays informational text (name, version, author...)
over a background image to be used as splash.
"""
import os
import optparse
import cairo
import pango, pangocairo
from PIL import Image #PIL

APPNAME = u"ViSol"
COPYTXT = u'© 2014 Rafael Villar Burke [GPL v2+]'
WEBTXT = u'http://www.rvburke.com'
APPDESC = u"Aplicación para la visualización de archivos de resultados de LIDER/CALENER"
IMGCRED = u"Fotografía: Dominio Público"

def splashimage(version='1.0', bgfile='background.png', outfile='splash.jpg'):
    """Create a splash image using a background image and a version string

    version: version string
    bgfile: background image in png format (400x470px)
    outfile: output file name. It will be written in png and jpg formats
    """
    PADDING = 15.0
    f, e = os.path.splitext(outfile)
    PNGFILE = f + '.png'
    JPGFILE = f + '.jpg'
    
    TXT = (u"<span size='8000'>%s</span><span size='4000'> v.%s\n"
           u"%s\n%s\n\n</span><span size='2100' weight='bold'>%s</span>\n"
           u"<span size='2000'>%s</span>"
           % (APPNAME, version, COPYTXT, WEBTXT, APPDESC, IMGCRED))
    surface = cairo.ImageSurface.create_from_png(bgfile)
    cr = cairo.Context(surface)
    width, height = surface.get_width(), surface.get_height()
    cr.set_source_rgb(1, 1, 1)
    pctx = pangocairo.CairoContext(cr)
    layout = pctx.create_layout()
    layout.set_font_description(pango.FontDescription("Arial"))
    layout.set_markup(TXT)
    w, h = layout.get_pixel_size()
    sc = min((width - 2 * PADDING) / w, (height - 2 * PADDING) / h)
    cr.translate(PADDING, (height - PADDING - sc * h))
    cr.scale(sc, sc)
    pctx.show_layout(layout)
    cr.stroke()
    surface.write_to_png(PNGFILE)
    cr.show_page()
    surface.finish()
    
    img = Image.open(PNGFILE)
    img.save(JPGFILE)

if __name__ == "__main__":
    parser = optparse.OptionParser(usage='%prog [options] <version>')
    parser.add_option('-b', action="store", dest="background",
        default="background.png", help="background image file")
    parser.add_option('-o', action="store", dest="outputfile",
        default="splash.png", help="output file name (png and jpg format)")
    options, remainder = parser.parse_args()
    version = remainder[0] if remainder else '1.0'
    splashimage(version, options.background, options.outputfile)
