#!/usr/bin/env python

import unittest
from test_basic import BaseDogTail
from dogtail.predicate import IsATextEntryNamed
import hashlib


class SettingDialogTest(BaseDogTail):
    def test_settings(self):
        #Just create new project
        self.pitivi.child(name="New", roleName='push button').click()

        #Play with project settings, look if they are correctly represented
        dialog = self.pitivi.child(name="Project Settings", roleName="dialog")
        video = self.pitivi.tab("Video")

        #Test presets
        video.child(name="720p24", roleName="table cell").click()
        children = video.findChildren(IsATextEntryNamed(""))
        childtext = {}
        for child in children:
                childtext[child.text] = child

        self.assertIn("1:1", childtext)
        self.assertIn("24M", childtext)
        self.assertIn("16:9", childtext)

        #Test frame rate combinations
        frameCombo = video.child(name="23.976 fps", roleName="combo box")
        frameText = childtext["24M"]
        frameCombo.click()
        video.child(name="120 fps", roleName="menu item").click()
        self.assertEqual(frameText.text, "120:1")
        frameText.click()
        frameText.typeText("0")
        video.child(name="12 fps", roleName="combo box")

        #Create project
        self.pitivi.child(name="OK", roleName="push button").click()
        self.saveAsProject("/tmp/settings.xptv")
        #TODO: save project and than checksum it with good one
        #print hashlib.md5(file("/tmp/settings.xptv", 'r').read()).digest()

if __name__ == '__main__':
    unittest.main()
