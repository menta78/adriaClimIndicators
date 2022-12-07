from datetime import datetime

import xarray as xr
import pandas as pd
import numpy as np
from dateutil.parser import parse 
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import rcParams
import csv
import netCDF4
from scipy import stats

import cartopy.feature as cfeature
import cartopy.crs as ccrs
from geocat.viz import util as gvutil   # python -m pip install geocat.viz

from acIndUtils import acIndUtils
from acIndUtils import acIndGrahUtils as gutl



def acPlotTimeSeries(dailySSTCsv, plotTitle):
    """
    Plot of the time series of SST and of its trend
    input: dailySSTCsv, csv file path of the daily values of SST
    """
    
    dateColId = 0
    sstColId = 1

 #loading and grouping by year/month
    ds = pd.read_csv(dailySSTCsv)
    ds.iloc[:,dateColId] = pd.to_datetime(ds.iloc[:,dateColId])
    dtCol = ds.iloc[:,dateColId]
    sstCol = ds.iloc[:,sstColId]
    mts = ds.groupby([(dtCol.dt.year), (dtCol.dt.month)]).mean()
    
    ssnl = ds.groupby(dtCol.dt.month).mean()
    ssnlvl = ssnl.values
    nmnt = len(mts)
    ssnltl = np.array([ssnlvl[im[1]-1] for im in mts.index]).reshape([nmnt,1])
    anmlMon = mts - ssnltl

 #getting the annual means
    ymean = ds.groupby(dtCol.dt.year).mean() 
    anmlYr = ymean - ymean.mean()

    dtmAnmlMon = [datetime(dt[0], dt[1], 1) for dt in anmlMon.index.values]
    dtmAnmlYr = [datetime(dt, 7, 1) for dt in anmlYr.index.values]

 #getting the trend slope and p-value
    medslope, medintercept, lo_slope, up_slope, pvalue = acIndUtils.acComputeAnnualTheilSenFitFromDailyFile(dailySSTCsv)
    confInt = (up_slope - lo_slope)/2

    f = plt.figure(figsize=[15, 7])
    plt.plot(dtmAnmlMon, anmlMon, color="teal", linewidth=1, label="Monthly anomaly")
    plt.plot(dtmAnmlYr, anmlYr, marker='o', markerfacecolor="firebrick", markeredgecolor='k', linewidth=0, label="Annual anomaly")
    yrii = np.arange(len(dtmAnmlYr))
    trndln = yrii*medslope
    trndln = trndln - np.mean(trndln)
    plt.plot(dtmAnmlYr, trndln, linewidth=.5, color="k", label=f"Trend = {medslope:2.3f}±{confInt:2.3f} K/year")

    plt.grid("on")

    plt.legend(fontsize=gutl.fontSizeLegend, loc="upper left", frameon=False)
    plt.xticks(fontsize=gutl.fontSizeTickLabels)
    plt.yticks(fontsize=gutl.fontSizeTickLabels)

    plt.xlabel("Year", fontsize=gutl.fontSizeAxisLabel)
    plt.ylabel(plotTitle, fontsize=gutl.fontSizeAxisLabel)

    plt.title(plotTitle, fontsize=gutl.fontSizeTitle)

    plt.tight_layout()

    return f



def plotMeanMap(meanNcFileSpec, plotTitle, valRange):
    """
    plots the map of the mean field specified by in meanNcFileSpec.
    input parameters:
      - meanNcFileSpec: definition of the input file
      - plotTitle: title to be given to the figure
    """
    t = xr.open_dataset(meanNcFileSpec.ncFileName)
    temp = t[meanNcFileSpec.varName][:,:,:]
    temp_av= np.mean(temp[:],axis = 0)
    thetao_area_1 = temp_av.values

    gs = gridspec.GridSpec(ncols=3, nrows=1, width_ratios=[1, .03, .03])
    fig = plt.figure(figsize=(17, 12))

    projection = ccrs.PlateCarree()
    ax = fig.add_subplot(gs[0, 0], projection=projection)
    #  coastlines, and adding features
    ax.coastlines(linewidths=1, alpha=0.9999, resolution="10m")
    
    # Import an NCL colormap
   #newcmp = gvcmaps.NCV_jet
    newcmp = "jet"
    
    vmin = valRange[0]
   #vmax = np.nanpercentile(temp_av, 99.99)
    vmax = valRange[1]

    # Contourf-plot data: external contour
    heatmap = temp_av.plot.contourf(ax=ax,
                              transform=projection,
                              levels=60,
                              vmin=vmin,
                              vmax=vmax,
                              cmap=newcmp,
                              add_colorbar=False)
    
    lines=temp_av.plot.contour(ax=ax,alpha=1,linewidths=0.5,colors = 'k',linestyles='None',levels=54)
    
    gvutil.add_major_minor_ticks(ax, y_minor_per_major=1, labelsize=15)
    
    gvutil.set_axes_limits_and_ticks(ax,
                                     xlim=(12, 22),
                                     ylim=(37, 46),
                                     xticks=np.linspace(12, 22, 6),
                                     yticks=np.linspace(37, 46, 10))
    
    cax = fig.add_subplot(gs[0, 2])
    cbar_ticks=np.arange(vmin, vmax, .1)
    cbar = plt.colorbar(heatmap,
                        orientation='vertical',
                        ticks=cbar_ticks,
                        cax=cax)
    cax.tick_params(labelsize=gutl.fontSizeTickLabels)
    
    plt.axes(ax)
    ax.set_extent([12, 20.2, 39.7, 46])
    gvutil.set_titles_and_labels(
        ax,
        maintitle=plotTitle,
        maintitlefontsize=16,
        xlabel="",
        ylabel="")

    ax.xlabel_style = {'size': 20, 'color': 'k'}
    ax.ylabel_style = {'size': 20, 'color': 'k'}




def plotTrendMap(trendNcFileSpec, plotTitle):
    """
    plots a map of trend loaded from the file/field specified by in meanNcFileSpec.
    input parameters:
      - trendNcFileSpec: definition of the input file
    """
    t = xr.open_dataset(trendNcFileSpec.ncFileName)

    thetao_area_1 = t[trendNcFileSpec.varName].values

    gs = gridspec.GridSpec(ncols=3, nrows=1, width_ratios=[1, .03, .03])
    fig = plt.figure(figsize=(17, 12))

    projection = ccrs.PlateCarree()
    ax = fig.add_subplot(gs[0, 0], projection=projection)
    ax.coastlines(linewidths=1,alpha=0.9999, resolution="10m")
    
    newcmp = "jet"
    vmin = np.nanpercentile(t[trendNcFileSpec.varName], .001)
    vmax = np.nanpercentile(t[trendNcFileSpec.varName], 99.999)
    vmax = np.max([np.abs(vmin), np.abs(vmax)])
    
    heatmap = t[trendNcFileSpec.varName].plot.contourf(ax=ax,
                              transform=projection,
                              levels=50,
                              vmin=-vmax,
                              vmax=vmax,
                              cmap=newcmp,
                              add_colorbar=False)
    
    lines=t[trendNcFileSpec.varName].plot.contour(ax=ax,alpha=1,linewidths=0.5,colors = 'k',linestyles='None',levels=50)
    gvutil.set_axes_limits_and_ticks(ax,
                                     xlim=(12, 22),
                                     ylim=(37, 46),
                                     xticks=np.linspace(12, 22, 6),
                                     yticks=np.linspace(37, 46, 10))
    
    gvutil.add_major_minor_ticks(ax, y_minor_per_major=1, labelsize=15)
    
    
    cax = fig.add_subplot(gs[0, 2])
    cbar_ticks=np.linspace(-vmax, vmax, 9)
    cbar = plt.colorbar(heatmap,
                        orientation='vertical',
                        ticks=cbar_ticks,
                        cax=cax)
    cax.tick_params(labelsize=gutl.fontSizeTickLabels)
    
    plt.axes(ax)
    ax.set_extent([12, 20.2, 39.7, 46])
    
    gvutil.set_titles_and_labels(
        ax,
        maintitle=plotTitle,
        maintitlefontsize=16,
        xlabel="",
        ylabel="")
    
    ax.xlabel_style = {'size': 20, 'color': 'k'}
    ax.ylabel_style = {'size': 20, 'color': 'k'}





