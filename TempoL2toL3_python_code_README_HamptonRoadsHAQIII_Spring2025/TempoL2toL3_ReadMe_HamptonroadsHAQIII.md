
# Hampton Roads HAQ III 
**Project:** Hampton Roads Health and Air Quality III     

**Node:** Virginia – Langley 

**Term:** Spring 2025


**Team:** Joe Horan (Project Lead), David Wilcox, Alexia Stechele, Stormi Nichols  
  

**Code Contact:** David Wilcox, david.c.wilcox@outlook.com         

## Introduction  
 This code is intended to create oversampled TEMPO maps at an increased resolution of 1:1km^2. To do so it uses multiple Level 2 (L2) TEMPO scans across various timescales (TEMPO has a 1 hour scan frequency), builds a 1:1km grid, and then takes a fixed cell radius average of all data seen within each grid cell. Given TEMPO's inherent "shake" during its scan process, these L2 scans have a spatial offset between eachother, this offset allows you to overlay multiple scans on top of eachother with unaligned grids. The overlaying of offset grids results in overlapping datapoints encompassed by the newly created grid cells. Though given the offset data is not within perfect alignment, oversampled grid cells incorporate only aspects of each encompassed scan. If scans were within perfect alignment high resolution rebuild would not be possible, as aligned native resolution grids would inhibit the ability to create an average beyond already pre-determined native grid cells. Without the offset this sort of temporal average would be moreso a general aggregate, rather than an oversampled grid rebuild. Fundamentally, you are building a new grid with the help of overlayed, non-uniformly oriented data. Trading TEMPO's high temporal resolution (1 hr) for an increased spatial resolution. 
 
 Within our project we intended to study a small area (Hampton Roads). Native L2 data has a resolution of 2:4.7km^2, and provisional Level 3 (L3) TEMPO data has a spatial resolution of 2:2km^2. This resolution makes analysis over a small study area challenging, which is why we employed oversampling to better analyze NO2 levels and emission causation on a small spatial scale. 
 Given an accurate fixed cell radius oversample requires multiple hourly scans, your used temporal extent is directly related to the accuracy of your created map. Short time periods have an increased chance to lead to data artifact issues, as some scans may show high NO2 levels that can skew the average of the fixed cell if a small number of scans are used. To best produce smoother, accurate maps, long timescales should be utilized (2 week+). Though, TEMPO's high temporal resolution allows for oversampling to be done on smaller timescales (there are around 12 scans per day, though some data points may be missing due to cloud masking etc.), however with the caveat that some artifact issues may be present. Short timescale created maps should be interpreted with that in mind. 

## Applications and Scope   
Script should be used when trying to increase resolution of TEMPO data for enhanced analysis capabilities over various timescales. This can be employed over small study areas, or across any spatial extent with TEMPO's Field of Regard (FOR). This can be best used for better causation analysis regarding emissions of pollutants, general concentration of pollutants, and differences in seen levels within various situations. As well as other general enhanced analysis capabilties that may be facilitated by the ability to increase resolution.

## Capabilities 
This code can increase resolution of TEMPO data for all included pollutants able to be scanned by TEMPO (NO2, CO2, HCHO, etc.). It can do so across all timescales in which files are present (if storage allows, each L2 is ~100MB, with ~12 scans per day). After producing maps they will be output as a NetCDF, and as a PNG. If GIS input of maps is needed, use the NetCDF file. Use "add data, multidimensional raster" (within add data function), and find your intended NetCDF for input. NetCDF will be correctly georeferenced, and able to be further analyzed with geoprocessing tools, etc.

## Interfaces 

### Languages
Python 3.10.16

### Packages
(packages seperated with commas are in the format: from ___ import ___)
- numpy
- os
- pathlib
- glob
- sys
- re
- pandas
- netCDF4, Dataset
- matplotlib.pyplot
- cartopy.crs
- cartopy.feature
- matplotlib.ticker
- cartopy.mpl.gridliner,  LONGITUDE_FORMATTER, LATITUDE_FORMATTER
- datetime
- matplotlib.cm
- cartopy.io.shapereader
- pyresample, geometry,kd_tree
- dateutil, tz
- subprocess, call
- cmocean
- matplotlib.colors, LinearSegmentedColormap

## Parameters
This code has various parameter inputs, allowing for complex analysis capabilities. Most are facilitated through specified arguments within a command line prompt that will be used to initiate runs from your code. 

###### Prompt:
- Command line prompt format with input arguments: !python TEMPOL2toL3.py  datapath  savepath  YYYYMMDD(beg) YYYYMMDD(end)  variable(s)  min_lon,min_lat,max_lon,max_lat,domain


###### Argument overview: 
- !python --> (run prompt, ! needed if done within a notebook and not a terminal)
- TEMPOL2toL3.py --> (script name called on within run prompt)
- datapath --> (path to directory where L2 scans are present)
- savepath --> (path to directory where created maps will be saved)
- YYYMMDD --> (beginning date of temporal extent), YYYYMMDD (ending date of temporal extent)
- variable --> (pollutant of interest)
- min_lon, min_lat, max_lon,max_lat,domain --> (bottom left corner, and top right corner of bounding spatial extent, domain is an input for file referencing, will not effect code beyond filenames created)

- Example Command Line Prompt: !python TempoL2toL3.py /Users/dwilcox3/Downloads/TEMPONO2L2V03FEB /Users/dwilcox3/Downloads/HAQ 20241003 20241231 NO2 -85.14,36.525,-74.17,40.47,VA

###### Parameters within script (some are omitted as they change is not needed for 1:1km oversample, just for further specifications with differing grid sizes): 
1. cmap = generate_cmap ('intended color')   --> (color of generated map) (line 88)
2. cldthresh = 0.2   --> (cloud threshold quality check) (line 176)
3. sza = 80   --> (solar zenith angle threshold) (line 178)
4. maxgran = 20  --> (maximum number of granules per TEMPO nominal scan, granules are a spatial extent index of scans, TEMPO FOR is seperated in standard granule numbers based on area scanned, Ex: GO1 is granule 1, eastern US) (line 181)
5. maxswath = 40   --> (maximum swaths throughout day, swath is the width of an area covered by a sensor as it moves along orbit) (line 183)
6. tversion = 'V03'   --> (version of TEMPO data, will only effect file name creation)
7. gridres = 0.01   --> (this is the radius of your fixed cell grid, this will determine your created resolution) (line 192, 193)
8. timezone = 'US/Eastern'   --> (specify timezone, though files will be in UTC) (line 291)
9. strtz = 'EST'   --> (timezone shorthand) (line 292)
10. ximgsize = 10, yimgsize = 7   --> (dimensions of PNG output) (lines 310,311)
11. producedfile = ('TEMPO_NO2_L3_' + begdate + '_' + enddate + '_l3_0p01_cf20_sza80_VA.nc')   --> (file name created, will index time, but data level, quality flags, and domain are hardcoded in within this version, change as needed, also seen in 'dum' on line 1378 as well) (line 424)
12. Within if loop on line 428, if iprod == 'intended pollutant'
vmin, vmax, vstep = 0, 9, 1   --> (this is your scale of molec/cm^2, vmin is minimum number, vmax is maximum, vstep is step interval between values, these scales are with a e+15 magnitude, IE: 0, 9, 1 is 0 to 9e+15, with a 1e+15 timestep) (line 446 in the case of NO2, varying per pollutant but within similar line numbers)


## Assumptions, Limitations, & Errors 
Code cannot go on an hourly basis as it is now, and requires a += day of scans. Cannot index specific time periods within each day (IE: if an average of NO2 production indexing only 1-3pm is desired, code cannot index in that format). This issue can likely be resolved with enhanced file indexing capabilities, I recommend attempting to index by scan number (S00# in L2 file name). If there is not enough data points to avoid skew, an error stating "np.mean runtime error" will occur, this will not stop your code, just signify that data may be skewed due to a lack of data within a grid cell. 

## Support
Given this code is CUI as of now, there are no online resources for help, I would rely on this readme, and attempt to understand each aspect of the code as best as possible. 

## Acknowledgments
Dr. Aaron Naeger (Original Creator, NASA Marshall Flight Center / SPoRT)
Dr. Hazem Mahmoud (Science Lead, NASA ASDC)
Dr. Kenton Ross (LaRC, NASA DEVELOP Lead Science Advisor)

