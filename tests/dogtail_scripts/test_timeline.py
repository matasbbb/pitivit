#!/usr/bin/env python

import unittest
from test_basic import BaseDogTail
from dogtail.predicate import GenericPredicate
import dogtail.rawinput
import os
import pprint
from time import sleep


class TimelineTest(BaseDogTail):
    def help_test_import_clip(self):
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

    def help_test_insert_at_end(self):
        sample = self.help_test_import_clip()
        #Right click
        seektime = self.search_by_text("0:00:00.000", self.pitivi, roleName="text")

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
        sample = self.help_test_import_clip()

        seektime = self.search_by_text("0:00:00.000", self.pitivi, roleName="text")
        self.assertIsNotNone(seektime)

        #Right click
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

    def test_split(self):
        self.help_test_insert_at_end()
        seektime = self.search_by_text("0:00:02.455", self.pitivi, roleName="text")
        timeline = self.pitivi.children[0].children[0].children[2].children[1].children[3]

        dogtail.rawinput.click(timeline.position[0] + 500, timeline.position[1] + 50)
        self.pitivi.child(name="Split", roleName="push button").click()
        dogtail.rawinput.click(timeline.position[0] + 450, timeline.position[1] + 50)
        self.pitivi.child(name="Delete", roleName="push button").click()

        self.pitivi.child(name="Next", roleName="push button").click()
        self.assertEqual(seektime.text, "0:00:02.455")

        dogtail.rawinput.click(timeline.position[0] + 550, timeline.position[1] + 50)
        self.pitivi.child(name="Delete", roleName="push button").click()

        self.pitivi.child(name="Next", roleName="push button").click()
        self.assertEqual(seektime.text, "0:00:01.227")

    def test_transition(self):
        self.help_test_insert_at_end()
        seektime = self.search_by_text("0:00:02.455", self.pitivi, roleName="text")
        timeline = self.pitivi.children[0].children[0].children[2].children[1].children[3]
        dogtail.rawinput.drag((timeline.position[0] + 500, timeline.position[1] + 50),
                              (timeline.position[0] + 300, timeline.position[1] + 50))
        sleep(1)
        dogtail.rawinput.click(timeline.position[0] + 200, timeline.position[1] + 50)
        #Check if we selected transition
        transitions = self.pitivi.child(name="Transitions", roleName="page tab")
        iconlist = transitions.child(roleName="layered pane")
        self.assertTrue(iconlist.sensitive)
        iconlist.children[-2].select()
        self.assertTrue(transitions.child(roleName="slider").sensitive)
        transitions.child(roleName="slider").value = 50

if __name__ == '__main__':
    unittest.main()
