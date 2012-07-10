import os
from dogtail.predicate import GenericPredicate
from dogtail.tree import SearchError


def help_test_import_media(self, filename="1sec_simpsons_trailer.mp4"):
        try:
            self.pitivi.child(name="New", roleName='push button').click()
            self.pitivi.child(name="OK", roleName="push button").click()
        except SearchError:
            None

        self.pitivi.child(name="Import Files...",
                          roleName="push button").click()
        add = self.pitivi.child(roleName='dialog')
        add.child(name="Type a file name", roleName="toggle button").click()
        filepath = os.path.realpath(__file__).split("dogtail_scripts/helper_functions.py")[0]
        filepath += "samples/" + filename
        add.child(roleName='text').text = filepath
        add.button('Add').click()
        icons = self.pitivi.findChildren(GenericPredicate(roleName="icon"))
        sample = None
        for icon in icons:
            if icon.text == filename:
                sample = icon

        self.assertIsNotNone(sample)
        return sample
