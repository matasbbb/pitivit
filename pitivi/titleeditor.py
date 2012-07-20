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
from pitivi.configure import get_ui_dir
from utils.text_buffer_markup import InteractivePangoBuffer

class TitleEditor():

    def __init__(self, instance, uimap):
        self.app = instance
        self.bt = {}
        self._createUI()
        self.textbuffer = gtk.TextBuffer()
        self.pangobuffer = InteractivePangoBuffer()
        self.textarea.set_buffer(self.pangobuffer)

        #Connect buttons
        self.pangobuffer.setup_widget_from_pango(self.bt["bold"], "<b>bold</b>")
        self.pangobuffer.setup_widget_from_pango(self.bt["italic"], "<i>italic</i>")
        self.pangobuffer.setup_widget_from_pango(self.bt["underline"], "<u>underline</u>")

    def _createUI(self):
        builder = gtk.Builder()
        builder.add_from_file(os.path.join(get_ui_dir(), "titleeditor.ui"))
        builder.connect_signals(self)
        self.widget = builder.get_object("box1")
        self.textarea = builder.get_object("textview1")
        buttons = ["bold","italic","underline","font","font_fore_color","font_back_color"]
        for button in buttons:
            self.bt[button] = builder.get_object(button)

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

    def _insertEndCb(self, unused_button):
        title = ges.TimelineTitleSource()
        title.set_text(self.pangobuffer.get_text())
        title.set_duration(long(gst.SECOND * 5))
        self.app.gui.timeline_ui.insertEnd([title])
