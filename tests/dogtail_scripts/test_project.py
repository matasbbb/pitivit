#!/usr/bin/env python

import unittest
from test_basic import BaseDogTail
from dogtail.predicate import IsATextEntryNamed, GenericPredicate
import hashlib
from time import time, sleep


class ProjectPropertiesTest(BaseDogTail):
    def test_settings_video(self):
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

        children = video.findChildren(GenericPredicate(roleName="spin button"))
        spintext = {}
        for child in children:
                spintext[child.text] = child
        self.assertIn("1280", spintext)
        self.assertIn("720", spintext)

        #Test frame rate combinations, link button
        frameCombo = video.child(name="23.976 fps", roleName="combo box")
        frameText = childtext["24M"]
        frameCombo.click()
        video.child(name="120 fps", roleName="menu item").click()
        self.assertEqual(frameText.text, "120:1")
        frameText.click()
        frameText.typeText("0")
        video.child(name="12 fps", roleName="combo box")

        #Test pixel and display ascpect ratio
        pixelCombo = video.child(name="Square", roleName="combo box")
        pixelText = childtext["1:1"]
        displayCombo = video.child(name="DV Widescreen (16:9)",
                                   roleName="combo box")
        displayText = childtext["16:9"]

        pixelCombo.click()
        video.child(name="576p", roleName="menu item").click()
        self.assertEqual(pixelCombo.combovalue, "576p")
        self.assertEqual(pixelText.text, "12:11")
        #self.assertEqual(displayCombo.combovalue, "")
        self.assertEqual(displayText.text, "64:33")

        pixelText.doubleClick()
        pixelText.click()
        pixelText.typeText("3:4")
        #self.assertEqual(pixelCombo.combovalue, "")
        self.assertEqual(pixelText.text, "3:4")
        self.assertEqual(displayCombo.combovalue, "Standard (4:3)")
        self.assertEqual(displayText.text, "4:3")

        video.child(name="Display aspect ratio",
                    roleName="radio button").click()
        displayCombo.click()
        video.child(name="Cinema (1.37)", roleName="menu item").click()
        #self.assertEqual(pixelCombo.combovalue, "")
        self.assertEqual(pixelText.text, "99:128")
        self.assertEqual(displayCombo.combovalue, "Cinema (1.37)")
        self.assertEqual(displayText.text, "11:8")

        displayText.doubleClick()
        displayText.click()
        displayText.typeText("37:20")
        #self.assertEqual(pixelCombo.combovalue, "")
        self.assertEqual(pixelText.text, "333:320")
        self.assertEqual(displayCombo.combovalue, "Cinema (1.85)")
        self.assertEqual(displayText.text, "37:20")

        #Test size spin buttons
        spin = video.findChildren(GenericPredicate(roleName="spin button"))
        oldtext = spin[1].text
        spin[0].doubleClick()
        spin[0].typeText("1000")
        self.assertEqual(spin[1].text, oldtext)
        spin[1].doubleClick()
        spin[1].typeText("2000")
        video.child(name="Link").click()
        spin[1].doubleClick()
        spin[1].typeText("1000")
        spin[0].click()
        self.assertEqual(spin[0].text, "500")

        #Create project, test saving without any object
        self.pitivi.child(name="OK", roleName="push button").click()
        self.saveAsProject("/tmp/settings.xptv")
        sleep(3)
        #Load project and test settings
        self.loadProject("/tmp/settings.xptv")
        sleep(1)
        self.pitivi.menu("Edit").click()
        self.pitivi.child(name="Project Settings", roleName="menu item").click()

        video = self.pitivi.tab("Video")

        children = video.findChildren(IsATextEntryNamed(""))
        childtext = {}
        for child in children:
                childtext[child.text] = child

        self.assertIn("333:320", childtext, "Pixel aspect ration not saved")
        self.assertIn("37:20", childtext, "Display aspect ratio not saved")

        children = video.findChildren(GenericPredicate(roleName="spin button"))
        spintext = {}
        for child in children:
                spintext[child.text] = child
        self.assertIn("500", spintext, "Video height is not saved")
        self.assertIn("1000", spintext, "Video width is not saved")


if __name__ == '__main__':
    unittest.main()
