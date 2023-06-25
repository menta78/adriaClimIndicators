import os, sys
sys.path.append('../acIndUtils')

import numpy as np

import acIndUtils, acIndAggregator

indicatorName = "BO11"
indicatorNcVarName = "TM"

erddapFilePathTemplate = "/data/inputs/metocean/AdriaClim/UniBo/WAVES_SINCE_1993/WAVES_VTM10/*_cmems_hourly_reanalysis_waves_vtm10_AdriaticSea.nc"

modelName = 'CMEMS'
variable = 'VTM10'

title = "BO11, Mean Period tm01 (s)"
description ="""Mean monthly wave period (s)."""
adriaclim_dataset = "indicator"
adriaclim_model = modelName
adriaclim_timeperiod = "monthly"
adriaclim_type = "timeseries"
adriaclim_scale = "adriatic"
version = 0.0
units = "s"


baselineScenarioName = "historical"
baselineYears = range(1992, 2012)

outDir = indicatorName + '_indicator'
os.system(f'mkdir -p {outDir}')



print("elaborating the historical data")
outNcFlName = acIndUtils.getNcFileName(source = modelName,
                                       variable = indicatorName,
                                       elaboration_type = "mean",
                                       scenario = "hist",
                                       time_agg = "monthly",
                                       year_start = baselineYears[0],
                                       year_end = baselineYears[-1])
outNcFlPath = os.path.join(outDir, outNcFlName)
inputNcFileSpec = acIndUtils.acNcFileSpec(
                          ncFileName = erddapFilePathTemplate, varName = variable,
                          xVarName = "longitude", yVarName = "latitude", tVarName = "time")
baselineNcFileSpec = acIndUtils.acNcFileSpec(
                          ncFileName = outNcFlPath, varName = indicatorNcVarName,
                          xVarName = "longitude", yVarName = "latitude", tVarName = "time")
acIndAggregator.collectMonthlyData(inputNcFileSpec, baselineNcFileSpec, 
                                   aggregator = acIndAggregator.meanAggregator,
                                   fill_value = np.nan, 
                                   lastYear = baselineYears[-1]) 
adriaclim_scenario = "hist"
adriaclim_type = "timeseries"
acIndUtils.addMetadata(baselineNcFileSpec.ncFileName,
                       baselineNcFileSpec.varName,
                       title = title,
                       description = description,
                       adriaclim_dataset = adriaclim_dataset,
                       adriaclim_model = adriaclim_model,
                       adriaclim_scale = adriaclim_scale,
                       adriaclim_timeperiod = adriaclim_timeperiod,
                       adriaclim_type = adriaclim_type,
                       adriaclim_scenario = adriaclim_scenario,
                       version = version,
                       units = units
                       )



tmpOutDir = os.path.join(outDir, 'tmp')
os.system(f'mkdir -p {tmpOutDir}')

description += " Trend computed using the Thiel/Sen slope approach."

print("computing the trend for historical")
units = "s/year"
annualMeanFile = os.path.join(tmpOutDir, '_annualmean.nc')
annualMeanFileSpec = acIndUtils.acCloneFileSpec(baselineNcFileSpec,
           ncFileName = annualMeanFile)
trendFileName = acIndUtils.getNcFileName(source = modelName,
                                       variable = indicatorName,
                                       elaboration_type = "trend",
                                       scenario = "hist",
                                       time_agg = "scenario",
                                       year_start = baselineYears[0],
                                       year_end = baselineYears[-1])
trendFilePath = os.path.join(outDir, trendFileName)
acIndUtils.acGenerateAnnualMeanMaps(baselineNcFileSpec, annualMeanFile)
acIndUtils.acComputeSenSlope2DMap(annualMeanFileSpec, trendFilePath)
adriaclim_scenario = "hist"
adriaclim_type = "trend"
_title = title + ". trend (s/y)"
acIndUtils.addMetadata(trendFilePath,
                       annualMeanFileSpec.varName,
                       title = _title,
                       description = description,
                       adriaclim_dataset = adriaclim_dataset,
                       adriaclim_model = adriaclim_model,
                       adriaclim_scale = adriaclim_scale,
                       adriaclim_timeperiod = adriaclim_timeperiod,
                       adriaclim_type = adriaclim_type,
                       adriaclim_scenario = adriaclim_scenario,
                       version = version,
                       units = units
                       )
os.system(f"rm {tmpOutDir}/*")





# graphs on baseline
from matplotlib import pyplot as plt
import acIndWavesGraphicUtils

tmpAnnualNcFileSpec = acIndUtils.acCloneFileSpec(baselineNcFileSpec, ncFileName="tmpAnnual.nc")
tmpWinterNcFileSpec = acIndUtils.acCloneFileSpec(baselineNcFileSpec, ncFileName="tmpWinter.nc")
tmpSummerNcFileSpec = acIndUtils.acCloneFileSpec(baselineNcFileSpec, ncFileName="tmpSummer.nc")
acIndUtils.acGenerateAnnualMeanMaps(baselineNcFileSpec, tmpAnnualNcFileSpec.ncFileName)
acIndUtils.acGenerateSeasonalWinter(baselineNcFileSpec, tmpWinterNcFileSpec.ncFileName)
acIndUtils.acGenerateSeasonalSummer(baselineNcFileSpec, tmpSummerNcFileSpec.ncFileName)
pltRange = [0, 5]
annualPlot = acIndWavesGraphicUtils.plotMeanMap(tmpAnnualNcFileSpec, "Mean Annual WTM (s)", pltRange)
plt.savefig(f'annualMap{indicatorName}.png', dpi=200)
winterPlot = acIndWavesGraphicUtils.plotMeanMap(tmpWinterNcFileSpec, "Mean Winter WTM (s)", pltRange)
plt.savefig(f'winterMap{indicatorName}.png', dpi=200)
summerPlot = acIndWavesGraphicUtils.plotMeanMap(tmpSummerNcFileSpec, "Mean Summer WTM (s)", pltRange)
plt.savefig(f'summerMap{indicatorName}.png', dpi=200)
os.system("rm tmp*.nc")


