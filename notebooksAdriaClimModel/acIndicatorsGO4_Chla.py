import os, sys
sys.path.append('../acIndUtils')

import numpy as np

import acIndUtils, acIndAggregator

indicatorName = "GO4"
indicatorNcVarName = "Chla"

erddapFilePathTemplate = "/data/products/ADRIACLIM_RESM/ERDDAP/BFM/{scenario}/BFM_5d_{year}*_grid_bfm.nc"
erddapFilePathTemplate = "/work/opa/lm09621/data/adriaClim/projectionOutput1/output/{scenario}/BFM_5d_{year}*_grid_bfm.nc"

modelName = 'BFM'
variable = 'Chla'

title = "G04, chlorophyll-a"
description = "Mean monthly concentration of chlorophyll-a, in mg/m3"
adriaclim_dataset = "indicator"
adriaclim_model = "BFM"
adriaclim_timeperiod = "monthly"
adriaclim_type = "timeseries"
adriaclim_scale = "adriatic"
version = 0.0
units = "mg/m3"


baselineScenarioName = "historical"
baselineYears = range(1992, 2012)
#baselineYears = range(1992, 1995)
projectnScenarioName = "projection"
projectnDirectory = "rcp85"
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
                          xVarName = "lon", yVarName = "lat", zVarName = "deptht", tVarName = "time_counter")
baselineNcFileSpec = acIndUtils.acNcFileSpec(
                          ncFileName = outNcFlPath, varName = indicatorNcVarName,
                          xVarName = "lon", yVarName = "lat", zVarName = "deptht", tVarName = "time_counter")
inputFiles = acIndAggregator.getFiles(erddapFilePathTemplate, 
                                      baselineScenarioName,
                                      baselineYears)
acIndAggregator.collectMonthlyData(inputNcFileSpec, baselineNcFileSpec, 
                                   aggregator = acIndAggregator.meanAggregator,
                                   inputFiles = inputFiles,
                                   fill_value = np.nan) 
adriaclim_scenario = "hist"
adriaclim_type = "timeseries"
_title = title + ", " + adriaclim_scenario
acIndUtils.addMetadata(baselineNcFileSpec.ncFileName,
                       baselineNcFileSpec.varName,
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
                          xVarName = "lon", yVarName = "lat", zVarName = "deptht", tVarName = "time_counter")
projectionNcFileSpec = acIndUtils.acNcFileSpec(
                          ncFileName = outNcFlPath, varName = indicatorNcVarName,
                          xVarName = "lon", yVarName = "lat", zVarName = "deptht", tVarName = "time_counter")
inputFiles = acIndAggregator.getFiles(erddapFilePathTemplate, 
                                      projectnDirectory,
                                      projectnYears)
acIndAggregator.collectMonthlyData(inputNcFileSpec, projectionNcFileSpec, 
                                   aggregator = acIndAggregator.meanAggregator,
                                   inputFiles = inputFiles, 
                                   fill_value = np.nan) 
adriaclim_scenario = "proj"
adriaclim_type = "timeseries"
_title = title + ", " + adriaclim_scenario
acIndUtils.addMetadata(projectionNcFileSpec.ncFileName,
                       projectionNcFileSpec.varName,
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

description += "Trend computed using the Thiel/Sen slope approach."

print("computing the trend for historical")
units = "mg/(m3*year)"
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
acIndUtils.acComputeSenSlope3DMap(annualMeanFileSpec, trendFilePath)
adriaclim_scenario = "hist"
adriaclim_type = "trend"
_title = title + ", trend, " + adriaclim_scenario
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
acIndUtils.acComputeSenSlope3DMap(annualMeanFileSpec, trendFilePath)
adriaclim_scenario = "proj"
adriaclim_type = "trend"
_title = title + ", trend, " + adriaclim_scenario
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
os.system(f"rm -rf {tmpOutDir}")



