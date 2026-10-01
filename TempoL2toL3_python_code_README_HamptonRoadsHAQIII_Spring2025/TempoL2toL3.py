
"""
TempoL2toL3.py

Initial Creator:
Aaron Naeger
aaron.naeger@nasa.gov
NASA Marshall Space Flight Center / SPoRT

Secondary User: 
Langley Research Center
LaRC DEVELOP, Hampton Roads HAQ III
David Wilcox (2025 Spring Participant)
david.c.wilcox@outlook.com

Description:
  This script will generate level 3 TEMPO maps and data files from L2 files
    for requested variables and dates/times

Usage:
  python TEMPO_L2toL3_maps.py  datapath  savepath  YYYYMMDD(beg) YYYYMMDD(end)  variable(s)  [min_lon,min_lat,max_lon,max_lat,domain]

Arguments:
    (1) datapath: TEMPO data path, e.g., /raid1/sport/people/anaeger/TEMPO/fast_l2/data
    (2) savepath: path to where PNGs will be saved
    (3) YYYYMMDD: YYYY (year), MM (month), DD (day), HH (hour) for start date
    (4) YYYYMMDD: YYYY (year), MM (month), DD (day), HH (hour) for end date
    (5) Variable(s), request one or more, e.g., NO2,HCHO,O3,SO2,CHOCHO,BRO,H2O
          Default is troposhere, but option available to specify stratosphere or total
             - Add column option (total,strat) to end of variable list
                e.g., NO2,HCHO,O3,total  OR   NO2,HCHO,O3,strat 
                    Leave blank for troposphere  e.g., NO2,HCHO             
             - Add option to plot AMF map with valid trace gases to end of variable list,
                          after column option if present
                e.g., NO2,HCHO,O3,AMF    OR   NO2,HCHO,O3,total,AMF
                    Leave blank for only product map, no AMF  e.g., NO2,HCHO
    (6) min_lon,min_lat,max_lon,max_lat (optional): PNG extent.
          Default is full TEMPO Field of Regard
        domain (only allowed with PNG extent argument):
          Name given to provided extent. Default is 'TempoFOR'
"""
import numpy as np
import os
import pathlib
import glob
import sys
import re
import pandas as pd
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import datetime
import matplotlib.cm as cm
import cartopy.io.shapereader as shpreader
from pyresample import geometry,kd_tree
from dateutil import tz
from subprocess import call
import cmocean
def generate_cmap(name, num_colors):
    if name == 'HomeyerRainbow':
        return plt.get_cmap('rainbow', num_colors)  # You can replace 'rainbow' with other colormap names
    return None
 
def main():
 
    cmap = generate_cmap('HomeyerRainbow', 40)
 
 
if __name__ == "__main__":
    main()
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
 
colors = ['#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FF0000']  # Replace with your actual color values
cmaps = LinearSegmentedColormap.from_list("no2barV2", colors)
 
def main():
    # Use the cmaps.no2barV2 colormap
    cmap = cmaps
    # Your other code here
 
if __name__ == "__main__":
    main()
# Ensure you are referencing the right variable, e.g., `cmap`
cmap = generate_cmap('HomeyerRainbow', 40)

#sys.path.insert(0,'/home/anaeger/special/')
#import colormap_generator
#import colormaps as cmaps
#sys.path.insert(0,'/home/anaeger/sensor_read_scripts/')
#import ABI_read

### ARGUMENTS GIVEN ON COMMAND LINE ###
# Error message if user messes up arguments

#EXAMPLE ARGUMENTS
# Real Argument will be given in command line when running the code through terminal, etc.

# Example Argument: !python TempoL2toL3.py /Users/dwilcox3/Downloads/TEMPONO2L2V03FEB /Users/dwilcox3/Downloads/HAQ 20240601 20240623 NO2 -76.93,36.5,-75.87,37.37,VA

nargs = len(sys.argv)
if (nargs == 6) or (nargs == 7):
    maindir = sys.argv[1]
    savepath = sys.argv[2]
    begdate = sys.argv[3]
    if len(begdate) != 8:
        raise ValueError('third argument should be of form YYYYMMDD')
    else:
        nc_beg = datetime.datetime.strptime(begdate, '%Y%m%d')
    enddate = sys.argv[4].split(',')
    if len(enddate[0]) != 8:
        raise ValueError('fourth argument should be of form YYYYMMDD')
    else:
        nc_end = datetime.datetime.strptime(enddate[0], '%Y%m%d')
    if len(enddate) == 2:
        tfreq = enddate[1]
    else:
        tfreq = 1
    enddate = enddate[0]
    var = np.asarray(sys.argv[5].split(','))
    dum = np.where((var == 'total') | (var == 'strat'))
    numvar = (var[dum])
    if len(numvar) == 1:
        coltype = var[dum]
        dummy = dum
    if len(numvar) > 1:
        raise ValueError('fifth argument cannot have more than 1 column type')
    if len(numvar) == 0:
        coltype = 'trop'
        dummy = 99
    dum = np.where((var == 'AMF'))
    numvar = (var[dum])
    if len(numvar) == 1:
        plotamf = True
        dummy2 = dum
    if len(numvar) == 0:
        plotamf = False
        dummy2 = 99
    if dummy == 99 and dummy2 == 99:
        spec = sys.argv[5].split(',')
    else:
        dumlow = np.squeeze(np.minimum(dummy,dummy2))
        spec = sys.argv[5].split(',')[:dumlow]
    if nargs == 6:
        extent = [-162.,16.,-26.,62.]
        domain = 'for'
    else: #nargs == 7 in this case
        input_extent = sys.argv[6].replace('[','')
        input_extent = input_extent.replace(']','')
        input_extent = input_extent.split(',')
        print(input_extent)
        extent = np.squeeze(np.array(input_extent[:-1], dtype=float))
        domain = str(input_extent[-1])
       # check that extent is valid
        if ((len(input_extent) != 5) or
            (extent[0] >= extent[2]) or (extent[1] >= extent[3])):
            raise SyntaxError(
            'Sixth argument should be of form "min_lon,min_lat,max_lon,max_lat,domain"')
else:
    raise SyntaxError('Incorrect number of arguments:\n'+usage+'\n')

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Switch to overlay multiple granules across hourly TEMPO Field of Regard
#  Set to False if plotting single granules is desired
mult_gran = True
# If a subset number of granules were downloaded only over a location of interest over the
#  TEMPO FoR, then set spec_gran = True
spec_gran = False

# cloud threshold to cloud clearing ... set to 1.0 for no cloud clearing
#  0.3 (typical)smooth = False
#cldthresh = 0.5
cldthresh = 0.2
# sza threshold
szathresh = 80.
#szathresh = 70.
# maximum # of granules per TEMPO nominal scan
maxgran = 20
# maximum swaths throughout the day
maxswath = 40

# Version of TEMPO data
tversion = 'V03'

# Fill value
fillval = -999.0

# Specifications for level 2 to 3 remapping
#gridres = 0.005
gridres = 0.01
# Radius distances (m) to search for points, longer distances useful for TEMPO FOR edges
## Specifications for 0.05 degree grid
interdis = 8000.
n_count_temp = 6
## Specifications for 0.02 degree grid
#interdis = 4000.
#n_count_temp = 6
##interdis = 3000.
##n_count_temp = 4
interdis = 2500.
n_count_temp = 1
### Switch to breakdown oversampled maps into hourly maps based on local time
### with 30 minute time window based on hourly TEMPO scans
dotime = True
#dotime = True
dotimeHHMM = ['1500','30']

# option to track a particular footprint along the TEMPO FoR (hardcode index settings for specific granule)
savepoint = False
scanl = 49
crosst = 750

# user can filter data based on day of week by setting value below. For all days, set to 8
dayfilter = 8

# Switch to remap to GOES ABI grid
abi_grid = False

# switch for saving data to gridded L3 file
savencdf_op = True
# netcdf file format with specifications similar to TEMPO operational files
savencdf = True
savepng = True
######
# Plot settings
#  for TEMPO Field of Regard
if domain == 'for':
    lon_spacing, lat_spacing = 20, 10
    lon_offset, lat_offset = 12, 4

    fontsize = 12
    barsize = 0.016
    linewidth = 0.6

    dpi = 300
    # resolution features in make_map
    resmap = '50m'
else:  #
    #  for regional
    lon_spacing, lat_spacing = 0.1, 0.1
    lon_offset, lat_offset = 0, 0

    fontsize = 14
    #barsize = 0.035
    barsize = 0.030
    linewidth = 1.0

    dpi = 300
    # resolution features in make_map
    resmap = '10m'

# does user want to plot counties? Set True or False, default is False
#  if True, user needs countyshape, must specify location and name of shapefile
#   e.g., /raid2/sport/people/anaeger/shapefiles/countyl010g.shp
drawcounty = False
if drawcounty:
    #shpdir = '/home/anaeger/shapefiles/countyl010g.shp'
    reader = shpreader.Reader(shpdir)
    counties = list(reader.geometries())

# CSV file with US cities for labeling later
labelcity = False
#cityloc = '/home/anaeger/special/us_cities.csv'
#citylist = ['San Francisco','Los Angeles','Fresno','Bakersfield','Sacramento','Las Vegas','Reno']
#statelist = ['CA','CA','CA','CA','CA','NV','NV']
#citylist = ['Chicago','Saint Louis','Milwaukee']
#citylist = ['Phoenix','Flagstaff']
#citylist = ['Charlottesville','Richmond']
#citylist = ['Dallas','Houston']
#statelist = ['TX','TX']
#citylist = ['Sacramento','Los Angeles','Las Vegas','Phoenix','Seattle','Boise','Helena','Denver','Salt Lake City','Portland','Dallas','Houston','Saint Louis','Minneapolis','Chicago','Pittsburgh','Nashville','Atlanta','Charlotte','Washington','Orlando','New York','Miami','Omaha']
#statelist = ['CA','CA','NV','AZ','WA','ID','MT','CO','UT','OR','TX','TX','MO','MN','IL','PA','TN','GA','NC','DC','FL','NY','FL','NE']
# Add gridlines and axis labels to map

#mapgrid = True
#maproad = True
mapgrid = False
maproad = False
if maproad:
    #mapdir = '/home/anaeger/special/tl_2019_us_primaryroads.shp'
    reader = shpreader.Reader(mapdir)
    roads = list(reader.geometries())
# add local time to map
addlocal = True
#specify time zone
# timezone = 'US/Central'
# strtz = 'CDT'
timezone = 'US/Eastern'
strtz = 'EST'
# timezone = 'US/Pacific'
# strtz = 'PDT'
#timezone = 'US/Mountain'
#strtz = 'MDT'

# User specifications for city labels, adjust accordingly
#  current settings are based on 'right' horizontal alignment
markersize = 5
cfontsize = 12
horpos ='center'
vertpos = 'bottom'
dbotleft,dtopright = 100.,100.
#!!!!!!!!!!!!!!!!!!!!!
# Standard settings
cb_pad = 0.02

# Figure size
ximgsize = 10
yimgsize = 7

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Set default boundary conditions for TEMPO FoR
#lllon,lllat,urlon,urlat = -162, 16, -26, 62
lllon,lllat,urlon,urlat = extent[0],extent[1],extent[2],extent[3]

# Set some boundary conditions for zoomed in basemap plotting based on arguments
lllon2,lllat2,urlon2,urlat2 = extent[0],extent[1],extent[2],extent[3]
latstep,lonstep = lat_spacing,lon_spacing

# Tick marks
latticks = np.arange(lllat2+lat_offset-latstep,urlat2+latstep,latstep)
lonticks = np.arange(lllon2+lon_offset-lonstep,urlon2+lonstep,lonstep)

# Get range of dates/times
#DATE_TIME_STRING_FORMAT = '%Y%m%d%H'
#d1 = datetime.datetime.strptime(begdate,DATE_TIME_STRING_FORMAT)
#d2 = datetime.datetime.strptime(enddate,DATE_TIME_STRING_FORMAT)

#date_times = [d1.strftime(DATE_TIME_STRING_FORMAT)]
#date_time = d1
#while date_time < d2:
#    date_time += datetime.timedelta(minutes=int(tfreq)*60)
#    date_times.append(date_time.strftime(DATE_TIME_STRING_FORMAT))

# Get range of dates/times
DATE_TIME_STRING_FORMAT = '%Y%m%d'
d1 = datetime.datetime.strptime(begdate,DATE_TIME_STRING_FORMAT)
d2 = datetime.datetime.strptime(enddate,DATE_TIME_STRING_FORMAT)

date_times = [d1.strftime(DATE_TIME_STRING_FORMAT)]
date_time = d1
while date_time < d2:
    date_time += datetime.timedelta(minutes=1440)
    date_times.append(date_time.strftime(DATE_TIME_STRING_FORMAT))

############### GRID ######################
### Latest grid specifications for TEMPO L3 products as of 12/2022
## 0.05 degree grid spacing
#minlat, maxlat = 17.025, 63.975
#minlon, maxlon = -154.975, -24.475
minlat, maxlat = lllat, urlat
minlon, maxlon = lllon, urlon

flats = np.linspace(minlat,maxlat,num=int(((maxlat-minlat)/gridres)+1),endpoint=True)
flons = np.linspace(minlon,maxlon,num=int(((maxlon-minlon)/gridres)+1),endpoint=True)

numlats = len(flats)
numlons = len(flons)

gridlon = np.resize(flons,(numlats,numlons))
gridlat = np.resize(flats,(numlons,numlats))
gridlat = np.transpose(gridlat)

grid_fixed = geometry.GridDefinition(lons=gridlon,lats=gridlat)

### Grid for pcolormesh plotting #################
flats_d = np.linspace(minlat-(gridres/2),maxlat+(gridres/2),num=int(((maxlat-minlat)/gridres)+2),endpoint=True)
flons_d = np.linspace(minlon-(gridres/2),maxlon+(gridres/2),num=int(((maxlon-minlon)/gridres)+2),endpoint=True)

#flats = np.linspace(beglat-(gridres/2),endlat-(gridres/2),num=((endlat-beglat)/gridres)+1,endpoint=True)
#flons = np.linspace(beglon+(gridres/2),endlon+(gridres/2),num=((endlon-beglon)/gridres)+1,endpoint=True)

numlats = len(flats_d)
numlons = len(flons_d)

gridlon_mesh = np.resize(flons_d,(numlats,numlons))
gridlat_mesh = np.resize(flats_d,(numlons,numlats))
gridlat_mesh = np.transpose(gridlat_mesh)

###########################################
"""
# Get ABI grid "Fixed"
if abi_grid:
    # GOES satellite
    gsat = '16'
    # Level & Product type
    levtype = 'L1b'
    prodtype = 'RadF'
    # scantype
    scantype = 'M6C13'

    jday = datetime.datetime.strptime(begdate[:8],"%Y%m%d").timetuple().tm_yday

# Set directories
    goesdir = '/raid2/sport/people/anaeger/GOES/'+gsat+'/data/'+levtype+'/'+\
      '202008'+'/'+'27'+'/'

    goeslist = glob.glob(goesdir+'OR_ABI-'+levtype+'-'+prodtype+'-'+scantype+'_G'+gsat+'_s'+\
      '202024018'+'*.nc')

    gridlat,gridlon,_,_,_,_,_ = ABI_read.abi_geo(goeslist[0],False)

    # Define grid
    grid_fixed = geometry.GridDefinition(lons=gridlon,lats=gridlat)

    # Grid for pcolormesh
    geolat_diff = (abs(gridlat[:-1,:]-gridlat[1:,:])/2.)
    geolon_diff = (abs(gridlon[:,1:]-gridlon[:,:-1])/2.)

    geolat_diff = np.resize(geolat_diff,(np.shape(gridlat)[0],np.shape(gridlat)[1]))
    geolon_diff = np.resize(geolon_diff,(np.shape(gridlon)[0],np.shape(gridlon)[1]))

    # ABI grid is from N-S and W-E, make appropriate boundaries
    gridlat_mesh = gridlat + geolat_diff
    gridlon_mesh = gridlon - geolon_diff

###########################################
"""
#### Main program  ######
def main():
   
    producedfile = ('TEMPO_NO2_L3_' + begdate + '_' + enddate + '_l3_0p01_cf20_sza80_VA.nc')
    #producedfile = ('TEMPO' + 'NO2' + _L3_' + begdate + '_' + enddate + '_l3_0p01_cf20_sza80_' + 'domain' + '.nc')
    dcount = 0
    # Loop through requested products
    for ifile in date_times:
        tcount = 0
        for iprod in spec:
            if iprod == 'O3PROF':
                if coltype == 'pbl':
                # Set O3 range for DU
                    vmin,vmax,vstep = 2,16,2
                if coltype == 'total':
                # Set O3 range for DU
                    vmin,vmax,vstep = 270,370,10
                if coltype == 'trop':
                    vmin,vmax,vstep = 10,60,10
                if coltype == 'strat':
                    vmin,vmax,vstep = 250,370,10
                cmap = plt.cm.jet
            if iprod == 'NO2':
                #scale change parameters
                #vmin,vmax,vstep = 4,12,1
                vmin, vmax, vstep = 0, 9, 1
                #vvmin, vmax, vstep = 1, 9, 1
                #cmap = colormap_generator._generate_cmap('HomeyerRainbow',40)
                #cmap = cmap.no2bar
                cmap = plt.cm.magma_r
                #cmap = cmap.no2barV2
                cmap = generate_cmap('HomeyerRainbow', 40)
                #cmap = cmocean.cm.solar_r
            if iprod == 'HCHO':
                #vmin,vmax,vstep = 0,35,5
                vmin, vmax, vstep = 0, 20, 4
                #cmap = colormap_generator._generate_cmap('HomeyerRainbow',40)
                cmap = generate_cmap('HomeyerRainbow', 40)
                cmap = cmocean.cm.solar_r
          # Set range for plotting
            vrange=np.arange(vmin,vmax+vstep,vstep)

            # Get long name of trace gas for output files
            #if iprod == 'NO2':
                #gas_name_long = 'nitrogen dioxide'
            if iprod == 'NO2':
                gas_name_long = 'troposphere nitrogen dioxide vertical column'
            if iprod == 'HCHO':
                gas_name_long = 'formaldehyde'
            if iprod == 'O3':
                gas_name_long = 'ozone'
            if iprod == 'H2O':
                gas_name_long = 'water vapor'
            if iprod == 'SO2':
                gas_name_long = 'sulfur dioxide'

            # Loop through dates/times #######
           # for ifile in date_times:
    #           # Get all available data files first in top datapath
             #   granlist = np.sort(glob.glob(maindir+'/'+iprod+'/'+\
                #  'TEMPO_'+iprod+'_L2_V01_'+ifile[:8]+'T'+ifile[8:]+'*Z_*G??'+'.nc'))
               # savedir = savepath
    #           # Search in subdirectories based on dates/times if no files found
              #  if len(granlist) == 0:
                   # granlist = np.sort(glob.glob(maindir+'/'+iprod+'/'+ifile[:6]+'/'+ifile[6:8]+'/'+\
                    #  'TEMPO_'+iprod+'_L2_V01_'+ifile[:8]+'T'+ifile[8:]+'*Z_*G??'+'.nc'))
    #              # use same subdirectory path for saving images
                   # savedir = savepath+'/'+ifile[:6]+'/'+ifile[6:8]+'/'

               # if len(granlist) == 0:
                   # print ('NO FILES AVAILABLE FOR '+ifile[:8]+' '+ifile[8:]+'UTC')
                   # continue

               # if len(granlist) > 1:
    #            # Check if all granules are available ...
                    #grannum = np.squeeze([re.findall(r'G..',x) for x in granlist])
                    #grannum = np.asarray([x[1:] for x in grannum],'i')

                # Identify any missing granules
                    #missgran = [x for x in range(grannum[0],grannum[-1]+1) if x not in grannum]
                    ########


           # Get all available data files first in top datapath
            #print(maindir+'/'+iprod+'/'+\
              #'TEMPO_'+iprod+'_L2_'+tversion+'_'+ifile[:8]+'T'+'*'+'*Z_*G??'+'.nc')
            
            #granlist = np.sort(glob.glob(maindir+'/'+iprod+'/'+ifile[:6]+'/'+ifile[6:8]+'/'+\
              #'TEMPO_'+iprod+'_L2_'+tversion+'_'+ifile[:8]+'T'+'*'+'*Z_*G??'+'.nc'))
            
            #granlist = np.sort(glob.glob(maindir+'/'+\
              #'TEMPO_'+iprod+'_L2_'+tversion+'_'+ifile[:8]+'T'+'*'+'*Z_*G??'+'.nc'))
            #granlist = np.sort(glob.glob(maindir+'/'+'TEMPO_'+iprod+'_L2_'+tversion+'_'+ifile[:8]+'T'+'*'+'*Z_*G??'+'.nc'))
            granlist = np.sort(glob.glob('TEMPO_'+iprod+'_L2_'+tversion+'_'+ifile[:8]+'T'+'*'+'*Z_*G??'+'.nc'))
            #if in same folder as data can get ride of maindir, start with tempo with same search pattern 
            for granelement in range(len(granlist)):
                path1 = pathlib.Path(granlist[granelement])
                granlist[granelement]=str(path1)
            print("granlist = ", granlist)
 
            if len(granlist) == 0:
                print ('NO FILES AVAILABLE FORRR '+ifile[:8]+' '+ifile[8:]+'UTC')
                continue
            savedir = savepath+'/'
            print("savedir = ", savedir)
            check=os.path.exists(granlist[0])
            print(check)

            if len(granlist) > 1:
            # Check if all granules are available ...
                grannum = np.squeeze([re.findall(r'G..',x) for x in granlist])
                grannum: ndarray = np.asarray([x[1:] for x in grannum],'i')

            # Identify any missing granules
                missgran = [x for x in range(grannum[0],grannum[-1]+1) if x not in grannum]
                if len(missgran) > 0:
                    print ('FATAL ERROR: Missing granules, check input data')
                    print ('FOUND GRANULES:')
                    print ("granlist = ", granlist)
                    ##continue

            scount, gcount, acount, rcount = 0, 0, 0, 0

            # Loop for arranging TEMPO data files per scan number
            tswath = 0
            tempswath, tempgran = 0, 0
            swath1 = False
            tempfiles = [[0] * maxgran for i in range(maxswath)]
            savesize = [[0] * maxgran for i in range(maxswath)]
            
            
            for igran in granlist:
                filename = igran.split('/')

                filename = filename[len(filename) - 1]
                #print(filename)
             
                filesplit = filename.split('_')
                #print(filesplit)
                
                #adjusting split number to actually fit my path 
                # cd to directory with data and notebooks 

             
                dateHH = int(filename.split('_')[4][9:11])
               
                print(dateHH)
                swath = int(filesplit[5].split('.')[0][2:4])
                gran = filesplit[5].split('.')[0][4:]
                
                
                ncfile = Dataset(igran, 'r')
                
                # Read geolocation group
                geo = ncfile.groups['geolocation']
                lat = geo.variables['latitude']
                xpts = np.shape(lat)[0]

                acount += 1

                # Start looking for files with Hour timestamp >= 10
                #                if tcount == 0 and swath != 1:
                if tcount == 0 and dateHH < 10:
                    continue

                dateHH = filesplit[4][9:11]
                print("dateHH = ", dateHH)
                print("swath =", swath)
                # For data files in YYYYMM/DD directory paths, look for first granule 1 'G01' file.
                if not spec_gran:
                    #if int(gran[1:]) == 1 or gcount >= 1:
                    #changed to find G02 rather than G01, my files start at G02
                    if int(gran[2:]) == 2 or gcount >= 2:
                        if swath > tempswath:
                            #scount += 2
                            scount += 1
                        print('##################################################')
                        print('scan = ' + str(scount - 1))
                        #print('scan = ' + str(scount - 2))
                        #print('granule = ' + str(int(gran[1:]) - 1))
                        print('granule = ' + str(int(gran[2:]) - 1))
                        print('file = ' + filename)
                        print("rcount =", rcount)
                        print("swath = ", swath)

                        if rcount == 0:
                            tempswath = swath

                   
                        tempfiles[scount - 1][int(gran[2:]) - 2] = igran
                     
                        print("igran = ", igran)
                        
                        savesize[scount - 1][int(gran[2:]) - 2] = xpts
                        #changed
                        print("xpts = ", xpts)
                        # tempfiles = np.append(tempfiles, igran, axis = int(swath[1:]))

                        gcount += 1
                       
                        rcount += 1
                       

                    else:
                        print('SKIPPING ... ' + filename)
                        continue
                else:
                    scount += 1
                   
                    savesize[scount - 1][int(gran[1:]) - 1] = xpts
                

                tempswath = int(filesplit[5].split('.')[0][2:4])
                print("tempswath =" ,tempswath)
                tempgran = int(filesplit[5].split('.')[0][5:])
                print("tempgram =" ,tempgran)

                # For final file in YYYYMM/DD directory path, check if files for next day are available for final swaths, check for HHHMM starting with '0'
                #this line was commented out, might help with dcount rewrite
            if acount == len(granlist) and dcount <= len(date_times)-1 and len(date_times) > 1:
                # Increment on day
                dumdate = datetime.datetime(int(filesplit[4][0:4]), int(filesplit[4][4:6]), int(filesplit[4][6:8]), 0,
                                            0, 0)
                print("dumdate = ",dumdate)
                dumdate += datetime.timedelta(days=1)
                print("dumdate 2 =", dumdate)
                dumdate = str(dumdate)
                print("dumdate 3 =",dumdate)
                dumdate = str(dumdate[:4]) + str(dumdate[5:7]) + str(dumdate[8:10])
                print("final dumdate =",dumdate)
                print("date_times = ",date_times)
                print("dcount =", dcount)
                print("acount =", acount)
                if acount == len(granlist) and dcount <= len(date_times):
                    print("len granlist =", len(granlist))
                    print("len date_times=", len(date_times))
                    # Search in subdirectories based on dates/times if no files found
                
                 
        
                    print("dumdate[:6] =", dumdate[:6])
                    print("dumdate :8 =", dumdate [:8])
                    print("dumdate 6:8 = ", dumdate[6:8])

                    #granlist = np.sort(glob.glob('TEMPO_'+iprod+'_L2_'+tversion+'_'+ifile[:8]+'T'+'*'+'*Z_*G??'+'.nc'))
                    print ("long glob dumdate str = ", (iprod + '/' + dumdate[:6] + '/' + \
                                                dumdate[
                                                6:8] + '/' + 'TEMPO_' + iprod + '_L2_' + tversion + '_' + dumdate[:8] + \
                                                'T0' + '*' + '*Z_*G??' + '.nc'))
                    
                  
                    templist = np.sort(glob.glob('TEMPO_'+iprod + '_L2_' + tversion+'_'+ dumdate[:8] + 'T'+'*'+'*Z_*G??'+'.nc'))
                    
             
                    
                print("templist =", templist)
                print("Check")

              
                
                if len(templist) == 0:
                    print ('NO FILES AVAILABLE FORR ' + dumdate[:8])
                    print (
                            'WARNING: ALL GRANULE FILES MAY BE NOT AVAILABLE FOR GENERATING FULLY STITCHED TEMPO MAPS')
                    continue

                    dswath = 0
                    for itemp in templist:
                        filename = itemp.split('/')
                        filename = filename[len(filename) - 1]
                        filesplit = filename.split('_')

                        tswath = int(filesplit[5].split('.')[0][2:4])
                        print("tswath = ", tswath)
                        tgran = int(filesplit[5].split('.')[0][5:])
                        print( "tgran =", tgran)

                        dateHH_next = filesplit[4][9:11]

                        if swath != tswath:
                            scount += 1
                            swath = tswath
                        # if tswath > tempswath and tswath >= dswath:
                        #    scount += 1

                        # Start looking for files with swath #1
                        #                        if int(daygap) == 1 and tswath == 1:
                        #                        if tswath == 1:
                        #                            print('STOP GATHERING DATA FILES: FILES ARE FROM NEXT DAY')
                        #                            break

                        ##                        if tswath == swath or tswath >= dswath:
                        tempfiles[scount - 1][tgran - 1] = itemp
                        savesize[scount - 1][int(gran[1:]) - 1] = xpts
                        print('##################################################')
                        print('ascan = ' + str(scount - 1))
                        print('agranule = ' + str(tgran - 1))
                        print('afile = ' + filename)

                        #                        if tswath < dswath:
                        #                            break

                        dswath = int(filesplit[5].split('.')[0][2:4])
                        dgran = int(filesplit[5].split('.')[0][5:])

                tcount += 1

        # Find maximum number of mirror steps, add 5 to account for possibility of additional mirror steps
            
        #changed indentation of xptsmax and below to next for loop 
            
            #xptsmax = np.max(savesize, axis=1)+5
                xptsmax = np.max(savesize, axis=1)+5
            # Loop through files
                xs, ys = np.shape(tempfiles)
                print("tempfiles = ",tempfiles)
                mcount = 0
                makemap = False
            # xs, ys = np.shape(tempfiles)
            # mcount = 0
            # makemap = False

       
            for nn in range(xs):
                print('#################################################')
                print('######### NEXT SCAN ###########################')
                count = 0
                numstep = 0
                    #added indent to for loop above 
                for mm in range(ys):
                    # Skip to next iteration if no file available
                    if tempfiles[nn][mm] == 0:
                        continue
                    # I think this is due to temp files
                    filename = tempfiles[nn][mm].split('/')
                    filename = filename[len(filename)-1]
                    filesplit = filename.split('_')

                    sattype = filename.split('_')[0]
                    print("sattype = ",sattype)
                    level = filename.split('_')[2]
                    version = filename.split('_')[3]
                    dateYYYYMMDD = filename.split('_')[4][:8]
                    dateHHMM = filename.split('_')[4][9:13]

                    swath = 'S'+filesplit[5].split('.')[0][1:4]
                    gran = filesplit[5].split('.')[0][4:]

                   # Hardcode gas factors for conversion
                    if iprod == 'NO2':
                        gasfact = 1.e15
                        print("NO2 Check")
                    if iprod == 'HCHO':
                        gasfact = 1.e15
                    if iprod == 'O3':
                        gasfact = 2.69e16
                    if iprod == 'O3PROF':
                        gasfact = 1.
                        

                 ### Process geolocation data ####
                    geodata = get_latlon(tempfiles[nn][mm])
                    lat,lon,sza,vza,raz = geodata['lat'],geodata['lon'],\
                      geodata['sza'],geodata['vza'],geodata['raz']

                ### Check day of week ( weekday 1-5, weekend 5-6 values)
                    dte = pd.to_datetime(dateYYYYMMDD[:4]+'-'+dateYYYYMMDD[4:6]+'-'+dateYYYYMMDD[6:8])
                ### Only process data files on certain days of week ####
                    ###if dte.isoweekday() <= 5:
                    if dte.isoweekday() <= dayfilter:

                      # Check to see if TEMPO granule falls within mapping bounds
                        ok = np.where(((lat > lllat) & (lat < urlat)) & ((lon > lllon) & (lon < urlon)))

                   ###################################################################
                        if np.size(ok) > 0:
                            if count == 0:
                                dateHHMM_start = dateHHMM
                                savegrans = []
                                forfiles = '"'+filename+'", '

                            if dcount == 0:
                                dateYYYYMMDD_start = dateYYYYMMDD

                            if addlocal:
                                # Convert to local time (comment out these lines, openaq is in UTC, no conversion needed)
                                to_zone = tz.gettz(timezone)
                                utc = datetime.datetime.strptime(dateYYYYMMDD + ' ' + dateHHMM + '00', '%Y%m%d %H%M%S')
                                lt = utc.replace(tzinfo=to_zone)

                                offset = lt.utcoffset()
                                ltmap = utc + offset
                                ltmap = str(ltmap).split(' ')[1][:5]

                            # Process time variable and convert to UTC
                            timeget = get_timeutc(tempfiles[nn][mm])
                            time = timeget['time']
                            ##timestr = timeget['timestr']

                            savegrans = np.append(savegrans,filename)
                            if count > 0:
                                forfiles += '"'+filename+'",'

                            if dotime:
                                # Do some work on time variables
                                t1 = datetime.timedelta(hours=int(ltmap[:2]), minutes=int(ltmap[3:]))
                                t2 = datetime.timedelta(hours=int(dotimeHHMM[0][:2]), minutes=int(dotimeHHMM[0][2:]))

                                valid_time = datetime.timedelta(hours=int(0), minutes=int(dotimeHHMM[1]))
                                timediff = abs(t1 - t2)
                            else:
                                valid_time = datetime.timedelta(hours=int(24), minutes=int(0))
                                timediff = datetime.timedelta(hours=int(0), minutes=int(0))
                    ############################################################################
                            if timediff < valid_time and count == 0:

                                print('################  PROCESSING FILE  ###################')
                                print('file: '+filename)
                                print(timediff)
                            #####--------------------------------------------------
                           #### Process product and support variables, & perform QC #######
                                vardata = get_vardata(tempfiles[nn][mm],iprod)
                                if iprod == 'O3PROF':
                                    cf = vardata['cf']
                                    gas_tot = vardata['gas_tot']
                                    alb = vardata['alb']
                                    cldpres = vardata['cldpres']
                                    o3pres = vardata['o3pres']
                                    o3ap = vardata['o3ap']
                                    o3aperr = vardata['o3aperr']
                                    o3alt = vardata['o3alt']
                                    o3ak = vardata['o3ak']
                                    o3noise = vardata['o3noise']
                                    tropidx = vardata['tropidx']
                                    o3info = vardata['o3info']
                                    gas_strat = vardata['gas_strat']
                                    gas_trop = vardata['gas_trop']
                                    o3prof = vardata['o3prof']

                                if iprod != 'O3PROF':
                                    var = vardata['gas_tot']
                                    qc = vardata['qc']
                                    snowice = vardata['snowice']
                                    sfcpres = vardata['sfcpres']
                                    hgt = vardata['hgt']
                                    gas_slt = vardata['gas_slt']
                                    gas_sltunc = vardata['gas_sltunc']
                                    eta_a = vardata['eta_a']
                                    eta_b = vardata['eta_b']
                                    amftot = vardata['amftot']
                                    cf = vardata['cf']
                                    long_name = vardata['long_name']

                                if iprod == 'NO2':
                                    var = vardata['gas_trop']
                                    gas_tropunc = vardata['gas_tropunc']
                                    gas_strat = vardata['gas_strat']
                                    troppres = vardata['troppres']
                                    amfstrat = vardata['amfstrat']
                                    amftrop = vardata['amftrop']
                                    cf = vardata['cf']
                                    gas_tot = vardata['gas_tot']
                                    long_name = vardata['long_name']

                         # Remove footprints with too high SZA >= 80 for V1 proxy data
                           # note SZA > 80 for defining unsuitable operational data
            #                    var[sza >= 80.] = np.nan
            #                    var[sza >= 80.] = -1.e30

                            # Apply cloud threshold
                                var[cf > cldthresh] = np.nan
                            # Apply sza threshold
                                var[sza >= szathresh] = np.nan
                            ## threshold for bad values
                                ###var[var < -1.e15] = np.nan

                         # Apply gas factor to convert data
            #                    var = var/gasfact

                         ###########################
                          # Dimension info for making larger array
                                fdims_up = np.shape(lat)
                                fdims = (xptsmax[nn],2048)
                                print("fdims initial =", fdims)
                                #fdims2 = np.shape(tsctwgt)
                                if iprod == 'O3PROF':
                                    fdims = np.shape(o3ak)
                                    fdims2 = np.shape(o3alt)

                            # Make larger arrays for individual data granules
                                if mult_gran and count == 0:
                                    geolat_for = np.zeros((len(granlist)+len(missgran),fdims[0],fdims[1]))+np.nan
                                    geolon_for = (geolat_for*0.)+np.nan
                                    var_for = (geolat_for*0.)+np.nan
                                    sza_for = (geolat_for * 0.) + np.nan
                                    vza_for = (geolat_for * 0.) + np.nan
                                    raz_for = (geolat_for * 0.) + np.nan

                                    if savepoint:
                                        if dcount == 0:
                                            dateYYYYMMDD_save = []
                                            dateHHMM_save = []
                                        # Save lat lon points at certain footprint along TEMPO granules
                                            lat_strip = []
                                            lon_strip = []
                                            #lat_strip = np.zeros(int(float(len(date_times)) * float(maxswath))) + np.nan
                                            #lon_strip = np.zeros(int(float(len(date_times)) * float(maxswath))) + np.nan

                                        if (lat[scanl,crosst] > -90.) & (lon[scanl,crosst] > -180.):
                                            #lat_strip[dcount] = lat[scanl,crosst]
                                            #lon_strip[dcount] = lon[scanl,crosst]
                                            lat_strip = np.append(lat_strip, lat[scanl,crosst])
                                            lon_strip = np.append(lon_strip, lon[scanl, crosst])
                                            dateYYYYMMDD_save = np.append(dateYYYYMMDD_save, dateYYYYMMDD)
                                            dateHHMM_save = np.append(dateHHMM_save, dateHHMM)

                                    if iprod != 'O3PROF':
                                        qc_for = (geolat_for*0.)+np.nan
                                        cf_for = (geolat_for*0.)+np.nan
                                        gastot_for = (geolat_for * 0.) + np.nan
                                        gasstrat_for = (geolat_for * 0.) + np.nan
                                        gastotunc_for = (geolat_for * 0.) + np.nan
                                        sfcpres_for = (geolat_for * 0.) + np.nan
                                        hgt_for = (geolat_for * 0.) + np.nan
                                        snowice_for = (geolat_for * 0.) + np.nan
                                        gasslt_for = (geolat_for * 0.) + np.nan
                                        gassltunc_for = (geolat_for * 0.) + np.nan
                                        alb_for = (geolat_for * 0.) + np.nan
                                        troppres_for = (geolat_for * 0.) + np.nan
                                        cldpres_for = (geolat_for * 0.) + np.nan
                                        amftrop_for = (geolat_for * 0.) + np.nan
                                        amfstrat_for = (geolat_for * 0.) + np.nan
                                        tvertcol_for = (geolat_for * 0.) + np.nan
                                        tamf_for = (geolat_for * 0.) + np.nan
                                        #tsctwgt_for = np.zeros((len(granlist)+len(missgran),fdims2[0],fdims2[1],fdims2[2]))+np.nan
                                        #tgas_for = (tsctwgt_for * 0.) + np.nan
                                        talb_for = (geolat_for * 0.) + np.nan
                                        amf_for = (geolat_for * 0.) + np.nan
                                        amfunc_for = (geolat_for * 0.) + np.nan
                                        pixsiz_for = (geolat_for * 0.) + np.nan

                                    if iprod == 'O3PROF':
                                        cf_for = (geolat_for*0.)+np.nan
                                        gastot_for = (geolat_for * 0.) + np.nan
                                        gasstrat_for = (geolat_for * 0.) + np.nan
                                        gastrop_for = (geolat_for * 0.) + np.nan
                                        o3prof_for = np.zeros((len(granlist) + len(missgran), fdims[0], fdims[1], fdims[2])) + np.nan
                                        alb_for = (geolat_for * 0.) + np.nan
                                        tropidx_for = (geolat_for * 0.) + np.nan
                                        cldpres_for = (geolat_for * 0.) + np.nan
                                        o3pres_for = np.zeros((len(granlist) + len(missgran), fdims2[0], fdims2[1], fdims2[2])) + np.nan
                                        o3alt_for = np.zeros((len(granlist) + len(missgran), fdims2[0], fdims2[1], fdims2[2])) + np.nan
                                        o3ak_for = np.zeros((len(granlist) + len(missgran), fdims[0], fdims[1], fdims[2], fdims[2])) + np.nan
                                        o3noise_for = (o3ak_for * 0.) + np.nan
                                        o3info_for = (geolat_for * 0.) + np.nan
                                        o3aperr_for = (o3prof_for * 0.) + np.nan
                                        o3ap_for = (o3prof_for * 0.) + np.nan
                                        pixsiz_for = (geolat_for * 0.) + np.nan

                                # get earliest time
                                    ##stime = timestr[0]
                                    estime = time[0]

                            # Make larger arrays
                                if mult_gran:
                                    
                                    geolat_for[count,:fdims_up[0],:fdims_up[1]] = lat
                                    
                                    geolon_for[count,:fdims_up[0],:fdims_up[1]] = lon
                                    print("fdims =", fdims_up[0],fdims_up[1])
                                    print("lat array =", len(lat))
                                    print("lon array =", len(lon))
                                    sza_for[count, :fdims_up[0],:fdims_up[1]] = sza
                                    vza_for[count, :fdims_up[0],:fdims_up[1]] = vza
                                    raz_for[count, :fdims_up[0],:fdims_up[1]] = raz

                                    if iprod != 'O3PROF':
                                        qc_for[count,:fdims_up[0],:fdims_up[1]] = qc
                                        cf_for[count,:fdims_up[0],:fdims_up[1]] = cf
                                        sfcpres_for[count, :fdims_up[0],:fdims_up[1]] = sfcpres
                                        hgt_for[count, :fdims_up[0],:fdims_up[1]] = hgt
                                        snowice_for[count, :fdims_up[0],:fdims_up[1]] = snowice
                                        gasslt_for[count, :fdims_up[0],:fdims_up[1]] = gas_slt
                                        gassltunc_for[count,:fdims_up[0],:fdims_up[1]] = gas_sltunc
                                        #tsctwgt_for[count,:fdims2[0],:fdims2[1],:fdims2[2]] = tsctwgt
                                        #tgas_for[count, :fdims2[0],:fdims2[1],:fdims2[2]] = tgas
                                        amf_for[count, :fdims_up[0],:fdims_up[1]] = amftot

                                    if iprod == 'O3PROF':
                                        cf_for[count, :fdims[0], :fdims[1]] = cf
                                        gastot_for[count, :fdims[0], :fdims[1]] = gas_tot
                                        gastropunc_for[count, :fdims_up[0], :fdims_up[1]] = gas_tropunc
                                        gasstrat_for[count, :fdims[0], :fdims[1]] = gas_strat
                                        gastrop_for[count, :fdims[0], :fdims[1]] = gas_trop
                                        o3prof_for[count, :fdims[0], :fdims[1], :fdims[2]] = o3prof
                                        alb_for[count, :fdims[0], :fdims[1]] = alb
                                        tropidx_for[count, :fdims[0], :fdims[1]] = tropidx
                                        cldpres_for[count, :fdims[0], :fdims[1]] = cldpres
                                        o3pres_for[count, :fdims[0], :fdims[1], :fdims2[2]] = o3pres
                                        o3alt_for[count, :fdims2[0], :fdims2[1], :fdims2[2]] = o3alt
                                        o3ak_for[count, :fdims[0], :fdims[1], :fdims[2], :fdims[2]] = o3ak
                                        o3info_for[count, :fdims[0], :fdims[1]] = o3info
                                        o3noise_for[count, :fdims[0], :fdims[1], :fdims[2], :fdims[2]] = o3noise
                                        o3aperr_for[count, :fdims2[0], :fdims2[1], :fdims2[2]] = o3aperr
                                        o3ap_for[count, :fdims2[0], :fdims2[1], :fdims2[2]] = o3ap
                                        pixsiz_for[count, :fdims[0], :fdims[1]] = pixsiz

                                    if iprod == 'NO2':
                                        var_for[count, :fdims_up[0],:fdims_up[1]] = var
                                        gasstrat_for[count, :fdims_up[0],:fdims_up[1]] = gas_strat
                                        troppres_for[count, :fdims_up[0],:fdims_up[1]] = troppres
                                        amftrop_for[count, :fdims_up[0],:fdims_up[1]] = amftrop
                                        amfstrat_for[count, :fdims_up[0],:fdims_up[1]] = amfstrat
                                        gastot_for[count, :fdims_up[0],:fdims_up[1]] = gas_tot

                                    if iprod == 'HCHO':
                                        var_for[count, :fdims_up[0],:fdims_up[1]] = var

                            # Save date
                                dateHHMM_end = dateHHMM

                                # get earliest time
                                ##etime = timestr[len(timestr)-1]
                                eetime = time[len(time)-1]

                                if mult_gran:
                                    numstep = np.shape(var)[0]+numstep

                            ############ Set some parameters for plotting ########
                                expf = str(len(str(int(gasfact)-1)))

                                # Prepare species name for plotting
                                if iprod == 'NO2' or iprod == 'SO2' or iprod == 'O3' or iprod == 'O3PROF':
                                    temp = re.compile("([a-zA-Z]+)([0-9]+)")
                                    res = temp.match(iprod).groups()
                                    prodf = (res[0]).upper()+'_'+(res[1])
                                else:
                                    prodf = iprod.upper()

                                if iprod != 'O3PROF':
                                    dum_label = long_name.title().split(' ')[0]
                                else:
                                    dum_label = ''

                                if dum_label != 'Stratosphere' and dum_label != 'Troposphere':
                                    para_label = 'Total $\mathregular{'+prodf+'}$'
                                else:
                                    para_label = 'Tropospheric'+' '+'$\mathregular{'+prodf+'}$'
                                if iprod == 'O3PROF' and coltype == 'pbl':
                                    para_label = '0-2 km'+' '+'$\mathregular{'+prodf+'}$'
                                if iprod == 'O3PROF' and coltype == 'trop':
                                    para_label = 'Tropospheric'+' '+'$\mathregular{'+prodf+'}$'
                                if iprod == 'O3PROF' and coltype == 'strat':
                                    para_label = 'Stratospheric'+' '+'$\mathregular{'+prodf+'}$'
                            ########################################################
                                count = count+1

            # Continue remapping only if valid data are present
                if count > 0:
                    numval = (var_for > 0.).sum()
                    print(np.nanmin(var_for), np.nanmax(var_for))
                    print(count)
                else:
                    numval = 0

                if mult_gran and count > 0 and numval > 0:
                 # Extract valid chunks from larger arrays
                    geolat_for = geolat_for[:count,:,:]
                    geolon_for = geolon_for[:count,:,:]
                    sza_for = sza_for[:count, :, :]
                    vza_for = vza_for[:count, :, :]
                    raz_for = raz_for[:count, :, :]

                    if iprod != 'O3PROF':
                        qc_for = qc_for[:count,:,:]
                        cf_for = cf_for[:count,:,:]
                        gastot_for = gastot_for[:count,:,:]
                        gastotunc_for = gastotunc_for[:count, :, :]
                        sfcpres_for = sfcpres_for[:count, :, :]
                        hgt_for = hgt_for[:count, :, :]
                        snowice_for = snowice_for[:count, :, :]
                        gasslt_for = gasslt_for[:count, :, :]
                        gassltunc_for = gassltunc_for[:count, :, :]
                        alb_for = alb_for[:count, :, :]
                        cldpres_for = cldpres_for[:count, :, :]
                        tvertcol_for = tvertcol_for[:count, :, :]
                        tamf_for = tamf_for[:count, :, :]
                        #tsctwgt_for = tsctwgt_for[:count, :, :]
                        #tgas_for = tgas_for[:count, :, :]
                        talb_for = talb_for[:count, :, :]
                        amf_for = amf_for[:count, :, :]
                        amfunc_for = amfunc_for[:count, :, :]
                        pixsiz_for = pixsiz_for[:count, :, :]

                    if iprod == 'O3PROF':
                        cf_for = cf_for[:count, :, :]
                        gastot_for = gastot_for[:count, :, :]
                        gasstrat_for = gasstrat_for[:count, :, :]
                        gastrop_for = gastrop_for[:count, :, :]
                        o3prof_for = o3prof_for[:count, :, :, :]
                        alb_for = alb_for[:count, :, :]
                        cldpres_for = cldpres_for[:count, :, :]
                        tropidx_for = tropidx_for[:count, :, :]
                        o3pres_for = o3pres_for[:count, :, :, :]
                        o3alt_for = o3alt_for[:count, :, :, :]
                        o3ak_for = o3ak_for[:count, :, :, :, :]
                        o3info_for = o3info_for[:count, :, :]
                        o3noise_for = o3noise_for[:count, :, :, :, :]
                        o3aperr_for = o3aperr_for[:count, :, :, :]
                        o3ap_for = o3ap_for[:count, :, :, :]
                        pixsiz_for = pixsiz_for[:count, :, :]

                    if iprod == 'NO2':
                        var_for = var_for[:count, :, :]
                        gasstrat_for = gasstrat_for[:count, :, :]
                        troppres_for = troppres_for[:count, :, :]
                        amftrop_for = amftrop_for[:count, :, :]
                        amfstrat_for = amfstrat_for[:count, :, :]

                    if iprod == 'HCHO':
                        var_for = var_for[:count, :, :]

                    geolat_for = np.reshape(geolat_for,[count*np.shape(geolat_for)[1],np.shape(geolat_for)[2]])
                    geolon_for = np.reshape(geolon_for,[count*np.shape(geolon_for)[1],np.shape(geolon_for)[2]])
                    sza_for = np.reshape(sza_for, [count * np.shape(sza_for)[1], np.shape(sza_for)[2]])
                    vza_for = np.reshape(vza_for, [count * np.shape(vza_for)[1], np.shape(vza_for)[2]])
                    raz_for = np.reshape(raz_for, [count * np.shape(raz_for)[1], np.shape(raz_for)[2]])

                    if iprod == 'O3PROF':
                        cf_for = np.reshape(cf_for, [count * np.shape(cf_for)[1], np.shape(cf_for)[2]])
                        gastot_for = np.reshape(gastot_for, [count * np.shape(gastot_for)[1], np.shape(gastot_for)[2]])
                        gasstrat_for = np.reshape(gasstrat_for,
                                                   [count * np.shape(gasstrat_for)[1], np.shape(gasstrat_for)[2]])
                        gastrop_for = np.reshape(gastrop_for, [count * np.shape(gastrop_for)[1], np.shape(gastrop_for)[2]])
                        o3prof_for = np.reshape(o3prof_for, [count * np.shape(o3prof_for)[1], np.shape(o3prof_for)[2], \
                                                            np.shape(o3prof_for)[3]])
                        alb_for = np.reshape(alb_for, [count * np.shape(alb_for)[1], np.shape(alb_for)[2]])
                        cldpres_for = np.reshape(cldpres_for, [count * np.shape(cldpres_for)[1], np.shape(cldpres_for)[2]])
                        tropidx_for = np.reshape(tropidx_for, [count * np.shape(tropidx_for)[1], np.shape(tropidx_for)[2]])
                        o3pres_for = np.reshape(o3pres_for, [count * np.shape(o3pres_for)[1], np.shape(o3pres_for)[2], \
                                                            np.shape(o3pres_for)[3]])
                        o3alt_for = np.reshape(o3alt_for, [count * np.shape(o3alt_for)[1], np.shape(o3alt_for)[2], \
                                                             np.shape(o3alt_for)[3]])
                        o3ak_for = np.reshape(o3ak_for, [count * np.shape(o3ak_for)[1], np.shape(o3ak_for)[2], \
                                                           np.shape(o3ak_for)[3], np.shape(o3ak_for)[4]])
                        o3info_for = np.reshape(o3info_for, [count * np.shape(o3info_for)[1], np.shape(o3info_for)[2]])
                        o3noise_for = np.reshape(o3noise_for, [count * np.shape(o3noise_for)[1], np.shape(o3noise_for)[2], \
                                                         np.shape(o3noise_for)[3], np.shape(o3noise_for)[4]])
                        o3ap_for = np.reshape(o3ap_for, [count * np.shape(o3ap_for)[1], np.shape(o3ap_for)[2], \
                                                           np.shape(o3ap_for)[3]])
                        o3aperr_for = np.reshape(o3aperr_for, [count * np.shape(o3aperr_for)[1], np.shape(o3aperr_for)[2], \
                                                           np.shape(o3aperr_for)[3]])
                        pixsiz_for = np.reshape(pixsiz_for, [count * np.shape(pixsiz_for)[1], np.shape(pixsiz_for)[2]])

                    if iprod == 'NO2' or iprod == 'HCHO':
                        var_for = np.reshape(var_for, [count * np.shape(var_for)[1], np.shape(var_for)[2]])

                 # Remove unused columns of data
                    sza_for = sza_for[:numstep, :]
                    vza_for = vza_for[:numstep, :]
                    raz_for = raz_for[:numstep, :]
                    lat = geolat_for[:numstep,:]
                    lon = geolon_for[:numstep,:]

                    if iprod == 'O3PROF':
                        # Remove unused columns of data
                        cf_for = cf_for[:numstep, :]
                        gastot_for = gastot_for[:numstep, :]
                        gasstrat_for = gasstrat_for[:numstep, :]
                        gastrop_for = gastrop_for[:numstep, :]
                        o3prof_for = o3prof_for[:numstep, :, :]
                        alb_for = alb_for[:numstep, :]
                        cldpres_for = cldpres_for[:numstep, :]
                        tropidx_for = tropidx_for[:numstep, :]
                        o3pres_for = o3pres_for[:numstep, :, :]
                        o3alt_for = o3alt_for[:numstep, :, :]
                        o3info_for = o3info_for[:numstep, :]
                        o3noise_for = o3noise_for[:numstep, :, :, :]
                        o3ak_for = o3ak_for[:numstep, :, :, :]
                        o3aperr_for = o3aperr_for[:numstep, :, :]
                        o3ap_for = o3ap_for[:numstep, :, :]
                        pixsiz_for = pixsiz_for[:numstep, :]

                    if iprod == 'NO2' or iprod == 'HCHO':
                        var_for = var_for[:numstep, :]

                  # Replace non-finite values in lat/lon arrays
                    ###var = np.ma.masked_invalid(var)

                    if count > 1:
                        dum = dateHHMM_start+' - '+dateHHMM_end
                    else:
                        dum = dateHHMM_start

                ########################################################
                # For standard cloud clearing on L3 grid - use fill values in data array when remapping
                    if iprod == 'NO2' or iprod == 'HCHO':
                        lat[np.isnan(var_for)] = -1.e30
                        lon[np.isnan(var_for)] = -1.e30
                    satgrid = geometry.SwathDefinition(lons=lon,lats=lat)
                # Remap product onto L3 grid
                    #var_t = remap(satgrid,grid_fixed,var_for,n_count_temp)
                    wf = lambda r: (interdis**2 - r**2) / (interdis**2 + r**2)

                    valid_input_index, valid_output_index, index_array, distance_array = \
                        kd_tree.get_neighbour_info(satgrid, grid_fixed, interdis, neighbours=n_count_temp)
                    distance_array = np.nan_to_num(distance_array,nan=9999.)

                    if iprod == 'NO2' or iprod == 'HCHO':
                        var_dum = np.ndarray.flatten(var_for)
                    if iprod == 'O3PROF':
                        var_dum = np.ndarray.flatten(gastrop_for)
                        gasstrat_dum = np.ndarray.flatten(gasstrat_for)

                    # extract valid values
                    ##var_idx = (index_array*0.) + np.nan
                    ###index_array[index_array > np.size(var_dum)-1] = np.size(var_dum)-1
                    ##for ii in np.arange(n_count_temp):
                    ##    var_idx[:,ii] = var_dum[index_array[:,ii]]

                    ##var_cnt = var_idx
                    ##var_cnt[(var_cnt <= -1.e30) | (var_cnt >= 1.e30)] = np.nan
                    ##var_cnt[(var_cnt > -1.e30) & (var_cnt < 1.e30)] = 1
                    ##var_cnt = np.nansum(var_cnt,axis=1)
                # get min and max of samples
                    ##var_max = np.nanmax(var_idx,axis=1)
                    ##var_min = np.nanmin(var_idx,axis=1)

                    var_dum = []

                    sza_for = remap(satgrid, grid_fixed, sza_for, n_count_temp)
                    vza_for = remap(satgrid, grid_fixed, vza_for, n_count_temp)
                    raz_for = remap(satgrid, grid_fixed, raz_for, n_count_temp)

                    if iprod == 'O3PROF':
                        print('REMAPPING VARIABLES TO REGULAR GRID')
                        cf_for = remap(satgrid, grid_fixed, cf_for, n_count_temp)
                        gastot_for = remap(satgrid, grid_fixed, gastot_for, n_count_temp)
                        gasstrat_for = remap(satgrid, grid_fixed, gasstrat_for, n_count_temp)
                        ###gastrop_for = remap(satgrid, grid_fixed, gastrop_for, n_count_temp)
                        alb_for = remap(satgrid, grid_fixed, alb_for, n_count_temp)
                        cldpres_for = remap(satgrid, grid_fixed, cldpres_for, n_count_temp)
                        tropidx_for = remap(satgrid, grid_fixed, tropidx_for, n_count_temp)
                        o3info_for = remap(satgrid, grid_fixed, o3info_for, n_count_temp)

                        gdims = np.shape(gridlat)
                        o3ap_for_dum = np.zeros((gdims[0], gdims[1], fdims[2])) + np.nan
                        o3aperr_for_dum = np.zeros((gdims[0], gdims[1], fdims[2])) + np.nan
                        o3prof_for_dum = np.zeros((gdims[0], gdims[1], fdims[2])) + np.nan
                        pixsiz_for = remap(satgrid, grid_fixed, pixsiz_for, n_count_temp)

                        gastrop_for, weights, wcount = remap_gas(satgrid, grid_fixed, gastrop_for, n_count_temp)
                        # calculate area weights in km2
                        areawgt = pixsiz_for * wcount

                        for jj in range(fdims[2]):
                            o3ap_for_dum[:, :, jj] = remap(satgrid, grid_fixed, o3ap_for[:,:,jj], n_count_temp)
                            o3aperr_for_dum[:, :, jj] = remap(satgrid, grid_fixed, o3aperr_for[:, :, jj], n_count_temp)
                            o3prof_for_dum[:, :, jj] = remap(satgrid, grid_fixed, o3prof_for[:, :, jj], n_count_temp)

                        o3pres_for_dum = np.zeros((gdims[0], gdims[1], fdims2[2])) + np.nan
                        o3alt_for_dum = np.zeros((gdims[0], gdims[1], fdims2[2])) + np.nan
                        for jj in range(fdims2[2]):
                            o3pres_for_dum[:, :, jj] = remap(satgrid, grid_fixed, o3pres_for[:, :, jj], n_count_temp)
                            o3alt_for_dum[:, :, jj] = remap(satgrid, grid_fixed, o3alt_for[:, :, jj], n_count_temp)

                        o3ap_for = o3ap_for_dum
                        o3aperr_for = o3aperr_for_dum
                        o3prof_for = o3prof_for_dum
                        o3pres_for = o3pres_for_dum
                        o3alt_for = o3alt_for_dum

                        # Average onto layer for Level 3 product
                        o3pres_for_dum = np.zeros((gdims[0], gdims[1], fdims[2])) + np.nan
                        o3alt_for_dum = np.zeros((gdims[0], gdims[1], fdims[2])) + np.nan
                        for jj in range(fdims[2]):
                            o3pres_for_dum[:, :, jj] = np.nanmean(o3pres_for[:,:,jj:jj+2])
                            o3alt_for_dum[:, :, jj] = np.nanmean(o3alt_for[:, :, jj:jj+2])

                        o3pres_for = o3pres_for_dum
                        o3alt_for = o3alt_for_dum

                    o3ap_for_dum, o3aperr_for_dum, o3prof_for_dum, o3pres_for_dum, o3alt_for_dum = [],[],[],[],[]

                    if iprod == 'HCHO':
                        ##gastot_for, weights, wcount = remap_gas(satgrid, grid_fixed, gastot_for, n_count_temp)
                        var_for = remap(satgrid, grid_fixed, var_for, n_count_temp)
                    # calculate area weights in km2
                        #areawgt = pixsiz_for*wcount
                        getdums = np.shape(var_for)

                    if iprod == 'NO2':
                    #    var_for, weights, wcount = remap_gas(satgrid, grid_fixed, var_for, n_count_temp)
                        var_for = remap(satgrid, grid_fixed, var_for, n_count_temp)
                        # calculate area weights in km2
                        getdums = np.shape(var_for)

                        var_for[var_for <= -1.e30] = np.nan

                    print('FINISHED REMAPPING VARIABLES TO REGULAR GRID')
                    print('dount: '+str(dcount))
                    if dcount == 0:
                        print('MAKE VARIABLE ARRAY')
                        var_avg = np.zeros((len(date_times)*maxswath, getdums[0], getdums[1])) + np.nan
                    var_avg[dcount,:,:]= var_for

                    dcount += 1
                    ################################################
         ###########################
                # Save data if requested
                    forfiles = forfiles[:-1]
                    
                    #check this for pathing issues, uses backslash break which has caused issues
                    
                    if savencdf_op:
                        #savefile = maindir+'/'+sattype+'_'+iprod+'_L3_'+'V01'+'_'+\
                        #  dateYYYYMMDD+'T'+dateHHMM[:2]+'0000Z'+'_'+swath+'.nc'
                        
                        #commented out savefile with maindir for check
                        #given this is save file might not be issue, but pathing could be wrong
                        
                        # savefile = maindir+'/'+iprod+'/'+ifile[:6]+'/'+ifile[6:8]+'/'+sattype+'_'+iprod+'_L3_'+tversion+'_'+\
                        #   dateYYYYMMDD + 'T' + dateHHMM[:2] + '0000Z' + '_' + swath + '.nc'
                        savefile = iprod+'/'+ifile[:6]+'/'+ifile[6:8]+'/'+sattype+'_'+iprod+'_L3_'+tversion+'_'+\
                          dateYYYYMMDD + 'T' + dateHHMM[:2] + '0000Z' + '_' + swath + '.nc'
                        if iprod == 'HCHO':
                            var_for, gasstrat_for, troppres_for, amftrop_for, amfstrat_for, strat_cnt, strat_min, \
                              strat_max = [],[],[],[],[],[],[],[]
                        # if iprod != 'O3PROF':
                        #     makencdf_op(savefile,var_for,qc_for,cf_for,sza_for,vza_for,raz_for,flats,flons,savegrans,\
                        #       gasstrat_for,gastot_for,gastotunc_for,sfcpres_for,hgt_for,snowice_for,gasslt_for,gassltunc_for,alb_for,\
                        #       troppres_for,cldpres_for,amftrop_for,amfstrat_for,var_cnt,var_min,var_max,strat_cnt,\
                        #       strat_min,strat_max,tvertcol_for,tamf_for,talb_for,\
                        #       eta_a,eta_b,amf_for,amfunc_for,stime,etime,estime,eetime, gas_name_long, forfiles, areawgt)
                        if iprod == 'O3PROF':
                            gas_name_long = 'ozone profile'
                            makencdf_o3(savefile,cf_for,sza_for,vza_for,raz_for,flats,flons,savegrans,\
                              gasstrat_for,gastot_for,gastrop_for,o3prof_for,alb_for,\
                              cldpres_for,var_cnt,var_min,var_max,\
                              stime,etime,estime,eetime, gas_name_long, forfiles, areawgt,\
                              tropidx_for,o3info_for,o3ap_for,o3aperr_for,o3pres_for,o3alt_for)

######################################################
######################################################
    if 'var_avg' in locals() and var_avg is not None:
        #this is making all var_avg nan
        var_avg[var_avg <= -1.e30] = np.nan
        #var_avg[var_avg >= - 1.e30] = np.nan
        print("var_avg line 1403 =", var_avg)
    else:
        print("var_avg is not defined or contains no data.")
    
    #var_avg[var_avg <= -1.e30] = np.nan
    #uncommented to see what happens
    print("nan min/nanmax =", np.nanmin(var_avg),np.nanmax(var_avg))
    var_avg = np.nanmean(var_avg,axis=0)

    dum = 'l3_0p01_cf20_sza80'
    ######## SAVE FILE ##########################
    if savencdf == True:
        #ncfile = Dataset('TEMPO_NO2_L3_20250205_20250207_l3_0p01_cf20_sza80_VA_scale2.nc', 'w',format = 'NETCDF4')
        ncfile = Dataset(producedfile, 'w',format = 'NETCDF4')
        # savecheck = ("savedir =",savedir + sattype + '_' + iprod + '_' + 'L3' + '_' + dateYYYYMMDD_start+'_'+dateYYYYMMDD + '_' + \
        #       dum+'_'+domain+ '.nc')
        savevar = (savepath)
        print("savedir =",savedir + sattype + '_' + iprod + '_' + 'L3' + '_' + dateYYYYMMDD_start+'_'+dateYYYYMMDD + '_' + \
              dum+'_'+domain+ '.nc')
        #templist = np.sort(glob.glob('TEMPO_'+iprod + '_L2_' + tversion+'_'+ dumdate[:8] + 'T'+'*'+'*Z_*G??'+'.nc'))
        #granlist = np.sort(glob.glob('TEMPO_'+iprod+'_L2_'+tversion+'_'+ifile[:8]+'T'+'*'+'*Z_*G??'+'.nc'))
        # ncfile = Dataset(
        #     savedir + sattype + '_' + iprod + '_' + 'L3' + '_' + dateYYYYMMDD_start+'_'+dateYYYYMMDD + '_' + \
        #       dum+'_'+domain+ '.nc','w', format='NETCDF4')
            
        # savedir + sattype + '_' + iprod + '_' + 'L3' + '_' + dateYYYYMMDD_start+'_'+dateYYYYMMDD + '_' + \
        #       dum+'_'+domain+ '.nc','w', format='NETCDF4')
        # savedir + sattype + '_' + iprod + '_' + 'L3' + '_' + dateYYYYMMDD_start+'_'+dateYYYYMMDD + '_' + dum+'_'+domain+ '.nc','w', format='NETCDF4')
        # ncfile = Dataset(savevar,'w',sattype + '_' + iprod + '_' + 'L3' + '_' + dateYYYYMMDD_start+'_'+dateYYYYMMDD + '_' + dum+'_'+domain+ '.nc', format='NETCDF4')
        # savedir + sattype + '_' + iprod + '_' + 'L3' + '_' + dateYYYYMMDD_start+'_'+dateYYYYMMDD + '_' + dum+'_'+domain+ '.nc','w', format='NETCDF4')
        
        ncfile.createDimension('latitude', len(flats))
        ncfile.createDimension('longitude', len(flons))

        lat_set = ncfile.createVariable('latitude', 'f4', ('latitude'))
        lat_set[:] = flats

        lat_set.long_name = 'latitude'
        lat_set.units = 'degrees_north'

        lon_set = ncfile.createVariable('longitude', 'f4', ('longitude'))
        lon_set[:] = flons

        lon_set.long_name = 'longitude'
        lon_set.units = 'degrees_east'

        no2_set = ncfile.createVariable('vertical_column_troposphere', 'float32',
                                        ('latitude', 'longitude'))
        #more dimensions than allowed in below line
        print("var_avg before remap =" , var_avg)
        print("no2_set = ", no2_set[:, :])
        no2_set[:, :] = var_avg
        no2_set.units = 'molecules/cm^2'

        ncfile.close()
        ################################################

    # Make image
    fig = make_map(resmap)

#                gridlon_mesh[np.isnan(gridlon_mesh)] = -1.e30
#                gridlat_mesh[np.isnan(gridlat_mesh)] = -1.e30

    var_avg = var_avg / gasfact
    print("var_avg after gasfact =", var_avg)
  # Plot city locations if requested
    if labelcity:
        get_cities()

#                plt.title('Proxy TEMPO '+para_label+'  '+dateYYYYMMDD+' '+dum+\
#                  ' UTC',fontsize=fontsize)
    plt.title('TEMPO '+para_label+'  '+dateYYYYMMDD_start+' '+dateYYYYMMDD,fontsize=fontsize)

    plt.pcolormesh(gridlon_mesh,gridlat_mesh,var_avg,transform=ccrs.PlateCarree(),cmap=cmap,\
      vmin=vmin,vmax=vmax,shading='flat')

    cbar=plt.colorbar(fraction=barsize,pad=cb_pad,ticks=vrange)

    if iprod != 'O3PROF':
        cbar.set_label('$\mathregular{10^{'+expf+'}}$ molec./$\mathregular{cm^2}$',size=fontsize)
    if iprod == 'O3PROF':
        cbar.set_label('Dobson Units',size=fontsize)

    cbar.ax.tick_params(labelsize=fontsize)

#                plt.savefig(savedir+sattype+'_'+dateYYYYMMDD+'_'+dateHHMM_start+'_'+\
#                  dateHHMM_end+'UTC'+'-'+iprod+'-'+domain+'.png',bbox_inches='tight')
    print('savedir: '+savedir)
    plt.savefig(savedir+dateYYYYMMDD_start+'_'+dateYYYYMMDD+'_'+\
      sattype.lower()+'_'+iprod.lower()+'_'+dum+'_'+domain+'_cf20_sza80_2p5km_1pts.png',dpi=dpi,bbox_inches='tight')

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Write csv file for lat lon values at certain mirror step and cross track pixel location
    if savepoint:
        #lat_strip_dum = lat_strip[(lat_strip > -90.) & (lon_strip > -180.)]
        #lon_strip_dum = lon_strip[(lat_strip > -90.) & (lon_strip > -180.)]

        lat_strip_dum = lat_strip
        lon_strip_dum = lon_strip
        print(np.shape(lat_strip))
        print(np.shape(lat_strip_dum))
        print(np.shape(dateYYYYMMDD_save))
	
        df = pd.DataFrame({'Date (YYYYMMDD)': dateYYYYMMDD_save, 'Time (HHMM)': dateHHMM_save, 'Latitude': lat_strip_dum, 'Longitude': lon_strip_dum})
        df['Latitude'] = df['Latitude'].astype(float).round(4)
        df['Longitude'] = df['Longitude'].astype(float).round(4)
        df.to_csv(maindir + '/' + 'pixel_latlon_values'+'_'+ dateYYYYMMDD_start+'_'+dateYYYYMMDD+'_'+domain+'.csv', index=False, sep=',')
###################################################################
####### FUNCTIONS ###############
def get_latlon(data):
    ncfile = Dataset(data,'r')
 # Read geolocation group
    geo = ncfile.groups['geolocation']

 # For level 3 data, use center lat/lon
    lat = geo.variables['latitude']
    lat = lat[:,:]

    lon = geo.variables['longitude']
    lon = lon[:,:]

  # Process SZA for QC
    sza = geo.variables['solar_zenith_angle']
    sza = sza[:,:]

    vza = geo.variables['viewing_zenith_angle']
    vza = vza[:,:]

    raz = geo.variables['relative_azimuth_angle']
    raz = raz[:,:]

    ncfile.close()

    return {'lat':lat,'lon':lon,'sza':sza,'vza':vza,'raz':raz}

#######################
def get_timeutc(data):
    ncfile = Dataset(data,'r')

    timeref = ncfile.getncattr('time_reference')

 # Read geolocation group
    geo =  ncfile.groups['geolocation']
  # Process time  
    time = geo.variables['time']
    fill = time._FillValue
    time = time[:]

    time[np.isnan(time)] = fill
    time = np.ma.fix_invalid(time,fill_value=np.nan)

    timestr = []
#    for n in range(0,len(time)):
#        timedum = datetime.datetime(2000,1,1,12,0,0) + datetime.timedelta(seconds=time[n])
#        timedum = str(timedum).split(' ')[1].replace(':','')[:4]
#        timestr = np.append(timestr,timedum)

    ncfile.close()

    return {'time':time,'timestr':timestr}
##################
def get_vardata(data,iprod):
    print ('***** VALID FILE ******* ')
    ncfile = Dataset(data,'r')
# Read group and variable based on input argument
    vars = ncfile.groups['product']
    support = ncfile.groups['support_data']
    if iprod == 'HCHO':
        gas_tot = vars.variables['vertical_column']
        long_name = gas_tot.long_name
        fill = gas_tot._FillValue
        gas_tot = gas_tot[:]
        gas_totunc = vars.variables['vertical_column_uncertainty']
        gas_totunc = gas_totunc[:]
    if iprod == 'NO2':
#        if coltype == 'trop' or coltype == 'total':
#            varget = vars.variables['vertical_column_troposphere']
#        if coltype == 'strat':
#            varget = vars.variables['vertical_column_stratosphere']
        gas_trop = vars.variables['vertical_column_troposphere']
    # Get name attribute for plotting purposes later
        long_name = gas_trop.long_name
        gas_trop = gas_trop[:]
    # Replace masked (fill) value with NaN
        gas_trop = np.ma.filled(gas_trop, fill_value=np.nan)

        gas_strat = vars.variables['vertical_column_stratosphere']
        gas_strat = gas_strat[:]
        gas_tot = gas_trop+gas_strat
        ##gas_tot = vars.variables['vertical_column_total']
        ##gas_tot = gas_tot[:]
        gas_tropunc = vars.variables['vertical_column_troposphere_uncertainty']
        gas_tropunc = gas_tropunc[:]

    if iprod == 'O3PROF':
        gas_tot = vars.variables['total_ozone_column']
        gas_tot = gas_tot[:]
        gas_strat = vars.variables['stratosphere_ozone_column']
        gas_strat = gas_strat[:]
        gas_trop = vars.variables['troposphere_ozone_column']
        gas_trop = gas_trop[:]
        o3prof = vars.variables['ozone_profile']
        o3prof = o3prof[:]

        ##fill = varget._FillValue
        
    ########### start quality control procedures ################
    if iprod != 'O3PROF':
    # Data quality for QC
        data_qc = vars.variables['main_data_quality_flag']#[:]
        data_qc = data_qc[:]

    # Cloud fraction for QC
        cldfra = support.variables['eff_cloud_fraction']#[:]
        cldfra = cldfra[:]

        sfcpres = support.variables['surface_pressure']  # [:]
        eta_a = sfcpres.Eta_A
        eta_b = sfcpres.Eta_B
        sfcpres = sfcpres[:]

        hgt = support.variables['terrain_height']  # [:]
        hgt = hgt[:]

        snowice = support.variables['snow_ice_fraction']  # [:]
        snowice = snowice[:]

        gas_slt = support.variables['fitted_slant_column']  # [:]
        gas_slt = gas_slt[:]

        gas_sltunc = support.variables['fitted_slant_column_uncertainty']  # [:]
        gas_sltunc = gas_sltunc[:]

        alb = support.variables['albedo']  # [:]
        alb = alb[:]

        cldpres = support.variables['amf_cloud_pressure']  # [:]
        cldpres = cldpres[:]

    if iprod == 'NO2':
        amftrop = support.variables['amf_troposphere']  # [:]
        amftrop = amftrop[:]

        amfstrat = support.variables['amf_stratosphere']  # [:]
        amfstrat = amfstrat[:]

        troppres = support.variables['tropopause_pressure']  # [:]
        troppres = troppres[:]

        amftot = support.variables['amf_total']  # [:]
        amftot = amftot[:]

    # Data quality for QC
        data_qc = vars.variables['main_data_quality_flag']#[:]
        fill = data_qc._FillValue
        data_qc = data_qc[:]

    # set flag field for masking poor data
        flags = (gas_trop*0)+0
    # Data quality (good = 0, suspect = 1 (not used), bad = 2)
      # V01 only flags invalid data
        bad = np.where(data_qc > 1)
        flags[bad] = 1

        data_qc = np.ma.filled(data_qc,fill_value=1)

        # Disregard poor data
        gas_trop[flags == 1] = np.nan

    # Cloud fraction for QC
        cldfra = support.variables['eff_cloud_fraction']#[:]
        cfill = cldfra._FillValue
        cldfra = cldfra[:]

    # Cloud fraction
        cldfra = np.ma.filled(cldfra,fill_value=1.0)
        bad = np.where((cldfra > cldthresh))

        gas_trop[bad] = np.nan

    if iprod == 'HCHO':
        amftot = support.variables['amf']  # [:]
        amftot = amftot[:]

#        amftotunc = support.variables['amf_uncertainty']  # [:]
#        amftotunc = amftotunc[:]

        #t_amf = true.variables['amf']  # [:]
        #t_amf = t_amf[:]

        #t_vertcol = true.variables['vertical_column']  # [:]
        #t_vertcol = t_vertcol[:]

    if iprod == 'O3PROF':
    # Cloud fraction for QC
        cldfra = support.variables['eff_cloud_fraction']
        cfill = cldfra._FillValue

#        if coltype == 'pbl':
#        # Get name attribute for plotting purposes later
#            long_name = '0-2 km ozone'
#        else:
#            long_name = varget.comment

        cldfra = cldfra[:]

        cldpres = support.variables['eff_cloud_pressure']  # [:]
        cldpres = cldpres[:]

        o3pres = support.variables['ozone_profile_pressure']  # [:]
        o3pres = o3pres[:]

        o3alt = support.variables['ozone_profile_altitude']  # [:]
        o3alt = o3alt[:]

        tropidx = support.variables['tropopause_index']  # [:]
        tropidx = tropidx[:]

        alb = support.variables['albedo']  # [:]
        alb = alb[:]

        o3ap = support.variables['ozone_apriori_profile']  # [:]
        o3ap = o3ap[:]

        o3aperr = support.variables['ozone_apriori_profile_error']  # [:]
        o3aperr = o3aperr[:]

        o3ak = support.variables['ozone_averaging_kernel']  # [:]
        o3ak = o3ak[:]

        o3noise = support.variables['ozone_noise_correlation_matrix']  # [:]
        o3noise = o3noise[:]

        o3info = support.variables['ozone_information_content']  # [:]
        o3info = o3info[:]

    # Cloud fraction
        #cldfra = np.ma.filled(cldfra,fill_value=1.0)
        #bad = np.where((cldfra > cldthresh))

        #var[bad] = np.nan
#        var[var < -9.] = np.nan

        #data_qc = (var*0.)
 #########################################

    ########### end quality control procedures ################
    ncfile.close()

    if iprod == 'NO2':
        return {'gas_trop':gas_trop,'qc':data_qc,'cf':cldfra,'long_name':long_name,\
                'gas_strat':gas_strat,'gas_tot':gas_tot,'gas_tropunc':gas_tropunc,\
                'sfcpres':sfcpres,'hgt':hgt,'snowice':snowice,'gas_slt':gas_slt,\
                'gas_sltunc':gas_sltunc,'alb':alb,'troppres':troppres,'cldpres':cldpres,\
                'amftrop':amftrop,'amfstrat':amfstrat, \
                'eta_a':eta_a, 'eta_b':eta_b,\
                'amftot':amftot,'long_name':long_name}
    if iprod == 'HCHO':
        return {'qc':data_qc,'cf':cldfra,'long_name':long_name,\
                'gas_tot':gas_tot,'gas_totunc':gas_totunc,\
                'sfcpres':sfcpres,'hgt':hgt,'snowice':snowice,'gas_slt':gas_slt,\
                'gas_sltunc':gas_sltunc,'alb':alb,'cldpres':cldpres,\
                'eta_a':eta_a, 'eta_b':eta_b,\
                'amftot':amftot}
    if iprod == 'O3PROF':
        return {'cf':cldfra,'gas_tot':gas_tot,\
                'alb':alb,'cldpres':cldpres,'o3pres':o3pres,\
                'o3aperr':o3aperr, 'o3ap':o3ap,'o3alt':o3alt,\
                'o3ak':o3ak, 'o3noise':o3noise, 'tropidx':tropidx, 'o3info':o3info, \
                'gas_strat':gas_strat,'gas_trop':gas_trop,'o3prof':o3prof,'long_name':long_name}

##################
def make_map(resmap):
    ### Basic map settings ###
    fig = plt.figure(figsize=(ximgsize, yimgsize))

    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([lllon, urlon, lllat, urlat], ccrs.PlateCarree())

    ax.coastlines(resolution=resmap, linewidth=linewidth)

    # Setting the background image
    ####ax.stock_img()

    # Create a feature for States/Admin 1 regions at 1:50m from Natural Earth
    states_provinces = cfeature.NaturalEarthFeature(category='cultural', edgecolor='black', \
                                                    name='admin_0_boundary_lines_land', scale=resmap, facecolor='none',
                                                    linewidth=linewidth / 1.5, linestyle='--')

    ax.add_feature(states_provinces, edgecolor='black')
    ax.add_feature(cfeature.STATES, edgecolor='black', linewidth=linewidth)

    lakes = cfeature.NaturalEarthFeature('physical', 'lakes', scale='110m', edgecolor='black', facecolor='none')
    ax.add_feature(lakes, linewidth=linewidth / 1.5)

    if drawcounty:
        COUNTIES = cfeature.ShapelyFeature(counties, ccrs.PlateCarree())
        ax.add_feature(COUNTIES, facecolor='none', edgecolor='black', linewidth=linewidth / 1.5)

    if maproad:
        roaddraw = cfeature.ShapelyFeature(roads, ccrs.PlateCarree())
        ax.add_feature(roaddraw, facecolor='none', edgecolor='black', linewidth=linewidth / 2)

    # Draw gridlines
    if mapgrid:
        gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                          linewidth=0.5, color='black', alpha=0.7, linestyle='--')

        gl.xlabels_top = False
        gl.xlabels_bottom = True
        gl.ylabels_left = True
        gl.ylabels_right = False
        gl.xlabel_style, gl.ylabel_style = {'fontsize': fontsize}, {'fontsize': fontsize}
        gl.xlocator = mticker.FixedLocator(lonticks)
        gl.ylocator = mticker.FixedLocator(latticks)
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER

    # prescribed burn Ft Stewart location
    # .plot(-81.8331, 32.0111, color='black', marker='o', markersize=50, markerfacecolor='none')
    # plt.plot(-81.5721, 31.8312, color='black', marker='o', markersize=10, fillstyle='full')

    plt.subplots_adjust(top=1.0, bottom=0.01, right=0.92, left=0.08)

    return {fig}

 ###########################
def get_cities():
    city_df = pd.read_csv(cityloc, sep = ',', encoding='latin1')
    city_df = city_df[city_df['CITY'].isin(citylist) & city_df['STATE_CODE'].isin(statelist)]
    #city_df = city_df[city_df['CITY'].isin(citylist)]

    cities = np.asarray(city_df['CITY'].tolist())
    state = np.asarray(city_df['STATE_CODE'].tolist())
    clats = np.asarray(city_df['LATITUDE'].tolist())
    clons = np.asarray(city_df['LONGITUDE'].tolist())

# Plot cities
    dum = 0
    for city in cities:
        ok = np.where(((clats[dum] > lllat+(urlat-lllat)/dbotleft) & (clats[dum] < urlat-(urlat-lllat)/dtopright)) \
          & ((clons[dum] > lllon+(urlon-lllon)/dbotleft) & (clons[dum] < urlon-(urlon-lllon)/dtopright)))
        if np.size(ok) == 0:
            dum = dum+1
            continue
        plt.plot(clons[dum],clats[dum],'ok', markersize=markersize,markerfacecolor='none')
        plt.text(clons[dum],clats[dum],city,fontsize=cfontsize,ha=horpos,va=vertpos)
        dum = dum+1

##############################
####################
# Cressman weighting function for pyresample
def wf(z_in):
    w    = np.zeros((z_in.shape))
    ww   = (interdis**2 - z_in**2) / (interdis**2 + z_in**2)
    mask = (np.abs(z_in) < interdis)
    w[mask] = ww[mask]
    return w
#####################
def remap(swath,fixed,inarg,valnum):
# Remap cloud and qc variables onto L3 grid
    out = kd_tree.resample_custom(swath,inarg, \
      fixed,radius_of_influence=interdis,reduce_data=True, \
      weight_funcs=wf,fill_value=np.nan,nprocs=1,neighbours=valnum)
    return out
def remap_gas(swath,fixed,inarg,valnum):
# Remap cloud and qc variables onto L3 grid
    out,weights,wcount = kd_tree.resample_custom(swath,inarg, \
      fixed,radius_of_influence=interdis,reduce_data=True, with_uncert= True, \
      weight_funcs=wf,fill_value=np.nan,nprocs=1,neighbours=valnum)
    return out,weights,wcount
#####################
def makencdf_op(savefile,var_for,qc_for, cf_for, sza_for, vza_for, raz_for, flats, flons, savegrans, \
  gasstrat_for, gastot_for, gastotunc_for, sfcpres_for, hgt_for, snowice_for, gasslt_for, gassltunc_for, alb_for, \
  troppres_for, cldpres_for, amftrop_for, amfstrat_for, var_cnt,var_min,var_max, strat_cnt, \
  strat_min, strat_max, tvertcol_for, tamf_for, talb_for, eta_a, eta_b, amf_for, amfunc_for, stime, etime, \
  estime, eetime, gas_name_long, forfiles, areawgt ):
    print ('SAVING DATA TO NETCDF FILE')
    print (savefile)

    splitfile = savefile.rsplit('/',1)
    getname = savefile.rsplit('/',1)
    getname = getname[1]
    # datetime object containing current date and time
    now = datetime.datetime.utcnow()
    # reformat date time
    now = str(now).replace(' ','T').split('.')
    now = now[0]
    # shortname
    splitname = getname.split('_'+tversion+'_')
    shortname = splitname[0]
    # get product type
    dum = shortname.split('_')
    gas_name = dum[1]
    # Get date of file only
    datename = splitname[1]
    # Reformat date string
    dum2 = savegrans[0].split('_')
    datestr = dum2[4]
    sfileYYYYMMDD = datestr.split('T')[0]
    sfileYYYYMMDD = sfileYYYYMMDD[:4]+'-'+sfileYYYYMMDD[4:6]+'-'+sfileYYYYMMDD[6:8]
    sfileHHMMSS = datestr.split('T')[1]
    sfileHHMMSS = sfileHHMMSS[:2]+':'+sfileHHMMSS[2:4]+':'+sfileHHMMSS[4:6]

    dum2 = savegrans[len(savegrans)-1].split('_')
    datestr = dum2[4]
    efileYYYYMMDD = datestr.split('T')[0]
    efileYYYYMMDD = efileYYYYMMDD[:4]+'-'+efileYYYYMMDD[4:6]+'-'+efileYYYYMMDD[6:8]
    efileHHMMSS = datestr.split('T')[1]
    efileHHMMSS = efileHHMMSS[:2]+':'+efileHHMMSS[2:4]+':'+efileHHMMSS[4:6]

    # add proxy in filename
    dum2 = savegrans[0].split('_')
    savefile = savefile.replace(shortname, dum[0]+'_'+dum[1]+'-PROXY'+'_'+dum[2])
    scan = int(dum2[5].split('.')[0][1:4])

    splitfile = savefile.rsplit('/', 1)
    fname = splitfile[1].split('.')

    dumfile = splitfile[0]+'/'+ fname[0] + '.' + fname[1] + '.met'

    # PVL text for metadata
    df = open(dumfile, 'w+')
    df.write('\n')
    df.write('GROUP                  = INVENTORYMETADATA \n')
    df.write('  GROUPTYPE            = MASTERGROUP \n')
    df.write('\n')
    df.write('  GROUP                  = ECSDATAGRANULE \n')
    df.write('\n')
    df.write('    OBJECT                 = LOCALGRANULEID \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = '+'"'+getname+'"'+'\n')
    df.write('    END_OBJECT             = LOCALGRANULEID \n')
    df.write('\n')
    df.write('    OBJECT                 = LOCALVERSIONID \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = '+'("RFC1321 MD5 = not yet calculated")'+'\n')
    df.write('    END_OBJECT             = LOCALVERSIONID \n')
    df.write('\n')
    df.write('    OBJECT                 = PRODUCTIONDATETIME \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = '+'"'+str(now)+'.000Z"'+'\n')
    df.write('    END_OBJECT             = PRODUCTIONDATETIME \n')
    df.write('\n')
    df.write('  END_GROUP              = ECSDATAGRANULE \n')
    df.write('\n')
    df.write('  GROUP                  = COLLECTIONDESCRIPTIONCLASS \n')
    df.write('\n')
    df.write('    OBJECT                 = SHORTNAME \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = '+'"'+shortname+'"'+'\n')
    df.write('    END_OBJECT             = SHORTNAME \n')
    df.write('\n')    
    df.write('    OBJECT                 = VERSIONID \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = 1 \n')
    df.write('    END_OBJECT             = VERSIONID \n')
    df.write('\n')    
    df.write('  END_GROUP              = COLLECTIONDESCRIPTIONCLASS \n')
    df.write('\n')
    df.write('  GROUP                  = INPUTGRANULE \n')
    df.write('\n')
    df.write('    OBJECT                 = INPUTPOINTER \n')
    df.write('      NUM_VAL              = '+str(len(savegrans))+' \n')
    df.write('      VALUE                = '+ '(' + forfiles + ')' +'\n')
    df.write('    END_OBJECT             = INPUTPOINTER \n')
    df.write('\n')    
    df.write('  END_GROUP              = INPUTGRANULE \n')
    df.write('\n')  
    df.write('  GROUP                  = SPATIALDOMAINCONTAINER \n')
    df.write('\n') 
    df.write('    GROUP                  = HORIZONTALSPATIALDOMAINCONTAINER \n')
    df.write('\n') 
    df.write('      GROUP                  = GPOLYGON \n')
    df.write('\n') 
    df.write('        GROUP                  = GPOLYGONCONTAINER \n')
    df.write('          CLASS                = "1" \n')
    df.write('\n') 
    df.write('          GROUP                  = GRINGPOINT \n')
    df.write('            CLASS                = "1" \n')   
    df.write('\n') 
    df.write('            OBJECT                 = GRINGPOINTLONGITUDE \n')
    df.write('              NUMVAL               = 4 \n')
    df.write('              CLASS                = "1" \n') 
    df.write('              VALUE                = (-155, -24.45, -24.45, -155) \n' )
    df.write('            END_OBJECT             = GRINGPOINTLONGITUDE \n') 
    df.write('\n')
    df.write('            OBJECT                 = GRINGPOINTLATITUDE \n')
    df.write('              NUMVAL               = 4 \n')
    df.write('              CLASS                = "1" \n')
    df.write('              VALUE                = (17, 17, 64, 64) \n' )
    df.write('            END_OBJECT             = GRINGPOINTLATITUDE \n')
    df.write('\n')
    df.write('            OBJECT                 = GRINGPOINTSEQUENCENO \n')
    df.write('              NUMVAL               = 4 \n')
    df.write('              CLASS                = "1" \n')
    df.write('              VALUE                = (1, 2, 3, 4) \n')
    df.write('            END_OBJECT             = GRINGPOINTSEQUENCENO \n')
    df.write('\n')
    df.write('          END_GROUP              = GRINGPOINT \n')
    df.write('\n')
    df.write('          GROUP                  = GRING \n')
    df.write('            CLASS                = "1" \n')
    df.write('\n')
    df.write('            OBJECT                 = EXCLUSIONGRINGFLAG \n')
    df.write('              NUM_VAL              = 1 \n')
    df.write('              VALUE                = "N" \n')
    df.write('              CLASS                = "1" \n')
    df.write('            END_OBJECT             = EXCLUSIONGRINGFLAG \n')
    df.write('\n')
    df.write('          END_GROUP              = GRING \n')
    df.write('\n')
    df.write('        END_GROUP              = GPOLYGONCONTAINER \n')
    df.write('\n')
    df.write('      END_GROUP              = GPOLYGON \n')
    df.write('\n')
    df.write('    END_GROUP              = HORIZONTALSPATIALDOMAINCONTAINER \n')
    df.write('\n')
    df.write('  END_GROUP              = SPATIALDOMAINCONTAINER \n')
    df.write('\n')
    df.write('  GROUP                  = RANGEDATETIME \n')
    df.write('\n')
    df.write('    OBJECT                 = RANGEENDINGDATE \n') 
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = "'+efileYYYYMMDD+'"' '\n')
    df.write('    END_OBJECT             = RANGEENDINGDATE \n')
    df.write('\n')
    df.write('    OBJECT                 = RANGEENDINGTIME \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = "'+efileHHMMSS+'"' '\n')
    df.write('    END_OBJECT             = RANGEENDINGTIME \n')
    df.write('\n')
    df.write('    OBJECT                 = RANGEBEGINNINGDATE \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = "'+sfileYYYYMMDD+'"' '\n')
    df.write('    END_OBJECT             = RANGEBEGINNINGDATE \n')
    df.write('\n')
    df.write('    OBJECT                 = RANGEBEGINNINGTIME \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = "'+sfileHHMMSS+'"' '\n')
    df.write('    END_OBJECT             = RANGEBEGINNINGTIME \n')
    df.write('\n')
    df.write('  END_GROUP              = RANGEDATETIME \n')
    df.write('\n')
    df.write('  GROUP                  = PGEVERSIONCLASS \n')
    df.write('\n')
    df.write('    OBJECT                 = PGEVERSION \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = "'+'0.1.0'+'"' '\n')
    df.write('    END_OBJECT             = PGEVERSION \n')
    df.write('\n')
    df.write('  END_GROUP              = PGEVERSIONCLASS \n')
    df.write('\n')
    df.write('END_GROUP              = INVENTORYMETADATA \n')
    df.write('\n')
    df.write('END')
    df.close()

    #dum = np.shape(tsctwgt_for)

    # Create dimensions
    nc_fid = Dataset( savefile, 'w', clobber=True)

    # Define groups
    grp_geo  = nc_fid.createGroup('geolocation')
    grp_prod = nc_fid.createGroup('product')
    grp_qa = nc_fid.createGroup('qa_statistics')
    grp_support = nc_fid.createGroup('support_data')

    nc_fid.createDimension('longitude', len(flons))
    nc_fid.createDimension('latitude', len(flats))
    nc_fid.createDimension('time', 1)

    #nc_fid.createDimension('swt_level', dum[2])

    # Latitude
    # --------
    var = nc_fid.createVariable('latitude',np.float32,('latitude'))
    var.setncattr_string('standard_name', 'latitude')
    var.setncattr_string('long_name','grid center latitude')
    var.setncattr_string('comment','latitude at grid center')
    var.setncattr_string('units','degrees_north')
    var.setncattr_string('valid_min',-90.0)
    var.setncattr('valid_max',90.0)

    # Write
    nc_fid.variables['latitude'][:] = flats[:]

    # Latitude
    # --------
    var = nc_fid.createVariable('longitude',np.float32,('longitude'))
    var.setncattr_string('standard_name', 'longitude')
    var.setncattr_string('long_name','grid center longitude')
    var.setncattr_string('comment','longitude at grid center')
    var.setncattr_string('units','degrees_east')
    var.setncattr_string('valid_min',-180.0)
    var.setncattr('valid_max',180.0)

    # Write
    nc_fid.variables['longitude'][:] = flons[:]

    # Area weights
    # --------
    var = nc_fid.createVariable('weight',np.float32,('latitude','longitude'),fill_value=9.96921e+36)
    var.setncattr_string('long_name','sum of area weights')
    var.setncattr_string('comment','sum of Level 2 pixel overlap areas')
    var.setncattr_string('units','km^2')
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    areawgt[np.isnan(areawgt)] = 9.96921e+36
    nc_fid.variables['weight'][:,:] = areawgt[:,:]

    # Time
    # --------
    var = nc_fid.createVariable('time',np.float64,('time'))
    var.setncattr_string('standard_name', 'time')
    var.setncattr_string('long_name','scan start time')
    var.setncattr_string('units','seconds since 2000-01-01T12:00:00Z')
    var.setncattr_string('calendar','gregorian')

    dum = np.float64(estime)
    # Write
    nc_fid.variables['time'] = dum


    if gas_name == 'NO2':
        # Vertical column troposphere
        # --------
        var = grp_prod.createVariable('vertical_column_troposphere',np.float64,('latitude','longitude'),fill_value=-1.0e30)
        var.setncattr_string('long_name','troposphere '+gas_name_long+' vertical column')
        var.setncattr_string('coordinates','time longitude latitude')
        var.setncattr_string('units','molec/cm^2')

        # Write
        var_for[np.isnan(var_for)] = -1.0e30
        grp_prod.variables['vertical_column_troposphere'][:,:] = var_for[:,:]

        # Vertical column stratosphere
        # --------
        var = grp_prod.createVariable('vertical_column_stratosphere', np.float64, ('latitude','longitude'), fill_value=-1.0e30)
        var.setncattr_string('long_name', 'stratosphere '+gas_name_long+' vertical column')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        gasstrat_for[np.isnan(gasstrat_for)] = -1.0e30
        grp_prod.variables['vertical_column_stratosphere'][:, :] = gasstrat_for[:, :]

        # Vertical column total
        # --------
        var = grp_prod.createVariable('vertical_column_total', np.float64, ('latitude','longitude'), fill_value=-1.0e30)
        var.setncattr_string('long_name', gas_name_long+' vertical column')
        var.setncattr_string('comment',  gas_name_long+' vertical column determined from fitted slant column and total AMF calculated from surface to top of atmosphere')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        gastot_for[np.isnan(gastot_for)] = -1.0e30
        grp_prod.variables['vertical_column_total'][:, :] = gastot_for[:, :]

        # Vertical column total  uncertainty
        # --------
        var = grp_prod.createVariable('vertical_column_total_uncertainty', np.float64, ('latitude','longitude'), fill_value=-1.0e30)
        var.setncattr_string('long_name', gas_name_long+' vertical column uncertainty')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        gastotunc_for[np.isnan(gastotunc_for)] = -1.0e30
        grp_prod.variables['vertical_column_total_uncertainty'][:, :] = gastotunc_for[:, :]

    if gas_name == 'HCHO':
        # Vertical column total
        # --------
        var = grp_prod.createVariable('vertical_column', np.float64, ('latitude', 'longitude'), fill_value=-1.0e30)
        var.setncattr_string('long_name', gas_name_long + ' vertical column')
        var.setncattr_string('comment',gas_name_long + ' vertical column determined from fitted slant column and total AMF calculated from surface to top of atmosphere')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        gastot_for[np.isnan(gastot_for)] = -1.0e30
        grp_prod.variables['vertical_column'][:, :] = gastot_for[:, :]

        # Vertical column total  uncertainty
        # --------
        var = grp_prod.createVariable('vertical_column_uncertainty', np.float64, ('latitude', 'longitude'), fill_value=-1.0e30)
        var.setncattr_string('long_name', gas_name_long + ' vertical column uncertainty')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        gastotunc_for[np.isnan(gastotunc_for)] = -1.0e30
        grp_prod.variables['vertical_column_uncertainty'][:, :] = gastotunc_for[:, :]

    # Vertical column total uncertainty
    # --------
    var = grp_prod.createVariable('main_data_quality_flag', np.int16, ('latitude','longitude'), fill_value=-1)
    var.setncattr_string('long_name', 'main data quality flag')
    var.setncattr_string('coordinates', 'time longitude latitude')
    var.setncattr('valid_min', np.int16(0))
    var.setncattr('valid_max', np.int16(2))
    var.setncattr_string('flag_meanings', 'normal suspicious bad')
    var.setncattr_string('flag_values', [0, 1, 2])

    # Write
    qc_for[np.isnan(qc_for)] = -1
    grp_prod.variables['main_data_quality_flag'][:, :] = qc_for[:, :]

    if gas_name == 'NO2':
        # Vertical column troposphere
        # --------
        var = grp_qa.createVariable('num_vertical_column_troposphere_samples', np.int32, ('latitude', 'longitude'),
          fill_value=-1)
        var.setncattr_string('comment', 'Number of Level 2 pixel values contributing to the area-weighted Level 3 pixel value')

        # Write
        var_cnt[np.isnan(var_cnt)] = -1
        grp_qa.variables['num_vertical_column_troposphere_samples'][:, :] = var_cnt[:, :]

        # --------
        var = grp_qa.createVariable('min_vertical_column_troposphere_sample', np.float64, ('latitude', 'longitude'),
          fill_value=-1.0e30)
        var.setncattr_string('comment', 'Smallest Level 2 pixel value contributing to the area-weighted Level 3 pixel value')
        var.setncattr_string('long_name', 'troposphere '+gas_name_long+' vertical column')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        var_min[np.isnan(var_min)] = -1.0e30
        grp_qa.variables['min_vertical_column_troposphere_sample'][:, :] = var_min[:, :]

        var = grp_qa.createVariable('max_vertical_column_troposphere_sample', np.float64, ('latitude', 'longitude'),
          fill_value=-1.0e30)
        var.setncattr_string('comment', 'Largest Level 2 pixel value contributing to the area-weighted Level 3 pixel value')
        var.setncattr_string('long_name', 'troposphere '+gas_name_long+' vertical column')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        var_max[np.isnan(var_max)] = -1.0e30
        grp_qa.variables['max_vertical_column_troposphere_sample'][:, :] = var_max[:, :]

        # Vertical column troposphere
        # --------
        var = grp_qa.createVariable('num_vertical_column_stratosphere_samples', np.int32, ('latitude', 'longitude'),
          fill_value=-1)
        var.setncattr_string('comment', 'Number of Level 2 pixel values contributing to the area-weighted Level 3 pixel value')

        # Write
        strat_cnt[np.isnan(strat_cnt)] = -1
        grp_qa.variables['num_vertical_column_stratosphere_samples'][:, :] = strat_cnt[:, :]

        # --------
        var = grp_qa.createVariable('min_vertical_column_stratosphere_sample', np.float64, ('latitude', 'longitude'),
          fill_value=-1.0e30)
        var.setncattr_string('comment', 'Smallest Level 2 pixel value contributing to the area-weighted Level 3 pixel value')
        var.setncattr_string('long_name', 'stratosphere '+gas_name_long+' vertical column')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        strat_min[np.isnan(strat_min)] = -1.0e30
        grp_qa.variables['min_vertical_column_stratosphere_sample'][:, :] = strat_min[:, :]

        var = grp_qa.createVariable('max_vertical_column_stratosphere_sample', np.float64, ('latitude', 'longitude'),
          fill_value=-1.0e30)
        var.setncattr_string('comment', 'Largest Level 2 pixel value contributing to the area-weighted Level 3 pixel value')
        var.setncattr_string('long_name', 'stratosphere '+gas_name_long+' vertical column')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        strat_max[np.isnan(strat_max)] = -1.0e30
        grp_qa.variables['max_vertical_column_stratosphere_sample'][:, :] = strat_max[:, :]

    if gas_name == 'HCHO':
        # Vertical column troposphere
        # --------
        var = grp_qa.createVariable('num_vertical_column_samples', np.int32, ('latitude', 'longitude'), fill_value=-1)
        var.setncattr_string('comment', 'Number of Level 2 pixel values contributing to the area-weighted Level 3 pixel value')

        # Write
        var_cnt[np.isnan(var_cnt)] = -1
        grp_qa.variables['num_vertical_column_samples'][:, :] = var_cnt[:, :]

        # --------
        var = grp_qa.createVariable('min_vertical_column_sample', np.float64, ('latitude', 'longitude'), fill_value=-1.0e30)
        var.setncattr_string('comment', 'Smallest Level 2 pixel value contributing to the area-weighted Level 3 pixel value')
        var.setncattr_string('long_name', gas_name_long+' vertical column')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        var_min[np.isnan(var_min)] = -1.0e30
        grp_qa.variables['min_vertical_column_sample'][:, :] = var_min[:, :]

        var = grp_qa.createVariable('max_vertical_column_sample', np.float64, ('latitude', 'longitude'), fill_value=-1.0e30)
        var.setncattr_string('comment', 'Largest Level 2 pixel value contributing to the area-weighted Level 3 pixel value')
        var.setncattr_string('long_name', gas_name_long+' vertical column')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        var_max[np.isnan(var_max)] = -1.0e30
        grp_qa.variables['max_vertical_column_sample'][:, :] = var_max[:, :]

    # solar zenith angle
    # --------
    var = grp_geo.createVariable('solar_zenith_angle', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
    var.setncattr_string('long_name', 'solar zenith angle at pixel center')
    var.setncattr_string('units', 'degrees')
    var.setncattr_string('valid_min',0.0)
    var.setncattr('valid_max',90.0)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    sza_for[np.isnan(sza_for)] = -1.0e30
    grp_geo.variables['solar_zenith_angle'][:, :] = sza_for[:, :]

    # viewing zenith angle
    # --------
    var = grp_geo.createVariable('viewing_zenith_angle', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
    var.setncattr_string('long_name', 'viewing zenith angle at pixel center')
    var.setncattr_string('units', 'degrees')
    var.setncattr_string('valid_min',0.0)
    var.setncattr('valid_max',90.0)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    vza_for[np.isnan(vza_for)] = -1.0e30
    grp_geo.variables['viewing_zenith_angle'][:, :] = vza_for[:, :]

    # relative azimuth angle
    # --------
    var = grp_geo.createVariable('relative_azimuth_angle', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
    var.setncattr_string('long_name', 'relative azimuth angle at pixel center')
    var.setncattr_string('units', 'degrees')
    var.setncattr_string('valid_min',-180.0)
    var.setncattr('valid_max',180.0)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    raz_for[np.isnan(raz_for)] = -1.0e30
    grp_geo.variables['relative_azimuth_angle'][:, :] = raz_for[:, :]

    # surface pressure
    # --------
    var = grp_support.createVariable('surface_pressure', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
    var.setncattr_string('long_name', 'surface pressure')
    var.setncattr_string('units', 'hPa')
    var.setncattr_string('valid_min',0.0)
    var.setncattr('valid_max',1030.0)
    var.setncattr_string('coordinates', 'time longitude latitude')
    var.setncattr('Eta_A', eta_a)
    var.setncattr('Eta_B', eta_b)

    # Write
    sfcpres_for[np.isnan(sfcpres_for)] = -1.0e30
    grp_support.variables['surface_pressure'][:, :] = sfcpres_for[:, :]

    # terrain height
    # --------
    var = grp_support.createVariable('terrain_height', np.int16, ('latitude','longitude'), fill_value=-30000)
    var.setncattr_string('long_name', 'terrain height')
    var.setncattr_string('units', 'm')
    var.setncattr_string('valid_min',-1000)
    var.setncattr('valid_max',10000)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    hgt_for = np.round(hgt_for)
    hgt_for[np.isnan(hgt_for)] = -30000
    grp_support.variables['terrain_height'][:, :] = hgt_for[:, :]

    # terrain height
    # --------
    var = grp_support.createVariable('snow_ice_fraction', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
    var.setncattr_string('long_name', 'Fraction of pixel area covered by snow and/or ice')
    var.setncattr_string('valid_min',0.)
    var.setncattr('valid_max',1.)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    snowice_for[np.isnan(snowice_for)] = -1.0e30
    grp_support.variables['snow_ice_fraction'][:, :] = snowice_for[:, :]

    # fitted slant column
    # --------
    var = grp_support.createVariable('fitted_slant_column', np.float64, ('latitude','longitude'), fill_value=-1.0e30)
    var.setncattr_string('long_name', gas_name_long+' fitted slant column')
    var.setncattr_string('coordinates', 'time longitude latitude')
    var.setncattr_string('units', 'molec/cm^2')

    # Write
    gasslt_for[np.isnan(gasslt_for)] = -1.0e30
    grp_support.variables['fitted_slant_column'][:, :] = gasslt_for[:, :]

    # fitted slant column
    # --------
    var = grp_support.createVariable('fitted_slant_column_uncertainty', np.float64, ('latitude','longitude'), fill_value=-1.0e30)
    var.setncattr_string('long_name', gas_name_long+' fitted slant column uncertainty')
    var.setncattr_string('coordinates', 'time longitude latitude')
    var.setncattr_string('units', 'molec/cm^2')

    # Write
    gassltunc_for[np.isnan(gassltunc_for)] = -1.0e30
    grp_support.variables['fitted_slant_column_uncertainty'][:, :] = gassltunc_for[:, :]

    # albedo
    # --------
    var = grp_support.createVariable('albedo', np.float32, ('latitude','longitude'), fill_value=0.)
    var.setncattr_string('long_name', 'surface albedo')
    var.setncattr_string('valid_min',0.)
    var.setncattr('valid_max',1.)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    alb_for[np.isnan(alb_for)] = 0.
    grp_support.variables['albedo'][:, :] = alb_for[:, :]

    # amf total
    # --------
    var = grp_support.createVariable('amf_total', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
    var.setncattr_string('long_name', gas_name_long+' air mass factor')
    var.setncattr_string('comment', 'total '+gas_name_long+' air mass factor (AMF) calculated from surface to top of atmosphere')
    var.setncattr_string('valid_min',0.)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    amf_for[np.isnan(amf_for)] = -1.0e30
    grp_support.variables['amf_total'][:, :] = amf_for[:, :]

    # amf total uncertainty
    # --------
    var = grp_support.createVariable('amf_total_uncertainty', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
    var.setncattr_string('long_name', gas_name_long+' air mass factor uncertainty')
    var.setncattr_string('valid_min',0.)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    amfunc_for[np.isnan(amfunc_for)] = -1.0e30
    grp_support.variables['amf_total_uncertainty'][:, :] = amfunc_for[:, :]

    # amf cloud fraction
    # --------
    var = grp_support.createVariable('amf_cloud_fraction', np.float32, ('latitude','longitude'), fill_value=-1.0)
    var.setncattr_string('long_name', 'cloud fraction')
    var.setncattr_string('comment', 'cloud radiance fraction for AMF computation')
    var.setncattr_string('valid_min',0.)
    var.setncattr_string('valid_max', 1.)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    cf_for[np.isnan(cf_for)] = -1.0e30
    grp_support.variables['amf_cloud_fraction'][:, :] = cf_for[:, :]

    # amf cloud fraction
    # --------
    var = grp_support.createVariable('amf_cloud_pressure', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
    var.setncattr_string('long_name', 'cloud pressure')
    var.setncattr_string('comment', 'cloud pressure for AMF computation')
    var.setncattr_string('units', 'hPa')
    var.setncattr_string('valid_min',0.)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    cldpres_for[np.isnan(cldpres_for)] = -1.0e30
    grp_support.variables['amf_cloud_pressure'][:, :] = cldpres_for[:, :]

    if gas_name == 'NO2':
        # tropopause pressure
        # --------
        var = grp_support.createVariable('tropopause_pressure', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
        var.setncattr_string('long_name', 'tropopause pressure')
        var.setncattr_string('units', 'hPa')
        var.setncattr_string('valid_min',0.)
        var.setncattr('valid_max',1030.)
        var.setncattr_string('coordinates', 'time longitude latitude')

        # Write
        troppres_for[np.isnan(troppres_for)] = -1.0e30
        grp_support.variables['tropopause_pressure'][:, :] = troppres_for[:, :]

        # amf troposphere
        # --------
        var = grp_support.createVariable('amf_troposphere', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
        var.setncattr_string('long_name', gas_name_long+' tropospheric air mass factor')
        var.setncattr_string('valid_min',0.)
        var.setncattr_string('coordinates', 'time longitude latitude')

        # Write
        amftrop_for[np.isnan(amftrop_for)] = -1.0e30
        grp_support.variables['amf_troposphere'][:, :] = amftrop_for[:, :]

        # amf stratosphere
        # --------
        var = grp_support.createVariable('amf_stratosphere', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
        var.setncattr_string('long_name', gas_name_long+' stratospheric air mass factor')
        var.setncattr_string('valid_min',0.)
        var.setncattr_string('coordinates', 'time longitude latitude')

        # Write
        amfstrat_for[np.isnan(amfstrat_for)] = -1.0e30
        grp_support.variables['amf_stratosphere'][:, :] = amfstrat_for[:, :]

    # amf total
    # --------
    var = grp_true.createVariable('amf_total', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
    var.setncattr_string('long_name', gas_name_long+' air mass factor')
    var.setncattr_string('comment', 'total '+gas_name_long+' air mass factor (AMF) calculated from mocel truth')
    var.setncattr_string('valid_min',0.)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    tamf_for[np.isnan(tamf_for)] = -1.0e30
    grp_true.variables['amf_total'][:, :] = tamf_for[:, :]

    if gas_name == 'NO2':
        # vertical column total
        # --------
        var = grp_true.createVariable('vertical_column_total', np.float32, ('latitude','longitude'), fill_value=-1.0e30)
        var.setncattr_string('long_name', gas_name_long+' vertical column')
        var.setncattr_string('comment', gas_name_long+' vertical column from model truth')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        tvertcol_for[np.isnan(tvertcol_for)] = -1.0e30
        grp_true.variables['vertical_column_total'][:, :] = tvertcol_for[:, :]

        print("check after line 2536")

    if gas_name == 'HCHO':
        # vertical column total
        # --------
        var = grp_true.createVariable('vertical_column', np.float32, ('latitude', 'longitude'), fill_value=-1.0e30)
        var.setncattr_string('long_name', gas_name_long + ' vertical column')
        var.setncattr_string('comment', gas_name_long + ' vertical column from model truth')
        var.setncattr_string('coordinates', 'time longitude latitude')
        var.setncattr_string('units', 'molec/cm^2')

        # Write
        tvertcol_for[np.isnan(tvertcol_for)] = -1.0e30
        grp_true.variables['vertical_column'][:, :] = tvertcol_for[:, :]

    # scattering weights
    # --------
    #var = grp_true.createVariable('scattering_weights', np.float32, ('latitude','longitude','swt_level'))
    #var.setncattr_string('long_name', 'scattering weights')
    #var.setncattr_string('comment', 'vertical profile of scattering weights calculated from model truth')
    #var.setncattr_string('coordinates', 'longitude latitude')
    #var.setncattr_string('valid_min', 0.)

    # Write
    #    var[np.isnan(var)] = -1.0e30
    #tsctwgt_for = np.transpose(tsctwgt_for,(2, 0, 1))
    #grp_true.variables['scattering_weights'][:, :, :] = tsctwgt_for[:, :, :]

    # gas profile
    # --------
    #var = grp_true.createVariable('gas_profile', np.float32, ('latitude','longitude','swt_level'))
    #var.setncattr_string('long_name', 'vertical profile of nitrogen dioxide from model truth')
    #var.setncattr_string('coordinates', 'longitude latitude')
    #var.setncattr_string('units', 'molec/cm^2')
    #var.setncattr_string('valid_min', 0.)

    # Write
    #    var[np.isnan(var)] = -1.0e30
    #grp_true.variables['gas_profile'][:, :, :] = tgas_for[:, :, :]

    # albedo
    # --------
    var = grp_true.createVariable('albedo', np.float32, ('latitude','longitude'))
    var.setncattr_string('long_name', 'surface albedo from model truth')
    var.setncattr_string('valid_min',0.)
    var.setncattr('valid_max',1.)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    talb_for[np.isnan(talb_for)] = -1.0e30
    grp_true.variables['albedo'][:, :] = talb_for[:, :]

    # =================================================================================
    # Global attributes
    # =================================================================================
    # Start date
    grandum = savegrans[0].split('_')[4]
    year, month, day = grandum[:4], grandum[4:6], grandum[6:8]

    dateYYYYMMDD = str(year) + str(month).zfill(2) + str(day).zfill(2)
    sformatdate = str(year) + '-' + str(month).zfill(2) + '-' + str(day).zfill(2)
    startdate = sformatdate + 'T' + stime[:2] + ':' + stime[2:4] + ':' + '00' + 'Z'

    # End date
    grandum = savegrans[len(savegrans)-1].split('_')[4]
    year, month, day = grandum[:4], grandum[4:6], grandum[6:8]
    eformatdate = str(year) + '-' + str(month).zfill(2) + '-' + str(day).zfill(2)
    enddate = eformatdate + 'T' + etime[:2] + ':' + etime[2:4] + ':' + '00' + 'Z'

    getname = savefile.rsplit('/',1)
    getname = getname[1]

    nc_fid.product_type = gas_name + " proxy"
    nc_fid.processing_level = "3"
    nc_fid.processing_version = "1"
    nc_fid.scan_num = str(scan)
    nc_fid.time_coverage_start = startdate
    nc_fid.time_coverage_end = enddate
    nc_fid.time_coverage_start_since_epoch = estime
    nc_fid.time_coverage_end_since_epoch = eetime
    nc_fid.collection_shortname = shortname
    nc_fid.input_files = forfiles
    nc_fid.geospatial_bounds = "POLYGON((17.0000 -155.0000,17.0000 -24.4500,64.0000 -24.4500,64.0000 -155.0000))"
    nc_fid.time_reference = '2000-01-01T12:00:00Z'
    nc_fid.geospatial_bounds_crs = 'EPSG:4326'
    nc_fid.geospatial_lon_min = np.float32(np.nanmin(flons))
    nc_fid.geospatial_lon_max = np.float32(np.nanmax(flons))
    nc_fid.geospatial_lat_min = np.float32(np.nanmin(flats))
    nc_fid.geospatial_lat_max = np.float32(np.nanmax(flats))
    nc_fid.local_granule_id = getname
    nc_fid.version_id = 1
    nc_fid.day_of_year = np.long(datetime.datetime.strptime(dateYYYYMMDD, "%Y%m%d").timetuple().tm_yday)
    nc_fid.project = 'TEMPO'
    nc_fid.platform = 'Intelsat 40e'
    nc_fid.source = 'UV-VIS hyperspectral imaging'
    nc_fid.institution = 'Short-term Prediction Research and Transition Center'
    nc_fid.creator_url = 'https://weather.msfc.nasa.gov/sport/'
    nc_fid.access_description = 'Pre-launch proxy data intended for TEMPO early adopters, not for scientific research. Data production url, https://weather.msfc.nasa.gov/sport/'
    nc_fid.access_value = np.long(0)
    nc_fid.Conventions = 'CF-1.8'
    nc_fid.title = 'TEMPO Level 3 ' + gas_name_long + ' product'
    nc_fid.collection_version = np.long(1)
    nc_fid.summary = gas_name_long.capitalize()+' Level 3 files provide trace gas information on a regular grid covering the TEMPO Field of Regard for TEMPO observations. Level 3 files are derived by combining information from all Level 2 files constituting a TEMPO East-West scan cycle. The files are provided in netCDF4 format, and contain information on tropospheric, stratospheric and total '+gas_name_long+' vertical columns, and ancillary data including product quality flags. The re-gridding algorithm uses an area-weighted approach.'

    # Open metadata file
    opendum = open(dumfile, "r+")
    readcont = opendum.read()

    nc_fid.coremetadata = str(readcont)

    # Close file
    nc_fid.close()

    ###### arn - add section to compress files
    outfile2 = splitfile[0] + '/' + fname[0].upper() + '_dum.' + fname[1]

    command = "nccopy -d9 -s " + savefile + " " + outfile2
    call(command, shell=True)

    command = "rm " + savefile
    call(command, shell=True)

    command = "mv " + outfile2 + " " + savefile
    call(command, shell=True)

    print("check after line 2659")

#############################################
#############################################
#############################################
def makencdf_o3(savefile, cf_for, sza_for, vza_for, raz_for, flats, flons, savegrans, \
  gasstrat_for, gastot_for, gastrop_for, o3prof_for, alb_for, \
  cldpres_for, var_cnt,var_min,var_max, \
  stime, etime, estime, eetime, gas_name_long, forfiles, areawgt, \
  tropidx_for, o3info_for, o3ap_for, o3aperr_for, o3pres_for, o3alt_for):

    print ('SAVING DATA TO NETCDF FILE')
    print (savefile)

    splitfile = savefile.rsplit('/',1)
    getname = savefile.rsplit('/',1)
    getname = getname[1]
    # datetime object containing current date and time
    now = datetime.datetime.utcnow()
    # reformat date time
    now = str(now).replace(' ','T').split('.')
    now = now[0]
    # shortname
    splitname = getname.split('_'+tversion+'_')
    shortname = splitname[0]
    # get product type
    dum = shortname.split('_')
    gas_name = dum[1]
    # Get date of file only
    datename = splitname[1]
    # Reformat date string
    dum2 = savegrans[0].split('_')
    datestr = dum2[4]
    sfileYYYYMMDD = datestr.split('T')[0]
    sfileYYYYMMDD = sfileYYYYMMDD[:4]+'-'+sfileYYYYMMDD[4:6]+'-'+sfileYYYYMMDD[6:8]
    sfileHHMMSS = datestr.split('T')[1]
    sfileHHMMSS = sfileHHMMSS[:2]+':'+sfileHHMMSS[2:4]+':'+sfileHHMMSS[4:6]

    dum2 = savegrans[len(savegrans)-1].split('_')
    datestr = dum2[4]
    efileYYYYMMDD = datestr.split('T')[0]
    efileYYYYMMDD = efileYYYYMMDD[:4]+'-'+efileYYYYMMDD[4:6]+'-'+efileYYYYMMDD[6:8]
    efileHHMMSS = datestr.split('T')[1]
    efileHHMMSS = efileHHMMSS[:2]+':'+efileHHMMSS[2:4]+':'+efileHHMMSS[4:6]

    # add proxy in filename
    dum2 = savegrans[0].split('_')
    savefile = savefile.replace(shortname, dum[0]+'_'+dum[1]+'-PROXY'+'_'+dum[2])
    scan = int(dum2[5].split('.')[0][1:4])

    splitfile = savefile.rsplit('/', 1)
    fname = splitfile[1].split('.')

    dumfile = splitfile[0]+'/'+ fname[0] + '.' + fname[1] + '.met'

    # PVL text for metadata
    df = open(dumfile, 'w+')
    df.write('\n')
    df.write('GROUP                  = INVENTORYMETADATA \n')
    df.write('  GROUPTYPE            = MASTERGROUP \n')
    df.write('\n')
    df.write('  GROUP                  = ECSDATAGRANULE \n')
    df.write('\n')
    df.write('    OBJECT                 = LOCALGRANULEID \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = '+'"'+getname+'"'+'\n')
    df.write('    END_OBJECT             = LOCALGRANULEID \n')
    df.write('\n')
    df.write('    OBJECT                 = LOCALVERSIONID \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = '+'("RFC1321 MD5 = not yet calculated")'+'\n')
    df.write('    END_OBJECT             = LOCALVERSIONID \n')
    df.write('\n')
    df.write('    OBJECT                 = PRODUCTIONDATETIME \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = '+'"'+str(now)+'.000Z"'+'\n')
    df.write('    END_OBJECT             = PRODUCTIONDATETIME \n')
    df.write('\n')
    df.write('  END_GROUP              = ECSDATAGRANULE \n')
    df.write('\n')
    df.write('  GROUP                  = COLLECTIONDESCRIPTIONCLASS \n')
    df.write('\n')
    df.write('    OBJECT                 = SHORTNAME \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = '+'"'+shortname+'"'+'\n')
    df.write('    END_OBJECT             = SHORTNAME \n')
    df.write('\n')
    df.write('    OBJECT                 = VERSIONID \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = 1 \n')
    df.write('    END_OBJECT             = VERSIONID \n')
    df.write('\n')
    df.write('  END_GROUP              = COLLECTIONDESCRIPTIONCLASS \n')
    df.write('\n')
    df.write('  GROUP                  = INPUTGRANULE \n')
    df.write('\n')
    df.write('    OBJECT                 = INPUTPOINTER \n')
    df.write('      NUM_VAL              = '+str(len(savegrans))+' \n')
    df.write('      VALUE                = '+ '(' + forfiles + ')' +'\n')
    df.write('    END_OBJECT             = INPUTPOINTER \n')
    df.write('\n')
    df.write('  END_GROUP              = INPUTGRANULE \n')
    df.write('\n')
    df.write('  GROUP                  = SPATIALDOMAINCONTAINER \n')
    df.write('\n')
    df.write('    GROUP                  = HORIZONTALSPATIALDOMAINCONTAINER \n')
    df.write('\n')
    df.write('      GROUP                  = GPOLYGON \n')
    df.write('\n')
    df.write('        GROUP                  = GPOLYGONCONTAINER \n')
    df.write('          CLASS                = "1" \n')
    df.write('\n')
    df.write('          GROUP                  = GRINGPOINT \n')
    df.write('            CLASS                = "1" \n')
    df.write('\n')
    df.write('            OBJECT                 = GRINGPOINTLONGITUDE \n')
    df.write('              NUMVAL               = 4 \n')
    df.write('              CLASS                = "1" \n')
    df.write('              VALUE                = (-155, -24.45, -24.45, -155) \n' )
    df.write('            END_OBJECT             = GRINGPOINTLONGITUDE \n')
    df.write('\n')
    df.write('            OBJECT                 = GRINGPOINTLATITUDE \n')
    df.write('              NUMVAL               = 4 \n')
    df.write('              CLASS                = "1" \n')
    df.write('              VALUE                = (17, 17, 64, 64) \n' )
    df.write('            END_OBJECT             = GRINGPOINTLATITUDE \n')
    df.write('\n')
    df.write('            OBJECT                 = GRINGPOINTSEQUENCENO \n')
    df.write('              NUMVAL               = 4 \n')
    df.write('              CLASS                = "1" \n')
    df.write('              VALUE                = (1, 2, 3, 4) \n')
    df.write('            END_OBJECT             = GRINGPOINTSEQUENCENO \n')
    df.write('\n')
    df.write('          END_GROUP              = GRINGPOINT \n')
    df.write('\n')
    df.write('          GROUP                  = GRING \n')
    df.write('            CLASS                = "1" \n')
    df.write('\n')
    df.write('            OBJECT                 = EXCLUSIONGRINGFLAG \n')
    df.write('              NUM_VAL              = 1 \n')
    df.write('              VALUE                = "N" \n')
    df.write('              CLASS                = "1" \n')
    df.write('            END_OBJECT             = EXCLUSIONGRINGFLAG \n')
    df.write('\n')
    df.write('          END_GROUP              = GRING \n')
    df.write('\n')
    df.write('        END_GROUP              = GPOLYGONCONTAINER \n')
    df.write('\n')
    df.write('      END_GROUP              = GPOLYGON \n')
    df.write('\n')
    df.write('    END_GROUP              = HORIZONTALSPATIALDOMAINCONTAINER \n')
    df.write('\n')
    df.write('  END_GROUP              = SPATIALDOMAINCONTAINER \n')
    df.write('\n')
    df.write('  GROUP                  = RANGEDATETIME \n')
    df.write('\n')
    df.write('    OBJECT                 = RANGEENDINGDATE \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = "'+efileYYYYMMDD+'"' '\n')
    df.write('    END_OBJECT             = RANGEENDINGDATE \n')
    df.write('\n')
    df.write('    OBJECT                 = RANGEENDINGTIME \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = "'+efileHHMMSS+'"' '\n')
    df.write('    END_OBJECT             = RANGEENDINGTIME \n')
    df.write('\n')
    df.write('    OBJECT                 = RANGEBEGINNINGDATE \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = "'+sfileYYYYMMDD+'"' '\n')
    df.write('    END_OBJECT             = RANGEBEGINNINGDATE \n')
    df.write('\n')
    df.write('    OBJECT                 = RANGEBEGINNINGTIME \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = "'+sfileHHMMSS+'"' '\n')
    df.write('    END_OBJECT             = RANGEBEGINNINGTIME \n')
    df.write('\n')
    df.write('  END_GROUP              = RANGEDATETIME \n')
    df.write('\n')
    df.write('  GROUP                  = PGEVERSIONCLASS \n')
    df.write('\n')
    df.write('    OBJECT                 = PGEVERSION \n')
    df.write('      NUM_VAL              = 1 \n')
    df.write('      VALUE                = "'+'0.1.0'+'"' '\n')
    df.write('    END_OBJECT             = PGEVERSION \n')
    df.write('\n')
    df.write('  END_GROUP              = PGEVERSIONCLASS \n')
    df.write('\n')
    df.write('END_GROUP              = INVENTORYMETADATA \n')
    df.write('\n')
    df.write('END')
    df.close()

    #dum = np.shape(tsctwgt_for)

    # Create dimensions
    nc_fid = Dataset( savefile, 'w', clobber=True)

    # Define groups
    grp_geo  = nc_fid.createGroup('geolocation')
    grp_prod = nc_fid.createGroup('product')
    grp_qa = nc_fid.createGroup('qa_statistics')
    grp_support = nc_fid.createGroup('support_data')

    nc_fid.createDimension('longitude', len(flons))
    nc_fid.createDimension('latitude', len(flats))
    nc_fid.createDimension('time', 1)
    nc_fid.createDimension('layer', 24)
    nc_fid.createDimension('level', 2)

    #nc_fid.createDimension('swt_level', dum[2])

    # Latitude
    # --------
    var = nc_fid.createVariable('latitude',np.float32,('latitude'))
    var.setncattr_string('standard_name', 'latitude')
    var.setncattr_string('long_name','grid center latitude')
    var.setncattr_string('comment','latitude at grid center')
    var.setncattr_string('units','degrees_north')
    var.setncattr_string('valid_min',-90.0)
    var.setncattr('valid_max',90.0)

    # Write
    nc_fid.variables['latitude'][:] = flats[:]

    # Latitude
    # --------
    var = nc_fid.createVariable('longitude',np.float32,('longitude'))
    var.setncattr_string('standard_name', 'longitude')
    var.setncattr_string('long_name','grid center longitude')
    var.setncattr_string('comment','longitude at grid center')
    var.setncattr_string('units','degrees_east')
    var.setncattr_string('valid_min',-180.0)
    var.setncattr('valid_max',180.0)

    # Write
    nc_fid.variables['longitude'][:] = flons[:]

    # Area weights
    # --------
    var = nc_fid.createVariable('weight',np.float32,('latitude','longitude'),fill_value=9.96921e+36)
    var.setncattr_string('long_name','sum of area weights')
    var.setncattr_string('comment','sum of Level 2 pixel overlap areas')
    var.setncattr_string('units','km^2')
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    areawgt[np.isnan(areawgt)] = 9.96921e+36
    nc_fid.variables['weight'][:,:] = areawgt[:,:]

    # Time
    # --------
    var = nc_fid.createVariable('time',np.float64,('time'))
    var.setncattr_string('standard_name', 'time')
    var.setncattr_string('long_name','scan start time')
    var.setncattr_string('units','seconds since 2000-01-01T12:00:00Z')
    var.setncattr_string('calendar','gregorian')

    dum = np.float64(estime)
    # Write
    nc_fid.variables['time'] = dum

    # Ozone profile
    # --------
    var = grp_prod.createVariable('ozone_profile',np.float32,('latitude','longitude','layer'),fill_value=-1.267651e30)
    var.setncattr_string('comment', 'retrieved ozone profile')
    var.setncattr_string('units', 'DU')
    var.setncattr('valid_min', np.float(-100))
    var.setncattr('valid_max', np.float(100))
    var.setncattr_string('coordinates','time longitude latitude ozone_profile_pressure ozone_profile_altitude')

    # Write
    o3prof_for[np.isnan(o3prof_for)] = -1.267651e30
    grp_prod.variables['ozone_profile'][:,:,:] = o3prof_for[:,:,:]

    # Total ozone column
    # --------
    var = grp_prod.createVariable('total_ozone_column', np.float32, ('latitude', 'longitude'),fill_value=-1.267651e30)
    var.setncattr_string('comment', 'total ozone column')
    var.setncattr_string('units', 'DU')
    var.setncattr('valid_min', np.float(0))
    var.setncattr('valid_max', np.float(600))
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    gastot_for[np.isnan(gastot_for)] = -1.267651e30
    grp_prod.variables['total_ozone_column'][:, :] = gastot_for[:, :]

    # Stratosphere ozone column
    # --------
    var = grp_prod.createVariable('stratosphere_ozone_column', np.float32, ('latitude', 'longitude'),fill_value=-1.267651e30)
    var.setncattr_string('comment', 'stratospheric ozone column')
    var.setncattr_string('units', 'DU')
    var.setncattr('valid_min', np.float(0))
    var.setncattr('valid_max', np.float(600))
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    gasstrat_for[np.isnan(gasstrat_for)] = -1.267651e30
    grp_prod.variables['stratosphere_ozone_column'][:, :] = gasstrat_for[:, :]

    # Troposphere ozone column
    # --------
    var = grp_prod.createVariable('troposphere_ozone_column', np.float32, ('latitude', 'longitude'),fill_value=-1.267651e30)
    var.setncattr_string('comment', 'tropospheric ozone column')
    var.setncattr_string('units', 'DU')
    var.setncattr('valid_min', np.float(0))
    var.setncattr('valid_max', np.float(100))
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    gastrop_for[np.isnan(gastrop_for)] = -1.267651e30
    grp_prod.variables['troposphere_ozone_column'][:, :] = gastrop_for[:, :]

    # solar zenith angle
    # --------
    var = grp_geo.createVariable('solar_zenith_angle', np.float32, ('latitude','longitude'), fill_value=-1.267651e30)
    var.setncattr_string('long_name', 'solar zenith angle at pixel center')
    var.setncattr_string('units', 'degrees')
    var.setncattr_string('valid_min',0.0)
    var.setncattr('valid_max',90.0)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    sza_for[np.isnan(sza_for)] = -1.267651e30
    grp_geo.variables['solar_zenith_angle'][:, :] = sza_for[:, :]

    # viewing zenith angle
    # --------
    var = grp_geo.createVariable('viewing_zenith_angle', np.float32, ('latitude','longitude'), fill_value=-1.267651e30)
    var.setncattr_string('long_name', 'viewing zenith angle at pixel center')
    var.setncattr_string('units', 'degrees')
    var.setncattr_string('valid_min',0.0)
    var.setncattr('valid_max',90.0)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    vza_for[np.isnan(vza_for)] = -1.267651e30
    grp_geo.variables['viewing_zenith_angle'][:, :] = vza_for[:, :]

    # relative azimuth angle
    # --------
    var = grp_geo.createVariable('relative_azimuth_angle', np.float32, ('latitude','longitude'), fill_value=-1.267651e30)
    var.setncattr_string('long_name', 'relative azimuth angle at pixel center')
    var.setncattr_string('units', 'degrees')
    var.setncattr_string('valid_min',-180.0)
    var.setncattr('valid_max',180.0)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    raz_for[np.isnan(raz_for)] = -1.267651e30
    grp_geo.variables['relative_azimuth_angle'][:, :] = raz_for[:, :]

    # eff cloud fraction
    # --------
    var = grp_support.createVariable('eff_cloud_fraction', np.float32, ('latitude','longitude'), fill_value=-1.267651e30)
    var.setncattr_string('comment', 'effective cloud fraction')
    var.setncattr_string('valid_min',0.)
    var.setncattr_string('valid_max', 1.)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    cf_for[np.isnan(cf_for)] = -1.267651e30
    grp_support.variables['eff_cloud_fraction'][:, :] = cf_for[:, :]

    # eff cloud pressure
    # --------
    var = grp_support.createVariable('eff_cloud_pressure', np.float32, ('latitude','longitude'), fill_value=-1.267651e30)
    var.setncattr_string('comment', 'effective cloud pressure')
    var.setncattr_string('units', 'hPa')
    var.setncattr_string('valid_min',0.)
    var.setncattr_string('valid_max', 1100.)
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    cldpres_for[np.isnan(cldpres_for)] = -1.267651e30
    grp_support.variables['eff_cloud_pressure'][:, :] = cldpres_for[:, :]

    # ozone apriori
    # --------
    var = grp_support.createVariable('ozone_apriori_profile', np.float32, ('latitude','longitude','layer'), fill_value=-1.267651e30)
    var.setncattr_string('comment', 'a priori ozone profile')
    var.setncattr_string('units', 'DU')
    var.setncattr_string('valid_min',np.float(0))
    var.setncattr_string('valid_max', np.float(100))
    var.setncattr_string('coordinates', 'time longitude latitude ozone_profile_pressure ozone_profile_altitude')

    # Write
    o3ap_for[np.isnan(o3ap_for)] = -1.267651e30
    grp_support.variables['ozone_apriori_profile'][:, :, :] = o3ap_for[:, :, :]

    # ozone apriori error
    # --------
    var = grp_support.createVariable('ozone_apriori_profile_error', np.float32, ('latitude','longitude','layer'), fill_value=-1.267651e30)
    var.setncattr_string('comment', 'a priori ozone profile error')
    var.setncattr_string('units', 'DU')
    var.setncattr_string('valid_min',np.float(0))
    var.setncattr_string('valid_max', np.float(100))
    var.setncattr_string('coordinates', 'time longitude latitude ozone_profile_pressure ozone_profile_altitude')

    # Write
    o3aperr_for[np.isnan(o3aperr_for)] = -1.267651e30
    grp_support.variables['ozone_apriori_profile_error'][:, :, :] = o3aperr_for[:, :, :]

    # ozone profile altitude
    # --------
    var = grp_support.createVariable('ozone_profile_altitude', np.float32, ('latitude','longitude','layer'), fill_value=-1.267651e30)
    var.setncattr_string('comment', 'altitude of each retrieval layer')
    var.setncattr_string('units', 'km')
    var.setncattr_string('valid_min',np.float(0))
    var.setncattr_string('valid_max', np.float(100))
    var.setncattr_string('coordinates', 'time longitude latitude ozone_profile_pressure ozone_profile_altitude')

    # Write
    o3alt_for[np.isnan(o3alt_for)] = -1.267651e30
    grp_support.variables['ozone_profile_altitude'][:, :, :] = o3alt_for[:, :, :]

    # ozone profile pressure
    # --------
    var = grp_support.createVariable('ozone_profile_pressure', np.float32, ('latitude','longitude','layer'), fill_value=-1.267651e30)
    var.setncattr_string('comment', 'pressure of each retrieval layer')
    var.setncattr_string('units', 'hPa')
    var.setncattr_string('valid_min',np.float(0))
    var.setncattr_string('valid_max', np.float(1100))
    var.setncattr_string('coordinates', 'time longitude latitude ozone_profile_pressure ozone_profile_altitude')

    # Write
    o3pres_for[np.isnan(o3pres_for)] = -1.267651e30
    grp_support.variables['ozone_profile_pressure'][:, :, :] = o3pres_for[:, :, :]

    # tropopause index
    # --------
    var = grp_support.createVariable('tropopause_index', np.int16, ('latitude','longitude'), fill_value=-32767)
    var.setncattr_string('comment', 'tropopause index')
    var.setncattr('valid_min', np.int16(0))
    var.setncattr('valid_max', np.int16(100))
    var.setncattr_string('coordinates', 'time longitude latitude')

    # Write
    tropidx_for[np.isnan(tropidx_for)] = -32767
    grp_support.variables['tropopause_index'][:, :] = tropidx_for[:, :]

    # =================================================================================
    # Global attributes
    # =================================================================================
    # Start date
    grandum = savegrans[0].split('_')[4]
    year, month, day = grandum[:4], grandum[4:6], grandum[6:8]

    dateYYYYMMDD = str(year) + str(month).zfill(2) + str(day).zfill(2)
    sformatdate = str(year) + '-' + str(month).zfill(2) + '-' + str(day).zfill(2)
    startdate = sformatdate + 'T' + stime[:2] + ':' + stime[2:4] + ':' + '00' + 'Z'

    # End date
    grandum = savegrans[len(savegrans)-1].split('_')[4]
    year, month, day = grandum[:4], grandum[4:6], grandum[6:8]
    eformatdate = str(year) + '-' + str(month).zfill(2) + '-' + str(day).zfill(2)
    enddate = eformatdate + 'T' + etime[:2] + ':' + etime[2:4] + ':' + '00' + 'Z'

    getname = savefile.rsplit('/',1)
    getname = getname[1]

    nc_fid.product_type = gas_name + " proxy"
    nc_fid.processing_level = "3"
    nc_fid.processing_version = "1"
    nc_fid.scan_num = str(scan)
    nc_fid.time_coverage_start = startdate
    nc_fid.time_coverage_end = enddate
    nc_fid.time_coverage_start_since_epoch = estime
    nc_fid.time_coverage_end_since_epoch = eetime
    nc_fid.collection_shortname = shortname
    nc_fid.input_files = forfiles
    nc_fid.geospatial_bounds = "POLYGON((17.0000 -155.0000,17.0000 -24.4500,64.0000 -24.4500,64.0000 -155.0000))"
    nc_fid.time_reference = '2000-01-01T12:00:00Z'
    nc_fid.geospatial_bounds_crs = 'EPSG:4326'
    nc_fid.geospatial_lon_min = np.float32(np.nanmin(flons))
    nc_fid.geospatial_lon_max = np.float32(np.nanmax(flons))
    nc_fid.geospatial_lat_min = np.float32(np.nanmin(flats))
    nc_fid.geospatial_lat_max = np.float32(np.nanmax(flats))
    nc_fid.local_granule_id = getname
    nc_fid.version_id = 1
    nc_fid.day_of_year = np.long(datetime.datetime.strptime(dateYYYYMMDD, "%Y%m%d").timetuple().tm_yday)
    nc_fid.project = 'TEMPO'
    nc_fid.platform = 'Intelsat 40e'
    nc_fid.source = 'UV-VIS hyperspectral imaging'
    nc_fid.institution = 'Short-term Prediction Research and Transition Center'
    nc_fid.creator_url = 'https://weather.msfc.nasa.gov/sport/'
    nc_fid.access_description = 'Pre-launch proxy data intended for TEMPO early adopters, not for scientific research. Data production url, https://weather.msfc.nasa.gov/sport/'
    nc_fid.access_value = np.long(0)
    nc_fid.Conventions = 'CF-1.8'
    nc_fid.title = 'TEMPO Level 3 ' + gas_name_long + ' product'
    nc_fid.collection_version = np.long(1)
    nc_fid.summary = gas_name_long.capitalize()+' Level 3 files provide trace gas information on a regular grid covering the TEMPO Field of Regard for TEMPO observations. Level 3 files are derived by combining information from all Level 2 files constituting a TEMPO East-West scan cycle. The files are provided in netCDF4 format, and contain information on tropospheric, stratospheric and total '+gas_name_long+' vertical columns, and ancillary data including product quality flags. The re-gridding algorithm uses an area-weighted approach.'

    # Open metadata file
    opendum = open(dumfile, "r+")
    readcont = opendum.read()

    nc_fid.coremetadata = str(readcont)

    # Close file
    nc_fid.close()

    ###### arn - add section to compress files
    outfile2 = splitfile[0] + '/' + fname[0].upper() + '_dum.' + fname[1]

    command = "nccopy -d9 -s " + savefile + " " + outfile2
    call(command, shell=True)

    command = "rm " + savefile
    call(command, shell=True)

    command = "mv " + outfile2 + " " + savefile
    call(command, shell=True)

    print("savefile near last line =" ,savefile)



#############################################
if __name__ == "__main__":
    main()
#TempoL2toL3.py
#Displaying TempoL2toL3.py
#Displaying TEMPO_L2toL3_maps.ipynb



