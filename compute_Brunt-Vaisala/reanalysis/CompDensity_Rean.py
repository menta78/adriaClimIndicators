#+++++++++++++++++++++++++++++++++++++++++++++
#          Compute Density (EOS80)
#+++++++++++++++++++++++++++++++++++++++++++++

import xarray as xr
import seawater as sw
import netCDF4 as nc
import numpy as np
import pandas

# path of temperature and salinity file
pathT = 'TEMPERATURE_SINCE_1987/'
pathS = 'SALINITY__since_1987/'

# create a tuple for years
years = ('1988','1989','1990','1991','1992','1993','1994','1995','1996','1997','1998','1999', \
        '2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010','2011','2012',  \
        '2013','2014','2015','2016','2017','2018','2019')
#years = ('2019',)

# Loop over the years 
i=0
for year in years:

   # file names
   fnameT = year+'_daily_cmems_reanalysis_temperature_AdriaticSea.nc'
   fnameS = year+'_daily_cmems_reanalysis_salinity_AdriaticSea.nc'

   # read netcdf file just to copy dimension, variables and attributes
   FileT = nc.Dataset(pathT+fnameT)
   FileS = nc.Dataset(pathS+fnameS)

   # read with Xarray to compute density
   FileTo = xr.open_dataset(pathT+fnameT)
   FileSo = xr.open_dataset(pathS+fnameS)

   # Temp and Salt to numpy
   Temp = FileTo.thetao.to_numpy()
   Salt = FileSo.so.to_numpy()

   # Compute potential density
   Dens = sw.eos80.dens0(Salt,Temp)

   #---------- exclude non-necessary variables and dimensions relative ------------#   
   toexcludedim=[]
   toexclude=['thetao']
   
   # name of output file
   pathout = 'output/'
   fout = year+'_daily_cmems_reanalysis_density_AdriaticSea.nc'
   #
   #------- save tidal components on a netcdf -------------#
   with FileT as src, nc.Dataset(pathout+fout, "w") as dst:
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

       #--------- seawater density ---------#
       swd = dst.createVariable('rho','float32',('time','depth','lat','lon'),fill_value=1.e+20)
       dst['rho'][:] = Dens
       swd.units = 'kg/m3'
       swd.standard_name = 'Seawater density'
       swd.long_name = 'Density'

   i = i + 1
   print('completed: ',(i/len(years))*100,'%')


