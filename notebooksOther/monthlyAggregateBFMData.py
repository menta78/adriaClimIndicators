import os, sys
sys.path.append('../acIndUtils')

import numpy as np

import acIndUtils, acIndAggregator


bfmDataFlPattern = "/gss/gss_work/DRES_uBOC2/adriaClim/bfm/output/historical/test1997-1999/BFM_5d_*.nc"
outFl = "/gss/gss_work/DRES_uBOC2/adriaClim/bfm/output/historical/test1997-1999/BFM_monthly.nc"
maskFilePath = "/g100/home/userexternal/lmentasc/src/git/projects/AdriaClim/configurationProjCineca/scenarios/mask_NEMO_AdriaClim_compressed.nc"

inputNcFileSpec = acIndUtils.acNcFileSpec(
                               ncFileName = bfmDataFlPattern,
                               varName = "Chla",
                               xVarName = "nav_lon",
                               yVarName = "nav_lat",
                               zVarName = "deptht",
                               tVarName = "time_counter"
                               )

outputNcFileSpec = acIndUtils.acNcFileSpec(
                               ncFileName = outFl,
                               varName = "Chla",
                               xVarName = "lon",
                               yVarName = "lat",
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

import pdb; pdb.set_trace()
acIndAggregator.collectMonthlyData(inputNcFileSpec,
                                   outputNcFileSpec,
                                   coordsNcFileSpec = coordsNcFileSpec,
                                   fill_value = 0)

