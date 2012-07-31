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
from utils.timeline import SELECT
from pitivi.configure import get_ui_dir, get_pixmap_dir
from pitivi.utils.loggable import Loggable
from pitivi.utils.signal import SignalGroup, Signallable
from utils.text_buffer_markup import InteractivePangoBuffer

INVISIBLE = gtk.gdk.pixbuf_new_from_file(os.path.join(get_pixmap_dir(), "invisible.png"))


class TitleEditor(Signallable, Loggable):
    __signals__ = {}

    def __init__(self, instance, uimap):
        Loggable.__init__(self)
        Signallable.__init__(self)
        self.app = instance
        self.bt = {}
        self._createUI()
        self.textbuffer = gtk.TextBuffer()
        self.pangobuffer = InteractivePangoBuffer()
        self.textarea.set_buffer(self.pangobuffer)

        #Conect updates
        self.textbuffer.connect("changed", self._updateSource)
        self.pangobuffer.connect("changed", self._updateSource)

        #Connect drag, no drag for now
        #self.drag_item.drag_source_set(gtk.gdk.BUTTON1_MASK, [], gtk.gdk.ACTION_COPY)
        #self.drag_item.connect("drag_begin", self._dndDragBeginCb)
        #self.drag_item.connect("drag_data_get", self._dndDragDataGetCb)
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
        self.info_bar_drag = builder.get_object("infobar2")
        self.drag_item = builder.get_object("drag_item")

        buttons = ["bold", "italic", "underline", "font", "font_fore_color", "font_back_color"]
        for button in buttons:
            self.bt[button] = builder.get_object(button)
        self.set_sensitive(False)

    def _focusedTextView(self, widget, notused_event):
        self.app.gui.timeline_ui.playhead_actions.set_sensitive(False)
        self.app.gui.timeline_ui.selection_actions.set_sensitive(False)

    def _unfocusedTextView(self, widget, notused_event):
        self.app.gui.timeline_ui.playhead_actions.set_sensitive(True)
        self.app.gui.timeline_ui.selection_actions.set_sensitive(True)

    def _backgroundColorButtonCb(self, widget):
        self.textarea.modify_base(self.textarea.get_state(), widget.get_color())

    def _frontTextColorButtonCb(self, widget):
        a, t, s = pango.parse_markup("<span color='" + widget.get_color().to_string() + "'>color</span>", u'\x00')
        ai = a.get_iterator()
        font, lang, attrs = ai.get_font()
        tags = self.pangobuffer.get_tags_from_attrs(None, None, attrs)
        self.pangobuffer.apply_tag_to_selection(tags[0])

    def _backTextColorButtonCb(self, widget):
        a, t, s = pango.parse_markup("<span background='" + widget.get_color().to_string() + "'>color</span>", u'\x00')
        ai = a.get_iterator()
        font, lang, attrs = ai.get_font()
        tags = self.pangobuffer.get_tags_from_attrs(None, None, attrs)
        self.pangobuffer.apply_tag_to_selection(tags[0])

    def _fontButtonCb(self, widget):
        font_desc = widget.get_font_name().split(" ")
        text = "<span font_desc='" + widget.get_font_name() + "'>text</span>"
        a, t, s = pango.parse_markup(text, u'\x00')
        ai = a.get_iterator()
        font, lang, attrs = ai.get_font()
        tags = self.pangobuffer.get_tags_from_attrs(font, None, attrs)
        for tag in tags:
            self.pangobuffer.apply_tag_to_selection(tag)

    def _markupToggleCb(self, markup_button):
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
                                         self.textbuffer.get_end_iter()))
            self.textarea.set_buffer(self.pangobuffer)

    def set_sensitive(self, sensitive):
        if sensitive:
            self.info_bar_create.hide()
            self.editing_box.set_sensitive(True)
        else:
            self.info_bar_create.show()
            self.info_bar_drag.hide()
            self.editing_box.set_sensitive(False)

    def _updateFromSource(self):
        #TODO: update not only text
        if self.source is not None:
            self.pangobuffer.set_text(self.source.get_text())

    def _updateSource(self, unused_object):
        #TODO: update not only text
        if self.source is not None:
            if self.markup_button.get_active():
                text = self.textbuffer.get_text(self.textbuffer.get_start_iter(),
                                                self.textbuffer.get_end_iter())
            else:
                text = self.pangobuffer.get_text()
            self.source.set_text(text)

    def _reset(self):
        #TODO: reset not only text
        self.markup_button.set_active(False)
        self.pangobuffer.set_text("")
        self.textbuffer.set_text("")
        #Set right buffer
        self._markupToggleCb(self.markup_button)

    def set_source(self, source):
        self.source = None
        self._reset()
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
        #Show drag only if created new source
        self.info_bar_drag.show()
        self.set_source(source)
        #Media library uses DiscovererInfo, while TimelineTitleSource can't have it..
        #self.app.gui.timeline_ui._project.medialibrary.addSources([self.source])

    def _insertEndCb(self, unused_button):
        self.info_bar_drag.hide()
        self.app.gui.timeline_ui.insertEnd([self.source])
        self.app.gui.timeline_ui.timeline.selection.setToObj(self.source, SELECT)

    def _dndDragBeginCb(self, view, context):
        self.info("Title drag begin")
        if self.source is None:
            context.drag_abort(int(time.time()))
        else:
            context.set_icon_pixbuf(gtk.STOCK_DND)

    def _dndDragDataGetCb(self, unused_widget_context, selection, targettype, unused_eventtime):
        self.info("Title drag data get, type:%d", targettype)
        if self.source is None:
            return
        selection.set(selection.target, 8, "fake")
        context.set_icon_pixbuf(INVISIBLE, 0, 0)
