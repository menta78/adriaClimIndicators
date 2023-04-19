import os, random, shutil, subprocess, glob

import netCDF4

import acIndUtils


mdlPath = os.path.dirname(os.path.abspath(__file__))
erddapCmdTmpl = mdlPath + "/erddap-downloader.sh -u lorenzo.mentaschi -p chua2Hahrahyoo,g -d \"{datasetId}\" -r \"{year}/(.*)\""

erddapDownloadSubdir = 'erddap.cmcc-opa.eu'

cdocmd = "cdo"


def monthMeanAggregator(inputNcFileSpec, outputNcFileSpec):
    """
    performs a monthly aggregation with cdo
    """
    cmd = f"{cdocmd} select,name={inputNcFileSpec.varName} -monmean -cat {inputNcFileSpec.ncFileName} {outputNcFileSpec.ncFileName}"
    flnm_ = os.path.basename(outputNcFileSpec.ncFileName)
    logfl = open(f'cdo_{flnm_}.log', 'w')
    print("        ... monthly aggregation with the command")
    print(f"          {cmd}")
    subprocess.run(cmd.split(), stdout=logfl, stderr=logfl)
    logfl.close()



def erddapDownloadAndAggregate(indicatorNcVarName, datasetId, years, outdir, aggregator=monthMeanAggregator):
    tmpdir = '../tmp/proc' + str(random.randint(0, 1e6)) 
    outdir = os.path.abspath(outdir)
    os.system(f"mkdir -p {tmpdir}")
    os.system(f"mkdir -p {outdir}")

    outFlNames = []

    curdir = os.getcwd()
    os.chdir(tmpdir)
    for yr in years:
        print(f"  processing year {yr}")
        print("      ... downloading (will take a while) ...")
        erddapCmd = erddapCmdTmpl.format(datasetId=datasetId, year=yr)
        logfl = open('erddap_download.log', 'w')
        subprocess.run([s.strip(' "') for s in erddapCmd.split()], stdout=logfl, stderr=logfl)
        logfl.close()
        
        print("      ... linking the files in a single directory ...")
        flsdir = erddapDownloadSubdir
        cmd = f"find {flsdir}/ -iname \"*.nc\" | xargs -i ln -s {{}} ./"
        os.system(cmd)

        print("      ... aggregating the files (will take a while) ...")
        fls = glob.glob("*.nc")
        if fls == []:
            print(f"          ... NOTHING FOUND for year {yr}, skipping ...")
            continue
        fltst = fls[0]
        ds = netCDF4.Dataset(fltst)
        vrtst = ds.variables[indicatorNcVarName]
        assert vrtst.get_dims()[0].isunlimited(),\
                'only dimensions (time, lat, lon), or (time, z, lat, lon) are supported'
        if len(vrtst.shape) == 3:
            (tVarName, yVarName, xVarName) = vrtst.dimensions
            zVarName = ''
        elif len(vrtst.shape) == 4:
            (tVarName, zVarName, yVarName, xVarName) = vrtst.dimensions
        ds.close()
        inFlSpc = acIndUtils.acNcFileSpec(
                ncFileName = '*.nc',
                varName = indicatorNcVarName,
                xVarName = xVarName,
                yVarName = yVarName,
                zVarName = zVarName,
                tVarName = tVarName
                )
        outFlName = f"{indicatorNcVarName}_{yr}.nc"
        outNcFlPth = os.path.join(outdir, outFlName)
        outFlSpc = acIndUtils.acCloneFileSpec(inFlSpc, ncFileName=outNcFlPth)
        aggregator(inFlSpc, outFlSpc)
        
        print("      ... tmp directory cleanup ..")
        os.system("rm *.nc")
        os.system("rm *.log")
        shutil.rmtree(erddapDownloadSubdir)
        outFlNames.append(outFlName)

    os.chdir(curdir)
    shutil.rmtree(tmpdir)
    return outFlNames


def mergeFiles(ncFlPaths, outNcFilePath):
    ncFlPathStr = ' '.join(ncFlPaths)
    cmd = f"{cdocmd} mergetime {ncFlPathStr} {outNcFilePath}"
    subprocess.run(cmd.split())



def testErddapDownloadAndAggregate():
    indicatorNcVarName = "sosstsst"
    datasetId = "adriaclim_resm_nemo_historical_3h_T"
    years = range(1992, 2012)
    aggregator = monthMeanAggregator
    outdir = './testOutput'
    erddapDownloadAndAggregate(indicatorNcVarName, datasetId, years, outdir, aggregator=aggregator)


if __name__ == "__main__":
    testErddapDownloadAndAggregate()


