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



def meanAggregator2D(dts, vrs, outVarName, outFl):
    meanVr = np.mean(vrs, 0)

    vrs_ = {outVarName: np.expand_dims(meanVr, 0)}
    outFl.writeVariables([dts[0]], **vrs_)


def collectMonthlyData2D(inputNcFileSpec, outputNcFileSpec, 
                         aggregator: meanAggregator2D,
                         inputFiles: None):
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

    def getByMonth():
        global outFl, actDt
        vrs = []
        dts = []
        for flpth in fls:
            inFl = netCDF4.Dataset(flpth)
            xx = inFl.variables[inputNcFileSpec.xVarName]
            yy = inFl.variables[inputNcFileSpec.yVarName]
            tm = inFl.variables[inputNcFileSpec.tVarName]
            vr = inFl.variables[inputNcFileSpec.varName]
            try:
                calendar = tm.calendar
            except:
                calendar = "standard"
            dts_ = netCDF4.num2date(tm[:], tm.units, calendar)
            if outFl is None:
                print("  initializing ...")
                actDt = dts_[0]
                actDtStr = actDt.strftime("%Y-%m-%d")
                print(f"    elaborating {actDt}")
                timeUnitsStr = f"days since {actDtStr}"
                outFl = acIndUtils.acNcFile(outputNcFileSpec, xx, yy, 
                                            varNames=varNames,
                                            timeUnitsStr=timeUnitsStr)
                outFl.createFile()

            for idt in range(len(dts_)):
                dt = dts_[idt]
                print(f"      {dt}")
                if dt.month == actDt.month:
                    vrs.append(vr[idt,...])
                    dts.append(dt)
                else:
                    yield dts, np.array(vrs)
                    actDt = dt
                    print(f"    elaborating {actDt}")
                    vrs = []
                    dts = []
        yield dts, np.array(vrs)

    for dt, vrs in getByMonth():
        aggregator(dt, vrs, outputNcFileSpec.varName, outFl)
    if not outFl is None:
        outFl.close()

