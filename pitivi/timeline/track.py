# PiTiVi , Non-linear video editor
#
#       pitivi/timeline/timeline.py
#
# Copyright (c) 2005, Edward Hervey <bilboed@bilboed.com>
# Copyright (c) 2009, Alessandro Decina <alessandro.decina@collabora.co.uk>
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

from gi.repository import GooCanvas
from gi.repository import GES
from gi.repository import GObject
from gi.repository import Gtk
import os.path
from gi.repository import Pango
import cairo

import pitivi.configure as configure

from gettext import gettext as _

from pitivi.dialogs.prefs import PreferencesDialog

from pitivi.utils.loggable import Loggable
from pitivi.utils.receiver import receiver, handler
from pitivi.utils.ui import Point
from pitivi.settings import GlobalSettings
from pitivi.utils.signal import Signallable
from pitivi.utils.timeline import SELECT, SELECT_ADD, UNSELECT, \
    SELECT_BETWEEN, MoveContext, TrimStartContext, TrimEndContext, Controller, \
    View, Zoomable
from pitivi.utils.ui import LAYER_HEIGHT_EXPANDED,\
        LAYER_HEIGHT_COLLAPSED, LAYER_SPACING, \
        unpack_cairo_pattern, unpack_cairo_gradient


#--------------------------------------------------------------#
#                       Private stuff                          #
LEFT_SIDE = Gdk.Cursor.new(Gdk.CursorType.LEFT_SIDE)
RIGHT_SIDE = Gdk.Cursor.new(Gdk.CursorType.RIGHT_SIDE)
ARROW = Gdk.Cursor.new(Gdk.CursorType.ARROW)
TRIMBAR_PIXBUF = GdkPixbuf.Pixbuf.new_from_file(
    os.path.join(configure.get_pixmap_dir(), "trimbar-normal.png"))
TRIMBAR_PIXBUF_FOCUS = GdkPixbuf.Pixbuf.new_from_file(
    os.path.join(configure.get_pixmap_dir(), "trimbar-focused.png"))
NAME_HOFFSET = 10
NAME_VOFFSET = 5
NAME_PADDING = 2
NAME_PADDING2X = 2 * NAME_PADDING

GlobalSettings.addConfigOption('videoClipBg',
    section='user-interface',
    key='videoclip-background',
    default=0x000000A0,
    notify=True)

PreferencesDialog.addColorPreference('videoClipBg',
    section=_("Appearance"),
    label=_("Color for video clips"),
    description=_("The background color for clips in video tracks."))

GlobalSettings.addConfigOption('audioClipBg',
    section='user-interface',
    key='audioclip-background',
    default=0x4E9A06C0,
    notify=True)

PreferencesDialog.addColorPreference('audioClipBg',
    section=_("Appearance"),
    label=_("Color for audio clips"),
    description=_("The background color for clips in audio tracks."))

GlobalSettings.addConfigOption('selectedColor',
    section='user-interface',
    key='selected-color',
    default=0x00000077,
    notify=True)

PreferencesDialog.addColorPreference('selectedColor',
    section=_("Appearance"),
    label=_("Selection color"),
    description=_("Selected clips will be tinted with this color."))

GlobalSettings.addConfigOption('clipFontDesc',
    section='user-interface',
    key='clip-font-name',
    default="Sans 9",
    notify=True)

PreferencesDialog.addFontPreference('clipFontDesc',
    section=_('Appearance'),
    label=_("Clip font"),
    description=_("The font to use for clip titles"))

GlobalSettings.addConfigOption('clipFontColor',
    section='user-interface',
    key='clip-font-color',
    default=0xFFFFFFAA,
    notify=True)


def text_size(text):
    ink, logical = text.get_natural_extents()
    x1, y1, x2, y2 = [Pango.PIXELS(x) for x in logical]
    return x2 - x1, y2 - y1


#--------------------------------------------------------------#
#                            Main Classes                      #
class Selected (Signallable):
    """
    A simple class that let us emit a selected-changed signal
    when needed, and that can be check directly to know if the
    object is selected or not.
    """

    __signals__ = {
        "selected-changed": []}

    def __init__(self):
        self._selected = False

    def __nonzero__(self):
        """
        checking a Selected object is the same as checking its _selected
        property
        """
        return self._selected

    def getSelected(self):
        return self._selected

    def setSelected(self, selected):
        self._selected = selected
        self.emit("selected-changed", selected)

    selected = property(getSelected, setSelected)


class TimelineController(Controller):

    _cursor = ARROW
    _context = None
    _handle_enter_leave = False
    previous_x = None
    next_previous_x = None
    ref = None

    def enter(self, unused, unused2):
        self._view.focus()

    def leave(self, unused, unused2):
        self._view.unfocus()

    def drag_start(self, item, target, event):
        self.debug("Drag started")
        if not self._view.element.selected:
            self._view.timeline.selection.setToObj(self._view.element, SELECT)
        if self.previous_x != None:
            ratio = float(self.ref / Zoomable.pixelToNs(10000000000))
            self.previous_x = self.previous_x * ratio
        self.ref = Zoomable.pixelToNs(10000000000)
        self._view.app.projectManager.current.timeline.enable_update(False)
        tx = self._view.props.parent.get_transform()
        # store y offset for later priority calculation
        self._y_offset = tx[5]
        # zero y component of mousdown coordiante
        self._mousedown = Point(self._mousedown[0], 0)

    def drag_end(self, item, target, event):
        self.debug("Drag end")
        self._context.finish()
        self._context = None
        self._view.app.projectManager.current.timeline.enable_update(True)
        self._view.app.action_log.commit()
        self._view.element.starting_start = self._view.element.props.start
        obj = self._view.element.get_timeline_object()
        obj.starting_start = obj.props.start
        self.previous_x = self.next_previous_x

    def set_pos(self, item, pos):
        x, y = pos
        x = x + self._hadj.get_value()
        position = Zoomable.pixelToNs(x)
        priority = int((y - self._y_offset + self._vadj.get_value()) //
            (LAYER_HEIGHT_EXPANDED + LAYER_SPACING))

        self._context.setMode(self._getMode())
        self.debug("Setting position")
        self._context.editTo(position, priority)

    def _getMode(self):
        if self._shift_down:
            return self._context.RIPPLE
        elif self._control_down:
            return self._context.ROLL
        return self._context.DEFAULT

    def key_press(self, keyval):
        if self._context:
            self._context.setMode(self._getMode())

    def key_release(self, keyval):
        if self._context:
            self._context.setMode(self._getMode())


class TrimHandle(View, GooCanvas.CanvasImage, Loggable, Zoomable):

    """A component of a TrackObject which manage's the source's edit
    points"""

    element = receiver()

    def __init__(self, instance, element, timeline, **kwargs):
        self.app = instance
        self.element = element
        self.timeline = timeline
        GooCanvas.CanvasImage.__init__(self,
            pixbuf=TRIMBAR_PIXBUF,
            line_width=0,
            pointer_events=GooCanvas.CanvasPointerEvents.FILL,
            **kwargs)
        View.__init__(self)
        Zoomable.__init__(self)
        Loggable.__init__(self)

    def focus(self):
        self.props.pixbuf = TRIMBAR_PIXBUF_FOCUS

    def unfocus(self):
        self.props.pixbuf = TRIMBAR_PIXBUF


class StartHandle(TrimHandle):

    """Subclass of TrimHandle wich sets the object's start time"""

    class Controller(TimelineController, Signallable):

        _cursor = LEFT_SIDE

        def drag_start(self, item, target, event):
            self.debug("Trim start %s" % target)
            TimelineController.drag_start(self, item, target, event)
            if self._view.element.is_locked():
                elem = self._view.element.get_timeline_object()
            else:
                elem = self._view.element
            self._context = TrimStartContext(self._view.timeline, elem, set([]))
            self._context.connect("clip-trim", self.clipTrimCb)
            self._context.connect("clip-trim-finished", self.clipTrimFinishedCb)
            self._view.app.action_log.begin("trim object")

        def clipTrimCb(self, unused_TrimStartContext, clip_uri, position):
            # While a clip is being trimmed, ask the viewer to preview it
            self._view.app.gui.viewer.clipTrimPreview(clip_uri, position)

        def clipTrimFinishedCb(self, unused_TrimStartContext):
            # When a clip has finished trimming, tell the viewer to reset itself
            self._view.app.gui.viewer.clipTrimPreviewFinished()


class EndHandle(TrimHandle):

    """Subclass of TrimHandle which sets the objects's end time"""

    class Controller(TimelineController):

        _cursor = RIGHT_SIDE

        def drag_start(self, item, target, event):
            self.debug("Trim end %s" % target)
            TimelineController.drag_start(self, item, target, event)
            if self._view.element.is_locked():
                elem = self._view.element.get_timeline_object()
            else:
                elem = self._view.element
            self._context = TrimEndContext(self._view.timeline, elem, set([]))
            self._context.connect("clip-trim", self.clipTrimCb)
            self._context.connect("clip-trim-finished", self.clipTrimFinishedCb)
            self._view.app.action_log.begin("trim object")

        def clipTrimCb(self, unused_TrimStartContext, clip_uri, position):
            # While a clip is being trimmed, ask the viewer to preview it
            self._view.app.gui.viewer.clipTrimPreview(clip_uri, position)

        def clipTrimFinishedCb(self, unused_TrimStartContext):
            # When a clip has finished trimming, tell the viewer to reset itself
            self._view.app.gui.viewer.clipTrimPreviewFinished()


class TrackObject(View, GooCanvas.CanvasGroup, Zoomable):

    class Controller(TimelineController):

        _handle_enter_leave = True

        def drag_start(self, item, target, event):
            point = self.from_item_event(item, event)
            TimelineController.drag_start(self, item, target, event)
            self._context = MoveContext(self._view.timeline,
                self._view.element, self._view.timeline.selection.getSelectedTrackObjs())
            self._view.app.action_log.begin("move object")

        def _getMode(self):
            if self._shift_down:
                return self._context.RIPPLE
            return self._context.DEFAULT

        def click(self, pos):
            timeline = self._view.timeline
            element = self._view.element
            if self._last_event.get_state() & Gdk.ModifierType.SHIFT_MASK:
                timeline.selection.setToObj(element, SELECT_BETWEEN)
            elif self._last_event.get_state() & Gdk.ModifierType.CONTROL_MASK:
                if element.selected:
                    mode = UNSELECT
                else:
                    mode = SELECT_ADD
                timeline.selection.setToObj(element, mode)
            else:
                x, y = pos
                x += self._hadj.get_value()
                self._view.app.current.seeker.seek(Zoomable.pixelToNs(x))
                timeline.selection.setToObj(element, SELECT)

    def __init__(self, instance, element, track, timeline, utrack, is_transition=False):
        GooCanvas.CanvasGroup.__init__(self)
        View.__init__(self)
        Zoomable.__init__(self)
        self.ref = Zoomable.nsToPixel(10000000000)
        self.app = instance
        self.track = track
        self.utrack = utrack
        self.timeline = timeline
        self.namewidth = 0
        self.nameheight = 0
        self.is_transition = is_transition

        self.snapped_before = False
        self.snapped_after = False

        self.bg = GooCanvas.CanvasRect(
            height=self.height,
            line_width=1)

        self.name = GooCanvas.CanvasText(
            x=NAME_HOFFSET + NAME_PADDING,
            y=NAME_VOFFSET + NAME_PADDING,
            operator=cairo.OPERATOR_ADD,
            alignment=Pango.Alignment.LEFT)
        self.namebg = GooCanvas.CanvasRect(
            radius_x=2,
            radius_y=2,
            x=NAME_HOFFSET,
            y=NAME_VOFFSET,
            line_width=0)

        self.start_handle = StartHandle(self.app, element, timeline,
            height=self.height)
        self.end_handle = EndHandle(self.app, element, timeline,
            height=self.height)

        self._selec_indic = GooCanvas.CanvasRect(
            visibility=GooCanvas.CanvasItemVisibility.INVISIBLE,
            line_width=0.0,
            height=self.height)

        if not self.is_transition:
            for thing in (self.bg, self._selec_indic,
                self.start_handle, self.end_handle, self.namebg, self.name):
                self.add_child(thing, 0)
        else:
            for thing in (self.bg, self.name):
                self.add_child(thing, 0)

        self.element = element
        element.max_duration = element.props.duration
        element.starting_start = element.props.start
        element.selected = Selected()
        element.selected.connect("selected-changed", self.selectedChangedCb)

        obj = self.element.get_timeline_object()
        obj.starting_start = obj.get_property("start")
        obj.max_duration = obj.props.duration

        self.settings = instance.settings
        self.unfocus()

## Properties

    _height = LAYER_HEIGHT_EXPANDED

    def setHeight(self, height):
        self._height = height
        self.start_handle.props.height = height
        self.end_handle.props.height = height
        self._update()

    def getHeight(self):
        return self._height

    height = property(getHeight, setHeight)

    _expanded = True

    def setExpanded(self, expanded):
        self._expanded = expanded
        if not self._expanded:
            self.height = LAYER_HEIGHT_COLLAPSED
            self.content.props.visibility = GooCanvas.CanvasItemVisibility.INVISIBLE
            self.namebg.props.visibility = GooCanvas.CanvasItemVisibility.INVISIBLE
            self.bg.props.height = LAYER_HEIGHT_COLLAPSED
            self.name.props.y = 0
        else:
            self.height = LAYER_HEIGHT_EXPANDED
            self.content.props.visibility = GooCanvas.CanvasItemVisibility.VISIBLE
            self.namebg.props.visibility = GooCanvas.CanvasItemVisibility.VISIBLE
            self.bg.props.height = LAYER_HEIGHT_EXPANDED
            self.height = LAYER_HEIGHT_EXPANDED
            self.name.props.y = NAME_VOFFSET + NAME_PADDING

    def getExpanded(self):
        return self._expanded

    expanded = property(getExpanded, setExpanded)

## Public API

    def focus(self):
        self.start_handle.props.visibility = GooCanvas.CanvasItemVisibility.VISIBLE
        self.end_handle.props.visibility = GooCanvas.CanvasItemVisibility.VISIBLE
        self.raise_(None)
        for transition in self.utrack.transitions:
            transition.raise_(None)

    def unfocus(self):
        self.start_handle.props.visibility = GooCanvas.CanvasItemVisibility.INVISIBLE
        self.end_handle.props.visibility = GooCanvas.CanvasItemVisibility.INVISIBLE

    def zoomChanged(self):
        self._update()

## settings signals

    def _setSettings(self):
        if self.settings:
            self.clipAppearanceSettingsChanged()

    settings = receiver(_setSettings)

    @handler(settings, "audioClipBgChanged")
    @handler(settings, "videoClipBgChanged")
    @handler(settings, "selectedColorChanged")
    @handler(settings, "clipFontDescChanged")
    def clipAppearanceSettingsChanged(self, *args):
        if self.element.get_track().props.track_type.first_value_name == 'GES_TRACK_TYPE_AUDIO':
            color = self.settings.audioClipBg
        else:
            color = self.settings.videoClipBg
        if self.is_transition:
            color = 0x0089CFF0
        pattern = unpack_cairo_gradient(color)
        self.bg.props.fill_pattern = pattern

        self.namebg.props.fill_pattern = pattern

        self._selec_indic.props.fill_pattern = unpack_cairo_pattern(
            self.settings.selectedColor)

        self.name.props.font = self.settings.clipFontDesc
        self.name.props.fill_pattern = unpack_cairo_pattern(
            self.settings.clipFontColor)
        twidth, theight = text_size(self.name)
        self.namewidth = twidth
        self.nameheight = theight
        self._update()

## element signals

    def _setElement(self):
        if self.element and not self.is_transition:
            from pitivi.utils.ui import info_name

            sources = self.app.current.medialibrary
            uri = self.element.props.uri
            info = sources.getInfoFromUri(uri)
            self.name.props.text = info_name(info)
            twidth, theight = text_size(self.name)
            self.namewidth = twidth
            self.nameheight = theight
            self._update()

    element = receiver(_setElement)

    @handler(element, "notify::start")
    @handler(element, "notify::duration")
    @handler(element, "notify::in-point")
    def startChangedCb(self, track_object, start):
        self._update()

    def selectedChangedCb(self, element, selected):
        if element.selected:
            self._selec_indic.props.visibility = GooCanvas.CanvasItemVisibility.VISIBLE
        else:
            self._selec_indic.props.visibility = GooCanvas.CanvasItemVisibility.INVISIBLE

    def _update(self):
        try:
            x = self.nsToPixel(self.element.get_start())
        except Exception, e:
            raise Exception(e)
        priority = (self.element.get_priority()) / 1000
        if priority < 0:
            priority = 0
        y = (self.height + LAYER_SPACING) * priority
        self.set_simple_transform(x, y, 1, 0)
        width = self.nsToPixel(self.element.get_duration())
        min_width = self.start_handle.props.width * 2
        if width < min_width:
            width = min_width
        w = width - self.end_handle.props.width
        self.name.props.clip_path = "M%g,%g h%g v%g h-%g z" % (
            0, 0, w, self.height, w)
        self.bg.props.width = width
        self._selec_indic.props.width = width
        self.end_handle.props.x = w
        if self.expanded:
            if w - NAME_HOFFSET > 0:
                self.namebg.props.height = self.nameheight + NAME_PADDING2X
                self.namebg.props.width = min(w - NAME_HOFFSET,
                    self.namewidth + NAME_PADDING2X)
                self.namebg.props.visibility = GooCanvas.CanvasItemVisibility.VISIBLE
            else:
                self.namebg.props.visibility = GooCanvas.CanvasItemVisibility.INVISIBLE
        self.app.gui.timeline_ui._canvas.regroupTracks()
        self.app.gui.timeline_ui.unsureVadjHeight()

TRACK_CONTROL_WIDTH = 75


class TrackControls(Gtk.Label, Loggable):
    """Contains a timeline track name.

    @ivar track: The track for which to display the name.
    @type track: An L{pitivi.timeline.track.Track} object
    """

    __gtype_name__ = 'TrackControls'

    def __init__(self, track):
        Gtk.Label.__init__(self)
        Loggable.__init__(self)
        # Center the label horizontally.
        self.set_alignment(0.5, 0)
        # The value below is arbitrarily chosen so the text appears
        # centered vertically when the represented track has a single layer.
        self.set_padding(0, LAYER_SPACING * 2)
        self.set_markup(self._getTrackName(track))
        self.track = track
        self._setSize(layers_count=1)

    def _setTrack(self):
        if self.track:
            self._maxPriorityChanged(None, self.track.max_priority)

    # FIXME Stop using the receiver
    #
    # TODO implement in GES
    #track = receiver(_setTrack)
    #@handler(track, "max-priority-changed")
    #def _maxPriorityChanged(self, track, max_priority):
    #    self._setSize(max_priority + 1)

    def _setSize(self, layers_count):
        assert layers_count >= 1
        height = layers_count * (LAYER_HEIGHT_EXPANDED + LAYER_SPACING)
        self.set_size_request(TRACK_CONTROL_WIDTH, height)

    @staticmethod
    def _getTrackName(track):
        track_name = ""
        #FIXME check that it is the best way to check the type
        if track.props.track_type.first_value_name == 'GES_TRACK_TYPE_AUDIO':
            track_name = _("Audio:")
        elif track.props.track_type.first_value_name == 'GES_TRACK_TYPE_VIDEO':
            track_name = _("Video:")
        elif track.props.track_type.first_value_name == 'GES_TRACK_TYPE_TEXT':
            track_name = _("Text:")
        return "<b>%s</b>" % track_name


class Transition(GooCanvas.CanvasRect, Zoomable):

    def __init__(self, transition):
        GooCanvas.CanvasRect.__init__(self)
        Zoomable.__init__(self)
        self.props.fill_color_rgba = 0xFFFFFF99
        self.props.stroke_color_rgba = 0x00000099
        self.set_simple_transform(0, - LAYER_SPACING + 3, 1.0, 0)
        self.props.height = LAYER_SPACING - 6
        self.props.pointer_events = GooCanvas.CanvasPointerEvents.NONE
        self.props.radius_x = 2
        self.props.radius_y = 2
        self.transition = transition

    def _setTransition(self):
        if self.transition:
            self._updateAll()

    def _updateAll(self):
        transition = self.transition
        start = transition.get_start()
        duration = transition.get_duration()
        priority = transition.get_priority()
        self._updateStart(transition, start)
        self._updateDuration(transition, duration)
        self._updatePriority(transition, priority)

    transition = receiver(_setTransition)

    @handler(transition, "notify::start")
    def _updateStart(self, transition, start):
        self.props.x = self.nsToPixel(start)

    @handler(transition, "notify::duration")
    def _updateDuration(self, transition, duration):
        width = max(0, self.nsToPixel(duration))
        if width == 0:
            self.props.visibility = GooCanvas.CanvasItemVisibility.INVISIBLE
        else:
            self.props.visibility = GooCanvas.CanvasItemVisibility.VISIBLE
        self.props.width = width

    @handler(transition, "notify::priority")
    def _updatePriority(self, transition, priority):
        self.props.y = (LAYER_HEIGHT_EXPANDED + LAYER_SPACING) * transition.get_priority()

    def zoomChanged(self):
        self._updateAll()


class Track(GooCanvas.CanvasGroup, Zoomable, Loggable):
    __gtype_name__ = 'Track'

    def __init__(self, instance, track, timeline=None):
        GooCanvas.CanvasGroup.__init__(self)
        Zoomable.__init__(self)
        Loggable.__init__(self)
        self.app = instance
        self.widgets = {}
        self.transitions = []
        self.timeline = timeline
        self.track = track
        self._expanded = True

## Properties

    def setExpanded(self, expanded):
        if expanded != self._expanded:
            self._expanded = expanded

            for widget in self.widgets.itervalues():
                widget.expanded = expanded
            self.get_canvas().regroupTracks()

    def getHeight(self):
        # FIXME we have a refcount issue somewhere, the following makes sure
        # no to crash because of it
        #track_objects = self.track.get_objects()
        if self._expanded:
            nb_layers = len(self.timeline.get_layers())

            return  nb_layers * (LAYER_HEIGHT_EXPANDED + LAYER_SPACING)
        else:
            return LAYER_HEIGHT_COLLAPSED + LAYER_SPACING

    height = property(getHeight)

## Public API

## track signals

    def _setTrack(self):
        self.debug("Setting track")
        if self.track:
            for trackobj in self.track.get_objects():
                self._objectAdded(None, trackobj)

    track = receiver(_setTrack)

    @handler(track, "track-object-added")
    def _objectAdded(self, unused_timeline, track_object):
        if isinstance(track_object, GES.TrackTransition):
            self._transitionAdded(track_object)
        elif not isinstance(track_object, GES.TrackEffect):
            #FIXME GES hack, waiting for the discoverer to do its job
            # so the duration properies are set properly
            GObject.timeout_add(1, self.check, track_object)

    def check(self, tr_obj):
        if tr_obj.get_timeline_object():
            w = TrackObject(self.app, tr_obj, self.track, self.timeline, self)
            self.widgets[tr_obj] = w
            self.add_child(w, 0)
            self.app.gui.setBestZoomRatio()

    @handler(track, "track-object-removed")
    def _objectRemoved(self, unused_timeline, track_object):
        if isinstance(track_object, GES.TrackVideoTestSource) or \
            isinstance(track_object, GES.TrackAudioTestSource) or \
            isinstance(track_object, GES.TrackParseLaunchEffect):
            return
        w = self.widgets[track_object]
        self.remove_child(w)
        del self.widgets[track_object]
        Zoomable.removeInstance(w)

    def _transitionAdded(self, transition):
        w = TrackObject(self.app, transition, self.track, self.timeline, self, True)
        self.widgets[transition] = w
        self.add_child(w, 0)
        self.transitions.append(w)
        w.raise_(None)
