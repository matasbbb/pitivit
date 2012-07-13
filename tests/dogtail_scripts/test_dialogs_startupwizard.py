#!/usr/bin/env python
import unittest
from test_basic import BaseDogTail
from time import time, sleep


class DialogsStartupWizardTest(BaseDogTail):
    def test_welcome(self):
        filename = "test_project%i.xptv" % time()
        #Save project
        self.pitivi.child(name="New", roleName='push button').click()
        self.pitivi.child(name="OK", roleName="push button").click()
        self.saveProject("/tmp/" + filename)
        sleep(2)
        #Hacky, but we need to open once more
        self.tearDown(clean=False)
        self.setUp()
        welcome = self.pitivi.child(name="Welcome", roleName="frame")
        #We expect that just saved project will be in welcome window
        welcome.child(name=filename)
