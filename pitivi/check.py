# PiTiVi , Non-linear video editor
#
#       pitivi/check.py
#
# Copyright (c) 2005, Edward Hervey <bilboed@bilboed.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA 02110-1301, USA.

"""
Runtime checks.
"""

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gst
from gi.repository import GES
from gi.repository import GooCanvas
from gettext import gettext as _

from pitivi.instance import PiTiVi
from pitivi.configure import APPNAME, GOOCANVAS_REQ, GTK_REQ, GST_REQ, GNONLIN_REQ, CAIRO_REQ, GES_REQ

global soft_deps
soft_deps = {}


def initiate_videosinks():
    """
    Test if the autovideosink element can initiate, return TRUE if it is the
    case.
    """
    sink = Gst.ElementFactory.make("autovideosink", None)
    if not sink.set_state(Gst.State.READY):
        return False
    sink.set_state(Gst.State.NULL)
    return True


def initiate_audiosinks():
    """
    Test if the autoaudiosink element can initiate, return TRUE if it is the
    case.
    """
    sink = Gst.ElementFactory.make("autoaudiosink", None)
    if not sink.set_state(Gst.State.READY):
        return False
    sink.set_state(Gst.State.NULL)
    return True


def __try_import__(modulename):
    """
    Attempt to load given module.
    Returns True on success, else False.
    """
    try:
        __import__(modulename)
        return True
    except:
        return False


def _version_to_string(version):
    return ".".join([str(x) for x in version])


def _string_to_list(version):
    return [int(x) for x in version.split(".")]


def check_required_version(modulename):
    """
    Checks if the installed module is the required version or more recent.
    Returns [None, None] if it's recent enough, else will return a list
    containing the strings of the required version and the installed version.
    This function does not check for the existence of the given module !
    """
    if modulename == "gtk":
        if list(Gtk._version)[0:3:2] < _string_to_list(GTK_REQ):
            return [GTK_REQ, _version_to_string(Gtk.gtk_version)]
    if modulename == "cairo":
        import cairo
        if _string_to_list(cairo.cairo_version_string()) < _string_to_list(CAIRO_REQ):
            return [CAIRO_REQ, cairo.cairo_version_string()]
    if modulename == "gst":
        if list(Gst.version()) < _string_to_list(GST_REQ):
            return [GST_REQ, _version_to_string(Gst.get_gst_version())]
    if modulename == "ges":
        if list(GES.version()) < _string_to_list(GES_REQ):
            return [GES_REQ, _version_to_string(GES.version())]
    if modulename == "goocanvas":
        if list(GooCanvas._version)[0:3:2] < _string_to_list(GOOCANVAS_REQ):
            return [GOOCANVAS_REQ, _version_to_string(Gtk.gtk_version)]
    if modulename == "gnonlin":
        gnlver = Gst.Registry.get().find_plugin("gnonlin").get_version()
        if _string_to_list(gnlver) < _string_to_list(GNONLIN_REQ):
            return [GNONLIN_REQ, gnlver]
    return [None, None]


def initial_checks():
    reg = Gst.Registry.get()
    if PiTiVi:
        return (_("%s is already running") % APPNAME,
                _("An instance of %s is already running in this script.") % APPNAME)
    if not reg.find_plugin("gnonlin"):
        return (_("Could not find the GNonLin plugins"),
                _("Make sure the plugins were installed and are available in the GStreamer plugins path."))
    if not reg.find_plugin("autodetect"):
        return (_("Could not find the autodetect plugins"),
                _("Make sure you have installed gst-plugins-good and that it's available in the GStreamer plugin path."))
    if not hasattr(Gdk.Window, 'cairo_create'):
        return (_("GTK doesn't have cairo support"),
                _("Please use a version of the GTK+ built with cairo support."))
    if not initiate_videosinks():
        return (_("Could not initiate the video output plugins"),
                _("Make sure you have at least one valid video output sink available (xvimagesink or ximagesink)."))
    if not initiate_audiosinks():
        return (_("Could not initiate the audio output plugins"),
                _("Make sure you have at least one valid audio output sink available (alsasink or osssink)."))
    if not __try_import__("cairo"):
        return (_("Could not import the cairo Python bindings"),
                _("Make sure you have the cairo Python bindings installed."))
    if not __try_import__("xdg"):
        return (_("Could not import the xdg Python library"),
                _("Make sure you have the xdg Python library installed."))
    if not __try_import__("gi"):
        return (_("Could not import PyGi"),
                _("Make sure you have PyGi installed."))
    req, inst = check_required_version("gtk")
    if req:
        return (_("You do not have a recent enough version of GTK+ (your version %s)") % inst,
                _("Install a version of the GTK+ greater than or equal to %s.") % req)
    req, inst = check_required_version("ges")
    if req:
        return (_("You do not have a recent enough version of GStreamer editing service (your version %s)") % inst,
                _("Install a version of the GStreamer editing service greater than or equal to %s.") % req)
    req, inst = check_required_version("goocanvas")
    if req:
        return (_("You do not have a recent enough version of GooCanvas") % inst,
                _("Install a version of the GooCanvas greater than or equal to %s.") % req)
    req, inst = check_required_version("gst")
    if req:
        return (_("You do not have a recent enough version of GStreamer (your version %s)") % inst,
                _("Install a version of the GStreamer greater than or equal to %s.") % req)
    req, inst = check_required_version("cairo")
    if req:
        return (_("You do not have a recent enough version of the cairo (your version %s)") % inst,
                _("Install a version of the cairo greater than or equal to %s.") % req)
    req, inst = check_required_version("gnonlin")
    if req:
        return (_("You do not have a recent enough version of the GNonLin GStreamer plugin (your version %s)") % inst,
                _("Install a version of the GNonLin GStreamer plugin greater than or equal to %s.") % req)
    if not __try_import__("zope.interface"):
        return (_("Could not import the Zope interface module"),
                _("Make sure you have the zope.interface module installed."))
    if not __try_import__("pkg_resources"):
        return (_("Could not import the distutils modules"),
                _("Make sure you have the distutils Python module installed."))

    # The following are soft dependencies
    # Note that instead of checking for plugins using Gst.Registry.get().find_plugin("foo"),
    # we could check for elements using Gst.ElementFactory.make("foo", None)
    if not __try_import__("numpy"):
        soft_deps["NumPy"] = _("Enables the autoalign feature")
    try:
        #if not Gst.Registry.get().find_plugin("frei0r"):
        element = Gst.ElementFactory.make("frei0r-filter-scale0tilt", None)
        if element == None:
            soft_deps["Frei0r"] = _("Additional video effects")
    except Gst.ElementNotFoundError:
        soft_deps["Frei0r"] = _("Additional video effects")

    if not Gst.Registry.get().find_plugin("ffmpeg"):
        soft_deps["GStreamer FFmpeg plugin"] = _('Additional multimedia codecs through the FFmpeg library')
    # Test for gst bad
    # This is disabled because, by definition, gst bad is a set of plugins that can
    # move to gst good or ugly, and we don't really have something to rely upon.
    #if not Gst.Registry.get().find_plugin("swfdec"): # FIXME: find a more representative plugin
    #    soft_deps["GStreamer bad plugins"] = _('Additional GStreamer plugins whose code is not of good enough quality, or are not considered tested well enough. The licensing may or may not be LGPL')
    # Test for gst ugly
    #if not Gst.Registry.get().find_plugin("x264"):
    #    soft_deps["GStreamer ugly plugins"] = _('Additional good quality GStreamer plugins whose license is not LGPL or with licensing issues')
    return None
