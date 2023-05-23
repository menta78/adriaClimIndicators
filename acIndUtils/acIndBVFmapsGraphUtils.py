from datetime import datetime

import xarray as xr
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose
from dateutil.parser import parse 
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import rcParams
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from cycler import cycler
import seaborn as sns
import csv
import netCDF4
from scipy import stats

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import cartopy.feature as cfeature
import cartopy.crs as ccrs
import geocat.datafiles as gdf
#from geocat.viz import cmaps as gvcmaps
import cmaps as gvcmaps
from geocat.viz import util as gvutil
from netcdf2csv import convert_file


from acIndUtils import acIndUtils
from acIndUtils import acIndGrahUtils as gutl

def acAnnualCyclePlot(dailySSTCsv,tocsv=False,csvpth=None):   

    """ Monthly TS Plot with percentiles 
    input: dailySSTCsv, csv file path of the daily values of SST
    """ 
    
    dateColId = 0
    sstColId = 1
        
    file2 = pd.read_csv(dailySSTCsv)
    file2.iloc[:,dateColId] = pd.to_datetime(file2.iloc[:,dateColId])
    dateCol = file2.iloc[:,dateColId]
    tCol = file2.iloc[:,sstColId]
    file2['Time_Series_from_1987_to_2019'] = [d.year for d in dateCol]
    file2['month'] = [d.strftime('%b') for d in dateCol]
    years = file2['Time_Series_from_1987_to_2019'].unique()

#    fig, axes = plt.subplots(1, figsize=(18,8), dpi= 100)
    fig, axes = plt.subplots(1, figsize=(20,12), dpi= 200)

    # Sorter for month
    sorter=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    # compute montlhy means and quantiles
    mean=file2.groupby("month").mean().sort_index().reset_index()
    minbvf=file2.groupby("month").quantile(0.0).sort_index().reset_index()
    per005=file2.groupby("month").quantile(0.05).sort_index().reset_index()
    quant1=file2.groupby("month").quantile(0.25).sort_index().reset_index()
    quant2=file2.groupby("month").quantile(0.5).sort_index().reset_index()
    quant3=file2.groupby("month").quantile(0.75).sort_index().reset_index()
    per095=file2.groupby("month").quantile(0.95).sort_index().reset_index()
    maxbvf=file2.groupby("month").quantile(1.0).sort_index().reset_index()

    # set month as index 
    mean=mean.set_index('month')
    minbvf=minbvf.set_index('month')
    per005=per005.set_index('month')
    quant1=quant1.set_index('month')
    quant2=quant2.set_index('month')
    quant3=quant3.set_index('month')
    per095=per095.set_index('month')
    maxbvf=maxbvf.set_index('month')

    # sort by month
    mean=mean.loc[sorter]
    minbvf=minbvf.loc[sorter]
    per005=per005.loc[sorter]
    quant1=quant1.loc[sorter]
    quant2=quant2.loc[sorter]
    quant3=quant3.loc[sorter]
    per095=per095.loc[sorter]
    maxbvf=maxbvf.loc[sorter]

    # mean quantiles values
    Mmean=mean.MaxBV.mean()
    Mminbvf=minbvf.MaxBV.mean()
    Mper005=per005.MaxBV.mean() 
    Mquant1=quant1.MaxBV.mean()
    Mquant2=quant2.MaxBV.mean()
    Mquant3=quant3.MaxBV.mean()
    Mper095=per095.MaxBV.mean()

    # plot annual cycle + quantiles
    p = plt.plot(sorter,mean.MaxBV,sorter,per005.MaxBV,sorter,quant1.MaxBV,\
                 sorter,quant2.MaxBV,sorter,quant3.MaxBV,sorter,per095.MaxBV)

    plt.setp(p[0],linewidth=5,color='magenta',zorder=6) 
    plt.setp(p[1],linewidth=3,color='aqua')
    plt.setp(p[5],linewidth=3,color='aqua')
    plt.setp(p[2],linewidth=3,color='turquoise')   
    plt.setp(p[3],linewidth=5,color='indigo')
    plt.setp(p[4],linewidth=3,color='turquoise')
    
    # fill between two lines
    plt.fill_between(sorter,per005.MaxBV,per095.MaxBV,alpha=0.8,color='lightcyan')
    plt.fill_between(sorter,quant1.MaxBV,quant3.MaxBV,alpha=0.2,color='skyblue')

    plt.grid("on",zorder=10,linestyle='--',alpha=0.6)

    plt.title("Max BVF, monthly plot", fontsize=gutl.fontSizeTitle)
    plt.xticks(size = gutl.fontSizeTickLabels)
    plt.yticks(size = gutl.fontSizeTickLabels)
    plt.xlabel('Month',fontsize=gutl.fontSizeAxisLabel)
    plt.ylabel('Max Brunt-Vaisala Frequency (cycle/hr)',fontsize=gutl.fontSizeAxisLabel)

    # add legend
    label = ['AVG : {:.2f}'.format(Mmean),'P05 : {:.2f}'.format(Mper005),'Q1  : {:.2f}'.format(Mquant1), \
             'Q2  : {:.2f}'.format(Mquant2), 'Q3  : {:.2f}'.format(Mquant3), 'P95 : {:.2f}'.format(Mper095)] 

    leg = axes.legend(label,fontsize=15,fancybox=True,prop={"size":20})
    
    # set the linewidth of each legend object
    for legobj in leg.legendHandles:
        legobj.set_linewidth(5.0)

    # write annualc cycle and quantiles on file 
    if tocsv:
       dic = { 'month' : sorter,'mean':mean.MaxBV,'min':minbvf.MaxBV,'P05':per005.MaxBV,'Q1':quant1.MaxBV, \
               'Q2':quant2.MaxBV,'Q3':quant3.MaxBV,'P95':per095.MaxBV }
       df = pd.DataFrame(data=dic)
       df.to_csv(csvpth,index=False)

    return fig

def acSBVFIplot(sbvfi_csv):
    """
    Read SBVFI csv file and plot results
    """

    # read csv data 
    df = pd.read_csv(sbvfi_csv,parse_dates=[[0,1]],infer_datetime_format=True)    

    # threshold levels
    zeros = np.zeros(len(df.Year_Month))
    ones  = np.ones(len(df.Year_Month))
    ones_half=np.full(len(df.Year_Month),1.5)
    twos  = np.full(len(df.Year_Month),2)

    # Compute percentage over threshold positive
    NN_plus = df.SFI_12m.loc[(df['SFI_12m'] > 0) & (df['SFI_12m'] <= 1) ]
    NN_plus = int(round(len(NN_plus)*100/(len(df.SFI_12m)-12),0))
    mod_plus = df.SFI_12m.loc[(df['SFI_12m'] > 1) & (df['SFI_12m'] <= 1.5) ]
    mod_plus =int(round(len(mod_plus)*100/(len(df.SFI_12m)-12),0))
    sev_plus = df.SFI_12m.loc[(df['SFI_12m'] > 1.5) & (df['SFI_12m'] <= 2) ]
    sev_plus =int(round(len(sev_plus)*100/(len(df.SFI_12m)-12),0))
    ext_plus = df.SFI_12m.loc[(df['SFI_12m'] > 2) ]
    ext_plus =int(round(len(ext_plus)*100/(len(df.SFI_12m)-12),0))
    # Compute percentage over threshold negative
    NN_neg = df.SFI_12m.loc[(df['SFI_12m'] < 0) & (df['SFI_12m'] >= -1) ]
    NN_neg = int(round(len(NN_neg)*100/(len(df.SFI_12m)-12),0))
    mod_neg = df.SFI_12m.loc[(df['SFI_12m'] < -1) & (df['SFI_12m'] >= -1.5) ]
    mod_neg =int(round(len(mod_neg)*100/(len(df.SFI_12m)-12),0))
    sev_neg = df.SFI_12m.loc[(df['SFI_12m'] < -1.5) & (df['SFI_12m'] >= -2) ]
    sev_neg =int(round(len(sev_neg)*100/(len(df.SFI_12m)-12),0))
    ext_neg = df.SFI_12m.loc[(df['SFI_12m'] < -2) ]
    ext_neg =int(round(len(ext_neg)*100/(len(df.SFI_12m)-12),0))

    fig, axes = plt.subplots(1, figsize=(20,12), dpi= 200)   

    # hline at 0 just for reference
    plt.hlines(0,df.Year_Month.min(),df.Year_Month.max()+ timedelta(weeks=300),linewidth=3,color='royalblue')

    # plot
    plt.plot(df.Year_Month,df.SFI_12m)

    # fill for positive values
    plt.fill_between(df.Year_Month,zeros,df.SFI_12m,where=(df.SFI_12m > 0) ,alpha=0.3,color='lightskyblue',interpolate=True)
    plt.fill_between(df.Year_Month,ones,df.SFI_12m,where=(df.SFI_12m > 1) ,alpha=0.5,color='lightskyblue',interpolate=True)
    plt.fill_between(df.Year_Month,ones_half,df.SFI_12m,where=(df.SFI_12m > 1.5) ,alpha=0.5,color='royalblue',interpolate=True)
    plt.fill_between(df.Year_Month,twos,df.SFI_12m,where=(df.SFI_12m > 2) ,alpha=0.5,color='midnightblue',interpolate=True)

    # fill for negative values
    plt.fill_between(df.Year_Month,zeros,df.SFI_12m,where=(df.SFI_12m < 0) ,alpha=0.3,color='lightpink',interpolate=True)
    plt.fill_between(df.Year_Month,-ones,df.SFI_12m,where=(df.SFI_12m < -1) ,alpha=0.5,color='lightpink',interpolate=True)
    plt.fill_between(df.Year_Month,-ones_half,df.SFI_12m,where=(df.SFI_12m < -1.5) ,alpha=0.5,color='palevioletred',interpolate=True)
    plt.fill_between(df.Year_Month,-twos,df.SFI_12m,where=(df.SFI_12m < -2) ,alpha=0.5,color='crimson',interpolate=True)

    # add the grid 
    plt.grid("on",zorder=10,linestyle='--',alpha=0.6)

    years = mdates.YearLocator() 
    axes.xaxis.set_major_locator(years)  
    fig.autofmt_xdate()

    # auxiliary plot options
    plt.title("Standardize BVF Index", fontsize=gutl.fontSizeTitle)
    plt.xticks(size = gutl.fontSizeTickLabels)
    plt.yticks(size = gutl.fontSizeTickLabels)
    plt.xlabel('Date',fontsize=gutl.fontSizeAxisLabel)
    plt.ylabel('SBVFI',fontsize=gutl.fontSizeAxisLabel)
    plt.xlim(right = (df.Year_Month.max() + timedelta(weeks=300)))

    #add rectangle to plot
    start=mdates.date2num(df.Year_Month.max() + timedelta(weeks=52))
    end=mdates.date2num(df.Year_Month.max() + timedelta(weeks=156))
    width=end - start
    # ====== postive values ======= #
    # NN+
    rectangle = axes.add_patch(Rectangle((start,0), width, 1, color='lightskyblue',alpha=0.3))
    rx, ry = rectangle.get_xy()
    cx = rx + rectangle.get_width()/2.0
    cy = ry + rectangle.get_height()/2.0
    axes.annotate("{:d}%".format(NN_plus), (cx, cy), color='black', weight='bold', fontsize=18, ha='center', va='center')
    axes.annotate("NN+", (cx + rectangle.get_width(), cy), color='darkcyan', weight='bold', fontsize=18, ha='center', va='center')
    # mod
    axes.add_patch(Rectangle((start,1), width, 0.5, color='lightskyblue',alpha=0.3))
    rectangle = axes.add_patch(Rectangle((start,1), width, 0.5, color='lightskyblue',alpha=0.5))
    rx, ry = rectangle.get_xy()
    cx = rx + rectangle.get_width()/2.0
    cy = ry + rectangle.get_height()/2.0
    axes.annotate("{:d}%".format(mod_plus), (cx, cy), color='black', weight='bold', fontsize=18, ha='center', va='center')
    axes.annotate("Mod", (cx + rectangle.get_width(), cy), color='darkcyan', weight='bold', fontsize=18, ha='center', va='center')
    # severe
    axes.add_patch(Rectangle((start,1.5), width, 0.5, color='lightskyblue',alpha=0.3))
    axes.add_patch(Rectangle((start,1.5), width, 0.5, color='lightskyblue',alpha=0.5))
    rectangle = axes.add_patch(Rectangle((start,1.5), width, 0.5, color='royalblue',alpha=0.5))
    rx, ry = rectangle.get_xy()
    cx = rx + rectangle.get_width()/2.0
    cy = ry + rectangle.get_height()/2.0
    axes.annotate("{:d}%".format(sev_plus), (cx, cy), color='black', weight='bold', fontsize=18, ha='center', va='center')
    axes.annotate("Sev", (cx + rectangle.get_width(), cy), color='darkcyan', weight='bold', fontsize=18, ha='center', va='center')
    # extreme
    axes.add_patch(Rectangle((start,2), width, df.SFI_12m.max()-2, color='lightskyblue',alpha=0.3))
    axes.add_patch(Rectangle((start,2), width, df.SFI_12m.max()-2, color='lightskyblue',alpha=0.5))
    axes.add_patch(Rectangle((start,2), width, df.SFI_12m.max()-2, color='royalblue',alpha=0.5))
    rectangle = axes.add_patch(Rectangle((start,2), width, df.SFI_12m.max()-2, color='midnightblue',alpha=0.5))
    rx, ry = rectangle.get_xy()
    cx = rx + rectangle.get_width()/2.0
    cy = ry + rectangle.get_height()/2.0
    axes.annotate("{:d}%".format(ext_plus), (cx, cy), color='black', weight='bold', fontsize=18, ha='center', va='center')
    axes.annotate("Ext", (cx + rectangle.get_width(), cy), color='darkcyan', weight='bold', fontsize=18, ha='center', va='center')

    # ====== negative values ======= #
    # NN+
    rectangle = axes.add_patch(Rectangle((start,0), width, -1, color='lightpink',alpha=0.3))
    rx, ry = rectangle.get_xy()
    cx = rx + rectangle.get_width()/2.0
    cy = ry + rectangle.get_height()/2.0
    axes.annotate("{:d}%".format(NN_neg), (cx, cy), color='black', weight='bold', fontsize=18, ha='center', va='center')
    axes.annotate("NN-", (cx + rectangle.get_width(), cy), color='mediumvioletred', weight='bold', fontsize=18, ha='center', va='center')
    # mod
    axes.add_patch(Rectangle((start,-1), width, -0.5, color='lightpink',alpha=0.3))
    rectangle = axes.add_patch(Rectangle((start,-1), width, -0.5, color='lightpink',alpha=0.5))
    rx, ry = rectangle.get_xy()
    cx = rx + rectangle.get_width()/2.0
    cy = ry + rectangle.get_height()/2.0
    axes.annotate("{:d}%".format(mod_neg), (cx, cy), color='black', weight='bold', fontsize=18, ha='center', va='center')
    axes.annotate("Mod", (cx + rectangle.get_width(), cy), color='mediumvioletred', weight='bold', fontsize=18, ha='center', va='center')
    # severe
    axes.add_patch(Rectangle((start,-1.5), width, -0.5, color='lightpink',alpha=0.3))
    axes.add_patch(Rectangle((start,-1.5), width, -0.5, color='lightpink',alpha=0.5))
    rectangle = axes.add_patch(Rectangle((start,-1.5), width, -0.5, color='palevioletred',alpha=0.5))
    rx, ry = rectangle.get_xy()
    cx = rx + rectangle.get_width()/2.0
    cy = ry + rectangle.get_height()/2.0
    axes.annotate("{:d}%".format(sev_neg), (cx, cy), color='black', weight='bold', fontsize=18, ha='center', va='center')
    axes.annotate("Sev", (cx + rectangle.get_width(), cy), color='mediumvioletred', weight='bold', fontsize=18, ha='center', va='center')
    # extreme
    axes.add_patch(Rectangle((start,-2), width, df.SFI_12m.min()+2, color='lightpink',alpha=0.3))
    axes.add_patch(Rectangle((start,-2), width, df.SFI_12m.min()+2, color='lightpink',alpha=0.5))
    axes.add_patch(Rectangle((start,-2), width, df.SFI_12m.min()+2, color='palevioletred',alpha=0.5))
    rectangle = axes.add_patch(Rectangle((start,-2), width,df.SFI_12m.min()+2, color='crimson',alpha=0.5))
    rx, ry = rectangle.get_xy()
    cx = rx + rectangle.get_width()/2.0
    cy = ry + rectangle.get_height()/2.0
    axes.annotate("{:d}%".format(ext_neg), (cx, cy), color='black', weight='bold', fontsize=18, ha='center', va='center')
    axes.annotate("Ext", (cx + rectangle.get_width(), cy), color='mediumvioletred', weight='bold', fontsize=18, ha='center', va='center')

    return fig

def acSSTViolinPlot(dailySSTCsv):   

    """ Monthly TS Violin Plot 
    input: dailySSTCsv, csv file path of the daily values of SST
    """ 
    
    dateColId = 0
    sstColId = 1
        
    file2 = pd.read_csv(dailySSTCsv)
    file2.iloc[:,dateColId] = pd.to_datetime(file2.iloc[:,dateColId])
    dateCol = file2.iloc[:,dateColId]
    tCol = file2.iloc[:,sstColId]
    file2['Time Series from 1987 to 2019'] = [d.year for d in dateCol]
    file2['month'] = [d.strftime('%b') for d in dateCol]
    years = file2['Time Series from 1987 to 2019'].unique()

    fig, axes = plt.subplots(1, figsize=(18,8), dpi= 100)
    sns.violinplot(x='month', y=tCol.name, data=file2.loc[~file2.month.isin([1987, 2019]), :], palette="tab10", bw=.2, cut=1, linewidth=1)

    plt.grid("on",zorder=10,linestyle='--',alpha=0.6)

    plt.title("Max BVF, monthly violin diagram", fontsize=gutl.fontSizeTitle)
    plt.xticks(size = gutl.fontSizeTickLabels)
    plt.yticks(size = gutl.fontSizeTickLabels)
    plt.xlabel('Month',fontsize=gutl.fontSizeAxisLabel)
    plt.ylabel('Max Brunt-Vaisala Frequency (cycle/hr)',fontsize=gutl.fontSizeAxisLabel)

    return fig


def acZMAXBVViolinPlot(dailySSTCsv):   

    """ Monthly TS Violin Plot 
    input: dailySSTCsv, csv file path of the daily values of SST
    """ 
    
    dateColId = 0
    sstColId = 1
        
    file2 = pd.read_csv(dailySSTCsv)
    file2.iloc[:,dateColId] = pd.to_datetime(file2.iloc[:,dateColId])
    dateCol = file2.iloc[:,dateColId]
    tCol = file2.iloc[:,sstColId]
    file2['Time Series from 1987 to 2019'] = [d.year for d in dateCol]
    file2['month'] = [d.strftime('%b') for d in dateCol]
    years = file2['Time Series from 1987 to 2019'].unique()

    fig, axes = plt.subplots(1, figsize=(18,8), dpi= 100)
    sns.violinplot(x='month', y=tCol.name, data=file2.loc[~file2.month.isin([1987, 2019]), :], palette="tab10", bw=.2, cut=1, linewidth=1)

    plt.grid("on",zorder=10,linestyle='--',alpha=0.6)

    plt.title("Depth of Max BVF, monthly violin diagram", fontsize=gutl.fontSizeTitle)
    plt.xticks(size = gutl.fontSizeTickLabels)
    plt.yticks(size = gutl.fontSizeTickLabels)
    plt.xlabel('Month',fontsize=gutl.fontSizeAxisLabel)
    plt.ylabel('Depth of Max Brunt-Vaisala Frequency (m)',fontsize=gutl.fontSizeAxisLabel)

    return fig



def acPlotMBVFTimeSeries(dailySSTCsv):
    """
    Plot of the time series of Max BVF and of its trend
    input: dailySSTCsv, csv file path of the daily values of Max BVF
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
    ssnltl = np.array([ssnlvl[im % 12][0] for im in range(nmnt)]).reshape([nmnt,1])
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
    plt.plot(dtmAnmlYr, trndln, linewidth=.5, color="k", label=f"Trend = {medslope:2.3f}±{confInt:2.3f} cycle/hr/year")

    plt.grid("on")

    plt.legend(fontsize=gutl.fontSizeLegend, loc="upper left", frameon=False)
    plt.xticks(fontsize=gutl.fontSizeTickLabels)
    plt.yticks(fontsize=gutl.fontSizeTickLabels)

    plt.xlabel("Year", fontsize=gutl.fontSizeAxisLabel)
    plt.ylabel("Max BVF anomaly", fontsize=gutl.fontSizeAxisLabel)

    plt.title("Max BVF anomaly (cycle/hr)", fontsize=gutl.fontSizeTitle)

    plt.tight_layout()

    return f

def acPlotZMBVFTimeSeries(dailySSTCsv):
    """
    Plot of the time series of depth of Max BVF and of its trend
    input: dailySSTCsv, csv file path of the daily values of Max BVF
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
    ssnltl = np.array([ssnlvl[im % 12][0] for im in range(nmnt)]).reshape([nmnt,1])
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
    plt.plot(dtmAnmlYr, trndln, linewidth=.5, color="k", label=f"Trend = {medslope:2.3f}±{confInt:2.3f} s-1/year")

    plt.grid("on")

    plt.legend(fontsize=gutl.fontSizeLegend, loc="upper left", frameon=False)
    plt.xticks(fontsize=gutl.fontSizeTickLabels)
    plt.yticks(fontsize=gutl.fontSizeTickLabels)

    plt.xlabel("Year", fontsize=gutl.fontSizeAxisLabel)
    plt.ylabel("depth of max BVF anomaly", fontsize=gutl.fontSizeAxisLabel)

    plt.title("depth of Max BVF anomaly (m)", fontsize=gutl.fontSizeTitle)

    plt.tight_layout()

    return f



def plotMeanMap(meanNcFileSpec, plotTitle, NCmean=None, tocsv=False, csvpath=None):
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

    # write to csv
    if tocsv:
       temp_mean = t[meanNcFileSpec.varName][:,:,:].mean(dim='year',skipna=True,keep_attrs=True)
       temp_mean.to_netcdf(path=NCmean,mode='w')
       convert_file(NCmean,csvpath,csvpath,clean_choice=1)
        
    gs = gridspec.GridSpec(ncols=3, nrows=1, width_ratios=[1, .03, .03])
    fig = plt.figure(figsize=(17, 12),dpi=300)

    ax = fig.add_subplot(gs[0, 0])
    #  coastlines, and adding features
    projection = ccrs.PlateCarree()
    ax = plt.axes(projection=projection)
    ax.coastlines(linewidths=1, alpha=0.9999, resolution="10m")
    
    # Import an NCL colormap
    newcmp = gvcmaps.NCV_jet
    
    vmin = np.nanpercentile(temp_av, .01)
    vmax = np.nanpercentile(temp_av, 99.99)

    #print(vmin,' ',vmax)

    # Contourf-plot data: external contour
    heatmap = temp_av.plot.contourf(ax=ax,
                              transform=projection,
                              levels=31,
                              vmin=0 ,#vmin,
                              vmax=30 ,#,
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
    cbar_ticks=np.arange(0, 31, 1)
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


def plotZMBVMeanMap(meanNcFileSpec, plotTitle):
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

    ax = fig.add_subplot(gs[0, 0])
    #  coastlines, and adding features
    projection = ccrs.PlateCarree()
    ax = plt.axes(projection=projection)
    ax.coastlines(linewidths=1, alpha=0.9999, resolution="10m")
    
    # Import an NCL colormap
    newcmp = gvcmaps.MPL_PuBuGn
    
    vmin = np.nanpercentile(temp_av, .01)
    vmax = np.nanpercentile(temp_av, 99.99)

    print(vmin,' ',vmax)

    # Contourf-plot data: external contour
    heatmap = temp_av.plot.contourf(ax=ax,
                              transform=projection,
                              levels=31,
                              vmin=0, #vmin,
                              vmax=210, #vmax,
#                              levels=43, 	Summer
#                              vmin=0, #vmin,	Summer
#                              vmax=42, #vmax,	Summer
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
    cbar_ticks=np.arange(0, 210, 7)
#    cbar_ticks=np.arange(0, 43, 1)  Summer
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


def plotTrendMap(trendNcFileSpec):
    """
    plots a map of trend loaded from the file/field specified by in meanNcFileSpec.
    input parameters:
      - trendNcFileSpec: definition of the input file
    """
    t = xr.open_dataset(trendNcFileSpec.ncFileName)

    thetao_area_1 = t.MaxBV.values

    gs = gridspec.GridSpec(ncols=3, nrows=1, width_ratios=[1, .03, .03])
    fig = plt.figure(figsize=(17, 12))

    ax = fig.add_subplot(gs[0, 0])

    projection = ccrs.PlateCarree()
    ax = plt.axes(projection=projection)
    ax.coastlines(linewidths=1,alpha=0.9999, resolution="10m")
    
    newcmp = gvcmaps.BlWhRe_r
    reversed_color_map = newcmp.reversed()
    
    heatmap = t.MaxBV.plot.contourf(ax=ax,
                              transform=projection,
                              levels=51,
                              vmin=-0.08, #0.025,
                              vmax=0.08, #0.055,
                              cmap=reversed_color_map,
                              add_colorbar=False)
    
    lines=t.MaxBV.plot.contour(ax=ax,alpha=1,linewidths=0.5,colors = 'k',linestyles='None',levels=50)
    gvutil.set_axes_limits_and_ticks(ax,
                                     xlim=(12, 22),
                                     ylim=(37, 46),
                                     xticks=np.linspace(12, 22, 6),
                                     yticks=np.linspace(37, 46, 10))
    
    gvutil.add_major_minor_ticks(ax, y_minor_per_major=1, labelsize=15)
    
    
    cax = fig.add_subplot(gs[0, 2])
    cbar_ticks=np.arange(-0.08, 0.08, 0.0032)
    cbar = plt.colorbar(heatmap,
                        orientation='vertical',
                        ticks=cbar_ticks,
                        cax=cax)
    cax.tick_params(labelsize=gutl.fontSizeTickLabels)
    
    plt.axes(ax)
    ax.set_extent([12, 20.2, 39.7, 46])
    
    gvutil.set_titles_and_labels(
        ax,
        maintitle="Trend of maxBVF (cycle/hr/year)",
        maintitlefontsize=16,
        xlabel="",
        ylabel="")
    
    ax.xlabel_style = {'size': 20, 'color': 'k'}
    ax.ylabel_style = {'size': 20, 'color': 'k'}


def plotTrendZmaxBVMap(trendNcFileSpec):
    """
    plots a map of trend loaded from the file/field specified by in meanNcFileSpec.
    input parameters:
      - trendNcFileSpec: definition of the input file
    """
    t = xr.open_dataset(trendNcFileSpec.ncFileName)

    thetao_area_1 = t.zmaxbv.values

    gs = gridspec.GridSpec(ncols=3, nrows=1, width_ratios=[1, .03, .03])
    fig = plt.figure(figsize=(17, 12))

    ax = fig.add_subplot(gs[0, 0])

    projection = ccrs.PlateCarree()
    ax = plt.axes(projection=projection)
    ax.coastlines(linewidths=1,alpha=0.9999, resolution="10m")
    
    newcmp = gvcmaps.BlWhRe_r
    reversed_color_map = newcmp.reversed()
    
    heatmap = t.zmaxbv.plot.contourf(ax=ax,
                              transform=projection,
                              levels=51,
                              vmin=-0.5,
                              vmax=0.5,
                              cmap=reversed_color_map,
                              add_colorbar=False)
    
    lines=t.zmaxbv.plot.contour(ax=ax,alpha=1,linewidths=0.5,colors = 'k',linestyles='None',levels=50)
    gvutil.set_axes_limits_and_ticks(ax,
                                     xlim=(12, 22),
                                     ylim=(37, 46),
                                     xticks=np.linspace(12, 22, 6),
                                     yticks=np.linspace(37, 46, 10))
    
    gvutil.add_major_minor_ticks(ax, y_minor_per_major=1, labelsize=15)
    
    
    cax = fig.add_subplot(gs[0, 2])
    cbar_ticks=np.arange(-0.50, 0.52, 0.02)
    cbar = plt.colorbar(heatmap,
                        orientation='vertical',
                        ticks=cbar_ticks,
                        cax=cax)
    cax.tick_params(labelsize=gutl.fontSizeTickLabels)
    
    plt.axes(ax)
    ax.set_extent([12, 20.2, 39.7, 46])
    
    gvutil.set_titles_and_labels(
        ax,
        maintitle="Trend of depth of max BVF (m/yr)",
        maintitlefontsize=16,
        xlabel="",
        ylabel="")
    
    ax.xlabel_style = {'size': 20, 'color': 'k'}
    ax.ylabel_style = {'size': 20, 'color': 'k'}


