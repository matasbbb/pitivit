# PiTiVi , Non-linear video editor
#
#       pitivi/medialibrary.py
#
# Copyright (c) 2005, Edward Hervey <bilboed@bilboed.com>
# Copyright (c) 2009, Alessandro Decina <alessandro.d@gmail.com>
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
Shows title editor
"""
import os
import gtk
import pango
import ges
import gst
import gobject

from gettext import gettext as _

from utils.timeline import SELECT
from pitivi.configure import get_ui_dir, get_pixmap_dir
from pitivi.utils.loggable import Loggable
from pitivi.utils.signal import SignalGroup, Signallable
from pitivi.utils.pipeline import Seeker
from utils.text_buffer_markup import InteractivePangoBuffer
INVISIBLE = gtk.gdk.pixbuf_new_from_file(os.path.join(get_pixmap_dir(), "invisible.png"))


class TitleEditor(Signallable, Loggable):
    __signals__ = {}

    def __init__(self, instance, uimap):
        Loggable.__init__(self)
        Signallable.__init__(self)
        self.app = instance
        self.bt = {}
        self.settings = {}
        self.source = None
        self.created = False
        self.seeker = Seeker()

        #Drag attributes
        self._drag_events = []
        self._drag_connected = False
        self._tab_opened = False

        #Creat UI
        self._createUI()
        self.textbuffer = gtk.TextBuffer()
        self.pangobuffer = InteractivePangoBuffer()
        self.textarea.set_buffer(self.pangobuffer)

        #Conect updates
        self.textbuffer.connect("changed", self._updateSourceText)
        self.pangobuffer.connect("changed", self._updateSourceText)

        #Connect buttons
        self.pangobuffer.setup_widget_from_pango(self.bt["bold"], "<b>bold</b>")
        self.pangobuffer.setup_widget_from_pango(self.bt["italic"], "<i>italic</i>")
        self.pangobuffer.setup_widget_from_pango(self.bt["underline"], "<u>underline</u>")

    def _createUI(self):
        builder = gtk.Builder()
        builder.add_from_file(os.path.join(get_ui_dir(), "titleeditor.ui"))
        builder.connect_signals(self)
        self.widget = builder.get_object("box1")
        self.editing_box = builder.get_object("editing_box")
        self.textarea = builder.get_object("textview1")
        self.markup_button = builder.get_object("markupToggle")
        self.info_bar_create = builder.get_object("infobar1")
        self.info_bar_insert = builder.get_object("infobar2")
        buttons = ["bold", "italic", "underline", "font", "font_fore_color", "font_back_color", "back_color"]
        for button in buttons:
            self.bt[button] = builder.get_object(button)
        settings = ["valignment", "halignment", "xpos", "ypos"]
        for setting in settings:
            self.settings[setting] = builder.get_object(setting)
        for n, en in {_("Custom"):"position",
                      _("Top"):"top",
                      _("Center"):"center",
                      _("Bottom"):"bottom",
                      _("Baseline"):"baseline"}.items():
            self.settings["valignment"].append(en, n)
        for n, en in {_("Custom"):"position",
                      _("Left"):"left",
                      _("Center"):"center",
                      _("Right"):"right"}.items():
            self.settings["halignment"].append(en, n)
        self.set_sensitive(False)

    def _focusedTextView(self, widget, notused_event):
        self.app.gui.timeline_ui.playhead_actions.set_sensitive(False)
        self.app.gui.timeline_ui.selection_actions.set_sensitive(False)

    def _unfocusedTextView(self, widget, notused_event):
        self.app.gui.timeline_ui.playhead_actions.set_sensitive(True)
        self.app.gui.timeline_ui.selection_actions.set_sensitive(True)

    def _backgroundColorButtonCb(self, widget):
        self.textarea.modify_base(self.textarea.get_state(), widget.get_color())
        color = widget.get_rgba()
        color_int = 0
        color_int += int(color.red   * 255) * 256**2
        color_int += int(color.green * 255) * 256**1
        color_int += int(color.blue  * 255) * 256**0
        color_int += int(color.alpha * 255) * 256**3
        self.debug("Setting title background color to %s", hex(color_int))
        self.source.set_background(color_int)

    def _frontTextColorButtonCb(self, widget):
        suc, a, t, s = pango.parse_markup("<span color='" + widget.get_color().to_string() + "'>color</span>", -1, u'\x00')
        ai = a.get_iterator()
        font, lang, attrs = ai.get_font()
        tags = self.pangobuffer.get_tags_from_attrs(None, None, attrs)
        self.pangobuffer.apply_tag_to_selection(tags[0])

    def _backTextColorButtonCb(self, widget):
        suc, a, t, s = pango.parse_markup("<span background='" + widget.get_color().to_string() + "'>color</span>", -1, u'\x00')
        ai = a.get_iterator()
        font, lang, attrs = ai.get_font()
        tags = self.pangobuffer.get_tags_from_attrs(None, None, attrs)
        self.pangobuffer.apply_tag_to_selection(tags[0])

    def _fontButtonCb(self, widget):
        font_desc = widget.get_font_name().split(" ")
        font_face = " ".join(font_desc[:-1])
        font_size = str(int(font_desc[-1]) * 1024)
        text = "<span face='" + font_face + "'><span size='" + font_size + "'>text</span></span>"
        suc, a, t, s = pango.parse_markup(text, -1, u'\x00')
        ai = a.get_iterator()
        font, lang, attrs = ai.get_font()
        tags = self.pangobuffer.get_tags_from_attrs(font, None, attrs)
        for tag in tags:
            self.pangobuffer.apply_tag_to_selection(tag)

    def _markupToggleCb(self, markup_button):
        self.textbuffer.disconnect_by_func(self._updateSourceText)
        self.pangobuffer.disconnect_by_func(self._updateSourceText)
        if markup_button.get_active():
            for name in self.bt:
                self.bt[name].set_sensitive(False)
            self.textbuffer.set_text(self.pangobuffer.get_text())
            self.textarea.set_buffer(self.textbuffer)
        else:
            for name in self.bt:
                self.bt[name].set_sensitive(True)
            self.pangobuffer.set_text(
                self.textbuffer.get_text(self.textbuffer.get_start_iter(),
                                         self.textbuffer.get_end_iter(), True))
            self.textarea.set_buffer(self.pangobuffer)
        self.textbuffer.connect("changed", self._updateSourceText)
        self.pangobuffer.connect("changed", self._updateSourceText)

    def set_sensitive(self, sensitive):
        if sensitive:
            self.info_bar_create.hide()
            self.editing_box.set_sensitive(True)
        else:
            self.info_bar_create.show()
            self.info_bar_insert.hide()
            self.editing_box.set_sensitive(False)

        self.preview(sensitive)

    def _updateFromSource(self):
        if self.source is not None:
            self.log("Title text set to %s", self.source.get_text())
            self.pangobuffer.set_text(self.source.get_text())
            self.textbuffer.set_text(self.source.get_text())
            self.settings['xpos'].set_value(self.source.get_xpos())
            self.settings['ypos'].set_value(self.source.get_ypos())
            self.settings['valignment'].set_active_id(self.source.get_valignment().value_name)
            self.settings['halignment'].set_active_id(self.source.get_halignment().value_name)
            if hasattr(self.source, "get_background"):
                self.bt["back_color"].set_visible(True)
                color = self.source.get_background()
                color = gtk.gdk.RGBA(color / 256**2 % 256 / 255.,
                                     color / 256**1 % 256 / 255.,
                                     color / 256**0 % 256 / 255.,
                                     color / 256**3 % 256 / 255.)
                self.bt["back_color"].set_rgba(color)
            else:
                self.bt["back_color"].set_visible(False)


    def _updateSourceText(self, updated_obj):
        if self.source is not None:
            if self.markup_button.get_active():
                text = self.textbuffer.get_text(self.textbuffer.get_start_iter(),
                                                self.textbuffer.get_end_iter(),
                                                True)
            else:
                text = self.pangobuffer.get_text()
            self.log("Source text updated to %s", text)
            self.source.set_text(text)
            self.preview()

    def _updateSource(self, updated_obj):
        if self.source is not None:
            for name, obj in self.settings.items():
                if obj == updated_obj:
                    if name == "valignment":
                       self.source.set_valignment(getattr(ges.TextVAlign, obj.get_active_id().upper()))
                       self.settings["ypos"].set_visible(obj.get_active_id() == "position")
                    if name == "halignment":
                       self.source.set_halignment(getattr(ges.TextHAlign, obj.get_active_id().upper()))
                       self.settings["xpos"].set_visible(obj.get_active_id() == "position")
                    if name == "xpos":
                       self.settings["halignment"].set_active_id("position")
                       self.source.set_xpos(obj.get_value())
                    if name == "ypos":
                       self.settings["valignment"].set_active_id("position")
                       self.source.set_ypos(obj.get_value())
                    self.preview()
                    return

    def _reset(self):
        #TODO: reset not only text
        self.markup_button.set_active(False)
        self.pangobuffer.set_text("")
        self.textbuffer.set_text("")
        #Set right buffer
        self._markupToggleCb(self.markup_button)

    def set_source(self, source, created=False):
        self.debug("Source set to %s", str(source))
        self.source = None
        self._reset()
        self.created = created
        if source is None:
            self.set_sensitive(False)
        else:
            self.source = source
            self._updateFromSource()
            self.set_sensitive(True)

    def _createCb(self, unused_button):
        source = ges.TimelineTitleSource()
        source.set_text("")
        source.set_duration(long(gst.SECOND * 5))
        #Show insert infobar only if created new source
        self.info_bar_insert.show()
        self.set_source(source, True)

    def _insertEndCb(self, unused_button):
        self.info_bar_insert.hide()
        self.app.gui.timeline_ui.insertEnd([self.source])
        self.app.gui.timeline_ui.timeline.selection.setToObj(self.source, SELECT)
        #After insertion consider as not created
        self.created = False

    def preview(self, show=True):
       if not show:
            #Disconect
            if self._drag_connected:
                self.app.gui.viewer.target.disconnect_by_func(self.drag_notify_event)
                self.app.gui.viewer.target.disconnect_by_func(self.drag_press_event)
                self.app.gui.viewer.target.disconnect_by_func(self.drag_release_event)
                self._drag_connected = False
       elif self.source is not None and not self.created:
            self.seeker.flush()
            if not self._drag_connected and self._tab_opened:
                #If source is in timeline and title tab opened enable title drag
                self._drag_connected = True
                self.app.gui.viewer.target.connect("motion-notify-event", self.drag_notify_event)
                self.app.gui.viewer.target.connect("button-press-event", self.drag_press_event)
                self.app.gui.viewer.target.connect("button-release-event", self.drag_release_event)


    def drag_press_event(self, widget, event):
        if event.button == 1:
            self._drag_events = [(event.x, event.y)]
            #Update drag by drag event change, but not too often
            self.timeout = gobject.timeout_add(100, self.drag_update_event)
            #If drag goes out for 0.3 second, and do not come back, consider drag end
            self._drag_updated = True
            self.timeout = gobject.timeout_add(1000, self.drag_posible_end_event)

    def drag_posible_end_event(self):
        if self._drag_updated:
            #Updated during last timeout, wait more
            self._drag_updated = False
            return True
        else:
            #Not updated - posibly out of bounds, stop drag
            self.log("Drag timeout")
            self._drag_events = []
            return False

    def drag_update_event(self):
        if len(self._drag_events) > 0:
            st = self._drag_events[0]
            self._drag_events = [self._drag_events[-1]]
            e = self._drag_events[0]
            xdiff = e[0] - st[0]
            ydiff = e[1] - st[1]
            xdiff /= self.app.gui.viewer.target.get_allocated_width()
            ydiff /= self.app.gui.viewer.target.get_allocated_height()
            newxpos = self.settings["xpos"].get_value() + xdiff
            newypos = self.settings["ypos"].get_value() + ydiff
            self.settings["xpos"].set_value(newxpos)
            self.settings["ypos"].set_value(newypos)
            self.seeker.flush()
            return True
        else:
            return False

    def drag_notify_event(self, widget, event):
        if len(self._drag_events) > 0 and event.get_state() & gtk.gdk.BUTTON1_MASK:
            self._drag_updated = True
            self._drag_events.append((event.x,event.y))
            st = self._drag_events[0]
            e = self._drag_events[-1]

    def drag_release_event(self, widget, event):
        self._drag_events = []

    def tab_switched(self, unused_notebook, arg1, arg2):
        if arg2 == 2:
            self._tab_opened = True
            self.preview(True)
        else:
            self._tab_opened = False
            self.preview(False)
