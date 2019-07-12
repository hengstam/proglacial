import archook #The module which locates arcgis
archook.get_arcpy()
import arcpy
from arcpy import env
import hashlib
import cv2
import numpy as np
from glob import glob

# Define the function we'll run from the command line
def objectifyRaster (shapefileToBuffer, outputBufferFile, bufferKms):
	# Get licensed
	if arcpy.CheckExtension("Spatial"):  
		arcpy.CheckOutExtension("Spatial")  
	else:  
		print "No SA licence"  
		exit  
	# Load the environment
	env.workspace = "C:/Users/hengstam/Desktop/projects/proglacial/"
	# Make sure we can mess with stuff
	arcpy.env.overwriteOutput = True
	#####################################################
	####			    GENERATE BUFFER				 ####
	#####################################################
	infile = env.workspace + "/" + shapefileToBuffer
	outfile = env.workspace + "/" + outputBufferFile
	print "Loading from: " + infile
	print "Exporting to: " + outfile
	arcpy.Buffer_analysis(infile, outfile,str(bufferKms) + " Kilometers", dissolve_option="ALL")
# Execute
if __name__ == "__main__":
	print "Loading script..."
	objectifyRaster(sys.argv[1], sys.argv[2], sys.argv[3])