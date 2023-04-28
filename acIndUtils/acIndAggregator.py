import glob
import netCDF4
import numpy as np
import xarray as xr

import acIndUtils


def getFiles(filePathTemplate, scenario, years):
    fls = []
    for yr in years:
        flpth = filePathTemplate.format(scenario=scenario,
                                        year=yr)
        _fls = glob.glob(flpth)       
        fls.extend(_fls)
    fls.sort()
    return fls



def meanAggregator(dts, vrs, outVarName, outFl):
    meanVr = np.mean(vrs, 0)

    vrs_ = {outVarName: np.expand_dims(meanVr, 0)}
    outFl.writeVariables([dts[0]], **vrs_)


def dateFallsInMonthlyBucket(aDate, bucketDate):
    return aDate.month == bucketDate.month



def dateFallsInAnnualBucket(aDate, bucketDate):
    return aDate.year == bucketDate.year



def collectMonthlyData(inputNcFileSpec, outputNcFileSpec, 
                         aggregator = meanAggregator,
                         inputFiles = None,
                         coordsNcFileSpec = None,
                         fill_value = None):
    aggregateDataOverTime(inputNcFileSpec, outputNcFileSpec, 
                         aggregator = meanAggregator,
                         timeBucketFunction = dateFallsInMonthlyBucket,
                         inputFiles = inputFiles,
                         coordsNcFileSpec = coordsNcFileSpec,
                         fill_value = fill_value)


def collectAnnualData(inputNcFileSpec, outputNcFileSpec, 
                         aggregator = meanAggregator,
                         inputFiles = None,
                         coordsNcFileSpec = None,
                         fill_value = None):
    aggregateDataOverTime(inputNcFileSpec, outputNcFileSpec, 
                         aggregator = meanAggregator,
                         timeBucketFunction = dateFallsInAnnualBucket,
                         inputFiles = inputFiles,
                         coordsNcFileSpec = coordsNcFileSpec,
                         fill_value = fill_value)


def aggregateDataOverTime(inputNcFileSpec, outputNcFileSpec, 
                         aggregator = meanAggregator,
                         timeBucketFunction = dateFallsInMonthlyBucket,
                         inputFiles = None,
                         coordsNcFileSpec = None,
                         fill_value = None):
   #here ncFileName is assumed to be a wildcard pattern
    if inputFiles is None:
        fls = glob.glob(inputNcFileSpec.ncFileName)
        fls.sort()
    else:
        fls = inputFiles
    global outFl, actDt
    outFl = None

    varNames = [outputNcFileSpec.varName] 
    
    actDt = None

    is3d = inputNcFileSpec.zVarName != ""

    def getByMonth():
        global outFl, actDt
        vrs = []
        dts = []
        for flpth in fls:
            inFl = netCDF4.Dataset(flpth)
            tm = inFl.variables[inputNcFileSpec.tVarName]
            vr = inFl.variables[inputNcFileSpec.varName]
            try:
                calendar = tm.calendar
            except:
                calendar = "standard"
            dts_ = netCDF4.num2date(tm[:], tm.units, calendar)
            if outFl is None:
                print("  initializing ...")
                zz = None
                if coordsNcFileSpec is None:
                    xx = inFl.variables[inputNcFileSpec.xVarName]
                    yy = inFl.variables[inputNcFileSpec.yVarName]
                    if is3d:
                        zz = inFl.variables[inputNcFileSpec.zVarName]
                else:
                    coordsFl = netCDF4.Dataset(coordsNcFileSpec.ncFileName)
                    xx = coordsFl.variables[coordsNcFileSpec.xVarName]
                    yy = coordsFl.variables[coordsNcFileSpec.yVarName]
                    if is3d:
                        zz = coordsFl.variables[coordsNcFileSpec.zVarName]
                actDt = dts_[0]
                actDtStr = actDt.strftime("%Y-%m-%d")
                print(f"    elaborating {actDt}")
                timeUnitsStr = f"days since {actDtStr}"
                outFl = acIndUtils.acNcFile(outputNcFileSpec, xx, yy, zz=zz,
                                            varNames=varNames,
                                            timeUnitsStr=timeUnitsStr)
                outFl.createFile()

            for idt in range(len(dts_)):
                dt = dts_[idt]
                print(f"      {dt}")
                vrdt = vr[idt,...]
                if ((not fill_value is None)
                        and (type(vrdt) is np.ma.core.MaskedArray)):
                    vrdt = vrdt.filled(fill_value)
                if timeBucketFunction(dt, actDt):
                    vrs.append(vrdt)
                    dts.append(dt)
                else:
                    yield dts, np.array(vrs)
                    actDt = dt
                    print(f"    elaborating {actDt}")
                    vrs = [vrdt]
                    dts = [dt]
        yield dts, np.array(vrs)

    for dt, vrs in getByMonth():
        aggregator(dt, vrs, outputNcFileSpec.varName, outFl)
    if not outFl is None:
        outFl.close()

