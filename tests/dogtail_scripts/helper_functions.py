import os
from dogtail.predicate import GenericPredicate
import dogtail.rawinput
from time import sleep


def improved_drag(fromcord, tocord):
    dogtail.rawinput.press(fromcord[0], fromcord[1])
    dogtail.rawinput.relativeMotion(5, 5)
    dogtail.rawinput.relativeMotion(-5, -5)
    dogtail.rawinput.absoluteMotion(tocord[0], tocord[1])
    dogtail.rawinput.relativeMotion(5, 5)
    dogtail.rawinput.relativeMotion(-5, -5)
    dogtail.rawinput.release(tocord[0], tocord[1])
