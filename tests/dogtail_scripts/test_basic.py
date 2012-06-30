#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import os
from dogtail.predicate import GenericPredicate


class BaseDogTail(unittest.TestCase):
    def setUp(self):
        #Try to speed up a little
        from dogtail.config import config
        config.load({'actionDelay': 0.1,
                     'typingDelay': 0.01,
                     'runTimeout': 3,
                     'searchCutoffCount': 5,
                     'defaultDelay': 0.05})
        from dogtail.utils import run
        from dogtail.tree import root
        #Run pitivi
        self.pid = run('bin/pitivi', dumb=True)
        #If pitivi is not runned, tests are skipped
        self.pitivi = root.application('pitivi')

    def saveAsProject(self, url):
        self.pitivi.menu("Project").click()

        #FIXME: cant get working with Save As…
        self.pitivi.menu("Project").children[4].click()
        saveas = self.pitivi.child(roleName='dialog')
        saveas.child(roleName='text').text = url

        #Click the Save button.
        saveas.button('Save').click()

    def loadProject(self, url, save=False):
        self.pitivi.menu("Project").click()
        self.pitivi.menu("Project").children[2].click()
        load = self.pitivi.child(roleName='dialog')
        load.child(name="Type a file name", roleName="toggle button").click()
        load.child(roleName='text').text = url
        load.button('Load').click()
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

    def tearDown(self):
        #Try to kill pitivi before leaving test
        os.system("kill -9 %i" % self.pid)

if __name__ == '__main__':
    unittest.main()
