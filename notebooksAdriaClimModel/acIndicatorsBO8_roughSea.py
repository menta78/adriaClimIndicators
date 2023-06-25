import os, sys
sys.path.append('../acIndUtils')

import numpy as np

import acIndUtils, acIndAggregator, acIndWavesUtils

indicatorName = "BO8"
indicatorNcVarName = "SWH"

erddapFilePathTemplate = "/data/products/ADRIACLIM_RESM/WW3/NEWWRF_WIND/{scenario}/3h/{year}/*/ww3.*.nc"
#erddapFilePathTemplate = "/data/products/ADRIACLIM_RESM/WW3/COSMO_WIND/{scenario}/3h/{year}/*/ww3.*.nc"

modelName = 'WW3'
variable = 'hs'

title = "BO8, Rough Sea Days"
description = "Count of days when rough-sea conditions (Hs>2.5 m) are met."
adriaclim_dataset = "indicator"
adriaclim_model = modelName
adriaclim_timeperiod = "monthly"
adriaclim_type = "timeseries"
adriaclim_scale = "adriatic"
version = 0.0
units = "n days"


baselineScenarioName = "historical"
baselineYears = range(1992, 2012)
#baselineYears = range(1992, 1995)
projectnScenarioName = "projection"
projectnYears = range(2031, 2051)
#projectnYears = range(2022, 2025)

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
inputFiles = acIndAggregator.getFiles(erddapFilePathTemplate, 
                                      baselineScenarioName,
                                      baselineYears)
acIndAggregator.collectMonthlyData(inputNcFileSpec, baselineNcFileSpec, 
                                   aggregator = acIndWavesUtils.countRoughSeaDays,
                                   inputFiles = inputFiles,
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









print("elaborating the projection data")
outNcFlName = acIndUtils.getNcFileName(source = modelName,
                                       variable = indicatorName,
                                       elaboration_type = "mean",
                                       scenario = "proj",
                                       time_agg = "monthly",
                                       year_start = projectnYears[0],
                                       year_end = projectnYears[-1])
outNcFlPath = os.path.join(outDir, outNcFlName)
inputNcFileSpec = acIndUtils.acNcFileSpec(
                          ncFileName = erddapFilePathTemplate, varName = variable,
                          xVarName = "longitude", yVarName = "latitude", tVarName = "time")
projectionNcFileSpec = acIndUtils.acNcFileSpec(
                          ncFileName = outNcFlPath, varName = indicatorNcVarName,
                          xVarName = "longitude", yVarName = "latitude", tVarName = "time")
#inputFiles = acIndAggregator.getFiles(erddapFilePathTemplate, 
flpthTemporary = "/data/products/ADRIACLIM_RESM/WW3/NEWWRF_WIND/projection/ww3.{year}*.nc"
#flpthTemporary = "/data/products/ADRIACLIM_RESM/WW3/COSMO_WIND/projection/ww3.{year}*.nc"
inputFiles = acIndAggregator.getFiles(flpthTemporary, 
                                      projectnScenarioName,
                                      projectnYears)
acIndAggregator.collectMonthlyData(inputNcFileSpec, projectionNcFileSpec, 
                                   aggregator = acIndWavesUtils.countRoughSeaDays,
                                   inputFiles = inputFiles, 
                                   fill_value = np.nan,
                                   lastYear = projectnYears[-1]) 
adriaclim_scenario = "proj"
adriaclim_type = "timeseries"
acIndUtils.addMetadata(projectionNcFileSpec.ncFileName,
                       projectionNcFileSpec.varName,
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




print("elaborating the difference projection-baseline")
outNcFlName = acIndUtils.getNcFileName(source = modelName,
                                       variable = indicatorName,
                                       elaboration_type = "mean",
                                       scenario = "difference",
                                       time_agg = "scenario",
                                       year_start = projectnYears[0],
                                       year_end = projectnYears[-1])
outNcFlPath = os.path.join(outDir, outNcFlName)
diffNcFileSpec = acIndUtils.acCloneFileSpec(projectionNcFileSpec, ncFileName=outNcFlPath)
acIndUtils.generateDifferencDataset(projectionNcFileSpec, 
                                    baselineNcFileSpec, 
                                    diffNcFileSpec)
adriaclim_scenario = "anomaly"
adriaclim_type = "anomaly"
_title = title + ", difference"
acIndUtils.addMetadata(diffNcFileSpec.ncFileName,
                       diffNcFileSpec.varName,
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



tmpOutDir = os.path.join(outDir, 'tmp')
os.system(f'mkdir -p {tmpOutDir}')

description += " Trend computed using the Thiel/Sen slope approach."

print("computing the trend for historical")
units = "n days/year"
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
_title = title + ", trend"
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


print("computing the trend for projection")
annualMeanFile = os.path.join(tmpOutDir, '_annualmean.nc')
annualMeanFileSpec = acIndUtils.acCloneFileSpec(projectionNcFileSpec,
           ncFileName = annualMeanFile)
trendFileName = acIndUtils.getNcFileName(source = modelName,
                                       variable = indicatorName,
                                       elaboration_type = "trend",
                                       scenario = "proj",
                                       time_agg = "scenario",
                                       year_start = projectnYears[0],
                                       year_end = projectnYears[-1])
trendFilePath = os.path.join(outDir, trendFileName)
acIndUtils.acGenerateAnnualMeanMaps(projectionNcFileSpec, annualMeanFile)
acIndUtils.acComputeSenSlope2DMap(annualMeanFileSpec, trendFilePath)
adriaclim_scenario = "proj"
adriaclim_type = "trend"
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





# graphs on baseline
from matplotlib import pyplot as plt
import acIndWavesGraphicUtils

tmpAnnualNcFileSpec = acIndUtils.acCloneFileSpec(baselineNcFileSpec, ncFileName=os.path.join(tmpOutDir, "tmpAnnual.nc"))
tmpWinterNcFileSpec = acIndUtils.acCloneFileSpec(baselineNcFileSpec, ncFileName=os.path.join(tmpOutDir, "tmpWinter.nc"))
tmpSummerNcFileSpec = acIndUtils.acCloneFileSpec(baselineNcFileSpec, ncFileName=os.path.join(tmpOutDir, "tmpSummer.nc"))
acIndUtils.acGenerateAnnualMeanMaps(baselineNcFileSpec, tmpAnnualNcFileSpec.ncFileName)
acIndUtils.acGenerateSeasonalWinter(baselineNcFileSpec, tmpWinterNcFileSpec.ncFileName)
acIndUtils.acGenerateSeasonalSummer(baselineNcFileSpec, tmpSummerNcFileSpec.ncFileName)
pltRange = [0, 3]
annualPlot = acIndWavesGraphicUtils.plotMeanMap(tmpAnnualNcFileSpec, "Mean Monthly count of rough-sea days", pltRange)
plt.savefig(f'annualMap{indicatorName}.png', dpi=200)
winterPlot = acIndWavesGraphicUtils.plotMeanMap(tmpWinterNcFileSpec, "Mean Winter Monthly count of rough-sea days", pltRange)
plt.savefig(f'winterMap{indicatorName}.png', dpi=200)
summerPlot = acIndWavesGraphicUtils.plotMeanMap(tmpSummerNcFileSpec, "Mean Summer Monthly count of rough-sea days", pltRange)
plt.savefig(f'summerMap{indicatorName}.png', dpi=200)



os.system(f"rm -rf {tmpOutDir}")
