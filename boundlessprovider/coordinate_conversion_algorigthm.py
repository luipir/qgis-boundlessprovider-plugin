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
import re

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
    DD_lat_regexp,
    DD_lon_regexp,
    DMS_lat_regexp,
    DMS_lon_regexp,
    DDM_lat_regexp,
    DDM_lat_regexp,
)

# external pypi library pygeodesy with MIT license
# https://github.com/mrJean1/PyGeodesy
# https://pypi.python.org/pypi/PyGeodesy
# pygeodesy is used to parse MGRS and UTM, but LatLon is parsed
# using complex custom RegExp that allow more flexibility in format
# e.g. LatLon is NOT parsed using pygeodesy parser
from pygeodesy import 
    mgrs,
    utm,
)

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

    DD_index = 0
    DMS_index = 1
    DDM_index = 2
    MGRS_index = 3
    UTM_index = 4
    FORMAT_LIST = ['DD-Decimal degrees', 'DMS-Degrees-minutes-seconds', 'DDM-Decimal minutes', 'MGRS-Military Grid Reference System', 'UTM-Universal Transverse Mercator']
    FORMAT_REGEXP = [
        {'lat':re.compile(self.DD_lat_regexp), 'lon':re.compile(self.DD_lon_regexp)},
        {'lat':re.compile(self.DMS_lat_regexp), 'lon':re.compile(self.DMS_lon_regexp)},
        {'lat':re.compile(self.DDM_lat_regexp), 'lon':re.compile(self.DDM_lat_regexp)},
    ]
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
        self.addParameter(ParameterTableField(self.SOURCE_X_FIELD, "X (lon) or mgrs field ", parent=self.SOURCE_TABLE, optional=True))
        self.addParameter(ParameterTableField(self.SOURCE_Y_FIELD, "Y (lat) or mgrs field", parent=self.SOURCE_TABLE, optional=True))
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
        SOURCE_X_FIELD_value = self.getParameterValue(self.SOURCE_X_FIELD)
        SOURCE_Y_FIELD_value = self.getParameterValue(self.SOURCE_X_FIELD)
        if not SOURCE_X_FIELD_value and not SOURCE_Y_FIELD_value:
            raise GeoAlgorithmExecutionException('At least an input field have to be set')

        OUTPUT_X_FIELD_value = self.getParameterValue(self.OUTPUT_X_FIELD)
        OUTPUT_Y_FIELD_value = self.getParameterValue(self.OUTPUT_Y_FIELD)
        OUTPUT_XY_FIELD_value = self.getParameterValue(self.OUTPUT_XY_FIELD)
        if not OUTPUT_X_FIELD_value and not OUTPUT_Y_FIELD_value and not OUTPUT_XY_FIELD_value:
            raise GeoAlgorithmExecutionException('At least an output field have to be set')
        
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
        
        SOURCE_FORMAT_value = self.getParameterValue(self.SOURCE_FORMAT)
        if SOURCE_FORMAT_value == MGRS_index and SOURCE_X_FIELD_value and SOURCE_Y_FIELD_value:
            raise GeoAlgorithmExecutionException('Ambiguity: OUTPUT_COORDINATE_FORMAT is {} and both SOURCE_X_FIELD and SOURCE_Y_FIELD are set. Please select only one source field'.format(self.FORMAT_LIST[OUTPUT_COORDINATE_FORMAT_value]) )

        # get parameters
        fieldType = QVariant.String
        if DESTINATION_FORMAT_value in [DD_index]:
            fieldType = QVariant.Double

        output = self.getOutputFromName(self.OUTPUT_TABLE)

        # do process

        layer = processing.getObject(self.SOURCE_TABLE)
        sourceXFieldIndex = None
        sourceYFieldIndex = None
        if SOURCE_X_FIELD_value:
            sourceXFieldIndex = inputTable.fieldNameIndex(SOURCE_X_FIELD_value)
        if SOURCE_Y_FIELD_value:
            sourceYFieldIndex = inputTable.fieldNameIndex(SOURCE_Y_FIELD_value)
        
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
        
        # create writer
        writer = output.getVectorWriter(fields, layer.wkbType(), layer.crs())
        outFeat = QgsFeature()
        features = vector.features(layer)
        total = 100.0 / len(features) if len(features) > 0 else 1

        # populate new layer
        for current, feat in enumerate(features):
            progress.setPercentage(int(current * total))
            # get source data to transform
            attributes = feat.attributes()
            x = None
            y = None
            if sourceXFieldIndex:
                x = str(attributes[sourceXFieldIndex]).replace(' ', '')
            if sourceYFieldIndex:
                y = str(attributes[sourceYFieldIndex]).replace(' ', '')

            # from source to wgs
            try:
                if SOURCE_FORMAT_value == MGRS_index:
                    mgrsObject = mgrs.parseMGRS( x? x:y )
                    utmObject = mgrsObject.toUtm()
                    latLonObject = utmObject.toLatLon()
                    newX = latLonObject.lon()
                    newY = latLonObject.lat()
                elif SOURCE_FORMAT_value == UTM_index:
                    utmObject = utm.parseUTM( x? x:y )
                    latLonObject = utmObject.toLatLon()
                    newX = latLonObject.lon()
                    newY = latLonObject.lat()
                elif SOURCE_FORMAT_value in [DD_index, DMS_index, DDM_index]
                    newX = self.lonFromSourceToWgs(x, SOURCE_FORMAT_value)
                    newY = self.latFromSourceToWgs(y, SOURCE_FORMAT_value)
                else:
                    raise GeoAlgorithmExecutionException('Unrecognised SOURCE_FORMAT in feature with id {}. It should be one of: {}'format(feat.id(), str(self.FORMAT_LIST) )

            except Exception as ex:
                raise GeoAlgorithmExecutionException(unicode(ex))

            # wrom wgs to destination format
            if SOURCE_FORMAT_value == MGRS_index:
                mgrsObject = mgrs.parseMGRS( x? x:y )
                utmObject = mgrsObject.toUtm()
                latLonObject = utmObject.toLatLon()
                newX = latLonObject.lon()
                newY = latLonObject.lat()
            elif SOURCE_FORMAT_value == UTM_index:
                utmObject = utm.parseUTM( x? x:y )
                latLonObject = utmObject.toLatLon()
                newX = latLonObject.lon()
                newY = latLonObject.lat()
            elif SOURCE_FORMAT_value in [DD_index, DMS_index, DDM_index]
                newX = self.lonFromSourceToWgs(x, SOURCE_FORMAT_value)
                newY = self.latFromSourceToWgs(y, SOURCE_FORMAT_value)
            else:
                raise GeoAlgorithmExecutionException('Unrecognised SOURCE_FORMAT in feature with id {}. It should be one of: {}'format(feat.id(), str(self.FORMAT_LIST) )

            geom = feat.geometry()
            outFeat.setGeometry(geom)
            atMap = feat.attributes()
            atMap.append(None)
            outFeat.setAttributes(atMap)
            writer.addFeature(outFeat)
        del writer

    def lonFromSourceToWgs(value, sourceFormatIndex):
        """Parse and convert Lon value form a format to another.
        Beaware that regext group position have to be aligned to the 
        related regexp 
        """
        if not value or not sourceFormatIndex:
            return None

        expression = FORMAT_REGEXP[sourceFormatIndex]['lon']
        match = expression.match(value)
        # general parsing error
        if not match:
            return None
        # if something does not match but other parts match
        if match.group(0) != value:
            return None
        # now parse 
        if sourceFormatIndex == DD_index:
            signItem = match.group(1)
            eastingNorthingItem = match.group(13)
            sign = self.giveMeSign(signItem, eastingNorthingItem)
            degrees = float(match.group(2))
            return sign * degrees
        elif sourceFormatIndex == DMS_index:
            signItem = match.group(1)
            eastingNorthingItem = match.group(23)
            sign = self.giveMeSign(signItem, eastingNorthingItem)
            if match.group(4): # case 180
                degrees == float(match.group(4))
                minutes = 0.0
                seconds = 0.0
            else: # case any value
                degrees = float(match.group(14))
                minutes = float(match.group(17))
                seconds = float(match.group(19))
            return sign * degrees + minutes/60.0 + seconds/3600.0
        elif sourceFormatIndex == DDM_index:
            signItem = match.group(1)
            eastingNorthingItem = match.group(18)
            sign = self.giveMeSign(signItem, eastingNorthingItem)
            if match.group(4): # case 180
                degrees == float(match.group(4))
                minutes = 0.0
            else: # case any value
                degrees = float(match.group(11))
                minutes = float(match.group(14))
            return sign * degrees + minutes/60.0
        else:
            raise GeoAlgorithmExecutionException('Invalid SOURCE_FORMAT value' )

    def latFromSourceToWgs(value, sourceFormatIndex):
        """Parse and convert Lat value form a format to another.
        Beaware that regext group position have to be aligned to the 
        related regexp 
        """
        if not value or not sourceFormatIndex:
            return None

        expression = FORMAT_REGEXP[sourceFormatIndex]['lat']
        match = expression.match(value)
        # general parsing error
        if not match:
            return None
        # if something does not match but other parts match
        if match.group(0) != value:
            return None
        # now parse 
        if sourceFormatIndex == DD_index:
            signItem = match.group(1)
            eastingNorthingItem = match.group(11)
            sign = self.giveMeSign(signItem, eastingNorthingItem)
            degrees = float(match.group(2))
            return sign * degrees
        elif sourceFormatIndex == DMS_index:
            signItem = match.group(1)
            eastingNorthingItem = match.group(22)
            sign = self.giveMeSign(signItem, eastingNorthingItem)
            if match.group(4): # case 90
                degrees == float(match.group(4))
                minutes = 0.0
                seconds = 0.0
            else: # case any value
                degrees = float(match.group(14))
                minutes = float(match.group(16))
                seconds = float(match.group(18))
            return sign * degrees + minutes/60.0 + seconds/3600.0
        elif sourceFormatIndex == DDM_index:
            signItem = match.group(1)
            eastingNorthingItem = match.group(18)
            sign = self.giveMeSign(signItem, eastingNorthingItem)
            if match.group(4): # case 90
                degrees == float(match.group(4))
                minutes = 0.0
            else: # case any value
                degrees = float(match.group(12))
                minutes = float(match.group(14))
            return sign * degrees + minutes/60.0
        else:
            raise GeoAlgorithmExecutionException('Invalid SOURCE_FORMAT value' )

    def giveMeSign(signItem, eastingNorthingItem):
        sign = 1
        # only one can be set
        if signItem and eastingNorthingItem:
            raise GeoAlgorithmExecutionException('Malformed value: {}'.format(value) ) 
        
        if signItem and signItem == '+':
            sign = 1
        else: 
            sign = -1
        if eastingNorthingItem and eastingNorthingItem in []'e', 'E', 'n', 'N':
            sign = 1
        else: 
            sign = -1
        
        
    def fromSourceToDest(value, sourceFormatIndex, destFormatIndex, isLat=True):
        """Parse and convert a value form a format to another.
        """
        expression = FORMAT_REGEXP[sourceFormatIndex][isLat? 'lat':'lon']
        match = expression.match(value)
        # general parsing error
        if not match:
            return None
        # if something does not match but other parts match
        if match.group(0) != value:
            return None
