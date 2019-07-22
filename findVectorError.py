#import modules - the order you do this in is very important due to bugs in shapely and fiona. Make sure you import in this order.
from shapely import geometry
import fiona
import fiona.crs
from pyproj import Proj, transform
import os
import shutil
import utm

## Thanks Dr. Armstrong for this utility function
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
	sourceFile = root + '/polygons/' + sourceVectorName + '.shp'
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
def findVectorError (truthVectorName, testVectorName):
	## Load files
	# Load the environment
	root = 'C:/Users/hengstam/Desktop/projects/proglacial'
	# Get feature class filenames
	truthFile = root + '/polygons/' + truthVectorName + '.shp'
	testFile = root + '/polygons/' + testVectorName + '.shp'
	tempFile = root + '/temp/polygons/findVectorErrorAreaTempFile.shp'
	outputFile = root + '/polygons/' + truthVectorName + '_' + testVectorName + '_intersect.shp'
	# Clear the output
	if os.path.exists(tempFile):
		os.remove(tempFile)
	if os.path.exists(outputFile):
		os.remove(outputFile)
	# Define schema for output
	schema = {
		'geometry': 'Polygon',
		'properties': {
			'areakm2': 'float'
		}
	}
	## Perform intersection
	# Keep track of how many features we've found
	featureCount = 0
	# Make new shapefile with intersection
	print "Finding intersection between " + truthVectorName + " and " + testVectorName + "."
	with fiona.open(outputFile, 'w', driver='ESRI Shapefile', schema=schema, crs=fiona.crs.from_epsg(4326)) as output: # Hardcode WGS84 as projection
		# Iterate through features
		for truthFeature in fiona.open(truthFile):
			# Get geometry
			truth = geometry.asShape(truthFeature['geometry'])
			for testFeature in fiona.open(testFile):
				# Get geometry
				test = geometry.asShape(testFeature['geometry'])
				# Save if the intersection exists
				if test.intersects(truth):
					featureCount += 1
					output.write({
						'geometry': test.intersection(truth), # Perform the intersection
						'properties': {}
					})
	# Display result metrics
	print str(featureCount) + " features found in intersection."
# Execute
if __name__ == "__main__":
	print "Loading script..."
	for filepath in ["A1_M7_9_VIS"]:
		findArea("area_1_lakes")