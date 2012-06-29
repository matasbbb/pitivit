#!/usr/bin/env python

import unittest
from test_basic import BaseDogTail
from dogtail.predicate import GenericPredicate
import dogtail.rawinput
import os
from time import sleep


class TimelineTest(BaseDogTail):

    def test_import_clip(self):
        self.pitivi.child(name="New", roleName='push button').click()
        self.pitivi.child(name="OK", roleName="push button").click()
        self.pitivi.child(name="Import Files...",
                          roleName="push button").click()
        add = self.pitivi.child(roleName='dialog')
        add.child(name="Type a file name", roleName="toggle button").click()
        filepath = os.path.realpath(__file__).split("dogtail_scripts/test_timeline.py")[0]
        filepath += "samples/1sec_simpsons_trailer.mp4"
        add.child(roleName='text').text = filepath
        add.button('Add').click()
        icons = self.pitivi.findChildren(GenericPredicate(roleName="icon"))
        sample = None
        for icon in icons:
            if icon.text == "1sec_simpsons_trailer.mp4":
                sample = icon

        self.assertIsNotNone(sample)
        return sample

    def test_insert_at_end(self):
        sample = self.test_import_clip()
        #Right click
        texts = self.pitivi.findChildren(GenericPredicate(roleName="text"))
        seektime = None
        for text in texts:
            if text.text == "0:00:00.000":
                seektime = text

        self.assertIsNotNone(seektime)

        sample.click(3)
        buttons = self.pitivi.findChildren(
            GenericPredicate(name="Insert at End of Timeline"))
        buttons[1].click()
        self.pitivi.child(name="Next", roleName="push button").click()
        self.assertEqual(seektime.text, "0:00:01.227")

        #Add one more
        sample.click(3)
        buttons = self.pitivi.findChildren(
            GenericPredicate(name="Insert at End of Timeline"))
        buttons[1].click()
        self.pitivi.child(name="Next", roleName="push button").click()

        self.assertEqual(seektime.text, "0:00:02.455")

    def test_drag_clip(self):
        sample = self.test_import_clip()
        #Right click
        texts = self.pitivi.findChildren(GenericPredicate(roleName="text"))
        seektime = None
        for text in texts:
            if text.text == "0:00:00.000":
                seektime = text

        self.assertIsNotNone(seektime)
        self.pitivi.findChildren(GenericPredicate(roleName="layered pane"))
        timeline = self.pitivi.children[0].children[0].children[2].children[1].children[3]
        dogtail.rawinput.press(sample.position[0] + sample.size[0] / 2,
                               sample.position[1] + sample.size[1] / 2)
        dogtail.rawinput.relativeMotion(10, 10)
        dogtail.rawinput.absoluteMotion(timeline.position[0] + timeline.size[0] / 2,
                                        timeline.position[1] + timeline.size[1] / 2)
        sleep(1)
        dogtail.rawinput.relativeMotion(10, 10)
        sleep(3)
        dogtail.rawinput.release(timeline.position[0] + timeline.size[0] / 2,
                                 timeline.position[1] + timeline.size[1] / 2)
        sleep(1)
        self.pitivi.child(name="Next", roleName="push button").click()
        self.assertNotEqual(seektime.text, "0:00:00.000")


if __name__ == '__main__':
    unittest.main()
