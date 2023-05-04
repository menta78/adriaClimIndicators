import glob
import netCDF4
import numpy as np
import xarray as xr

import acIndUtils


roughSeaThrshld = 2.5


def countRoughSeaDays(dts, hss, outVarName, outFl):
    """
    countRoughSeaDays, rough-sea detecting aggregator, to be used
    with the functions acIndAggregator.collectMonthlyData
    """
    meanHs = np.mean(hss, 0)
    meanHs[meanHs < 0] = np.nan

    actDay = dts[0]
    roughDt = np.zeros([hss.shape[1], hss.shape[2]])
    rough = [roughDt]
    for dt, hs in zip(dts, hss):
        if dt.day != actDay.day:
            actDay = dt
            roughDt = np.zeros([hss.shape[1], hss.shape[2]])
            rough.append(roughDt)            
        cnd = roughDt == 0
        roughDt[cnd] = (hs > roughSeaThrshld)[cnd]
    nRough = np.sum(np.array(rough), 0)

    vrs = {outVarName: np.expand_dims(nRough, 0)}
    outFl.writeVariables([dts[0]], **vrs)




