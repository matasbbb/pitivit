#!/usr/bin/env python

import unittest
from test_basic import BaseDogTail
from dogtail.predicate import GenericPredicate
from helper_functions import help_test_import_media, drag
import dogtail.rawinput
from time import sleep


class TimelineTest(BaseDogTail):
    help_test_import_media = help_test_import_media

    def help_test_insertEnd(self):
        sample = self.help_test_import_media()
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
        sample = self.help_test_import_media()

        seektime = self.search_by_text("0:00:00.000", self.pitivi, roleName="text")
        self.assertIsNotNone(seektime)

        #Right click
        timeline = self.pitivi.children[0].children[0].children[2].children[1].children[3]

        center = lambda obj: (obj.position[0] + obj.size[0] / 2, obj.position[1] + obj.size[1] / 2)
        drag(center(sample), center(timeline))
        self.pitivi.child(name="Next", roleName="push button").click()
        self.assertNotEqual(seektime.text, "0:00:00.000")

    def test_split(self):
        self.help_test_insertEnd()
        seektime = self.search_by_text("0:00:02.455", self.pitivi, roleName="text")
        timeline = self.pitivi.children[0].children[0].children[2].children[1].children[3]

        #Adjust to different screen sizes
        adj = (float)(timeline.size[0]) / 900

        dogtail.rawinput.click(timeline.position[0] + 500 * adj, timeline.position[1] + 50)
        self.pitivi.child(name="Split", roleName="push button").click()
        dogtail.rawinput.click(timeline.position[0] + 450 * adj, timeline.position[1] + 50)
        self.pitivi.child(name="Delete", roleName="push button").click()

        self.pitivi.child(name="Next", roleName="push button").click()
        self.assertEqual(seektime.text, "0:00:02.455")

        dogtail.rawinput.click(timeline.position[0] + 550 * adj, timeline.position[1] + 50)
        self.pitivi.child(name="Delete", roleName="push button").click()

        self.pitivi.child(name="Next", roleName="push button").click()
        self.assertEqual(seektime.text, "0:00:01.227")

    def test_transition(self):
        self.help_test_insertEnd()
        seektime = self.search_by_text("0:00:02.455", self.pitivi, roleName="text")
        timeline = self.pitivi.children[0].children[0].children[2].children[1].children[3]
        tpos = timeline.position

        #Adjust to different screen sizes
        adj = (float)(timeline.size[0]) / 900

        dogtail.rawinput.press(tpos[0] + 500 * adj, tpos[1] + 50)
        #Drag in, drag out, drag in and release
        dogtail.rawinput.relativeMotion(-200 * adj, 10)
        sleep(3)
        dogtail.rawinput.relativeMotion(300 * adj, -10)
        sleep(3)
        dogtail.rawinput.absoluteMotion(tpos[0] + 300 * adj, tpos[1] + 50)
        sleep(1)
        dogtail.rawinput.release(tpos[0] + 300 * adj, tpos[1] + 50)
        sleep(1)
        dogtail.rawinput.click(tpos[0] + 250 * adj, tpos[1] + 50)
        #Check if we selected transition
        transitions = self.pitivi.child(name="Transitions", roleName="page tab")
        iconlist = transitions.child(roleName="layered pane")
        self.assertTrue(iconlist.sensitive)
        iconlist.children[-2].select()
        self.assertTrue(transitions.child(roleName="slider").sensitive)
        transitions.child(roleName="slider").value = 50

if __name__ == '__main__':
    unittest.main()
