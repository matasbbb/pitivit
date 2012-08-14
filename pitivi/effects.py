# PiTiVi , Non-linear video editor
#
#       effects.py
#
# Copyright (c) 2010, Thibault Saunier <tsaunier@gnome.org>
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
Effects global handling
 Note: Some effects are available through the frei0r
 library and the libavfilter0 library

 There are different types of effects available:
  _ Simple Audio/Video Effects
     GStreamer elements that only apply to audio OR video
     Only take the elements who have a straightforward meaning/action
  _ Expanded Audio/Video Effects
     These are the Gstreamer elements that don't have a easy meaning/action or
     that are too cumbersome to use as such
  _ Complex Audio/Video Effects
"""
import glib
import gst
import gtk
import re
import os
import gobject
import time
import pango

from gi.repository import Gdk

from gettext import gettext as _

from pitivi.configure import get_pixmap_dir
from pitivi.settings import GlobalSettings

import pitivi.utils.ui as dnd
from pitivi.utils.loggable import Loggable
from pitivi.utils.ui import SPACING

from pitivi.utils.widgets import GstElementSettingsWidget, FractionWidget


#------------- Helper to handle effect in the backend ---------------------------#
(VIDEO_EFFECT, AUDIO_EFFECT) = range(2)

BLACKLISTED_EFFECTS = ["colorconvert", "coglogoinsert", "festival",
                       "alphacolor", "cogcolorspace", "videodetect",
                       "navigationtest", "videoanalyse"]

#FIXME Check if this is still true with GES
#We should unblacklist it when #650985 is solved
BLACKLISTED_PLUGINS = ["ldaspa"]


class Effect():
    """
    Factories that applies an effect on a stream
    """
    def __init__(self, effect, media_type, categories=[_("Uncategorized")],
                  human_name="", description="", icon=None):
        self.effectname = effect
        self.media_type = media_type
        self.categories = categories
        self.description = description
        self.human_name = human_name
        self._icon = icon

    def getHumanName(self):
        return self.human_name

    def getDescription(self):
        return self.description

    def getCategories(self):
        return self.categories


class EffectsHandler(object):
    """
    Handles all the effects
    """
    def __init__(self):
        object.__init__(self)
        self._pixdir = os.path.join(get_pixmap_dir(), "effects")
        self._audio_categories_effects = ((_("All effects"), ("")),)
        self._video_categories_effects = (
            (_("All effects"), ("")),
            (_("Colors"), ("cogcolorspace", "alphacolor", "videobalance",
                  "gamma", "alpha", "frei0r-filter-color-distance",
                  "frei0r-filter-contrast0r", "frei0r-filter-invert0r",
                  "frei0r-filter-saturat0r", "frei0r-filter-r",
                  "frei0r-filter-white-balance", "frei0r-filter-brightness",
                  "frei0r-filter-b", "frei0r-filter-gamma",
                  "frei0r-filter-hueshift0r", "frei0r-filter-transparency",
                  "frei0r-filter-equaliz0r", "frei0r-filter-glow",
                  "frei0r-filter-g", "frei0r-filter-bw0r", "burn", "dodge",
                  "coloreffects", "chromium", "exclusion", "glfiltersobel",
                  "Solarize", "frei0r-filter-threshold0r",
                  "frei0r-filter-twolay0r",
                )
            ),
            (_("Noise"), ("videorate", "frei0r-filter-edgeglow",
                  "gaussianblur", "diffuse", "dilate", "marble", )),
            (_("Analysis"), ("videoanalyse", "videodetect", "videomark",
                 "revtv", "navigationtest", "frei0r-filter-rgb-parade",
                 "frei0r-filter-vectorscope", "frei0r-filter-luminance",
                          )),
            (_("Blur"), ("frei0r-filter-squareblur", "gaussianblur", "diffuse",
                 "dilate", "marble", )),
            (_("Geometry"), ("cogscale", "aspectratiocrop", "cogdownsample",
                  "videocrop", "videoflip", "videobox", "gdkpixbufscale",
                  "frei0r-filter-letterb0xed",
                  "frei0r-filter-k-means-clustering",
                  "videoscale", "frei0r-filter-lens-correction",
                  "frei0r-filter-perspective",
                  "frei0r-filter-scale0tilt", "frei0r-filter-pixeliz0r",
                  "frei0r-filter-flippo", "frei0r-filter-3dflippo",
                  "frei0r-filter-letterb0xed", "bulge", "circle", "fisheye",
                  "kaleidoscope", "mirror", "pinch", "sphere", "square",
                  "stretch", "twirl", "waterriple",
                  )
            ),
            (_("Fancy"), ("rippletv", "streaktv", "radioactv", "optv",
                 "quarktv", "vertigotv", "shagadelictv", "warptv", "dicetv",
                 "agingtv", "edgetv", "frei0r-filter-cartoon",
                 "frei0r-filter-water", "frei0r-filter-nosync0r",
                 "frei0r-filter-k-means-clustering", "frei0r-filter-delay0r",
                 "bulge", "circle", "fisheye", "kaleidoscope", "mirror",
                 "pinch", "sphere", "square", "stretch", "twirl", "waterriple",
             )
            ),
            (_("Time"), ("frei0r-filter-delay0r",)),
            (_("Uncategorized"), ("",))
        )
        self._audio_categories = set([])
        self._video_categories = set([])
        self.video_effects = []
        self.audio_effects = []
        self._effect_factories_dict = {}
        self._setAllEffects()

    def _setAllEffects(self):
        """
        go trough the list of element factories and
        add them to the correct list filtering if necessary
        """
        factlist = gst.registry_get_default().get_feature_list(
            gst.ElementFactory)
        for element_factory in factlist:
            klass = element_factory.get_klass()
            name = element_factory.get_name()
            if "Effect" in klass and name not in BLACKLISTED_EFFECTS and not\
                [bplug for bplug in BLACKLISTED_PLUGINS if bplug in name]:
                if 'Audio' in klass:
                    self.audio_effects.append(element_factory)
                    media_type = AUDIO_EFFECT
                elif 'Video' in klass:
                    self.video_effects.append(element_factory)
                    media_type = VIDEO_EFFECT
                effect = Effect(name, media_type,
                                   self._getEffectCategories(name),
                                   self._getEffectName(element_factory),
                                   self._getEffectDescripton(element_factory))
                self._addEffectToDic(name, effect)

    def getAllAudioEffects(self):
        """
        @returns:  the list off available audio effects elements
        """
        return self.audio_effects

    def getAllVideoEffects(self):
        """
        @returns: the list off available video effects elements
        """
        return self.video_effects

    def _addEffectToDic(self, name, factory):
        self._effect_factories_dict[name] = factory

    def getFactoryFromName(self, name):
        """
        @ivar name: Factory name.
        @type name: C{str}
        @returns: The l{Effect} corresponding to the name
        @raises: KeyError if the name doesn't  exist
        """
        return self._effect_factories_dict.get(name)

    def _getEffectDescripton(self, element_factory):
        """
        @ivar element_factory: The element factory
        @type element_factory: L{gst.ElementFactory}
        @returns: A human description C{str} for the effect
        """
        return element_factory.get_description()

    def _getEffectCategories(self, effect_name):
        """
        @ivar effect_name: the name of the effect for wich we want the category
        @type effect_name: L{str}
        @returns: A C{list} of name C{str} of categories corresponding the
        effect
        """
        categories = []

        for categorie in self._audio_categories_effects:
            for name in categorie[1]:
                if name == effect_name:
                    categories.append(categorie[0])
                    self._audio_categories.append(categorie[0])

        for categorie in self._video_categories_effects:
            for name in categorie[1]:
                if name == effect_name:
                    categories.append(categorie[0])
                    self._video_categories.add(categorie[0])

        if not categories:
            uncategorized = _("Uncategorized")
            categories.append(uncategorized)
            self._video_categories.add(uncategorized)
            self._audio_categories.add(uncategorized)

        categories.insert(0, self._video_categories_effects[0][0])
        categories.insert(0, self._audio_categories_effects[0][0])

        return categories

    def _getEffectName(self, element_factory):
        """
        @ivar element_factory: The element factory
        @type element_factory: L{gst.ElementFactory}
        @returns: A human readable name C{str} for the effect
        """
        #TODO check if it is the good way to make it translatable
        #And to filter actually!
        video = _("Video")
        audio = _("Audio |audio")
        effect = _("effect")
        pipe = " |"
        uselessWords = re.compile(video + pipe + audio + pipe + effect)
        return uselessWords.sub("", element_factory.get_longname()).title()

    def getVideoCategories(self, aware=True):
        """
        @ivar  aware: C{True} if you want it to return only categories on
        whichs
        there are effects on the system, else C{False}
        @type aware: C{bool}
        @returns: All video effect categories names C{str} that are available
        on the system if it has been filled earlier, if it hasen't it will
        just return all categories
        """
        if not self._video_categories or not aware:
            for categorie in self._video_categories_effects[1:]:
                self._video_categories.add(categorie[0])

        ret = list(self._video_categories)
        ret.sort()
        ret.insert(0, self._video_categories_effects[0][0])

        return ret

    video_categories = property(getVideoCategories)

    def getAudioCategories(self, aware=True):
        """
        @ivar  aware: C{True} if you want it to return only categories on
        whichs there are effects on the system, else C{False}
        @type aware: C{bool}
        @returns: All audio effect categories names C{str}
        """
        if not self._audio_categories or not aware:
            for categorie in self._audio_categories_effects[1:]:
                self._audio_categories.add(categorie[0])

        ret = list(self._audio_categories)
        ret.sort()
        ret.insert(0, self._audio_categories_effects[0][0])

        return ret

    audio_categories = property(getAudioCategories)

    def getAllCategories(self):
        """
        @returns: All effect categories names C{str}
        """
        effects_categories = []
        return effects_categories.extended(self.video_categories).extended(
            self.audio_categories)

    def getEffectIcon(self, effect_name):
        effect_name = effect_name + ".png"
        icon = None
        try:
            icon = gtk.gdk.pixbuf_new_from_file(os.path.join(self._pixdir,
                effect_name))
        # empty except clause is bad but load_icon raises gio.Error.
        ## Right, *gio*.
        except:
            try:
                icon = gtk.gdk.pixbuf_new_from_file(os.path.join(self._pixdir,
                    "defaultthumbnail.svg"))
            except:
                return None

        return icon


#----------------------- UI classes to manage effects -------------------------#
HIDDEN_EFFECTS = ["frei0r-filter-scale0tilt"]

GlobalSettings.addConfigSection('effect-library')

(COL_NAME_TEXT,
 COL_DESC_TEXT,
 COL_EFFECT_TYPE,
 COL_EFFECT_CATEGORIES,
 COL_FACTORY,
 COL_ELEMENT_NAME,
 COL_ICON) = range(7)

INVISIBLE = gtk.gdk.pixbuf_new_from_file(os.path.join(get_pixmap_dir(),
    "invisible.png"))


class EffectListWidget(gtk.VBox, Loggable):
    """ Widget for listing effects """

    def __init__(self, instance, uiman):
        gtk.VBox.__init__(self)
        Loggable.__init__(self)

        self.app = instance
        self.settings = instance.settings

        self._dragButton = None
        self._dragStarted = False
        self._dragSelection = False
        self._dragX = 0
        self._dragY = 0

        #Searchbox and combobox
        hfilters = gtk.HBox()
        hfilters.set_spacing(SPACING)
        hfilters.set_border_width(3)  # Prevents being flush against the notebook
        self.effectType = gtk.ComboBoxText()
        self.effectType.append_text(_("Video effects"))
        self.effectType.append_text(_("Audio effects"))
        self.effectCategory = gtk.ComboBoxText()
        self.effectType.set_active(VIDEO_EFFECT)

        hfilters.pack_start(self.effectType, expand=True)
        hfilters.pack_end(self.effectCategory, expand=True)

        hsearch = gtk.HBox()
        hsearch.set_spacing(SPACING)
        hsearch.set_border_width(3)  # Prevents being flush against the notebook
        searchStr = gtk.Label(_("Search:"))
        self.searchEntry = gtk.Entry()
        self.searchEntry.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, "gtk-clear")
        hsearch.pack_start(searchStr, expand=False)
        hsearch.pack_end(self.searchEntry, expand=True)

        # Store
        self.storemodel = gtk.ListStore(str, str, int, object, object, str, gtk.gdk.Pixbuf)

        scrollwin = gtk.ScrolledWindow()
        scrollwin.props.hscrollbar_policy = gtk.POLICY_NEVER
        scrollwin.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        scrollwin.props.shadow_type = gtk.SHADOW_ETCHED_IN

        self.view = gtk.TreeView(self.storemodel)
        scrollwin.add(self.view)
        self.view.props.headers_visible = False
        tsel = self.view.get_selection()
        tsel.set_mode(gtk.SELECTION_SINGLE)

        icon_col = gtk.TreeViewColumn()
        self.view.append_column(icon_col)
        icon_col.props.spacing = SPACING
        icon_col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        icon_col.props.fixed_width = 96
        icon_cell = gtk.CellRendererPixbuf()
        icon_cell.props.xpad = 6
        icon_col.pack_start(icon_cell)
        icon_col.add_attribute(icon_cell, "pixbuf", COL_ICON)

        text_col = gtk.TreeViewColumn()
        self.view.append_column(text_col)
        text_col.set_expand(True)
        text_col.set_spacing(SPACING)
        text_col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        text_col.set_min_width(150)
        text_cell = gtk.CellRendererText()
        text_cell.props.yalign = 0.0
        text_cell.props.xpad = 6
        text_cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        text_col.pack_start(text_cell)
        text_col.set_cell_data_func(text_cell,
                                    self.view_description_cell_data_func,
                                    None)

        self.effectType.connect("changed", self._effectTypeChangedCb)

        self.effectCategory.connect("changed", self._effectCategoryChangedCb)

        self.searchEntry.connect("changed", self.searchEntryChangedCb)
        self.searchEntry.connect("focus-in-event", self.searchEntryActivateCb)
        self.searchEntry.connect("focus-out-event", self.searchEntryDesactvateCb)
        self.searchEntry.connect("icon-press", self.searchEntryIconClickedCb)

        self.view.connect("button-press-event", self._buttonPressEventCb)
        self.view.connect("select-cursor-row", self._enterPressEventCb)
        self.view.connect("motion-notify-event", self._motionNotifyEventCb)
        self.view.connect("button-release-event", self._buttonReleaseCb)
        self.view.drag_source_set(0, [], gtk.gdk.ACTION_COPY)
        self.view.connect("drag_begin", self._dndDragBeginCb)
        self.view.connect("drag_data_get", self._dndDataGetCb)

        # Delay the loading of the available effects so the application
        # starts faster.
        gobject.idle_add(self._loadAvailableEffectsCb)

        self.pack_start(hfilters, expand=False)
        self.pack_start(hsearch, expand=False)
        self.pack_end(scrollwin, expand=True)

        #create the filterModel
        self.modelFilter = self.storemodel.filter_new()
        self.modelFilter.set_visible_func(self._setRowVisible, data=None)
        self.view.set_model(self.modelFilter)

        self.show_categories(VIDEO_EFFECT)

        # Individually show the tab's widgets.
        # If you use self.show_all(), the tab will steal focus on startup.
        hfilters.show_all()
        hsearch.show_all()
        scrollwin.show_all()

    @staticmethod
    def view_description_cell_data_func(column, cell, model, iter_, data):

        name, desc = model.get(iter_, COL_NAME_TEXT, COL_DESC_TEXT)
        escape = glib.markup_escape_text
        cell.props.markup = "<b>%s</b>\n%s" % (escape(name),
                                               escape(desc),)

    def _loadAvailableEffectsCb(self):
        self._addFactories(self.app.effects.getAllVideoEffects(), VIDEO_EFFECT)
        self._addFactories(self.app.effects.getAllAudioEffects(), AUDIO_EFFECT)
        return False

    def _addFactories(self, elements, effectType):
        for element in elements:
            name = element.get_name()
            if name not in HIDDEN_EFFECTS:
                effect = self.app.effects.getFactoryFromName(name)
                self.storemodel.append([effect.getHumanName(),
                                         effect.getDescription(), effectType,
                                         effect.getCategories(),
                                         effect, name,
                                         self.app.effects.getEffectIcon(name)])
                self.storemodel.set_sort_column_id(COL_NAME_TEXT, gtk.SORT_ASCENDING)

    def show_categories(self, effectType):
        self.effectCategory.get_model().clear()
        self._effect_type_ref = effectType
        icon_column = self.view.get_column(0)

        if effectType is VIDEO_EFFECT:
            for categorie in self.app.effects.video_categories:
                self.effectCategory.append_text(categorie)
            icon_column.props.visible = True
        else:
            for categorie in self.app.effects.audio_categories:
                self.effectCategory.append_text(categorie)
            icon_column.props.visible = False

        self.effectCategory.set_active(0)

    def _dndDragBeginCb(self, view, context):
        self.info("tree drag_begin")

        model, paths = self.view.get_selection().get_selected_rows()

        if not paths:
            context.drag_abort(int(time.time()))
            return

        path = paths[0]
        pixbuf = model.get_value(model.get_iter(path), COL_ICON)
        if pixbuf:
            gtk.drag_set_icon_pixbuf(context, pixbuf, 0, 0)

    def _rowUnderMouseSelected(self, view, event):
        result = view.get_path_at_pos(int(event.x), int(event.y))
        if result:
            path = result[0]
            selection = view.get_selection()
            return selection.path_is_selected(path) and\
                selection.count_selected_rows() > 0
        return False

    def _enterPressEventCb(self, view, event=None):
        factory_name = self.getSelectedItems()
        if factory_name is not None:
            self.app.gui.clipconfig.effect_expander.addEffectToCurrentSelection(factory_name)

    def _buttonPressEventCb(self, view, event):
        chain_up = True

        if event.button == 3:
            chain_up = False
        elif event.type == Gdk.EventType._2BUTTON_PRESS:
            factory_name = self.getSelectedItems()
            if factory_name is not None:
                self.app.gui.clipconfig.effect_expander.addEffectToCurrentSelection(factory_name)
        else:
            chain_up = not self._rowUnderMouseSelected(view, event)

            self._dragStarted = False
            self._dragSelection = False
            self._dragButton = event.button
            self._dragX = int(event.x)
            self._dragY = int(event.y)

        if chain_up:
            gtk.TreeView.do_button_press_event(view, event)
        else:
            view.grab_focus()

        return True

    def _motionNotifyEventCb(self, view, event):
        chain_up = True

        if not self._dragButton:
            return True

        if self._nothingUnderMouse(view, event):
            return True

        if not event.state & (gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK):
            chain_up = not self._rowUnderMouseSelected(view, event)

        if view.drag_check_threshold(self._dragX, self._dragY,
            int(event.x), int(event.y)):
            context = view.drag_begin(
                gtk.TargetList.new(self._getTargetEntries()),
                gtk.gdk.ACTION_COPY,
                self._dragButton,
                event)
            self._dragStarted = True

        if chain_up:
            gtk.TreeView.do_button_press_event(view, event)
        else:
            view.grab_focus()

        return False

    def _buttonReleaseCb(self, treeview, event):
        if event.button == self._dragButton:
            self._dragButton = None
        return False

    def getSelectedItems(self):
        model, rows = self.view.get_selection().get_selected_rows()
        path = self.modelFilter.convert_path_to_child_path(rows[0])

        return self.storemodel[path][COL_ELEMENT_NAME]

    def _dndDataGetCb(self, unused_widget, context, selection,
                      targettype, unused_eventtime):
        self.info("data get, type:%d", targettype)
        factory = self.getSelectedItems()
        if factory is None or len(factory) < 1:
            return

        selection.set(selection.target, 8, factory)
        gtk.drag_set_icon_pixbuf(context, INVISIBLE, 0, 0)

    def _effectTypeChangedCb(self, combobox):
        self.modelFilter.refilter()
        self.show_categories(combobox.get_active())

    def _effectCategoryChangedCb(self, combobox):
        self.modelFilter.refilter()

    def searchEntryChangedCb(self, entry):
        self.modelFilter.refilter()

    def searchEntryIconClickedCb(self, entry, unused, unsed1):
        entry.set_text("")

    def searchEntryDesactvateCb(self, entry, event):
        self.app.gui.setActionsSensitive(True)

    def searchEntryActivateCb(self, entry, event):
        self.app.gui.setActionsSensitive(False)

    def _setRowVisible(self, model, iter, data):
        if self.effectType.get_active() == model.get_value(iter, COL_EFFECT_TYPE):
            if model.get_value(iter, COL_EFFECT_CATEGORIES) is None:
                return False
            if self.effectCategory.get_active_text() in model.get_value(iter, COL_EFFECT_CATEGORIES):
                text = self.searchEntry.get_text().lower()
                return text in model.get_value(iter, COL_DESC_TEXT).lower() or\
                       text in model.get_value(iter, COL_NAME_TEXT).lower()
            else:
                return False
        else:
            return False

    def _nothingUnderMouse(self, view, event):
        return not bool(view.get_path_at_pos(int(event.x), int(event.y)))

    def _getTargetEntries(self):
        if self.effectType.get_active() == VIDEO_EFFECT:
            return [dnd.VIDEO_EFFECT_TARGET_ENTRY, dnd.EFFECT_TARGET_ENTRY]
        else:
            return [dnd.AUDIO_EFFECT_TARGET_ENTRY, dnd.EFFECT_TARGET_ENTRY]

PROPS_TO_IGNORE = ['name', 'qos', 'silent', 'message']


class EffectsPropertiesManager:
    def __init__(self, instance):
        self.cache_dict = {}
        self._current_effect_setting_ui = None
        self._current_element_values = {}
        self.action_log = instance.action_log
        self.app = instance

    def getEffectConfigurationUI(self, effect):
        """
            Permit to get a configuration GUI for the effect
            @param effect: The effect for which we want the configuration UI
            @type effect: C{gst.Element}
        """

        if effect not in self.cache_dict:
            #Here we should handle special effects configuration UI
            effect_set_ui = GstElementSettingsWidget()
            effect_set_ui.setElement(effect, ignore=PROPS_TO_IGNORE,
                                     default_btn=True, use_element_props=True)
            nb_rows = effect_set_ui.get_children()[0].get_property('n-rows')
            effect_configuration_ui = gtk.ScrolledWindow()
            effect_configuration_ui.add_with_viewport(effect_set_ui)
            effect_configuration_ui.set_policy(gtk.POLICY_AUTOMATIC,
                                               gtk.POLICY_AUTOMATIC)
            self.cache_dict[effect] = effect_configuration_ui
            self._connectAllWidgetCbs(effect_set_ui, effect)
            self._postConfiguration(effect, effect_set_ui)

        effect_set_ui = self._getUiToSetEffect(effect)

        self._current_effect_setting_ui = effect_set_ui
        element = self._current_effect_setting_ui.element
        count = 0
        for prop in element.list_children_properties(count):
            self._current_element_values[prop.name] = element.get_child_property(prop.name)

        return self.cache_dict[effect]

    def cleanCache(self, effect):
        if effect in self.cache_dict:
            conf_ui = self.cache_dict.get(effect)
            self.cache_dict.pop(effect)
            return conf_ui

    def _postConfiguration(self, effect, effect_set_ui):
        if 'aspectratiocrop' in effect.get_property("bin-description"):
            for widget in effect_set_ui.get_children()[0].get_children():
                if isinstance(widget, FractionWidget):
                    widget.addPresets(["4:3", "5:4", "9:3", "16:9", "16:10"])

    def _getUiToSetEffect(self, effect):
        """ Permit to get the widget to set the effect and not its container """
        if type(self.cache_dict[effect]) is gtk.ScrolledWindow:
            effect_set_ui = self.cache_dict[effect].get_children()[0].get_children()[0]
        else:
            effect_set_ui = self.cache_dict[effect]

        return effect_set_ui

    def _connectAllWidgetCbs(self, effect_configuration_ui, effect):
        for prop, widget in effect_configuration_ui.properties.iteritems():
            widget.connectValueChanged(self._onValueChangedCb, widget, prop)

    def _onSetDefaultCb(self, widget, dynamic):
        dynamic.setWidgetToDefault()

    def _onValueChangedCb(self, widget, dynamic, prop):
        value = dynamic.getWidgetValue()

        #FIXME Workaround in order to make aspectratiocrop working
        if isinstance(value, gst.Fraction):
            value = gst.Fraction(int(value.num), int(value.denom))

        if value != self._current_element_values.get(prop.name):
            self.action_log.begin("Effect property change")
            self._current_effect_setting_ui.element.set_child_property(prop.name, value)
            self.action_log.commit()

            self.app.current.pipeline.flushSeek()
            self._current_element_values[prop.name] = value
