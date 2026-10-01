# Hampton Roads HAQ III 
**Project:** Hampton Roads Health and Air Quality III    

**Node:**  Virginia – Langley   

**Term:** Spring 2025


**Team:** Joe Horan (Project Lead), David Wilcox, Alexia Stechele, Stormi Nichols
  

**Code Contact:** David Wilcox, david.c.wilcox@outlook.com

## Introduction  
This code uses an API connection to RSIG (Remote Sensing Information Gateway, EPA) to download TEMPO, TROPOMI, Pandora, and AirNow NO2 Data. 
Data is downloaded within a specified spatial bounding box, and with an input time interval. It then uses RSIG regridding capabilties to increase remote sensing data resolution.

Basic Overview of Use: 
- Download NO2 data from various sensors (remote and in-situ)
- Regrid remote sensing data into a 1:1km fixed grid cell format
- Plot downloaded data
- Convert plots into CSV format for input into other data analysis interfaces (IE: Excel, other scripts, etc.)
- Build xarray and map regridded TEMPO data with WGS 1984 coordinate referencing.
- Convert xarray dataset into GeoTiff format for input into GIS

## Applications and Scope   
-   Gather and analyze NO2 data in specified study area
-   Increase resolution of Earth observations (EO) NO2 data to better study specified area (in the case of this project intended for analysis for a small study area)
-   Compare in-situ and remote sensing NO2 measurements for validation purposes

## Capabilities 
-  Compile NO2 data from various sensors (remote and in-situ)
-  Average data points on an hourly timescale
-  Plot in-situ and EO data, and export into usable CSVs
-  Regrid EO data into an increased resolution (Provisional Resolution of EO -> 1:1km)
-  Compare in-situ and EO data within specified area
-  Compare in-situ and EO data from a point of in-situ sensor, using 1:1km regrid to better index data to a sensors specific location. Increasing validation/comparison capabilities (if bounding box is altered to index specific location of a sensor)
-  Map increased resolution EO data within script as xarray
-  Convert xarray as georeferenced Tiff file (GeoTiff) for subsequent GIS input (This GeoTiff will download within your working directory, rather than your locname folder)

Script allows for increased validation capabilities between remote and in-situ NO2 data comparison, utilizing high spatial resolution regrid to better index sensors encapsulated within a single grid. 

Creates a high resolution NO2 TEMPO map that can be used to study any scanned area over various timescales, including: hourly, daily, etc. 

Allows for situational analysis, mapping a specific time period in which NO2 production is intended to be analyzed (within our project we mapped specific traffic build-ups and how NO2 was produced locally over the period of traffic instance of focus)



## Interfaces 

### Languages
Python 3.10.16

### Packages
pyproj
xarray
pyrsig
pandas
pycno
getpass
matplotlib.pyplot

## Parameters (All Within Cell 3):
1. Specify Grid Parameters
- grid = dict(
    GDNAM='GLOBAL', GDTYP=1, NCOLS=7200, NROWS=3600,
    XORIG=-125, YORIG=20, XCELL=0.01, YCELL=0.01,
    P_ALP=0., P_BET=0., P_GAM=0., XCENT=0., YCENT=0.) 
- This grid set-up uses 'GLOBAL' to form WGS 1984 (geographic crs) referenced grid
- Other grid parameters include '1US1' for conic crs, grid parameters can be located through RSIG resources
- Other included grid variables build dimensions of mapping grid and future xarray, ex: XCELL = 0.01 creates the 1:1 km fixed cell radius in which data is re-gridded.

2. Specify File Download Location:
- locname = 'Intended File location'
- Ex: locname = 'HRBT'

3. Specify Spatial Extent (Bounding Box):
- Created bounding box uses a bottom left corner, and top right corner coordinate reference to build box of spatial boundaries
- Ex: bbox = (-76.93, 36.55, -75.86, 37.37)

4. Specify intended time interval (UTC):
- bdate = yyyy-mm-dd hh:mm:ss (Inital timestamp of intended interval)
- Ex: bdate = '2024-09-13 13:00:00'
- edate = yyyy-mm-dd hh:mm:ss (Ending timestamp of intended interval)
- Ex: edate = '2024-09-13 19:00:00'


## Assumptions, Limitations, & Errors 
This code has various limitations, and is best utilized with a supplementary code meant for longer timescale oversampling (fixed cell radius grid creation using L2 scans).

- Script has issues processing long time periods of data due to backend issues with RSIG connection.
- Will produce an error stating backend connection to RSIG has timed out
- Occasionally RSIG will fail to build dataframe for indexed data, this is likely due to a lack of RSIG connection, which results in an empty gzip file being downloaded. Clear the cached data from your 'locname' folder, and re-run the script. 
- Sometimes data will be available for some sensors, and unavailable for others. If that is the case the gzip file downloaded for the unavailable sensor will be empty. This results in an error during the hourly average of data. To skip a specific sensor and continue to get data from other sensors run the code past the failed cell, or implement an 'if' statement that skips the specific error and moves on to the next dataset.
- Error Ex: (KeyError: 'The grouper name time is not found')
- If parameter is changed on a timestamp where data is already cached, that data must be deleted from the 'locname' directory to implement the parameter change into mapping. 
- Ex: Changing grid parameter for a time interval that has already been processed within the code will require previous data to be cleared before new parameter run. If cached files are not cleared mapped data will lack the new parameter change and instead show the previous run's cached data.

## Support
Code is based off of ASDC RSIG template (TEMPO Folder):
- https://github.com/nasa/ASDC_Data_and_User_Services/tree/main


## Acknowledgments
NASA ASDC (Atmospheric Science Data Center)
Dr. Hazem Mahmoud (Science Lead, ASDC)

