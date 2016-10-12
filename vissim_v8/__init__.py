#!/usr/bin/env python
"""
PyVISSIM for PTV VISSIM v8+
========================

    PyVISSIM is a Python package for the creation, manipulation, and
    automation of traffic models created using PTV's VISSIM
    microsimulation modeling software.
"""
#    Copyright (C) 2015-2016 by
#    S. Brian Huey (sbhuey@gmail.com)
#    All rights reserved.
#
#
import sys
if sys.version_info[:2] < (2, 7):
    m = "Python 2.7 or later is required for PyVISSIM (%d.%d detected)."
    raise ImportError(m % sys.version_info[:2])
del sys

from vissim_objs import *
from osm_to_vissim import *
from vissim_to_geojson import *
