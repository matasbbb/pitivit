#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import os
from dogtail.predicate import GenericPredicate


class BaseDogTail(unittest.TestCase):
    def setUp(self):
        # Force the locale/language to English.
        # Otherwise we won't be able to grab the right widgets.
        os.environ["LANG"] = 'C'
        #Try to speed up a little
        from dogtail.config import config
        config.load({'actionDelay': 0.1,
                     'typingDelay': 0.01,
                     'runTimeout': 1,
                     'searchCutoffCount': 5,
                     'defaultDelay': 0.1})
        from dogtail.utils import run
        from dogtail.tree import root
        # Setting appName is critically important here.
        # Otherwise it will try to look for "bin/pitivi" through AT-SPI and fail,
        # making the tests take ages to start up.
        self.pid = run('bin/pitivi', dumb=False, appName="pitivi")
        self.pitivi = root.application('pitivi')
        try:
            self.unlink
        except AttributeError:
            self.unlink = []

    def saveProject(self, url=None, saveAs=True):
        self.pitivi.menu("Project").click()
        if saveAs:
            #FIXME: cant get working with searching for Save As…
            self.pitivi.menu("Project").children[4].click()
            saveas = self.pitivi.child(roleName='dialog')
            saveas.child(roleName='text').text = url
            #Click the Save button.
            saveas.button('Save').click()
            #Save for deleting afterwards
            self.unlink.append(url)
        else:
            #Just save
            self.pitivi.menu("Project").menuItem("Save").click()

    def loadProject(self, url, save=False):
        self.pitivi.menu("Project").click()
        self.pitivi.menu("Project").children[2].click()
        load = self.pitivi.child(roleName='dialog')
        load.child(name="Type a file name", roleName="toggle button").click()
        load.child(roleName='text').text = url
        load.button('Open').click()
        try:
            if save:
                load.child(name="Close without saving", roleName="push button")
        except:
            return

    def search_by_text(self, text, parent, name=None, roleName=None):
        children = parent.findChildren(GenericPredicate(roleName=roleName,
                                                        name=name))
        searched = None
        for child in children:
            if child.text == text:
                searched = child
        return searched

    def tearDown(self, clean=True):
        #Try to kill pitivi before leaving test
        os.system("kill -9 %i" % self.pid)
        if clean:
            for filename in self.unlink:
                try:
                    os.unlink(filename)
                except:
                    None


if __name__ == '__main__':
    unittest.main()
