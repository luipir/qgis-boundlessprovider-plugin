# -*- coding: utf-8 -*-
#
# (c) 2017 Boundless Spatial Inc, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
__author__ = 'Luigi Pirelli'
__date__ = '2017-09-26'
__copyright__ = '(C) Boundless Spatial Inc'

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

try:
    from processing.core.Processing import Processing
    from boundlessprovider.provider import BoundlessProvider
    processingOk = True
except:
    processingOk = False

class BoundlessProviderPlugin(object):

    def __init__(self, iface):
        if processingOk:
            self.provider = BoundlessProvider()

    def initGui(self):
        if processingOk:
            Processing.addProvider(self.provider)
   
    def unload(self):
        if processingOk:
            Processing.removeProvider(self.provider)
