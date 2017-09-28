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

from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from boundlessprovider.coordinate_conversion_algorigthm import CoordinateFormatConversion

class BoundlessProvider(AlgorithmProvider):

    MY_DUMMY_SETTING = 'MY_DUMMY_SETTING'

    def __init__(self):
        AlgorithmProvider.__init__(self)

        # Activate provider by default
        self.activate = True

        # Load algorithms
        self.alglist = [CoordinateFormatConversion()]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        """In this method we add settings needed to configure our
        provider.

        Do not forget to call the parent method, since it takes care
        or automatically adding a setting for activating or
        deactivating the algorithms in the provider.
        """
        AlgorithmProvider.initializeSettings(self)
        ProcessingConfig.addSetting(Setting('Example algorithms',
            BoundlessProvider.MY_DUMMY_SETTING,
            'Example setting', 'Default value'))

    def unload(self):
        """Setting should be removed here, so they do not appear anymore
        when the plugin is unloaded.
        """
        AlgorithmProvider.unload(self)

    def getName(self):
        """This is the name that will appear on the toolbox group.

        It is also used to create the command line name of all the
        algorithms from this provider.
        """
        return 'Boundless'

    def getDescription(self):
        """This is the provired full name.
        """
        return 'Boundless Spatial algorithms'

    def getIcon(self):
        """We return the default icon.
        """
        return AlgorithmProvider.getIcon(self)

    def _loadAlgorithms(self):
        """Here we fill the list of algorithms in self.algs.

        This method is called whenever the list of algorithms should
        be updated. If the list of algorithms can change (for instance,
        if it contains algorithms from user-defined scripts and a new
        script might have been added), you should create the list again
        here.

        In this case, since the list is always the same, we assign from
        the pre-made list. This assignment has to be done in this method
        even if the list does not change, since the self.algs list is
        cleared before calling this method.
        """
        self.algs = self.alglist
