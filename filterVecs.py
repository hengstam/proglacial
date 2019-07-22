import os
# import sys
import numpy as np
# import scipy as sci 
# import csv
import glob
from functools import partial
import matplotlib.pyplot as plt
import json
from shapely import geometry
from shapely.ops import transform
import fiona
from osgeo import ogr, osr, gdal
from pyproj import Proj, transform
from fiona.crs import from_epsg
from gdalconst import *
import datetime as dt
import time
import matplotlib.gridspec as gridspec


areaThresh = 0.1 # 1e5 m^2 = 0.1 km^2
fn = r'C:\Users\hengstam\Desktop\projects\proglacial\polygons\c2018_0.shp'
ds = fiona.open(fn)

outDict = {}
outCount = 0

n = len(ds)

for i in range(0,n):
    dataNow = ds[i]
    areaNow = dataNow['properties']['area']

    if areaNow > areaThresh:
        outDict[outCount] = dataNow
        outCount += 1

