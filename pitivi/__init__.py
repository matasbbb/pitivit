"""
Main PiTiVi package
"""

from gi.repository import GObject
from gi.repository import GES

# This call must be made before any "import gst" call!
GObject.threads_init()

GES.init()
