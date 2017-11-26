# -*- coding: utf-8 -*-
"""Control your home with MegaD Devices"""

from pymegad import metadata
import logging

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger('pymegad')

__version__ = metadata.version
__author__ = metadata.authors[0]
__license__ = metadata.license
__copyright__ = metadata.copyright
