If you're working in the conda environment I wrote this in, you 
may need to run the following to allow ArcPy (a 32 bit program)
to run in Python 2.7:

	set CONDA_FORCE_32BIT=1
	activate py27_32
	cd C:\Users\hengstam\Desktop\projects\proglacial

The following scripts are provided:

	vectorize.py [subfolder]

		The argument it takes is the subdirectory of a folder in /rasters. It will process all files in this folder. 
		NOTE: Will output to the same subfolder in /polygons. Make sure it exists first!

	generateBuffer.py [shapefilePath] [outputPath] [bufferSizeInKm]

		Takes arguments for the path within the roglacial directory. For example, `python generateBuffer misc/01_rgi60_Alaska/01_rgi60_Alaska.shp misc/buffers/rgi_buffer_5km 5` would generate a 5 km buffer of the 01_rgi60_Alaska.shp file.

	findVectorError.py (Cannot be run in 32 bit mode!!!)

	unify.py [subdirectory of /proglacial]

		

How to duplicate the bug: Download the .7z from the google drive /data/proglacialRasters and extract the folder /rasters into the root directory of this repository. 

1) Running vectorize.py should die on c2018_1.tif. 
2) If you edit vectorize.py, uncommenting the final line and commenting out the for loop above it, it'll process a much smaller raster. Uncomment the section after line 48 to use opencv. Running it will run out of memory, but running the identical commands:
	
	```python
	python
	import cv2
	img = cv2.imread(<REPO>/temp/tiny.tif, 0)
	opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
	cv2.imwrite(<REPO>/temp/tiny_morph.tif, opening)```

should work just fine.
