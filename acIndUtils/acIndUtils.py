import os
from glob import glob
import numpy as np
from scipy import stats, signal
import xarray as xr
import pandas as pd
import netCDF4
from shapely import geometry as g

import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)


class acNcFileSpec:
    
    def __init__(self, ncFileName="",varName="", xVarName="", yVarName="", zVarName="", tVarName=""):
        self.ncFileName = ncFileName
        self.varName = varName
        self.xVarName = xVarName
        self.yVarName = yVarName
        self.zVarName = zVarName
        self.tVarName = tVarName

    def printSpec(self):
        print(f"  ncFileName: {self.ncFileName}")
        print(f"  varName: {self.varName}")
        print(f"  xVarName: {self.xVarName}")
        print(f"  yVarName: {self.yVarName}")
        print(f"  zVarName: {self.zVarName}")
        print(f"  tVarName: {self.tVarName}")

    def clone(self, src, **kwargs):
        self.__dict__.update(src.__dict__)
        self.__dict__.update(kwargs)


def acCloneFileSpec(src, **kwargs):
    out = acNcFileSpec()
    out.clone(src, **kwargs)
    return out


def getNcFileName(dataset="adriaclim",
                  source="NEMO",
                  dataset_type="indicator",
                  variable="variable",
                  elaboration_type="mean/p95/anomaly",
                  scenario="hist", # can be hist/proj/anomaly
                  time_agg="monthly", # can be monthly, yearly, scenario
                  domain="adriatic",
                  year_start=1992,
                  year_end=2011):
    fnm = "_".join([dataset,
                    source,
                    dataset_type,
                    variable,
                    elaboration_type,
                    scenario,
                    time_agg,
                    domain,
                    str(year_start),
                    str(year_end)]) + ".nc"
    return fnm


def addMetadata(ncFilePath, ncVarName,
                title = "title",
                description = "description",
                adriaclim_dataset = "indicator",
                adriaclim_model = "NEMO",
                adriaclim_scale = "adriatic",
                adriaclim_timeperiod = "monthly",
                adriaclim_type = "timeseries|anomaly|trend",
                adriaclim_scenario = "hist|proj|anomaly",
                institution = "UNIBO",
                version = "0.0",
                units = 'units'
                ):
    ds = netCDF4.Dataset(ncFilePath, 'r+')
    ds.title = title
    ds.description = description
    ds.adriaclim_dataset = adriaclim_dataset
    ds.adriaclim_model = adriaclim_model
    ds.adriaclim_scale = adriaclim_scale
    ds.adriaclim_timeperiod = adriaclim_timeperiod
    ds.adriaclim_type = adriaclim_type
    ds.adriaclim_scenario = adriaclim_scenario
    ds.institution = institution
    ds.version = version
    ds[ncVarName].units = units
    ds.close()


def changeMetadata(ncFilePath, **kwargs):
    ds = netCDF4.Dataset(ncFilePath, "r+")
    for att in kwargs.keys():
        setattr(ds, att, kwargs[att])



def _get3DMaskOnPolygon(lon, lat, map3D, polygon):
    # polygon is given in form of [xcoordinates, ycoordinates]
    # assuming that map3D is (z, y, x)
    lonflatten = lon.flatten()
    latflatten = lat.flatten()
    pts = np.array([lonflatten, latflatten]).transpose()
  
    ply = g.Polygon(polygon)
    ncnt = np.vectorize(lambda p: ply.contains(g.Point(p)), signature='(n)->()')
    maskFlatten = ncnt(pts)
    mask = maskFlatten.reshape(lon.shape)
  
    nz = map3D.shape[0]
    mask_ = np.expand_dims(mask, 0)
    mask3D = mask_[np.zeros([nz]).astype(int), :, :]
  
    return mask3D

        
def acClipDataOnRegion(dataInputNcSpec, areaPerimeter, dataOutputNcFpath, otherVarNames=[]):
       
    """ CLIP INPUT OVER THE AREA OF INTEREST.
     Input File
     dataInputNcSpec: instance of acNcFileSpec describing the input nc file.
     areaPerimeter: pandas dataset delimiting the area being analysed. In the dataset, the 1st column is longitude, 
     the 2nd column is latitude 
     dataOutputNcFpath: path of the output nc file.
     otherVarNames: names of other variables to be clipped, if present
    """
    
    print("CMEMS SST Dimension:",dataInputNcSpec)
    print("Clipped Area Dimensions:",areaPerimeter)

    iLonCol = 0
    iLatCol = 1
    areaPerLon = areaPerimeter.iloc[:,iLonCol]
    areaPerLat = areaPerimeter.iloc[:,iLatCol]
    lat_max = areaPerLat.max()
    lat_min = areaPerLat.min()
    lon_max = areaPerLon.max()
    lon_min = areaPerLon.min()

    fls = glob(dataInputNcSpec.ncFileName)
    if len(fls) == 1:
        inputNc = xr.open_dataset(dataInputNcSpec.ncFileName, decode_times=False)
    elif len(fls) > 1:
       #inputNc = xr.open_mfdataset(dataInputNcSpec.ncFileName, chunks="auto")
        inputNc = xr.open_mfdataset(dataInputNcSpec.ncFileName, parallel=True, decode_times=False)
    else:
        raise Exception(f"file {dataInputNcSpec.ncFileName} not found")

    nclon = inputNc[dataInputNcSpec.xVarName]
    nclat = inputNc[dataInputNcSpec.yVarName]
    t = inputNc.sel({dataInputNcSpec.yVarName:slice(lat_min,lat_max), dataInputNcSpec.xVarName:slice(lon_min,lon_max)})
    
    hasZCoord = dataInputNcSpec.zVarName != ""

    #ensuring that the dimensions are in the correct order
    if hasZCoord:
        t = t.transpose(dataInputNcSpec.tVarName, dataInputNcSpec.zVarName, dataInputNcSpec.yVarName, dataInputNcSpec.xVarName)
    else:
        t = t.transpose(dataInputNcSpec.tVarName, dataInputNcSpec.yVarName, dataInputNcSpec.xVarName)

    print ('preselecting the mininumn containing rectangle, saving to ', dataOutputNcFpath)

    if os.path.isfile(dataOutputNcFpath):
        os.remove(dataOutputNcFpath)

    lon = inputNc[dataInputNcSpec.xVarName].values
    lat = inputNc[dataInputNcSpec.yVarName].values
    zzz = inputNc[dataInputNcSpec.zVarName].values if dataInputNcSpec.zVarName in inputNc else None
    tms = inputNc[dataInputNcSpec.tVarName].values
    timeUnitsStr = inputNc[dataInputNcSpec.tVarName].attrs["units"]
    varNames = [dataInputNcSpec.varName]
    varNames.extend(otherVarNames)

    print ('clipping over the polygon and storing frame by frame (may take a while ...)')
    outNcFlSpec = acCloneFileSpec(dataInputNcSpec, ncFileName=dataOutputNcFpath)
    outFl = acNcFile(outNcFlSpec, lon, lat, zzz, varNames, timeUnitsStr)
    outFl.createFile()
    ds = outFl.ds
    ds[outNcFlSpec.tVarName][:] = tms
    lonmtx, latmtx = np.meshgrid(lon, lat)
    nframe = ds.variables[dataInputNcSpec.tVarName].shape[0]

    for varName in varNames:
        varsrc = inputNc[varName]
        varnc = ds.variables[varName]
        mask3d = None
        for ifrm in range(nframe):
            if ifrm % 100 == 0:
                percDone = ifrm/nframe*100
                print(f"  done {percDone:2.0f} %", end="\r")
            vls = varsrc.values[ifrm, :]
            vls3d = vls if hasZCoord else np.expand_dims(vls, 0)
            if mask3d is None:
                mask3d = _get3DMaskOnPolygon(lonmtx, latmtx, vls3d, areaPerimeter.values)
            clp3d = vls3d.copy()
            clp3d[~mask3d] = np.nan
            clp = clp3d if hasZCoord else clp3d[0,:]
            varnc[ifrm, :] = clp
    ds.close()
    inputNc.close()
    print("")

    

def __acGenerateAnnualMeanMaps(inputNcSpec, outputFileName, timeSelector):
    inDt = xr.open_dataset(inputNcSpec.ncFileName)
    tm = inDt[inputNcSpec.tVarName]

    _sel = inDt.sel({tm.name: timeSelector(tm)})
    aggstr = f"{tm.name}.year"
    ouDt = _sel.groupby(aggstr).mean()
    if os.path.isfile(outputFileName):
      os.remove(outputFileName)
    ouDt.to_netcdf(path=outputFileName)
    


def acGenerateAnnualMeanMaps(inputNcSpec, annualMapsNcFile): 
    
    """ Annual Mean map on previously clipped data within 33 years
    """
    def AM(tm):
        month = tm.dt.month
        return (month >= 1) & (month <= 12)
    __acGenerateAnnualMeanMaps(inputNcSpec, annualMapsNcFile, AM)
    


def acGenerateSeasonalWinter(inputNcSpec, winterMapsNcFile):
    
    """ Winter Period time selection for the creation of WINTER PERIOD NetCDF file, over previously clipped data
    """    
    def WINTER(tm):
        month = tm.dt.month
        return (month >= 1) & (month <= 4)
    __acGenerateAnnualMeanMaps(inputNcSpec, winterMapsNcFile, WINTER)


    
def acGenerateSeasonalSummer(inputNcSpec, summerMapsNcFile):
    
    """ Summer Period time selection for the creation of SUMMER PERIOD NetCDF file, over previously clipped data
    """
    def SUMMER(tm):
        month = tm.dt.month
        return (month >= 7) & (month <= 10)
    __acGenerateAnnualMeanMaps(inputNcSpec, summerMapsNcFile, SUMMER)



def acGenerateMeanTimeSeries(inputNcSpec, outCsvFile):
    
    """ Mean sized LAT an LON  1 dimensional NetCDF file over previously clipped data, for the next csv file creation function
    """
    inDs = xr.open_dataset(inputNcSpec.ncFileName) 
    if inputNcSpec.zVarName == "":
      fy_1D= inDs.mean(dim=(inputNcSpec.yVarName, inputNcSpec.xVarName), skipna=True)
    else:
      fy_1D= inDs.mean(dim=(inputNcSpec.yVarName, inputNcSpec.xVarName, inputNcSpec.zVarName), skipna=True)
    ouDs = fy_1D.to_dataframe()[inputNcSpec.varName]
    ouDs.to_csv(outCsvFile)
    return ouDs
  


def acComputeAnnualTheilSenFitFromDailyFile(dailyCsvFile):
    """
    computeAnnualTheilSenFitFromDailyFile: computes the Theil-Sen fit of the annual means, using an input file with daily values
    input:
      dailyCsvFile: csv file with daily values.
    output:
      medslope, medintercept, lo_slope, up_slope, pvalue. lo_slope and up_slope are computed with a 95% confidence.
    """
    
    ds = pd.read_csv(dailyCsvFile)
    # assuming that date is the 1st column, value is the 2nd column
    dateCol = 0
    valCol = 1
    # converting object to date
    ds.iloc[:,dateCol] = pd.to_datetime(ds.iloc[:,dateCol])
    valColName = ds.iloc[:,valCol].name
    dsDateCol = ds.iloc[:,dateCol]
    dsy = ds.groupby(dsDateCol.dt.year)[valColName].agg("mean")

    vals = dsy.values
    alpha = .95
    medslope, medintercept, lo_slope, up_slope = stats.mstats.theilslopes(vals, alpha=alpha)
    
    tii = np.arange(len(vals))
    kendallTau, pvalue = stats.kendalltau(tii, vals)

    return medslope, medintercept, lo_slope, up_slope, pvalue



def acComputeSenSlope2DMap(annualMapsNcSpec, outputNcFile, smoothingKernelSide=3, otherVarNames=[]):
    """
    computeSenSlopeMap: generates a map with the sen's slope for each pixel, given the series of annual maps in file inputNcFile.
    input:
      annualMapsNcFile: input nc file with annual maps of the variable of interest. The time variable is assumed to be called "year".
    output:
      outputNcFile: file where the slope is stored.
    other parameters:
      smoothingKernelSide: ouptut smoothing kernel side (expressed in number of cells)
    """
    inputDs = xr.open_dataset(annualMapsNcSpec.ncFileName)
  
    def _compSenSlope(vals):
      alpha = .95
      medslope, _, _, _ = stats.mstats.theilslopes(vals, alpha=alpha)
      return medslope
  
    slp = xr.apply_ufunc(_compSenSlope, inputDs, input_core_dims=[["year"]], dask="allowed", vectorize=True)

    varNames = [annualMapsNcSpec.varName]
    varNames.extend(otherVarNames)

    for varName in varNames:
        # applying some smoothing by means of a convolution (2D only)
        vls = slp[varName].values
        msk = (~np.isnan(vls)).astype(int)
        vls[msk == 0] = 0
        krnl = np.ones((smoothingKernelSide, smoothingKernelSide))
        cellCount = signal.convolve2d(msk, krnl, mode="same")
        cellCount[msk == 0] = 1
        smoothedVls = signal.convolve2d(vls, krnl, mode="same")/cellCount
        smoothedVls[msk == 0] = np.nan
        slp[varName].values = smoothedVls

    # adding time dimension
    tmcrd = inputDs["year"].mean()
    yr = np.round(tmcrd.values).astype(int)
    unitsStr = f"days since {yr}-01-01"
    slp = slp.expand_dims({annualMapsNcSpec.tVarName: [0]}, axis=0)
    slp[annualMapsNcSpec.tVarName].attrs = {"units": unitsStr}

    # saving
    slp.to_netcdf(outputNcFile)




def acComputeSenSlope3DMap(annualMapsNcSpec, outputNcFile):
    """
    computeSenSlopeMap: generates a map with the sen's slope for each pixel in the 3D map, given the series of annual maps in file inputNcFile.
    input:
      annualMapsNcFile: input nc file with annual maps of the variable of interest. The time variable is assumed to be called "year".
    output:
      outputNcFile: file where the slope is stored.
    """
    inputDs = xr.open_dataset(annualMapsNcSpec.ncFileName)
  
    def _compSenSlope(vals):
      alpha = .95
      medslope, _, _, _ = stats.mstats.theilslopes(vals, alpha=alpha)
      return medslope
  
    slp = xr.apply_ufunc(_compSenSlope, inputDs, input_core_dims=[["year"]], dask="allowed", vectorize=True)

    # adding time dimension
    tmcrd = inputDs["year"].mean()
    yr = np.round(tmcrd.values).astype(int)
    unitsStr = f"days since {yr}-01-01"
    slp = slp.expand_dims({annualMapsNcSpec.tVarName: [0]}, axis=0)
    slp[annualMapsNcSpec.tVarName].attrs = {"units": unitsStr}

    # saving
    slp.to_netcdf(outputNcFile)




def acGetVProfile(ac3DFieldNcSpec, maxDepth, zlevs=None):
    """
    acGetVProfile: computes a vertical profile for a given 3D file. If time is included in the file, this is also taken into account.
    Input:
        ac3DFieldNcSpec: file spec with 3D file.
        maxDepth: depth down to which the profile is computed.
        zlevs: vertical coordinates. If this parameter is not given, the coordinates found in the file are used.
    Output:
        dpth: depth
        vprov: vertical profile
    """
    assert maxDepth < 0
    ds = xr.open_dataset(ac3DFieldNcSpec.ncFileName)
    meandims = [ac3DFieldNcSpec.xVarName, ac3DFieldNcSpec.yVarName]
    if ac3DFieldNcSpec.tVarName in ds:
        meandims.append(ac3DFieldNcSpec.tVarName)
    vprof_ = ds.mean(dim=meandims, skipna=True)
    dpth = vprof_[ac3DFieldNcSpec.zVarName].values
    vprof = vprof_[ac3DFieldNcSpec.varName].values
    if np.max(dpth) > 0:
        dpth=-dpth
    assert len(vprof.shape) == 1
    if not zlevs is None:
        assert np.min(zlevs) < 0
        if np.nanmean(np.diff(dpth)[0]) < 0:
            dpth = dpth[::-1]
            vprof = vprof[::-1]
        vprof_ = vprof
        vprof = np.interp(zlevs, dpth, vprof_)
        dpth = zlevs
    cnd = dpth > maxDepth
    dpth = dpth[cnd]
    vprof = vprof[cnd]
    ds.close()
    return dpth, vprof




def acGetVProfileStDev(ac3DFieldNcSpec, maxDepth, zlevs=None):
    """
    acGetVProfile: computes the standard deviation of the vertical profile for a given 3D file. 
    If time is included in the file, this is also taken into account.
    Input:
        ac3DFieldNcSpec: file spec with 3D file.
        maxDepth: depth down to which the profile is computed.
        zlevs: vertical coordinates. If this parameter is not given, the coordinates found in the file are used.
    Output:
        dpth: depth
        vprov: standard devition of the vertical profile
    """
    assert maxDepth < 0
    ds = xr.open_dataset(ac3DFieldNcSpec.ncFileName)
    meandims = [ac3DFieldNcSpec.xVarName, ac3DFieldNcSpec.yVarName]
    if ac3DFieldNcSpec.tVarName in ds:
        meandims.append(ac3DFieldNcSpec.tVarName)
    vprof_ = ds.std(dim=meandims, skipna=True)
    dpth = vprof_[ac3DFieldNcSpec.zVarName].values
    vprof = vprof_[ac3DFieldNcSpec.varName].values
    if np.max(dpth) > 0:
        dpth=-dpth
    assert len(vprof.shape) == 1
    if not zlevs is None:
        assert np.min(zlevs) < 0
        if np.nanmean(np.diff(dpth)[0]) < 0:
            dpth = dpth[::-1]
            vprof = vprof[::-1]
        vprof_ = vprof
        vprof = np.interp(zlevs, dpth, vprof_)
        dpth = zlevs
    cnd = dpth > maxDepth
    dpth = dpth[cnd]
    vprof = vprof[cnd]
    ds.close()
    return dpth, vprof

    
class acNcFile:

    def __init__(self, ncFileSpec, xx, yy, zz=None, varNames=None, 
                       timeUnitsStr=""):
        self.ncFileSpec = ncFileSpec
        self.xx = xx
        self.yy = yy
        self.zz = zz
        self.varNames = (varNames if not varNames is None
                                  else [ncFileSpec.varName])
        self.timeUnitsStr = timeUnitsStr
        self.calendar = "standard"

    def createFile(self):
        fs = self.ncFileSpec
        self.ds = netCDF4.Dataset(fs.ncFileName, "w")
        self.tDim = self.ds.createDimension(fs.tVarName, None)
        if len(self.yy.shape) == 1:
            self.yDim = self.ds.createDimension(fs.yVarName, self.yy.shape[0])
            self.xDim = self.ds.createDimension(fs.xVarName, self.xx.shape[0])
        elif len(self.yy.shape) == 2:
            self.yDim = self.ds.createDimension(fs.yVarName, self.yy.shape[0])
            self.xDim = self.ds.createDimension(fs.xVarName, self.xx.shape[1])
        else:
            raise Exception("x, y coords can only be 1D or 2D")
        self.yVar = self.ds.createVariable(fs.yVarName, 'f4', (fs.yVarName,))
        self.xVar = self.ds.createVariable(fs.xVarName, 'f4', (fs.xVarName,))

        self.tVar = self.ds.createVariable(fs.tVarName, 'f4', (fs.tVarName,))
        self.tVar.units = self.timeUnitsStr
        self.tVar.calendar = self.calendar
        if not self.zz is None:
            self.zDim = self.ds.createDimension(fs.zVarName, self.zz.shape[0])
            self.zVar = self.ds.createVariable(fs.zVarName, 'f4', 
                                              (fs.zVarName,))
            dims = [fs.tVarName, fs.zVarName, fs.yVarName, fs.xVarName]
        else:
            dims = [fs.tVarName, fs.yVarName, fs.xVarName]
        if len(self.yy.shape) == 1:
            self.yVar[:] = self.yy[:]
            self.xVar[:] = self.xx[:]
        elif len(self.yy.shape) == 2:
            self.yVar[:] = self.yy[:, 0]
            self.xVar[:] = self.xx[0, :]
        if not self.zz is None:
            self.zVar[:] = self.zz[:]
        self.vars = {}
        for varName in self.varNames:
            self.vars[varName] = self.ds.createVariable(varName,
                                                        'f4',
                                                        dims)
        self.ntime = 0
        
    def writeVariables(self, dateTimes, **kwargs):
        newNTime = len(dateTimes)
        tmnums = netCDF4.date2num(dateTimes, self.timeUnitsStr, self.calendar)
        self.tVar[self.ntime:self.ntime+newNTime] = tmnums
        for varName in kwargs.keys():
            vr = kwargs[varName]
            if vr.shape[0] != newNTime:
                raise Exception("""acIndUtils.writeVariables: 
                                   the number of time frame must be the same 
                                   for all the variables""")
            self.vars[varName][self.ntime:self.ntime+newNTime] = vr
        self.ntime += newNTime

    def close(self):
        self.ds.close()
        self.ds = None



def generateDifferencDataset(projNcFileSpec, 
                             bslnNcFileSpec, 
                             outNcFileSpec):

    dsproj = xr.open_dataset(projNcFileSpec.ncFileName)
    projmean = dsproj.mean(dim=projNcFileSpec.tVarName)
    
    dshist = xr.open_dataset(bslnNcFileSpec.ncFileName)
    histmean = dshist.mean(dim=bslnNcFileSpec.tVarName)

    dff = projmean - histmean

    tmcrd = dsproj[projNcFileSpec.tVarName].mean()
    tmcrd = tmcrd.expand_dims(projNcFileSpec.tVarName)
    dff = dff.expand_dims({projNcFileSpec.tVarName: tmcrd}, axis=0)

    dff.to_netcdf(outNcFileSpec.ncFileName)

    dsproj.close()
    dshist.close()
        


def addNavlonNavlatFields(ncFileSpec):
    ds = netCDF4.Dataset(ncFileSpec.ncFileName, "r+")
    x = ds.variables[ncFileSpec.xVarName][:]
    y = ds.variables[ncFileSpec.yVarName][:]
    lonmtx, latmtx = np.meshgrid(x, y)
    nav_lon = ds.createVariable("nav_lon", 'f4', (ncFileSpec.yVarName, ncFileSpec.xVarName))
    nav_lon[:] = lonmtx
    nav_lat = ds.createVariable("nav_lat", 'f4', (ncFileSpec.yVarName, ncFileSpec.xVarName))
    nav_lat[:] = latmtx
    ds.close()
    



        

