import os, sys
sys.path.append('../acIndUtils')

import numpy as np

import acIndUtils, acIndAggregator

indicatorName = "BO6"
indicatorNcVarName = "PAR"

erddapFilePathTemplate = "/data/products/ADRIACLIM_RESM/ERDDAP/NEMO_NEW_WIND/{scenario}/3h/*/*/ADRIACLIM2_3h_{year}*_grid_T.nc"

modelName = 'NEMO'
variable = 'soshfldo'
parFactor = 0.4

title = "B06, Photosynthetic Active Radiation"
description ="""Mean monthly Photosynthetic Active Radiation (W/m2).
Obtained by multiplying the mean shortwave radiation by
a Fraction of Photosynthetically Available Radiation equal to 0.4.
"""
adriaclim_dataset = "indicator"
adriaclim_model = "NEMO"
adriaclim_timeperiod = "monthly"
adriaclim_type = "timeseries"
adriaclim_scale = "adriatic"
version = 0.0
units = "W/m2"


baselineScenarioName = "historical"
baselineYears = range(1992, 2012)
#baselineYears = range(1992, 1995)
projectnScenarioName = "projection"
projectnYears = range(2031, 2051)
#projectnYears = range(2022, 2025)

outDir = indicatorName + '_indicator'
os.system(f'mkdir -p {outDir}')




def aggregatorComputeMeanPAR(dts, vrs, outVarName, outFl):
    meanVr = np.mean(vrs, 0)*parFactor
    vrs_ = {outVarName: np.expand_dims(meanVr, 0)}
    outFl.writeVariables([dts[0]], **vrs_)




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
                          xVarName = "lon", yVarName = "lat", tVarName = "time_counter")
baselineNcFileSpec = acIndUtils.acNcFileSpec(
                          ncFileName = outNcFlPath, varName = indicatorNcVarName,
                          xVarName = "lon", yVarName = "lat", tVarName = "time_counter")
inputFiles = acIndAggregator.getFiles(erddapFilePathTemplate, 
                                      baselineScenarioName,
                                      baselineYears)
#acIndAggregator.collectMonthlyData2D(inputNcFileSpec, baselineNcFileSpec, 
#                                   aggregator = aggregatorComputeMeanPAR,
#                                   inputFiles = inputFiles) 
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
                          xVarName = "lon", yVarName = "lat", tVarName = "time_counter")
projectionNcFileSpec = acIndUtils.acNcFileSpec(
                          ncFileName = outNcFlPath, varName = indicatorNcVarName,
                          xVarName = "lon", yVarName = "lat", tVarName = "time_counter")
inputFiles = acIndAggregator.getFiles(erddapFilePathTemplate, 
                                      projectnScenarioName,
                                      projectnYears)
#acIndAggregator.collectMonthlyData2D(inputNcFileSpec, projectionNcFileSpec, 
#                                   aggregator = aggregatorComputeMeanPAR,
#                                   inputFiles = inputFiles) 
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
acIndUtils.addMetadata(diffNcFileSpec.ncFileName,
                       diffNcFileSpec.varName,
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

description +=\
"""
Trend computed using the Thiel/Sen slope approach.
"""

print("computing the trend for historical")
units = "W/(m2*year)"
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
acIndUtils.addMetadata(trendFilePath,
                       annualMeanFileSpec.varName,
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
os.system(f"rm -rf {tmpOutDir}")



