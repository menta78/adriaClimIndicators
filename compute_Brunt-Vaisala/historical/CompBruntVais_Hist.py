#+++++++++++++++++++++++++++++++++++++++
#     Compute Brunt-Vaisala Freq.
#+++++++++++++++++++++++++++++++++++++++

import xarray as xr
import numpy as np
import numpy.ma as ma
import netCDF4 as nc
from datetime import date, timedelta
import os
from progress.bar import Bar

#--- date range ---#
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

# path of density files
path = '/Volumes/alessandri/AdriaClim_Data/Indicator/Historical_Nemo/Density/'

#--- start and end date ---#
start_date = date(1992,1,9)
end_date = date(1992,1,11)

ndays=int((end_date - start_date).days)

# define some constants
p0 = 1026.
g  = 9.81

with Bar('Processing...',suffix='%(percent).1f%% - %(eta)ds',max=ndays) as bar:

   # Loop over the years
   y=0
   for single_date in daterange(start_date, end_date):

      #--- save date info ---#
      year=single_date.strftime("%Y")
      month=single_date.strftime("%m")
      day=single_date.strftime("%d")
#      print(single_date)
   
      inpth = path+year+'/'+month+'/'
   
      # --- file names ---#
      fname = inpth+'ADRIACLIM2_1d_'+year+month+day+'_Dens_grid_T.nc'
   
      # read file for copying nc file
      Filetc= nc.Dataset(fname)
   
      # read file with xarray
      FileD = xr.open_dataset(fname)
   
      # variables to numpy
      Dens = FileD.rho.to_numpy()
   
      depth= FileD.depth.to_numpy()
      lat  = FileD.lat.to_numpy()
      lon  = FileD.lon.to_numpy()
      time = FileD.time_counter.to_numpy()
   
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

      # Exlcude first two level to compute maximum BVF
      dumpBV=BV[:,2:,:,:]
   
      # Compute Max value of BV
      maxBV = np.nanmax(dumpBV,axis=1,keepdims=False)
   
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
      pathout = '/Volumes/alessandri/AdriaClim_Data/Indicator/Historical_Nemo/Brunt-Vaisala/'
   
      #--- generate sub-directory if not exist ---#
      #os.makedirs(pathout+year+'/'+month+'/', exist_ok=True)
   
      #pathout = pathout+year+'/'+month+'/'
      
      fout = 'ADRIACLIM2_1d_'+year+month+day+'_BVF_grid_T.nc'
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
          swd = dst.createVariable('BVF','float32',('time_counter','depth','lat','lon'),fill_value=1.e+20)
          dst['BVF'][:] = BV
          swd.units = 'cycle/hr'
          swd.standard_name = 'Brunt Vaisala Frequency'
          swd.long_name = 'Brunt Vaisala Frequency'
   
          #--------- Max Brunt-Vaisala Freqeuncy ---------#
          swd1 = dst.createVariable('MaxBV','float32',('time_counter','lat','lon'),fill_value=1.e+20)
          dst['MaxBV'][:] = maxBV
          swd1.units = 'cycle/hr'
          swd1.standard_name = 'Max Brunt Vaisala Frequency'
          swd1.long_name = 'Max Brunt Vaisala Frequency'
   
          #--------- Depth of max Brunt-Vaisala  ---------#
          swd2 = dst.createVariable('zmaxbv','float32',('time_counter','lat','lon'),fill_value=1.e+20)
          dst['zmaxbv'][:] = zmax
          swd2.units = 'm'
          swd2.standard_name = 'depth of Max Brunt Vaisala Frequency'
          swd2.long_name = 'depth of Max Brunt Vaisala Frequency'
   
      bar.next()
   bar.finish()
