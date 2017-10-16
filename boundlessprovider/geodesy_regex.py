# -*- coding: utf-8 -*-
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Authors:     Chris Gudea
#                Dustin Lambright
#    Contact:    pulala@gmail.com
#                dustin.lambright@gmail.com
#    Version:    1
#    Info:        This program uses regular expressions to test single lines of text
#                to test for compliance of the expression against coordinate system
#                standards.
#    Standards:
#                DDMS (Degrees Minutes Seconds)
#                UTM (Universal Transverse Mercator coordinate system)
#                Decimal (-180.0 to 180.0)
#                MGRS (Military Grid Reference System)

import re
# DMS test data
dmsLatFails = ['20/60/0', '80/60/1.11', '80/59/70', '90/59/0', '86/60/1']
dmsLatMatches = ['-12/23/59.999999999999999', '-1/2/1.000234','-1:2:12.000234', 
                '0 59 0.22', '60/34/34']
dmsLatFails_new = ["20º60'0\"", "80º60'1.11\"", "80º59'70\"", "90º59'0\"", "86º60'1\""]
dmsLatMatches_new = ['-12º23\'59.999999999999999"', '-1º2\'1.000234"','-1º2\'12.000234"', 
                '0º 59\' 0.22"', '60º34\'34"']
dmsLonFails = ['123:60:59.99999999', '-180:12:0', '180:60:0', 
                '700 50 50.11', '23/79/22.22', 
                '0 60 2.2', '0 60 0']
dmsLonMatches = ['-179/59/0.23', '127/12/12.223', '-180/0/0', 
                '179:59:59.99999999', '-59:13:58.22212345', 
                '0:0:2.3', '127 12 12.333', '180 0 0', '-0 0 0.00001']

# decimal test data
decimalFails = ["323.312.0", "ABC", "abc", "2.a23", "e2.31", "123-213", "-123e", "180.1", "-190", "-200.1"]
decimalMatches = ["-22.311", "-12", "-170", "28.324125", "179.0111111111111", "13", "-100.0"]

# mgrs test data
mgrsMatches = ["4QFJ1093763778", "2QFK3093763778", "2QaK3093763778", "1fgh23456789"]
mgrsFails = ["QFJ1093763778", "4QFJ109373778", "123a", "12.4.41"]

# utm test data
utmMatches = ['4Q6109372363778', '1f21', '2e01928391087509127405123521353526798', 
                '4:Q6109372363778', '4/Q/6109372363778', '4 Q 6109372363778', '1 e 231']
utmFails = ['4a6109372363778', 'asljkd', '123f', '1a21', '1234', '1/2:123', '1:./21', '1 a 1234']

# regular expressions (all the magic)
flat_float_regexp = '[+-]?\d+(\.\d+\s*)?'

DMS_lat_regexp =  '[+-]?(((90)(\s*)(\/|\:|\s|\º)(\s*)?((0*)(\s*)(\/|\:|\s|\'))?(\s*)((0*)(\.0*)?(\")?)?)|([1-8]?\d)(\/|\:|\s|\º)(\s*)?(([1-5]?\d))(\/|\:|\s|\')(\s*)?[1-5]?\d(\.\d*)?(\")?)(\s*)?([nNsS])?'
DMS_lon_regexp = '[-+]?(((180)(\s*)(\/|\:|\s|\º)(\s*)?((0*)(\s*)(\/|\:|\s|\'))?(\s*)((0*)(\.0*)?(\")?)?)|(([1]?[1-7]\d)|\d?\d)(\/|\:|\s|\º)(\s*)([1-5]?\d)(\/|\:|\s|\')(\s*)[1-5]?\d(\.\d*)?(\")?)(\s*)([eEwW])?'

DDM_lat_regexp =  '[+-]?(((90)(\s*)(\/|\:|\s|\º)(\s*)?(\s*)((0*)(\.0*)?(\')?)?)|([1-8]?\d)(\s*)(\/|\:|\s|\º)(\s*)?(\s*)?[1-5]?\d(\.\d+)?(\')?)(\s*)?([nNsS])?'
DDM_lon_regexp = '[+-]?(((180)(\s*)(\/|\:|\s|\º)(\s*)?(\s*)((0*)(\.0*)?(\')?)?)|(([1]?[1-7]\d)|\d?\d)(\s*)(\/|\:|\s|\º)(\s*)[1-5]?\d(\.\d+)?(\'))(\s*)([eEwW])?'

DD_lat_regexp = '[+-]?(((90)(\.(0*)))|(([1-8]?\d)(\.(\d+))))((\s*)(\º)?)((\s*)[nNsS])?'
DD_lon_regexp = '[+-]?(((180)(\.(0*)))|((([1]?[1-7]\d)|(\d?\d))(\.\d+)?))((\s*)(\º)?)((\s*)[eEwW])?'

dmsLatRegEx = '^-?((90\/[0]*\/[0]*$)|([1-8]?\d))(\/|\:|\ )(([1-5]?\d))(\/|\:|\ )[1-5]?\d(\.\d*)?$'
dmsLatIsoRegEx = '^[-+]?((90\/[0]*\/[0]*$)|([1-8]?\d))(\º)?(\s*)(\/|\:|\ )(([1-5]?\d)(\')?)(\s*)((\/|\:|\ )[1-5]?\d(\.\d*)?(\")?)(\s*)([NS])?$'
dmsLonRegEx = '^-?((180(\/|\:| )0(\/|\:| )0((\.0*)?))|(([1]?[1-7]\d)|\d?\d)(\/|\:| )([1-5]?\d)(\/|\:| )[1-5]?\d(\.\d*)?$)'
decimalRegEx = "^-?(180((\.0*)?)|([1]?[0-7]?\d(\.\d*)?))$"
mgrsRegEx = "^\d{1,2}[^ABIOYZabioyz][A-Za-z]{2}([0-9][0-9]){1,5}$"
utmRegEx = "^\d(\/|\:| |)[^aboiyzABOIYZ\d\[-\` -@](\/|\:| |)\d{2,}$"

# used to evaluate if the test is successful
def unitTester(item, expected, actual):
    if (not expected) and actual == None:print "NO MATCH:",item
    elif expected and actual:
        print "MATCH:",item
    else:
        print "expected:",expected, " | actual:",actual
        print "FAILED:",item

# check 'item' string using 'regex' string 
def regexCheck(regex, item):
    expr = re.compile(regex)
    m = expr.match(item)
    if not m:
        return m
    if (m.group(0) != item):
        return None
    return m


# Everyone needs a main squeeze
if __name__ == "__main__":
    print "----Degrees Minutes Seconds regular expression----"
    print "Testing all examples that should show NO MATCH:"
    for fail in dmsLatFails:
        unitTester(fail, False, regexCheck(dmsLatRegEx, fail))
    print "\nTesting all examples that should show MATCH:"
    for match in dmsLatMatches:
        unitTester(match, True, regexCheck(dmsLatRegEx, match))

    print "\nTesting all examples that should show NO MATCH:"
    for fail in dmsLonFails:
        unitTester(fail, False, regexCheck(dmsLonRegEx, fail))
    print "\nTesting all examples that should show MATCH:"
    for match in dmsLonMatches:
        unitTester(match, True, regexCheck(dmsLonRegEx, match))

    print "\n----Degrees Minutes Seconds NEW regular expression----"
    print "Testing all examples that should show NO MATCH:"
    for fail in dmsLatFails:
        unitTester(fail, False, regexCheck(DMS_lat_regexp, fail))
    print "\nTesting all examples that should show MATCH:"
    for match in dmsLatMatches:
        unitTester(match, True, regexCheck(DMS_lat_regexp, match))
    print "\nTesting all NEW examples that should show NO MATCH:"
    for fail in dmsLatFails_new:
        unitTester(fail, False, regexCheck(DMS_lat_regexp, fail))
    print "\nTesting all NEW examples that should show MATCH:"
    for match in dmsLatMatches_new:
        unitTester(match, True, regexCheck(DMS_lat_regexp, match))

    print "\nTesting all examples that should show NO MATCH:"
    for fail in dmsLonFails:
        unitTester(fail, False, regexCheck(DMS_lon_regexp, fail))
    print "\nTesting all examples that should show MATCH:"
    for match in dmsLonMatches:
        unitTester(match, True, regexCheck(DMS_lon_regexp, match))

    print "\n----Testing Decimal coordinates----"
    print "Testing all examples that should show NO MATCH:"
    for fail in decimalFails:
        unitTester(fail, False, regexCheck(decimalRegEx, fail))
    print "\nTesting all examples that should show MATCH:"
    for match in decimalMatches:
        unitTester(match, True, regexCheck(decimalRegEx, match))

    print "\n----Testing MGRS coordinates----"
    print "Testing all examples that should show NO MATCH:"
    for fail in mgrsFails:
        unitTester(fail, False, regexCheck(mgrsRegEx, fail))
    print "\nTesting all examples that should show MATCH:"
    for match in mgrsMatches:
        unitTester(match, True, regexCheck(mgrsRegEx, match))

    print "\n----Testing UTM coordinates----"
    print "Testing all examples that should show NO MATCH:"
    for fail in utmFails:
        unitTester(fail, False, regexCheck(utmRegEx, fail))
    print "\nTesting all examples that should show MATCH:"
    for match in utmMatches:
        unitTester(match, True, regexCheck(utmRegEx, match))