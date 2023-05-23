#+++++++++++++++++++++++++++++++++++++++++++++
#          Compute Density (EOS80)
#+++++++++++++++++++++++++++++++++++++++++++++

import xarray as xr
import seawater as sw
import netCDF4 as nc
from datetime import date, timedelta
import os
from progress.bar import Bar
import numpy as np

#--- date range ---#
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

# path of temperature and salinity file
path = '/Volumes/alessandri/AdriaClim_Data/erddap.cmcc-opa.eu/erddap/files/adriaclim_resm_nemo_projection_day_T/'

# path of the mask file
maskpath='/Volumes/alessandri/AdriaClim_Data/erddap.cmcc-opa.eu/erddap/files/mask_NEMO_AdriaClim_compressed.nc'

# open mask dataset
maskfile = xr.open_dataset(maskpath)
tmask = maskfile.tmask.to_numpy()

#--- start and end date ---#
start_date = date(2022,1,1)
end_date = date(2050,12,31)

ndays=int((end_date - start_date).days)

with Bar('Processing...',suffix='%(percent).1f%% - %(eta)ds',max=ndays) as bar:

   # Loop over the years 
   for single_date in daterange(start_date, end_date):
   
      #--- save date info ---#
      year=single_date.strftime("%Y")
      month=single_date.strftime("%m")
      day=single_date.strftime("%d")
#      print(single_date)
   
      inpth = path+year+'/'+month+'/'
   
      # --- file names ---#
      fname = inpth+'ADRIACLIM2_1d_'+year+month+day+'_grid_T.nc'
   
      # --- read netcdf file just to copy dimension, variables and attributes ---#
      File = nc.Dataset(fname)
   
      # --- read with Xarray to compute density --- #
      FileDens = xr.open_dataset(fname)

      # --- Temp and Salt to numpy ---#
      Temp = FileDens.votemper.to_numpy()
      Salt = FileDens.vosaline.to_numpy()

      # --- mask file --- #
      Temp = np.where(tmask == 1,Temp,np.nan)
      Salt = np.where(tmask == 1,Salt,np.nan)
   
      # --- Compute potential density --- #
      Dens = sw.eos80.dens0(Salt,Temp)
   
      #---------- exclude non-necessary variables and dimensions relative ------------#   
      toexcludedim=[]
      toexclude=['votemper','vosaline','SL_R','SL_S','SSH_C','sowaflup','sossheig','sosstsst', \
                 'sosfldow','somxl010','somixhgt','sohefldo' ,'sosaline']
      
      # name of output file
      pathout = '/Volumes/alessandri/AdriaClim_Data/Projection_Nemo/Density/'
   
      #--- generate sub-directory if not exist ---#
      os.makedirs(pathout+year+'/'+month+'/', exist_ok=True)
   
      pathout = pathout+year+'/'+month+'/'
      
      fout = 'ADRIACLIM2_1d_'+year+month+day+'_Dens_grid_T.nc'
      #
      #------- save tidal components on a netcdf -------------#
      with File as src, nc.Dataset(pathout+fout, "w") as dst:
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
          swd = dst.createVariable('rho','float32',('time_counter','depth','lat','lon'),fill_value=1.e+20)
          dst['rho'][:] = Dens
          swd.units = 'kg/m3'
          swd.standard_name = 'Seawater density'
          swd.long_name = 'Density'

      bar.next()
   bar.finish()
