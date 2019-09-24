#import modules - the order you do this in is very important due to bugs in shapely and fiona. Make sure you import in this order.
from shapely import geometry
import fiona
import fiona.crs
from pyproj import Proj, transform
import os
import shutil
import utm

## Thanks Dr. Armstrong for these utility functions
def getPolyAream2 (polyGeom):
	# This assumes the polygon has lat/lon coordinates (epsg 4326, wgs84)
	# input = shapely polygon geometry with lat/lon coordinates
	# output = polygon area in m^2	
	def makePolyGeomFromCoordLists (xList, yList):
		# Make a shapely polygon geometry from a list of x (lon or easting) and y (lat or nothing) vertex coordinates
		# outputs polyOut, a shapely polygon geometry
		coordPairs = []
		# Make list of coordinate pair tuples
		for i in range(0, len(xList)):   
			coordPairs.append((xList[i], yList[i]))
		polyOut = geometry.Polygon(coordPairs)
		return polyOut

	def getPolygonVertexCoords (polyVertGeom):
		# get vertex coordinates from a shapely polygon geometry
		# returns xList, yList lists of vertex locations
		ext = polyVertGeom.exterior
		coords = ext.coords.xy
		xArr = coords[0]
		yArr = coords[1]
		xList = xArr.tolist()
		yList = yArr.tolist()			
		return xList, yList

	# Get wgs84 projection (assumes this input geometry projection)
	src_crs = Proj(init='EPSG:4326') 
	# Get centroid to use in calculating utm zone
	c = polyGeom.centroid
	# Get UTM zone
	utmZone = utm.from_latlon(c.y, c.x)[2]
	# EPSG code for UTM zone 
	epsgLocalUtm = 32600+utmZone			
	dst_crs = Proj(init='EPSG:'+str(epsgLocalUtm))
	# Get vertex coordinates in lat/lon
	lonList, latList = getPolygonVertexCoords(polyGeom)
	# Transform these coordiantes to local utm
	easting, northing = transform(src_crs, dst_crs, lonList, latList) 
	# Make polygon in utm coordinate system
	utmPoly = makePolyGeomFromCoordLists(easting, northing) 
	# Polygon area in m^2
	area_m2 = utmPoly.area	 
	return area_m2

## Define the functions we'll run from the command line
def findArea (sourceVectorName):
	## Load files
	# Load the environment
	root = 'C:/Users/hengstam/Desktop/projects/proglacial'
	# Get feature class filenames
	sourceFile = root + sourceVectorName + '.shp'
	tempFile = root + '/temp/polygons/findAreaSwapFile.shp'
	# Clear the output
	if os.path.exists(tempFile):
		os.remove(tempFile)
	# Define schema for output
	schema = {
		'geometry': 'Polygon',
		'properties': {
			'areakm2': 'float'
		}
	}
	## Process shapefiles with area, etc.
	# Keep track of total area
	areaSum = 0
	# Generate the processed feature class in the temp file
	with fiona.open(tempFile, 'w', driver='ESRI Shapefile', schema=schema, crs=fiona.crs.from_epsg(4326)) as output: # Hardcode WGS84 as projection
		for feature in fiona.open(sourceFile):
			# Get geometry
			polygon = geometry.asShape(feature['geometry']) 
			# Calculate area
			area = getPolyAream2(polygon) / 1e6
			areaSum += area
			# Write it to the temp file
			output.write({
				'geometry': geometry.mapping(polygon),
				'properties': {
					'areakm2': area
				},
			})
	# Display results
	print "Total area: " + str(areaSum) + " km."
	# Copy it back over
	# shutil.copyfile(tempfile, sourceFile)

# This function finds the intersection 
def findVectorError (truthVectorName, testVectorName, totalVectorName):
	## Load files
	# Load the environment
	root = 'C:/Users/hengstam/Desktop/projects/proglacial'
	# Get feature class filenames
	truthFile = root + '/polygons/' + truthVectorName + '.shp'
	testFile = root + '/polygons/' + testVectorName + '.shp'
	totalFile = root + '/polygons/areaMaps/' + totalVectorName + '.shp'
	## Perform intersection
	# Keep track of how much area we've found
	truthArea = 0.0
	testArea = 0.0
	intersectionArea = 0.0
	# Open features
	truthFeatureClass = fiona.open(truthFile)
	testFeatureClass = fiona.open(testFile)
	totalFeatureClass = fiona.open(totalFile)
	# Make feature lists
	truthFeatures = [geometry.shape(truth['geometry']) for truth in truthFeatureClass]
	testFeatures = [geometry.shape(test['geometry']) for test in testFeatureClass]
	totalFeatures = [geometry.shape(total['geometry']) for total in totalFeatureClass]
	# Make new shapefile with intersection
	print "> Finding error between " + truthVectorName + " and " + testVectorName + "."
	# Iterate through features to find intersections
	for test in testFeatures:
		testArea += test.area
	for truth in truthFeatures:
		truthArea += truth.area
	for test in testFeatures:
		for truth in truthFeatures:
			if test.intersects(truth):
				intersectionArea += test.intersection(truth).area
	# Get total area
	totalArea = totalFeatures[0].area
	# Display result metrics
	print "Actual positives area: " + str(truthArea*1000)
	print "All positives area: " + str(testArea*1000)
	print "True positives area: " + str(intersectionArea*1000)
	print "Total area: " + str(totalArea*1000)
	# Display result metrics
	# print "Positives identified: " + str(100*intersectionArea/truthArea)
	# print "Identifications correct: " + str(100*(1-(testArea-intersectionArea)/testArea))
# Execute
if __name__ == "__main__":
	print "Loading script..."
	a1list = [
		"A1_M7_VIS",
		"A1_M7_VIS_BR",
		"A1_M7_VIS_BR_LVR1",
		"A1_M7_VIS_BR_LVR2",
		"A1_M7_VIS_BR_LVR3",
		"A1_M7_VIS_BR_LVR1_DEM",
		"A1_M7_VIS_LVR1_DEM",
		"A1_M7_VIS_LVR3_DEM",
		"A1_M9_VIS",
		"A1_M9_VIS_BR",
		"A1_M9_VIS_BR_LVR1",
		"A1_M9_VIS_BR_LVR2",
		"A1_M9_VIS_BR_LVR3",
		"A1_M9_VIS_BR_LVR1_DEM",
		"A1_M9_VIS_LVR1_DEM",
		"A1_M7_9_VIS",
		"A1_M7_9_VIS_BR",
		"A1_M7_9_VIS_BR_LVR1",
		"A1_M7_9_VIS_BR_LVR2",
		"A1_M7_9_VIS_BR_LVR3",
		"A1_M7_9_VIS_BR_LVR1_DEM",
		"A1_M7_9_VIS_LVR1_DEM",
	]
	a2list = [
		"A2_M7_VIS",
		"A2_M7_VIS_BR",
		"A2_M7_VIS_BR_LVR1",
		"A2_M7_VIS_BR_LVR2",
		"A2_M7_VIS_BR_LVR3",
		"A2_M7_VIS_BR_LVR1_DEM",
		"A2_M7_VIS_LVR1_DEM",
		"A2_M7_VIS_LVR3_DEM",
		"A2_M9_VIS",
		"A2_M9_VIS_BR",
		"A2_M9_VIS_BR_LVR1",
		"A2_M9_VIS_BR_LVR2",
		"A2_M9_VIS_BR_LVR3",
		"A2_M9_VIS_BR_LVR1_DEM",
		"A2_M9_VIS_LVR1_DEM",
		"A2_M7_9_VIS",
		"A2_M7_9_VIS_BR",
		"A2_M7_9_VIS_BR_LVR1",
		"A2_M7_9_VIS_BR_LVR2",
		"A2_M7_9_VIS_BR_LVR3",
		"A2_M7_9_VIS_BR_LVR1_DEM",
		"A2_M7_9_VIS_LVR1_DEM",
	]
	a3list = [
		"A3_M7_VIS",
		"A3_M7_VIS_BR",
		"A3_M7_VIS_BR_LVR1",
		"A3_M7_VIS_BR_LVR2",
		"A3_M7_VIS_BR_LVR3",
		"A3_M7_VIS_BR_LVR1_DEM",
		"A3_M7_VIS_LVR1_DEM",
		"A3_M7_VIS_LVR3_DEM",
		"A3_M9_VIS",
		"A3_M9_VIS_BR",
		"A3_M9_VIS_BR_LVR1",
		"A3_M9_VIS_BR_LVR2",
		"A3_M9_VIS_BR_LVR3",
		"A3_M9_VIS_BR_LVR1_DEM",
		"A3_M9_VIS_LVR1_DEM",
		"A3_M7_9_VIS",
		"A3_M7_9_VIS_BR",
		"A3_M7_9_VIS_BR_LVR1",
		"A3_M7_9_VIS_BR_LVR2",
		"A3_M7_9_VIS_BR_LVR3",
		"A3_M7_9_VIS_BR_LVR1_DEM",
		"A3_M7_9_VIS_LVR1_DEM",
	]
	for filepath in a1list:	findVectorError("A1_TRUTH", filepath, 'a1-polygon')
	# for filepath in a1list:	findVectorError("A1_TRUTH", "noRiver/" + filepath, 'a1-polygon')

	for filepath in a2list:	findVectorError("A2_TRUTH", filepath, 'a2-polygon')
	# for filepath in a2list:	findVectorError("A2_TRUTH", "noRiver/" + filepath, 'a2-polygon')

	for filepath in a3list:	findVectorError("A3_TRUTH", filepath, 'a3-polygon')
	# for filepath in a3list:	findVectorError("A3_TRUTH", "noRiver/" + filepath, 'a3-polygon')

	findVectorError("A1_TRUTH", "v2/" + "A1_M7_9_VIS_BR_LVR1_DEM", 'a1-polygon')
	findVectorError("A2_TRUTH", "v2/" + "A2_M7_9_VIS_BR_LVR1_DEM", 'a2-polygon')
	findVectorError("A3_TRUTH", "v2/" + "A3_M7_9_VIS_BR_LVR1_DEM", 'a3-polygon')