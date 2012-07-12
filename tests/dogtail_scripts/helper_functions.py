import os
from dogtail.predicate import GenericPredicate
from dogtail.tree import SearchError
import dogtail.rawinput
from time import sleep


def help_test_import_media(self, filename="1sec_simpsons_trailer.mp4"):
        #Just try search for object without retries
        button = self.pitivi.findChildren(GenericPredicate(name="New", roleName="push button"))
        if len(button) != 0:
            self.pitivi.child(name="New", roleName='push button').click()
            self.pitivi.child(name="OK", roleName="push button").click()

        self.pitivi.child(name="Import Files...",
                          roleName="push button").click()
        add = self.pitivi.child(roleName='dialog')
        add.child(name="Type a file name", roleName="toggle button").click()
        filepath = os.path.realpath(__file__).split("dogtail_scripts/helper_functions.py")[0]
        filepath += "samples/" + filename
        add.child(roleName='text').text = filepath
        add.button('Add').click()
        for i in range(5):
            icons = self.pitivi.findChildren(GenericPredicate(roleName="icon"))
            sample = None
            for icon in icons:
                if icon.text == filename:
                    sample = icon
            if sample is not None:
                break
            sleep(1)
        self.assertIsNotNone(sample)
        return sample


def drag(fromcord, tocord):
    dogtail.rawinput.press(fromcord[0], fromcord[1])
    dogtail.rawinput.relativeMotion(5, 5)
    dogtail.rawinput.relativeMotion(-5, -5)
    dogtail.rawinput.absoluteMotion(tocord[0], tocord[1])
    dogtail.rawinput.relativeMotion(5, 5)
    dogtail.rawinput.relativeMotion(-5, -5)
    dogtail.rawinput.release(tocord[0], tocord[1])
