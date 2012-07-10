#!/usr/bin/env python
import unittest
from test_basic import BaseDogTail
from dogtail.tree import SearchError
from helper_functions import help_test_import_media
from dogtail.predicate import GenericPredicate, IsATextEntryNamed
from dogtail.tree import SearchError


class DialogsClipMediaPropsTest(BaseDogTail):
    help_test_import_media = help_test_import_media

    def test_pref_dialog(self):
        sample = self.help_test_import_media("flat_colour1_640x480.png")
        sample.click(3)
        buttons = self.pitivi.findChildren(GenericPredicate(name="Clip Properties..."))
        buttons[1].click()
        #Check if we have real info, can't check if in correct place.
        dialog = self.pitivi.child(name="Clip Properties", roleName="dialog")
        labels = ["640", "480"]
        for label in labels:
            try:
                dialog.child(name=label, roleName="label")
            except SearchError:
                self.fail("Not displayed %s in clip information" % label)
        self.assertFalse(dialog.child(name="Audio:", roleName="panel").showing)
        dialog.child(name="Cancel").click()

        sample = self.help_test_import_media()
        sample.click(3)
        buttons = self.pitivi.findChildren(GenericPredicate(name="Clip Properties..."))
        buttons[1].click()
        #Check if we have real info, can't check if in correct place.
        dialog = self.pitivi.child(name="Clip Properties", roleName="dialog")
        labels = ["1280", "544", "23.976 fps", "Square", "Stereo", "48 KHz", "16 bit"]
        for label in labels:
            try:
                dialog.child(name=label, roleName="label")
            except SearchError:
                self.fail("Not displayed %s in clip information" % label)

        #Uncheck frame rate
        dialog.child(name="Frame rate:").click()
        dialog.child(name="Apply to project").click()

        #Check if applied
        self.pitivi.menu("Edit").click()
        self.pitivi.child(name="Project Settings", roleName="menu item").click()
        dialog = self.pitivi.child(name="Project Settings", roleName="dialog")

        children = dialog.findChildren(IsATextEntryNamed(""))
        childtext = {}
        for child in children:
                childtext[child.text] = child

        self.assertIn("25:1", childtext)
        self.assertIn("1:1", childtext)
        children = dialog.findChildren(GenericPredicate(roleName="spin button"))
        spintext = {}
        for child in children:
                spintext[child.text] = child
        self.assertIn("1280", spintext)
        self.assertIn("544", spintext)
