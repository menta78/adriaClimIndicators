import glob
import netCDF4
import numpy as np
import xarray as xr

from acIndUtils import acIndUtils


def collectMonthlyHsData(inputNcFileSpec, outputNcFileSpec):
   #here ncFileName is assumed to be a wildcard pattern
    fls = glob.glob(inputNcFileSpec.ncFileName)
    fls.sort()
    global outFl, actDt
    outFl = None

    moderSeaThrshld = 1.25
    roughSeaThrshld = 2.5
    varNames = [inputNcFileSpec.varName, 
                "moderSeaCount", 
                "roughSeaCount"]
    actDt = None

    def getHsByMonth():
        global outFl, actDt
        hss = []
        dts = []
        for flpth in fls:
            inFl = netCDF4.Dataset(flpth)
            xx = inFl.variables[inputNcFileSpec.xVarName]
            yy = inFl.variables[inputNcFileSpec.yVarName]
            tm = inFl.variables[inputNcFileSpec.tVarName]
            hs = inFl.variables[inputNcFileSpec.varName]
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
                    hss.append(hs[idt,...])
                    dts.append(dt)
                else:
                    yield dts, np.array(hss)
                    actDt = dt
                    print(f"    elaborating {actDt}")
                    hss = []
                    dts = []

    def processMonthly(dts, hss):
        meanHs = np.mean(hss, 0)
        meanHs[meanHs < 0] = np.nan

        actDay = dts[0]
        moderDt = np.zeros([hss.shape[1], hss.shape[2]])
        roughDt = np.zeros([hss.shape[1], hss.shape[2]])
        moder = [moderDt]
        rough = [roughDt]
        for dt, hs in zip(dts, hss):
            if dt.day != actDay.day:
                actDay = dt
                moderDt = np.zeros([hss.shape[1], hss.shape[2]])
                roughDt = np.zeros([hss.shape[1], hss.shape[2]])
                moder.append(moderDt)
                rough.append(roughDt)            
            cnd = moderDt == 0
            moderDt[cnd] = (hs > moderSeaThrshld)[cnd]
            cnd = roughDt == 0
            roughDt[cnd] = (hs > roughSeaThrshld)[cnd]
        nModer = np.sum(np.array(moder), 0)
        nRough = np.sum(np.array(rough), 0)

        vrs = {outputNcFileSpec.varName: np.expand_dims(meanHs, 0),
                "moderSeaCount": np.expand_dims(nModer, 0),
                "roughSeaCount": np.expand_dims(nRough, 0)
                }
        outFl.writeVariables([dts[0]], **vrs)

    for dt, hss in getHsByMonth():
        processMonthly(dt, hss)


def collectMonthlyTmData(inputNcFileSpec, outputNcFileSpec):
   #here ncFileName is assumed to be a wildcard pattern
    fls = glob.glob(inputNcFileSpec.ncFileName)
    fls.sort()
    global outFl, actDt
    outFl = None

    varNames = [inputNcFileSpec.varName] 
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

    def processMonthly(dts, vrs):
        meanVr = np.mean(vrs, 0)
        meanVr[meanVr < 0] = np.nan

        vrs_ = {outputNcFileSpec.varName: np.expand_dims(meanVr, 0)}
        outFl.writeVariables([dts[0]], **vrs_)

    for dt, vrs in getByMonth():
        processMonthly(dt, vrs)



def aggregateBySeason(inputFileSpec, hsSeasonalFlPath, roughtSeaFlPath):
    ds = xr.open_dataset(inputFileSpec.ncFileName)

    dsHs = ds[inputFileSpec.varName].groupby("f{inputFileSpec.tVarName}.season").mean()
    dsHs.to_netcdf(hsFlPath)
    
    dsRough = ds["moderSeaCount", "roughSeaCount"].groupby("f{inputFileSpec.tVarName}.season").sum()
    dsRough.to_netcdf(roughFlPath)


        
def testCollectMonthlyHsData():
    import pdb; pdb.set_trace()
    inputNcFilePath = "/home/lmentaschi/DATA/cmemsWavesReanalysisAdriaclim/Hs/*_hourly_reanalsis_significant_wave_height_AdriaticSea.nc"
    inputNcFileSpec = acIndUtils.acNcFileSpec(
            ncFileName=inputNcFilePath, 
            varName="VHM0", 
            xVarName="longitude", 
            yVarName="latitude", 
            tVarName="time" )
    outputNcFileSpec = acIndUtils.acCloneFileSpec(inputNcFileSpec, ncFileName="swhMonthlyData.nc")
    collectMonthlyHsData(inputNcFileSpec, outputNcFileSpec)



        
def testCollectMonthlyTmData():
    import pdb; pdb.set_trace()
    inputNcFilePath = "/home/lmentaschi/DATA/cmemsWavesReanalysisAdriaclim/Tm/*_cmems_hourly_reanalysis_waves_vtm10_AdriaticSea.nc"
    inputNcFileSpec = acIndUtils.acNcFileSpec(
            ncFileName=inputNcFilePath, 
            varName="VTM10", 
            xVarName="longitude", 
            yVarName="latitude", 
            tVarName="time" )
    outputNcFileSpec = acIndUtils.acCloneFileSpec(inputNcFileSpec, ncFileName="tmMonthlyData.nc")
    collectMonthlyTmData(inputNcFileSpec, outputNcFileSpec)



if __name__ == "__main__":
    testCollectMonthlyHsData()
   #testCollectMonthlyTmData()




