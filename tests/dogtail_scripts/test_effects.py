#!/usr/bin/env python
import unittest
from test_basic import BaseDogTail
from dogtail.tree import SearchError
from helper_functions import help_test_import_media, drag
from dogtail.predicate import GenericPredicate, IsATextEntryNamed
from dogtail.tree import SearchError
import dogtail.rawinput
from time import sleep


class EffectLibraryTest(BaseDogTail):
    help_test_import_media = help_test_import_media

    def ig_test_effect_library(self):
        #Load sample
        self.help_test_import_media()
        tab = self.pitivi.tab("Effect Library")
        tab.click()
        search = tab.textentry("")
        iconview = tab.child(roleName="layered pane")
        combotypes = tab.child(name="All effects", roleName="combo box")
        #Some test of video effects and search
        search.text = "Crop"
        self.assertEqual(len(iconview.children), 3)
        combotypes.click()
        tab.menuItem("Colours").click()
        self.assertEqual(len(iconview.children), 0)
        combotypes.click()
        tab.menuItem("Geometry").click()
        self.assertEqual(len(iconview.children), 3)

        #Audio effects
        tab.child(name="Video effects", roleName="combo box").click()
        tab.menuItem("Audio effects").click()
        search.text = "Equa"
        #Titles plus 3 plugins, two collumns = 8
        self.assertEqual(len(tab.child(roleName="table").children), 8)

    def test_effect_drag(self):
        sample = self.help_test_import_media()
        sample.click(3)
        buttons = self.pitivi.findChildren(
            GenericPredicate(name="Insert at End of Timeline"))
        buttons[1].click()
        timeline = self.pitivi.children[0].children[0].children[2].children[1].children[3]
        clippos = (timeline.position[0] + 20, timeline.position[1] + 20)

        tab = self.pitivi.tab("Effect Library")
        tab.click()
        conftab = self.pitivi.tab("Clip configuration")
        conftab.click()
        table = conftab.child(roleName="table")
        tbpos = (table.position[0] + 50, table.position[1] + 50)

        dogtail.rawinput.click(clippos[0], clippos[1])
        sleep(2)
        self.assertTrue(table.sensitive)
        #No effects added
        self.assertEqual(len(table.children), 3)

        iconf = lambda obj: (obj.position[0] + obj.size[0] / 2, obj.position[1] + obj.size[1] / 2)
        icon = self.search_by_text("Agingtv ", tab, roleName="icon")

        #drag effect on the clip
        drag(iconf(icon), clippos)
        self.assertEqual(len(table.children), 6)
        #drag effect to the table
        icon = self.search_by_text("3Dflippo", tab, roleName="icon")
        drag(iconf(icon), tbpos)
        self.assertEqual(len(table.children), 9)
