import archook #The module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
import hashlib
import cv2
import numpy as np
from glob import glob
import gc
import os

# Define the function we'll run from the command line
def objectifyRaster (rasterName):
	# Get licensed
	if arcpy.CheckExtension("Spatial"):  
		arcpy.CheckOutExtension("Spatial")  
	else:  
		print "No SA licence"  
		exit  
	# Load the environment
	env.workspace = "C:/Users/hengstam/Desktop/projects/proglacial"
	# Make sure we can mess with stuff
	arcpy.env.overwriteOutput = True
	#####################################################
	####				VECTORIZE IT				 ####
	#####################################################
	inputRasterFilename = '/rasters/annual/' + rasterName + '.tif'
	# Set up temp files names
	tempRasterFilename = '/temp/rasters/' + rasterName + '.tif'
	tempMorphRasterFilename = '/temp/rasters/' + rasterName + '_morph.tif'
	tempShapesFilename = '/temp/polygons/' + rasterName + '.shp'
	# Set up our output
	outputShapesFilename = "/polygons/annual/" + rasterName + ".shp"
	# Clear potiential old output
	if arcpy.Exists(tempRasterFilename):
		arcpy.Delete_management(tempRasterFilename)
	if arcpy.Exists(tempMorphRasterFilename):
		arcpy.Delete_management(tempRasterFilename)
	if arcpy.Exists(tempShapesFilename):
		arcpy.Delete_management(tempShapesFilename)
	if arcpy.Exists(outputShapesFilename):
		arcpy.Delete_management(outputShapesFilename)
	print "Converting raster " + inputRasterFilename + " into " + outputShapesFilename + '...'
	# Select water and save it to a temp location for morphological operations
	waterRasterBeforeMorpOps = arcpy.sa.Con(inputRasterFilename, 1, 0, "Value <= 6 AND Value >= 4") #"Value <= 10 AND Value >= 7")
	waterRasterBeforeMorpOps.save(env.workspace + tempRasterFilename)
	arcpy.CopyRaster_management(env.workspace+tempRasterFilename, env.workspace+tempMorphRasterFilename , pixel_type = "1_BIT")
	# Move to the next step
	print "Raster successfully imported."
	##############################################
	## Apply morphological operations to the water
	# print "Loading OpenCV2..."
	# print "Preforming morphological operations on " +env.workspace+tempMorphRasterFilename + "..."
	# # Clear memory
	# gc.collect()
	# # Load it into cv2
	# img = cv2.imread(env.workspace+tempMorphRasterFilename, 0)
	# # Open it
	# print "Applying morphological opening operations..."
	# opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
	# # Save it
	# cv2.imwrite(env.workspace+tempMorphRasterFilename, opening)
	# print "Raster successfully opened."
	#############################
	## Reload the modified raster
	# Load it
	waterRasterAfterMorphOps = arcpy.Raster(tempMorphRasterFilename) 
	# Clear the falses out for compatability with arcpy
	waterRasterAfterMorphOps = arcpy.sa.SetNull(waterRasterAfterMorphOps != 1, waterRasterAfterMorphOps)
	###########################
	## Make the output
	print "Making a feature class at " + tempShapesFilename + "..."
	# Make a new feature class
	arcpy.CreateFeatureclass_management(
		env.workspace, 
		tempShapesFilename, 
		"POLYGON"
	)
	# Convert it
	print "Converting raster to temp polygons..."
	arcpy.RasterToPolygon_conversion(
		waterRasterAfterMorphOps, 
		tempShapesFilename, 
		"NO_SIMPLIFY"
	)
	print "Raster successfully converted."
	#####################################################
	####			 PROCESS IT NOW PLZ				 ####
	#####################################################
	# Copy it over
	print "Processing " + tempShapesFilename + " to " + outputShapesFilename + "..."
	arcpy.CopyFeatures_management(tempShapesFilename, outputShapesFilename)
	# # Get the date and location
	# date = int(rasterName[17:25])
	# loc = (int(rasterName[10:13]), int(rasterName[13:16]))
	# print "Date:", date, "Location:", loc
	###################################
	## Calculate area and get centroids
	print "Detailing shapefiles..."
	# Add fields
	arcpy.AddField_management(outputShapesFilename, "area", "DOUBLE")
	arcpy.AddField_management(outputShapesFilename, "centr_x", "DOUBLE")
	arcpy.AddField_management(outputShapesFilename, "centr_y", "DOUBLE")
	arcpy.AddField_management(outputShapesFilename, "lake_id", "STRING")
	arcpy.AddField_management(outputShapesFilename, "date", "LONG")
	arcpy.AddField_management(outputShapesFilename, "loc1", "SHORT")
	arcpy.AddField_management(outputShapesFilename, "loc2", "SHORT")
	# Write area value 		
	arcpy.CalculateField_management(outputShapesFilename, "area", "!SHAPE.AREA@SQUAREKILOMETERS!", "PYTHON_9.3")
	# Build a cursor to set our new fields
	cursor = arcpy.da.UpdateCursor(outputShapesFilename, ["SHAPE@TRUECENTROID", "centr_x", "centr_y", "date", "loc1", "loc2"])
	# Start summing area
	minAreaThreshold = 0.1 # 0.001
	# Work through all lakeOutputName in the feature class
	for row in cursor:
		# Write centroid values 
		row[1] = row[0][0] 
		row[2] = row[0][1]
		# Write date and location
		# row[5] = date
		# row[6] = loc[0]
		# row[7] = loc[1]
		# Save it
		cursor.updateRow(row)
	# Clean up cursor objects
	del row, cursor 
	print "Shapefiles successfully detailed."
	################################################
	## Only save large polygons (originally more than 0.1 km^2, but see above where `minAreaThreshold` is defined.)
	print "Removing small polygons..."
	arcpy.MakeFeatureLayer_management(outputShapesFilename, "removingSmallLakes_lyr")
	arcpy.SelectLayerByAttribute_management("removingSmallLakes_lyr", "NEW_SELECTION", "area < " + str(minAreaThreshold))
	arcpy.DeleteFeatures_management("removingSmallLakes_lyr")
	print "Small polygons successfully removed."
	###########################
	## Name the remaining lakes
	print "Naming lakes..."
	# Make a cursor to update the stuff
	cursor = arcpy.da.UpdateCursor(outputShapesFilename, ["SHAPE@AREA", "SHAPE@TRUECENTROID", "lake_id"])
	# n is used to count the number of lakes, which is displayed at the end of this script.
	n = 0 
	# Go through all lakes in the feature class
	for row in cursor:	
		# Counting works like this
		n += 1
		# Make hash
		m = hashlib.sha224()
		# Use centroid, area, and date to mutate hash
		m.update(str(row[1]))
		m.update(str(row[1][0]))
		m.update(str(row[1][1]))
		# m.update(str(date))
		# Save it
		row[2] = m.hexdigest()
		cursor.updateRow(row)
	# Clean up cursor objects
	del cursor 
	# IO
	print "Success! " + str(n) + " lakes found and named." 	
	print "Output located at " + outputShapesFilename + '.'
# Execute
if __name__ == "__main__":
	print "Loading script..."
	l=os.listdir(r"C:\Users\hengstam\Desktop\projects\proglacial\rasters\annual")
	li=[x.split('.')[0] for x in l]
	print li
	##li = ["A1_M7_9_VIS_BR_LVR1_DEM", "A2_M7_9_VIS_BR_LVR1_DEM", "A3_M7_9_VIS_BR_LVR1_DEM"]
	for filepath in li:
		objectifyRaster(filepath)