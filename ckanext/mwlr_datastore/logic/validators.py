import ckan.plugins.toolkit as tk
from ckan.plugins.toolkit import Invalid
from ckan.lib.navl.dictization_functions import Missing
import sys
import datetime
import math
import logging

def is_missing_or_empty(data,key):
    """Convenience function to see if an element of a data dict is
    not there, Missing, None, or the empty string."""
    key = (key,)
    return (key not in data
            or isinstance(data[key],Missing)
            or data[key] is None
            or data[key] == '')

def is_number(value):
    '''Validates value is a number'''
    if value is None:
        return None
    if hasattr(value, 'strip') and not value.strip():
        return None

    try :
        float(value)
    except ValueError :
        raise Invalid("The value is not a number")

    return value

def is_elevation_range(value):
    '''Validates value is within a valid range'''
    if value is None:
        return None
    if hasattr(value, 'strip') and not value.strip():
        return None

    try :
        r = float(value)
        if -20 < r and r < 3000 :
            return value
        else :
            raise Invalid("The value is not a number between -20 and 3000")
    except ValueError :
        raise Invalid("The value is not a number between -20 and 3000")

    return value

def is_year(value):
    '''Validates value is the date format YYYY'''
    try:
        datetime.datetime.strptime(value, '%Y')
    except ValueError:
        raise Invalid("Year must be in the format YYYY, e.g. 2015")
    return value


def is_year_month(value):
    '''Validates value is in the date format YYYY-MM'''
    try:
        datetime.datetime.strptime(value, '%Y-%m')
    except ValueError:
        raise Invalid("Date must be in the format YYYY-MM, e.g. 2015-01")
    return value


def is_year_month_day(value):
    '''Validates value is in the date format YYYY-MM-DD'''
    try:
        datetime.datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        raise Invalid("Date must be in the format YYYY-MM-DD, e.g. 2015-01-29")
    return value


def is_date(value):
    '''Validates value is in one of three various formats'''
    for m in ['is_year', 'is_year_month', 'is_year_month_day']:
        try:
            getattr(sys.modules[__name__], m)(value)
        except Invalid:
            pass
        else:
            return value

    raise Invalid("Date must be in the format YYYY-MM-DD, YYYY-MM, or YYYY")

## === for creating a bounding box around a lat/lon === #
## Semi-axes of WGS-84 geoidal reference
WGS84_a = 6378137.0  # Major semiaxis [m]
WGS84_b = 6356752.3  # Minor semiaxis [m]

## Earth radius at a given latitude, according to the WGS-84 ellipsoid [m]
def WGS84EarthRadius(lat):
    ## http://en.wikipedia.org/wiki/Earth_radius
    An = WGS84_a*WGS84_a * math.cos(lat)
    Bn = WGS84_b*WGS84_b * math.sin(lat)
    Ad = WGS84_a * math.cos(lat)
    Bd = WGS84_b * math.sin(lat)
    return math.sqrt( (An*An + Bn*Bn)/(Ad*Ad + Bd*Bd) )

## Degrees to radians
def deg2rad(degrees):
    return math.pi*degrees/180.0

## Radians to degrees
def rad2deg(radians):
    return 180.0*radians/math.pi

## Bounding box surrounding the point at given coordinates,
## assuming local approximation of Earth surface as a sphere
## of radius given by WGS84
def boundingBox(lat, lon, halfSideHeightInKm, halfSideWidthInKm):
    ## lat, lon = tuple(map(deg2rad, (lat, lon)))
    lat = deg2rad(lat)
    lon = deg2rad(lon)
    halfSideH = 1000*halfSideHeightInKm
    halfSideW = 1000*halfSideWidthInKm
    ## Radius of Earth at given latitude
    radius = WGS84EarthRadius(lat)
    ## Radius of the parallel at given latitude
    pradius = radius*math.cos(lat)
    latMin = lat - halfSideH/radius
    latMax = lat + halfSideH/radius
    lonMin = lon - halfSideW/pradius
    lonMax = lon + halfSideW/pradius
    return tuple(map(rad2deg, (latMin, lonMin, latMax, lonMax)))

def convert_spatial(key, data, errors, context):
    """Computes a spatial extent polygon from latitude / longitude if
    necessary. See scheming/dataset.yml for the definition of data
    fields."""
    #logger = logging.getLogger(__name__)
    #logger.info("[convert_spatial-data] = %s" % data)
    if all([is_missing_or_empty(data,key) for key in ('latitude','longitude','area_height','area_width')]):
        ## no data to set bbox - do nothing
        pass
    elif not is_missing_or_empty(data,'spatial'):
        ## user has set the bbox-  do nothing
        pass
    else:
        if is_missing_or_empty(data,'area_height'):
            ## set default height
            data[('area_height',)] = 0.05 # 50m
        if is_missing_or_empty(data,'area_width'):
            ## set default width
            data[('area_width',)] = 0.05 # 50m
        if any([is_missing_or_empty(data,key) for key in ('latitude','longitude','area_height','area_width')]):
            ## incomplete set of data to define bbox
            raise Invalid("Incomplete set of elements defining spatial bbox: latitude, longitude, area_height (has default), area_width (has default)")
        else:
            ## compute spatial extent
            bbox = boundingBox(
                float(data[('latitude',)]),
                float(data[('longitude',)]),
                float(data[('area_height',)])/2.0,
                float(data[('area_width',)])/2.0,)
            ## store coordinates as lon / lat
            upper_left  = (str(bbox[3]),str(bbox[2]))
            upper_right = (str(bbox[3]),str(bbox[0]))
            lower_right = (str(bbox[1]),str(bbox[0]))
            lower_left  = (str(bbox[1]),str(bbox[2]))
            polygon = "{ \"type\": \"Polygon\",\"coordinates\": [ [ [" + upper_left[0] + ", " + upper_left[1] + "],[" + upper_right[0] + ", " + upper_right[1] + "],[" + lower_right[0] + ", " + lower_right[1] + "], [" + lower_left[0] + ", " + lower_left[1] + "], ["+ upper_left[0] + ", " + upper_left[1] + "] ] ] }"
            ## set in data
            data[('spatial',)] = polygon

def convert_custom_fields(key, data, errors, context):
    """Validate and convert repeating Custom Fields."""
    ## raise Exception('DEBUG:\n'+'\n'.join([repr(key),repr(data),repr(errors)])) # DEBUG Print args as error string
    ## 
    ## loop through all data and remove custom data where both key and
    ## value are empty strings
    keys_to_pop = []
    for key in data:
        ## match key = ('custom', index::int, 'custom_key')
        if (isinstance(key,tuple) and len(key) == 3 and key[0]=='custom' and key[2]=='custom_key'):
            index = key[1]
            key_key = ('custom',index,'custom_key')
            value_key = ('custom',index,'custom_value')
            if data[key_key]=='' and data[value_key]=='':
                keys_to_pop += [key_key,value_key]
    for key in keys_to_pop:
        data.pop(key)

def  strip_values_in_list(key, data, errors, context):
    """Strip leading and trailing whitespace from each element of a
    list of strings."""
    values = data[key]
    stripped_values = [value.strip() for value in values]
    data[key] = stripped_values

def get_validators():
    return {
        'ckanext_mwlr_datastore_is_year'               : is_year,
        'ckanext_mwlr_datastore_is_date'               : is_date,
        'ckanext_mwlr_datastore_is_number'             : is_number,
        'ckanext_mwlr_datastore_is_elevation_range'    : is_elevation_range,
        'ckanext_mwlr_datastore_convert_spatial'       : convert_spatial,
        'ckanext_mwlr_datastore_convert_custom_fields' : convert_custom_fields,
        'ckanext_mwlr_datastore_strip_values_in_list'  : strip_values_in_list,
    }
