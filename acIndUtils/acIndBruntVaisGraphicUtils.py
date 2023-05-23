import matplotlib.pyplot as plt

from acIndUtils import acIndUtils
from acIndUtils import acIndGrahUtils as gutl


def acBruntVaisPlotVProfileAll(annual3DFlNcFileSpec, summer3DFlNcFileSpec, winter3DFlNcFileSpec, maxDepth, zlevs=None, psuLims=None, csv=False, pth=None):
    """
    acBruntVaisPlotVProfileAll: plot the vertical profiles of Brunt-Vaisala Frequency for winter, summer and annual mean in a single plot.
    input: 
        annual3DFlNcFileSpec, summer3DFlNcFileSpec, winter3DFlNcFileSpec: file specs for annual mean, summer, winter
        maxDepth: max depth to which the vertical profile is plotted.
        zlevs: vertical cooridnates (if this variable is none, the one found in the file is used)
        psuLims: if given this param is used to adjust the limits of the x axis
    """
    if csv:
       dpthAnnual, vprofAnnual = acIndUtils.acGetVProfile(annual3DFlNcFileSpec, maxDepth, zlevs=zlevs, tocsv=csv, csvpth=pth+'_Annual.csv')
       dpthSummer, vprofSummer = acIndUtils.acGetVProfile(summer3DFlNcFileSpec, maxDepth, zlevs=zlevs, tocsv=csv, csvpth=pth+'_Summer.csv')
       dpthWinter, vprofWinter = acIndUtils.acGetVProfile(winter3DFlNcFileSpec, maxDepth, zlevs=zlevs, tocsv=csv, csvpth=pth+'_Winter.csv')
    else:
       dpthAnnual, vprofAnnual = acIndUtils.acGetVProfile(annual3DFlNcFileSpec, maxDepth, zlevs=zlevs)
       dpthSummer, vprofSummer = acIndUtils.acGetVProfile(summer3DFlNcFileSpec, maxDepth, zlevs=zlevs)
       dpthWinter, vprofWinter = acIndUtils.acGetVProfile(winter3DFlNcFileSpec, maxDepth, zlevs=zlevs)

    fig = plt.figure(figsize=[12, 12], dpi=300)
    plt.plot(vprofAnnual, dpthAnnual, linewidth=6, color='navy', label="Annual mean")
    plt.plot(vprofWinter, dpthWinter, linewidth=3, color='darkcyan', label="Winter")
    plt.plot(vprofSummer, dpthSummer, linewidth=3, color='darkorange', label="Summer")
    plt.legend(fontsize = gutl.fontSizeLegend)
    if not psuLims is None:
        plt.xlim(psuLims)
    plt.xlabel("Brunt-Vaisala Freq. (Cycle/hr)", fontsize=gutl.fontSizeAxisLabel)
    plt.ylabel("Depth (m)", fontsize=gutl.fontSizeAxisLabel)
    plt.xticks(size = gutl.fontSizeTickLabels)
    plt.yticks(size = gutl.fontSizeTickLabels)
    plt.grid("on")
    plt.title("Vertical profile of Brunt-Vaisala Freq.", fontsize=gutl.fontSizeTitle)
    
    return fig


def acBruntVaisPlotVProfileTrend(trendMapNcSpec, maxDepth, zlevs=None, psuLims=None, csv=False, pth=None):
    """
    acBruntVaisPlotVProfileTrend: plot the vertical profiles of the trend of Brunt-Vaisala frequency and its spatial variabliity.
    input: 
        trendMapNcFileSpec: file spec for trend map
        maxDepth: max depth to which the vertical profile is plotted.
        zlevs: vertical cooridnates (if this variable is none, the one found in the file is used)
    """
    if csv:
       dpth, vprof = acIndUtils.acGetVProfile(trendMapNcSpec, maxDepth, zlevs=zlevs, tocsv=csv, csvpth=pth+'_trend.csv')
       dpth, vprofStd = acIndUtils.acGetVProfileStDev(trendMapNcSpec, maxDepth, zlevs=zlevs, tocsv=csv, csvpth=pth+'_std.csv')    
    else:
       dpth, vprof = acIndUtils.acGetVProfile(trendMapNcSpec, maxDepth, zlevs=zlevs)
       dpth, vprofStd = acIndUtils.acGetVProfileStDev(trendMapNcSpec, maxDepth, zlevs=zlevs)

    fig = plt.figure(figsize=[12, 12], dpi=300)
    ax = fig.gca()
    plt.plot(vprof, dpth, linewidth=6, color='navy', label="Trend")
    plt.plot(vprof-vprofStd, dpth, linewidth=2, color='darkcyan', label="Spatial variability ($1 \cdot \sigma$)")
    plt.plot(vprof+vprofStd, dpth, linewidth=2, color='darkcyan')
    ax.fill_betweenx(dpth, vprof-vprofStd, vprof+vprofStd, color="lightcyan", alpha=.5)
    plt.xlabel("Brunt Vaisala freq. trend ((Cycle/hr) \cdot year^-1$)", fontsize=gutl.fontSizeAxisLabel)
    plt.ylabel("Depth (m)", fontsize=gutl.fontSizeAxisLabel)
    plt.xticks(size = gutl.fontSizeTickLabels)
    plt.yticks(size = gutl.fontSizeTickLabels)
    plt.grid("on")
    plt.title("Brunt-Vaisala Freq. trend, vertical profile", fontsize=gutl.fontSizeTitle)
    if not psuLims is None:
        plt.xlim(psuLims)
    plt.legend(fontsize = gutl.fontSizeLegend)
    
    return fig



    

