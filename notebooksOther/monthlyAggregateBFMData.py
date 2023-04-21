import os, sys
sys.path.append('../acIndUtils')

import numpy as np

import acIndUtils, acIndAggregator

cdo = "/g100/home/userexternal/lmentasc/usr/Miniconda3/bin/cdo"
nccopy = "/g100/home/userexternal/lmentasc/usr/Miniconda3/bin/nccopy"

outdir = "/gss/gss_work/DRES_uBOC2/adriaClim/bfm/output/historical/test1997-1999/"

bfmDataFlPattern = os.path.join(outdir, "BFM_5d_*.nc")
maskFilePath = "/g100/home/userexternal/lmentasc/src/git/projects/AdriaClim/configurationProjCineca/scenarios/mask_NEMO_AdriaClim_compressed.nc"

os.system(f"cd {outdir}; rm BFM_1monclim*.nc BFM_monthly*.nc")

inputNcFileSpec = acIndUtils.acNcFileSpec(
                               ncFileName = bfmDataFlPattern,
                               varName = "Chla",
                               xVarName = "nav_lon",
                               yVarName = "nav_lat",
                               zVarName = "deptht",
                               tVarName = "time_counter"
                               )

outputNcFileSpec = acIndUtils.acNcFileSpec(
                               ncFileName = "",
                               varName = "",
                               xVarName = "x",
                               yVarName = "y",
                               zVarName = "deptht",
                               tVarName = "time_counter"
                               )

coordsNcFileSpec = acIndUtils.acNcFileSpec(
                               ncFileName = maskFilePath,
                               varName = "NONE",
                               xVarName = "nav_lon",
                               yVarName = "nav_lat",
                               zVarName = "nav_lev",
                               tVarName = "time_counter"
                               )


varName = "Chla"
print("")
print(f"elaborating {varName}")
outFl = os.path.join(outdir, f"BFM_monthly_{varName}.nc")
inputNcFileSpec.varName = varName
outputNcFileSpec.varName = varName
outputNcFileSpec.ncFileName = outFl
acIndAggregator.collectMonthlyData(inputNcFileSpec,
                                   outputNcFileSpec,
                                   coordsNcFileSpec = coordsNcFileSpec,
                                   fill_value = 0)


varName = "O2o"
print("")
print(f"elaborating {varName}")
outFl = os.path.join(outdir, f"BFM_monthly_{varName}.nc")
inputNcFileSpec.varName = varName
outputNcFileSpec.varName = varName
outputNcFileSpec.ncFileName = outFl
acIndAggregator.collectMonthlyData(inputNcFileSpec,
                                   outputNcFileSpec,
                                   coordsNcFileSpec = coordsNcFileSpec,
                                   fill_value = 0)


varName = "N1p"
print("")
print(f"elaborating {varName}")
outFl = os.path.join(outdir, f"BFM_monthly_{varName}.nc")
inputNcFileSpec.varName = varName
outputNcFileSpec.varName = varName
outputNcFileSpec.ncFileName = outFl
acIndAggregator.collectMonthlyData(inputNcFileSpec,
                                   outputNcFileSpec,
                                   coordsNcFileSpec = coordsNcFileSpec,
                                   fill_value = 0)


varName = "N3n"
print("")
print(f"elaborating {varName}")
outFl = os.path.join(outdir, f"BFM_monthly_{varName}.nc")
inputNcFileSpec.varName = varName
outputNcFileSpec.varName = varName
outputNcFileSpec.ncFileName = outFl
acIndAggregator.collectMonthlyData(inputNcFileSpec,
                                   outputNcFileSpec,
                                   coordsNcFileSpec = coordsNcFileSpec,
                                   fill_value = 0)


varName = "N5s"
print("")
print(f"elaborating {varName}")
outFl = os.path.join(outdir, f"BFM_monthly_{varName}.nc")
inputNcFileSpec.varName = varName
outputNcFileSpec.varName = varName
outputNcFileSpec.ncFileName = outFl
acIndAggregator.collectMonthlyData(inputNcFileSpec,
                                   outputNcFileSpec,
                                   coordsNcFileSpec = coordsNcFileSpec,
                                   fill_value = 0)


curdir = os.getcwd()
os.chdir(outdir)
print("merging ...")
os.system(f"{cdo} merge BFM_monthly_*.nc BFM_monthly.nc")
outputNcFileSpec.ncFileName = "BFM_monthly.nc"
acIndUtils.addNavlonNavlatFields(outputNcFileSpec)
print("creating monthly climatology ...")
os.system(f"{cdo} ymonmean BFM_monthly.nc BFM_1monclim_uncompressed.nc")
print("compressing ...")
os.system(f"{nccopy} -d9 BFM_1monclim_uncompressed.nc BFM_1monclim.nc")
os.chdir(curdir)


