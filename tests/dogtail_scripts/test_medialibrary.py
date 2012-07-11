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
        self.help_test_import_media("flat_colour1_640x480.png")
        self.help_test_import_media("flat_colour2_640x480.png")
        self.help_test_import_media("flat_colour3_320x180.png")
        tab = self.pitivi.tab("Media Library")
        self.assertEqual(len(tab.child(roleName="layered pane").children), 3)
        search = tab.textentry("")
        search.text = "colour2"
        self.assertEqual(len(tab.child(roleName="layered pane").children), 1)
        search.text = "640"
        self.assertEqual(len(tab.child(roleName="layered pane").children), 2)
        search.text = ""
        self.assertEqual(len(tab.child(roleName="layered pane").children), 3)
