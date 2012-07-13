#!/usr/bin/env python
import unittest
from test_basic import BaseDogTail
from dogtail.tree import SearchError
from helper_functions import help_test_import_media
from dogtail.predicate import GenericPredicate, IsATextEntryNamed
from dogtail.tree import SearchError


class MediaLibraryTest(BaseDogTail):
    help_test_import_media = help_test_import_media

    def test_medialibrary(self):
        #Load few samples
        samples = []
        samples.append(self.help_test_import_media("flat_colour1_640x480.png"))
        samples.append(self.help_test_import_media("flat_colour2_640x480.png"))
        samples.append(self.help_test_import_media("flat_colour3_320x180.png"))
        self.insert_clip(samples[0])
        self.insert_clip(samples[2])

        self.pitivi.menu("Library").click()
        self.pitivi.menu("Library").menuItem("Select Unused Media").click()
        self.assertFalse(samples[0].isSelected)
        self.assertTrue(samples[1].isSelected)
        self.assertFalse(samples[2].isSelected)

        tab = self.pitivi.tab("Media Library")
        iconview = tab.child(roleName="layered pane")
        self.assertEqual(len(iconview.children), 3)
        search = tab.textentry("")
        search.text = "colour2"
        self.assertEqual(len(iconview.children), 1)
        search.text = "640"
        self.assertEqual(len(iconview.children), 2)
        search.text = ""
        self.assertEqual(len(iconview.children), 3)
