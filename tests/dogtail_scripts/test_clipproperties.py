#!/usr/bin/env python
import unittest
from test_basic import BaseDogTail
from dogtail.tree import SearchError
from helper_functions import help_test_import_media, drag
from dogtail.predicate import GenericPredicate, IsATextEntryNamed
from dogtail.tree import SearchError
import dogtail.rawinput
from time import sleep


class ClipTransforamtionTest(BaseDogTail):
    help_test_import_media = help_test_import_media

    def test_transformation_options(self):
        #Load sample
        sample = self.help_test_import_media()
        self.insert_clip(sample)

        timeline = self.pitivi.children[0].children[0].children[2].children[1].children[3]
        clippos = []
        clippos.append((timeline.position[0] + 20, timeline.position[1] + 20))
        clippos.append((timeline.position[0] + timeline.size[0] / 2, timeline.position[1] + 20))
        dogtail.rawinput.click(clippos[0][0], clippos[0][1])

        conftab = self.pitivi.tab("Clip configuration")
        conftab.click()
        conftab.child(name="Transformation", roleName="toggle button").click()
        #Just try changing values
        #Test slider
        self.assertEqual(conftab.child(roleName="slider").value, 1)
        conftab.child(roleName="slider").click()
        self.assertNotEqual(conftab.child(roleName="slider").value, 1)

        #Test position
        spinb = conftab.child(roleName="panel", name="Position").findChildren(GenericPredicate(roleName="spin button"))
        self.assertEqual(len(spinb), 2)
        spinb[0].text = "0.3"
        spinb[1].text = "0.2"

        #Test size
        spinb = conftab.child(roleName="panel", name="Size").findChildren(GenericPredicate(roleName="spin button"))
        self.assertEqual(len(spinb), 2)
        spinb[0].text = "0.4"
        spinb[1].text = "0.1"

        #Test crop
        spinb = conftab.child(roleName="panel", name="Crop").findChildren(GenericPredicate(roleName="spin button"))
        self.assertEqual(len(spinb), 4)
        spinb[0].text = "0.05"
        spinb[1].text = "0.12"
        spinb[2].text = "0.14"
        spinb[3].text = "0.07"

        #Click second clip, look that settings not changed(not linked)
        dogtail.rawinput.click(clippos[1][0], clippos[1][1])
        self.assertEqual(conftab.child(roleName="slider").value, 1.0)

        #Click back, look if settings saved
        dogtail.rawinput.click(clippos[0][0], clippos[0][1])
        self.assertNotEqual(conftab.child(roleName="slider").value, 1.0)

        self.assertNotNone(self.search_by_text("0.3", conftab.child(roleName="panel", name="Position")))
        self.assertNotNone(self.search_by_text("0.2", conftab.child(roleName="panel", name="Position")))

        self.assertNotNone(self.search_by_text("0.4", conftab.child(roleName="panel", name="Size")))
        self.assertNotNone(self.search_by_text("0.1", conftab.child(roleName="panel", name="Size")))

        self.assertNotNone(self.search_by_text("0.05", conftab.child(roleName="panel", name="Crop")))
        self.assertNotNone(self.search_by_text("0.12", conftab.child(roleName="panel", name="Crop")))
        self.assertNotNone(self.search_by_text("0.14", conftab.child(roleName="panel", name="Crop")))
        self.assertNotNone(self.search_by_text("0.07", conftab.child(roleName="panel", name="Crop")))

        #Push clear
        conftab.child(roleName="scroll bar").value = 140
        conftab.button("Clear")

        self.assertEqual(conftab.child(roleName="slider").value, 1.0)

        self.assertNone(self.search_by_text("0.3", conftab.child(roleName="panel", name="Position")))
        self.assertNone(self.search_by_text("0.2", conftab.child(roleName="panel", name="Position")))

        self.assertNone(self.search_by_text("0.4", conftab.child(roleName="panel", name="Size")))
        self.assertNone(self.search_by_text("0.1", conftab.child(roleName="panel", name="Size")))

        self.assertNone(self.search_by_text("0.05", conftab.child(roleName="panel", name="Crop")))
        self.assertNone(self.search_by_text("0.12", conftab.child(roleName="panel", name="Crop")))
        self.assertNone(self.search_by_text("0.14", conftab.child(roleName="panel", name="Crop")))
        self.assertNone(self.search_by_text("0.07", conftab.child(roleName="panel", name="Crop")))
