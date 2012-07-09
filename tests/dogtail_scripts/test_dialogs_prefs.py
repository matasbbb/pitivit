#!/usr/bin/env python
import unittest
from test_basic import BaseDogTail
from dogtail.tree import SearchError


class DialogsPreferencesTest(BaseDogTail):
    def test_pref_dialog(self):
        self.pitivi.child(name="New", roleName='push button').click()
        self.pitivi.child(name="OK", roleName="push button").click()
        self.pitivi.menu("Edit").click()
        self.pitivi.child(name="Preferences", roleName="menu item").click()
        dialog = self.pitivi.child(name="Preferences", roleName="dialog")
        dialog.child("Reset to Factory Settings", roleName="push button").click()

        #Try choose the font
        dialog.child(name="Sans", roleName="label").click()
        fontchooser = self.pitivi.child(name="Pick a Font", roleName="fontchooser")
        fontchooser.child(name="Serif").click()
        fontchooser.child(name="OK", roleName="push button").click()

        #Try choose thumbnail gap
        dialog.child(roleName="spin button").text = "12"

        #Restart pitivi, look if saved
        dialog.button("Close")

        self.tearDown()
        self.setUp()
        self.pitivi.child(name="New", roleName='push button').click()
        self.pitivi.child(name="OK", roleName="push button").click()
        self.pitivi.menu("Edit").click()
        self.pitivi.child(name="Preferences", roleName="menu item").click()
        dialog = self.pitivi.child(name="Preferences", roleName="dialog")

        #Just search of such item
        try:
            dialog.child(name="Serif", roleName="label")
        except SearchError:
            self.fail("Font is not saved")
        self.assertEqual(dialog.child(roleName="spin button").text, 12)

        #Check revert
        dialog.child(roleName="spin button").text = "7"
        dialog.child("Revert", roleName="push button").click()
        self.assertEqual(dialog.child(roleName="spin button").text, 12, "Spacing is not reverted")

        #Check reset to factory settings
        dialog.child("Reset to Factory Settings", roleName="push button").click()
        dialog.child(name="Sans", roleName="label")
        self.assertEqual(dialog.child(roleName="spin button").text, 5, "Spacing is not reseted")
