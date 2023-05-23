#+++++++++++++++++++++++++++++++++++++++
#     Compute Brunt-Vaisala Freq.
#+++++++++++++++++++++++++++++++++++++++

import xarray as xr
import numpy as np
import numpy.ma as ma
import netCDF4 as nc

# path of density files
path = 'output/Density/'

# create a tuple for years
years = ('1988','1989','1990','1991','1992','1993','1994','1995','1996','1997','1998','1999', \
        '2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010','2011','2012',  \
        '2013','2014','2015','2016','2017','2018','2019')
#years = ('1987',)

# define some constants
p0 = 1026.
g  = 9.81

# Loop over the years
y=0
for year in years:

   # file names
   fname = year+'_daily_cmems_reanalysis_density_AdriaticSea.nc'

   # read file for copying nc file
   Filetc= nc.Dataset(path+fname)

   # read file with xarray
   FileD = xr.open_dataset(path+fname)

   # variables to numpy
   Dens = FileD.rho.to_numpy()

   depth= FileD.depth.to_numpy()
   lat  = FileD.lat.to_numpy()
   lon  = FileD.lon.to_numpy()
   time = FileD.time.to_numpy()

   # length of variables
   NZ = len(depth)-1
   NY = len(lat)
   NX = len(lon)
   NT = len(time)

   # define BV array
   BV = np.zeros((NT,NZ+1,NY,NX),float)

   # Compute difference among levels
   dz = depth[1:NZ+1] - depth[0:NZ]

   # Compute actual Brunt-Vaisala Freq.
   for k in range(NZ):
      BV[:,k,:,:] = (Dens[:,k+1,:,:] - Dens[:,k,:,:]) / dz[k]

   BV[:,k+1,:,:] = np.nan
   
   sign = np.where(BV < 0.,-1,1)
   BV = sign * np.sqrt((g/p0)*abs(BV)) * (3600/2/np.pi)  # cycle/hr 

   # Compute Max value of BV
   maxBV = np.nanmax(BV,axis=1,keepdims=False)

   ### compute depth of max BV ###
   # compute first argument of max value of BV
   zmaxarg = np.zeros((NT,NY,NX), float)
   zmax = np.zeros((NT,NY,NX), float)
   for j in range(NY):
      for i in range(NX):
         try:  
            zmaxarg[:,j,i] = np.nanargmax(BV[:,:,j,i],axis=1,keepdims=False)
         except ValueError:
            zmaxarg[:,j,i] = np.nan

   i=0
   j=0
   t=0

   # assign to zmax variable the depth of max value of BV
   for t in range(NT):
      for j in range(NY):
        for i in range(NX):  
           if ~np.isnan(zmaxarg[t,j,i]):
               zmax[t,j,i] = depth[int(zmaxarg[t,j,i])]
           else:
               zmax[t,j,i] = np.nan


   #---------- exclude non-necessary variables and dimensions relative ------------#   
   toexcludedim=[]
   toexclude=['rho']
   
   # name of output file
   pathout = 'output/'
   fout = year+'_daily_cmems_reanalysis_BV_AdriaticSea.nc'
   #
   #------- save tidal components on a netcdf -------------#
   with Filetc as src, nc.Dataset(pathout+fout, "w") as dst:
       # copy global attributes all at once via dictionary
       dst.setncatts(src.__dict__)
       #dst.event=evtime
       #dst.simulations=args.exp
       # copy dimensions
       for name, dimension in src.dimensions.items():
           if name not in toexcludedim:
              dst.createDimension(
                  name, (len(dimension) if not dimension.isunlimited() else None))
       # copy all file data except for the excluded
       for name, variable in src.variables.items():
           if name not in toexclude:
               xy= dst.createVariable(name, variable.datatype, variable.dimensions)
               # copy variable attributes all at once via dictionary
               dst[name].setncatts(src[name].__dict__)
               dst[name][:] = src[name][:]

       #--------- Brunt-Vaisala Freqeuncy ---------#
       swd = dst.createVariable('BVF','float32',('time','depth','lat','lon'),fill_value=1.e+20)
       dst['BVF'][:] = BV
       swd.units = 'cycle/hr'
       swd.standard_name = 'Brunt Vaisala Frequency'
       swd.long_name = 'Brunt Vaisala Frequency'

       #--------- Max Brunt-Vaisala Freqeuncy ---------#
       swd1 = dst.createVariable('MaxBV','float32',('time','lat','lon'),fill_value=1.e+20)
       dst['MaxBV'][:] = maxBV
       swd1.units = 'cycle/hr'
       swd1.standard_name = 'Max Brunt Vaisala Frequency'
       swd1.long_name = 'Max Brunt Vaisala Frequency'

       #--------- Depth of max Brunt-Vaisala  ---------#
       swd2 = dst.createVariable('zmaxbv','float32',('time','lat','lon'),fill_value=1.e+20)
       dst['zmaxbv'][:] = zmax
       swd2.units = 'm'
       swd2.standard_name = 'depth of Max Brunt Vaisala Frequency'
       swd2.long_name = 'depth of Max Brunt Vaisala Frequency'

   y = y + 1
   print('completed: ',(y/len(years))*100,'%')


