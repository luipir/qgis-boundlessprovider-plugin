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

import os

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QIcon

try:
    from qgis.core import  QGis
except ImportError:
    from qgis.core import  Qgis as QGis

from qgis.core import QgsField, QgsFields, QgsFeature, QgsGeometry, QgsPoint, QgsRaster

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import (
    ParameterSelection,
    ParameterString,
    ParameterNumber,
    ParameterTable,
    ParameterTableField)
from processing.core.outputs import (
    OutputTable,
    OutputVector)
from processing.tools import dataobjects, vector, raster
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

from geodesy_regex import (
    dmsLatRegEx,
    dmsLonRegEx,
    decimalRegEx,
    mgrsRegEx,
    utmRegEx)


class CoordinateFormatConversion(GeoAlgorithm):
    """Algorithm to transform coordinate format adding a add a new
    column to a trable or vector layer.
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    SOURCE_TABLE = 'SOURCE_TABLE'
    # SOURCE_VECTOR = 'SOURCE_VECTOR'
    SOURCE_X_FIELD = 'SOURCE_X_FIELD'
    SOURCE_Y_FIELD = 'SOURCE_Y_FIELD'
    SOURCE_FORMAT = 'SOURCE_FORMAT'
    DESTINATION_FORMAT = 'DESTINATION_FORMAT'
    CUSTOM_FORMAT = 'CUSTOM_FORMAT'
    OUTPUT_X_FIELD = 'OUTPUT_X_FIELD'
    OUTPUT_Y_FIELD = 'OUTPUT_Y_FIELD'
    OUTPUT_XY_FIELD = 'OUTPUT_XY_FIELD'
    OUTPUT_COORDINATE_FORMAT = 'OUTPUT_COORDINATE_FORMAT'
    OUTPUT_TABLE = 'OUTPUT_TABLE'
    # OUTPUT_VECTOR = 'OUTPUT_VECTOR'

    FORMAT_LIST = ['DD-Decimal degrees', 'DMS-Degrees-minutes-seconds', 'DDM-Decimal minutes', 'MGRS-Military Grid Reference System', 'UTM-Universal Transverse Mercator']
    FORMAT_REGEXP = [
        {'lat':self.flat_float_regexp, 'lon':self.flat_float_regexp},
        {'lat':self.DMS_lat_regexp, 'lon':self.DMS_lon_regexp},
        {'lat':self.DDM_lat_regexp, 'lon':self.DDM_lat_regexp},
        , 'MGRS-Military Grid Reference System', 
        {'lat':self.flat_float_regexp, 'lon':self.flat_float_regexp}]
    CUSTOM_COORD_FORMAT = u'{degree}º{minutes}\'{seconds}"'
    SINGLE_FIELD_COORD_FORMAT = '{X} {Y}'
    FIELD_LENGHT = 10
    FIELD_PRECISION = 3

    def defineCharacteristics(self):
        """Inputs and output description of the algorithm, along
        with some other properties.
        """
        # The name that the user will see in the toolbox
        self.name = 'Coordinate format convertion'
        self.i18n_name = self.name
        # The branch of the toolbox under which the algorithm will appear
        self.group = 'Formatting'
        self.i18n_group = self.group
        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterTable(self.SOURCE_TABLE, 'Source table', optional=False))
        self.addParameter(ParameterTableField(self.SOURCE_X_FIELD, "X field (longitude)", parent=self.SOURCE_TABLE))
        self.addParameter(ParameterTableField(self.SOURCE_Y_FIELD, "Y field (latitude)", parent=self.SOURCE_TABLE))
        self.addParameter(ParameterSelection(self.SOURCE_FORMAT, "Source format", options=self.FORMAT_LIST, default=0))
        self.addParameter(ParameterSelection(self.DESTINATION_FORMAT, "Destination format", options=self.FORMAT_LIST, default=0, optional=True))
        self.addParameter(ParameterString(self.CUSTOM_FORMAT, "Custom coordinate format", default=self.CUSTOM_COORD_FORMAT, optional=True))
        self.addParameter(ParameterString(self.OUTPUT_X_FIELD, "Destination X field", optional=True))
        self.addParameter(ParameterString(self.OUTPUT_Y_FIELD, "Destination Y field", optional=True))
        self.addParameter(ParameterString(self.OUTPUT_XY_FIELD, "Destination single XY field", optional=True))
        self.addParameter(ParameterString(self.OUTPUT_COORDINATE_FORMAT, "Single field coord fromat", default=self.SINGLE_FIELD_COORD_FORMAT, optional=True))
        # We add a table layer as output
        self.addOutput(OutputTable(self.OUTPUT_TABLE, 'Input table modified'))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        # check input parameters
        OUTPUT_X_FIELD_value = self.getParameterValue(self.OUTPUT_X_FIELD)
        OUTPUT_Y_FIELD_value = self.getParameterValue(self.OUTPUT_Y_FIELD)
        OUTPUT_XY_FIELD_value = self.getParameterValue(self.OUTPUT_XY_FIELD)
        if not OUTPUT_X_FIELD_value and not OUTPUT_Y_FIELD_value and not OUTPUT_XY_FIELD_value:
            raise GeoAlgorithmExecutionException('At least an autput field have to be set')
        
        OUTPUT_COORDINATE_FORMAT_value = self.getParameterValue(self.OUTPUT_COORDINATE_FORMAT)
        if OUTPUT_XY_FIELD_value and not OUTPUT_COORDINATE_FORMAT_value:
            raise GeoAlgorithmExecutionException('If OUTPUT_XY_FIELD is set, it\'s necessary to set also OUTPUT_COORDINATE_FORMAT' )

        DESTINATION_FORMAT_value = self.getParameterValue(self.DESTINATION_FORMAT)
        CUSTOM_FORMAT_value = self.getParameterValue(self.CUSTOM_FORMAT)
        if not DESTINATION_FORMAT_value and not CUSTOM_FORMAT_value:
            raise GeoAlgorithmExecutionException('At least DESTINATION_FORMAT or CUSTOM_FORMAT have to be set' )

        OUTPUT_COORDINATE_FORMAT_value = self.getParameterValue(self.OUTPUT_COORDINATE_FORMAT)
        if OUTPUT_XY_FIELD_value and not OUTPUT_COORDINATE_FORMAT_value:
            raise GeoAlgorithmExecutionException('If OUTPUT_XY_FIELD is set, it\'s necessary to set also OUTPUT_COORDINATE_FORMAT' )

        # get parameters
        DESTINATION_FORMAT_value = self.getParameterValue(self.DESTINATION_FORMAT)
        fieldType = QVariant.String
        if DESTINATION_FORMAT_value in [0, 4]: # eg DD and UTM
            fieldType = QVariant.Double

        output = self.getOutputFromName(self.OUTPUT_TABLE)

        # do process
        layer = processing.getObject(self.SOURCE_TABLE)
        sourceXFieldIndex = inputTable.fieldNameIndex(X_coord_longitude)
        sourceYFieldIndex = inputTable.fieldNameIndex(Y_coord_latitude)
        # set new field types
        # copy table structure and add new columns
        fields = layer.fields()
        if OUTPUT_X_FIELD_value:
            fields.append(QgsField(OUTPUT_X_FIELD_value, fieldType, '',
                                self.FIELD_LENGHT, self.FIELD_PRECISION))
            OUTPUT_X_FIELD_index = fields.size()
        if OUTPUT_Y_FIELD_value:
            fields.append(QgsField(OUTPUT_Y_FIELD_value, fieldType, '',
                                self.FIELD_LENGHT, self.FIELD_PRECISION))
            OUTPUT_Y_FIELD_index = fields.size()
        if OUTPUT_XY_FIELD_value:
            fields.append(QgsField(OUTPUT_XY_FIELD_value,  QVariant.String, '', 20, 20))

            OUTPUT_XY_FIELD_index = fields.size()
        writer = output.getVectorWriter(fields, layer.wkbType(), layer.crs())
        outFeat = QgsFeature()
        features = vector.features(layer)
        total = 100.0 / len(features) if len(features) > 0 else 1
        for current, feat in enumerate(features):
            progress.setPercentage(int(current * total))
            # get source data to transform
            attributes = feat.attributes()
            x = attributes[sourceXFieldIndex]
            y = attributes[sourceYFieldIndex]

            geom = feat.geometry()
            outFeat.setGeometry(geom)
            atMap = feat.attributes()
            atMap.append(None)
            outFeat.setAttributes(atMap)
            writer.addFeature(outFeat)
        del writer