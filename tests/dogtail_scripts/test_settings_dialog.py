#!/usr/bin/env python

from dogtail.config import config

from dogtail.utils import screenshot, run
from dogtail.tree import *
from dogtail.predicate import *
import os
import thread

run('bin/pitivi', 10)
pitivi = root.application('pitivi')
#Just create new project
pitivi.child(name="New", roleName='push button').click()

#Play with project settings, look if they are correctly represented
dialog = pitivi.child(name="Project Settings", roleName="dialog")
video = pitivi.tab("Video")

#Test presets
video.child(name="720p24", roleName="table cell").click()
children = video.findChildren(IsATextEntryNamed(""))
childtext = {}
for child in children:
        childtext[child.text] = child

assert("1:1" in childtext)
assert("24M" in childtext)
assert("16:9" in childtext)

#Test frame rate combinations
frameCombo = video.child(name="23.976 fps", roleName="combo box")
frameText = childtext["24M"]
frameCombo.click()
video.child(name="59.94 fps", roleName="menu item").click()
assert (frameText.text == "60M")
frameText.typeText("30M")
video.child(name="29.97 fps", roleName="combo box")

#Create project
pitivi.child(name="OK", roleName="push button").click()
