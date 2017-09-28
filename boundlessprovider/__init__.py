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

def classFactory(iface):
    from boundlessprovider.plugin import BoundlessProviderPlugin
    return BoundlessProviderPlugin(iface)
