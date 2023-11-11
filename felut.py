import os
import re
import time
import platform
import argparse
import xml.etree.ElementTree as et
from multiprocessing import Pool
################################### configure the script before executing ################################

#Step1:  Configure the .exe paths of Odin Yosys abc and vpr.  
OdinExePath="path of OdinII"
YosysExePath="path of yosys"
abcExePath="path of abc"
vprExePath="path of vpr"
vprFlowPath="path of vtr_flow"
#Step2: Configure the input path. First, put the config.xml in inputPath. Then under the input path, creat dirctory "arch", "blif" and "verilog". 
#Finally, put the arch files in dir "arch", put the blif files in dir "blif" and put the verilog files in dir "verilog".
inputPath="path of FinalWork"
#Step3: Configure the result output path
resPath="path of FinalWork"
#Step4: Configure the vpr channel width
channel_width = 282
#Step5 giving a blif file name if you need only one file to execute runOne().
fileName="sha.odin.blif"
#Step6 choose which functions do you want to execute:
BuildDsdFlag=False
RunOdinFlag=False
RunSrcPathFlag=False
RunOneFileFlag=True
RunParseResFlag=True
########################################### end of configuration ###########################################

localtime = time.asctime(time.localtime(time.time()))
print("Local time :", localtime)
curOs = platform.system()
print("Current OS: ", curOs)
if curOs == "Linux":
    flagLinux = True
elif curOs == "Windows":
    flagLinux = False
else:
    print("Unknown system")
    exit()


def runOdin(srcFile, archFile, configTemplateFile, outputPath="."):
    path, fileName = os.path.split(srcFile)
    netlistName, fileExt = os.path.splitext(fileName)
    if fileExt == '':
        fileName = fileName + '.v'
    elif fileExt != '.v':
        print("Error in runOdin(): invalid file extension: %s" % (fileName))
        exit()

    if os.path.isdir(outputPath):
        print(outputPath, "exists.")
    else:
        os.mkdir(outputPath)
        print(outputPath, "is newly created.")
    
    resFile = os.path.join(outputPath, "%s.odin.blif" % (netlistName))
    configFile = os.path.join(outputPath, "config.xml")
    logFile = os.path.join(outputPath, "odin.out")

    tree = et.parse(configTemplateFile)
    root = tree.getroot()
    root.find(".//verilog_file").text = srcFile
    root.find(".//output_path_and_name").text = resFile
    root.find(".//arch_file").text = archFile
    tree.write(configFile)

    cmd = OdinExePath+"  -c %s > %s" % (configFile, logFile)
    print(cmd)
    if flagLinux:
        os.system(cmd)
    print("Odin finished!")
    return resFile


def runYosys(srcFile, outputPath="."):
    print(outputPath, "is newly created.")
    path, fileName = os.path.split(srcFile)
    netlistName, fileExt = os.path.splitext(fileName)
    if fileExt == '':
        fileName = fileName + '.v'
    elif fileExt != '.v':
        print("Error in runYosys(): invalid file extension: %s" % (fileName))
        exit()
    if os.path.isdir(outputPath):
        print(outputPath, "exists.")
    else:
        os.mkdir(outputPath)
    blifFile=os.path.join(outputPath, "%s.yosys.blif" % (netlistName))
    logFile = os.path.join(outputPath, "yosys.out")
    scriptFile = os.path.join(outputPath, "%s.ys" % (netlistName))
    cmdf=open(scriptFile,"w+")
    print("read_verilog %s"%srcFile,file=cmdf)
    print("hierarchy -auto-top \nflatten \nproc \nopt \nread_verilog -lib +/xilinx/cells_sim.v",file=cmdf)
    print("techmap -map +/techmap.v -map +/xilinx/cells_map.v \nopt",file=cmdf)
    print("dfflegalize -cell $_DFF_P_ 01 -cell $_DLATCH_P_ 01",file=cmdf)
    print("write_blif -noalias %s" %blifFile,file=cmdf)
    print("stat",file=cmdf)
    cmdf.close()
    catscript="cat %s" %scriptFile
    os.system(catscript)
    yosysCmd=YosysExePath+" -s %s -l %s" %(scriptFile,logFile)
    print(yosysCmd)
    if flagLinux:
        os.system(yosysCmd)
    print("Yosys finished!")
    return blifFile


def dsdLib(Type,srcPath, libFile, preMatchFile, K, outputPath="."):
    if os.path.isdir(outputPath):
        print(outputPath, "exists.")
    else:
        os.mkdir(outputPath)
        print(outputPath, "is newly created.")
    targetFiles = []
    for path,dirs,files in os.walk(srcPath):
        for fi in files:
            netlistName, fileExt = os.path.splitext(fi)
            if fileExt == '.blif':
                targetFiles.append(os.path.join(srcPath, fi))
    logFileName="abcBuildDsd_"+Type +".out"
    logFile = os.path.join(outputPath, logFileName)
    if Type == "andlut":
        cellFormat= "h=(fg);i={abcdeh}"
    elif Type == "lut2lut":
        cellFormat= "h={fg};i={abcdeh}"
    elif Type == "xorlut":
        cellFormat= "h=[fg];i={abcdeh}"
    elif Type == "Jason":
        cellFormat= "h={abcdef};i={g};j=(ih)"
    elif Type == "andandlut":
        cellFormat= "i=(ab);j=(cd);k={efghij}"
    elif Type == "lut2lut2":
        cellFormat= "i={ab};j={cd};k={efghij}"
    elif Type == "andlut2":
        cellFormat= "i={ab};j=(cd);k={efghij}"
    else:
        cellFormat = None
    script="dsdLib.abc_"+Type+".script"
    abcscript=os.path.join(outputPath, script)
    cmdf=open(abcscript,"w+")
    for srcFile in targetFiles:
        print("read %s;if -n -K %d; strash; dc2;if -n -K %d;"%(srcFile,K,K),file=cmdf)
    print("dsd_save %s; dsd_load %s;"%(preMatchFile,preMatchFile),file=cmdf)
    print("dsd_match -S \"%s\" -P 30;"%cellFormat,file=cmdf)
    print("dsd_save %s; dsd_ps" %libFile,file=cmdf)
    cmdf.close()
    cmd = abcExePath+" -F %s > %s" % (abcscript, logFile)
    print(cmd)
    if flagLinux:
        os.system(cmd)
    
    print("Build Dsd Library finished!")


def runAbcBase(srcFile,restoreClkScript, K, outputPath="."):
    _, fileName = os.path.split(srcFile)
    tmplist = fileName.split('.')
    if tmplist[-1] != 'blif':
        print("Error in runAbc(): invalid file extension: %s" % (fileName))
        exit()
    if tmplist[-2] == 'yosys':
        netlistName = fileName[:-11]
    elif tmplist[-2] == 'odin':
        netlistName = fileName[:-10]
    else:
        netlistName = fileName[:-5]
    outputPath=outputPath+"/"+netlistName
    if os.path.isdir(outputPath):
        print(outputPath, "exists.")
    else:
        os.mkdir(outputPath)
        print(outputPath, "is newly created.")

    abcNoClkFile = os.path.join(outputPath, "%s.base.abc_noclk.blif" % (netlistName))
    logFile = os.path.join(outputPath, "abc.out")
    resFile = os.path.join(outputPath, "%s.base.pre-vpr.blif" % (netlistName))
    abcCmd = "read %s; strash; ifraig -v;scorr -v;dc2 -v;dch -f;if -K %d; print_stats; write_hie %s %s" \
        % (srcFile, K, srcFile, abcNoClkFile)
    cmd = abcExePath+' -c "%s" > %s' % (abcCmd, logFile)
    print(cmd)
    if flagLinux:
        os.system(cmd)

    cmd = '%s %s %s %s' % (restoreClkScript, srcFile, abcNoClkFile, resFile)
    print(cmd)
    if flagLinux:
        os.system(cmd)
    
    print("Abc baseline Flow finished!")
    return resFile


def runAbcHllut(srcFile, libFile,restoreClkScript, K, outputPath="."):
    _, fileName = os.path.split(srcFile)
    tmplist = fileName.split('.')
    if tmplist[-1] != 'blif':
        print("Error in runAbc(): invalid file extension: %s" % (fileName))
        exit()
    if tmplist[-2] == 'yosys':
        netlistName = fileName[:-11]
    elif tmplist[-2] == 'odin':
        netlistName = fileName[:-10]
    else:
        netlistName = fileName[:-5]
    print(netlistName)
    outputPath=outputPath+"/"+netlistName
    if os.path.isdir(outputPath):
        print(outputPath, "exists.")
    else:
        os.mkdir(outputPath)
        print(outputPath, "is newly created.")

    abcNoClkFile = os.path.join(outputPath, "%s.abc_noclk.blif" % (netlistName))
    logFile = os.path.join(outputPath, "abc.out")
    resFile = os.path.join(outputPath, "%s.pre-vpr.blif" % (netlistName))
    abcCmd = "dsd_load %s; read %s; strash; ifraig -v;scorr -v;dc2 -v;dch -f;if -k -K %d; print_stats; write_hie %s %s" \
        % (libFile, srcFile, K, srcFile, abcNoClkFile)
    cmd = abcExePath+' -c "%s" > %s' % (abcCmd, logFile)
    print(cmd)
    if flagLinux:
        os.system(cmd)

    cmd = '%s %s %s %s' % (restoreClkScript, srcFile, abcNoClkFile, resFile)
    print(cmd)
    if flagLinux:
        os.system(cmd)
    
    print("Abc Hard logic Flow finished!")
    return resFile


def runVpr(srcFile, archFile, chanWidth):
    outputPath, fileName = os.path.split(srcFile)
    tmplist = fileName.split('.')
    if tmplist[-1] != 'blif':
        print("Error in runVpr(): invalid file extension: %s" % (fileName))
        exit()
    if tmplist[-2] == 'pre-vpr':
        netlistName = fileName[:-13]
    else:
        netlistName = fileName[:-5]
    logFile = "vpr.out" #% (netlistName)

    cmd = "cd %s; "%(outputPath) +vprExePath+" %s %s --circuit_file %s --route_chan_width %d > %s" \
        % (archFile, netlistName, fileName, chanWidth, logFile)

    print(cmd)
    if flagLinux:
        os.system(cmd)
    # remove the report file if needed
    """ cmd = "cd %s; rm *.rpt *.log *.net* *.place *.route" % (outputPath)
    #cmd = "cd %s; rm *.rpt *.net* *.place *.route" % (outputPath)
    print(cmd)
    if flagLinux:
        os.system(cmd) """
    print("Vpr finished!")


class ResData(object):
    def __init__(self, netlistName, abcNplb=0, abcLev=0, vprDelay=0, vprAreaRouting=0, vprAreaClb=0, vprNclb=0, flowRuntime=0, chanWidth=0):
        self.netlistName = netlistName
        self.abcNplb = abcNplb
        self.abcLev = abcLev
        self.vprDelay = vprDelay
        self.vprAreaClb = vprAreaClb
        self.vprAreaRouting = vprAreaRouting
        self.vprNclb = vprNclb
        self.flowRuntime = flowRuntime
        self.odinRuntime = 0
        self.abcRuntime = 0
        self.vprRuntime = 0
        self.chanWidth = chanWidth
    
    def print(self):
        print("\n====================\n")
        print("netlistName: ", self.netlistName)
        print("abcNplb: ", self.abcNplb)
        print("abcLev: ", self.abcLev)
        print("vprDelay: ", self.vprDelay)
        print("vprAreaRouting: ", self.vprAreaRouting)
        print("vprAreaClb: ", self.vprAreaClb)
        print("vprNclb: ", self.vprNclb)
        print("odinRuntime: ", self.odinRuntime)
        print("abcRuntime: ", self.abcRuntime)
        print("vprRuntime: ", self.vprRuntime)
        print("flowRuntime: ", self.flowRuntime)
        print("channelWidth:  ", self.chanWidth)


class VtrFlow(object):
    def __init__(self, Type="base", archFile=None, configTemplate=None, restoreClkScript=None, libFile=None, preMatchFile=None, K=7, chanWidth=114, outputPath="."):
        self.Type=Type 
        self.archFile = archFile
        self.configTemplate = configTemplate
        self.restoreClkScript = restoreClkScript
        self.libFile = libFile
        self.preMatchFile = preMatchFile
        self.K = K
        self.chanWidth = chanWidth
        self.outputPath = outputPath
        if os.path.isdir(outputPath):
            print(outputPath, "exists.")
        else:
            os.mkdir(outputPath)
            print(outputPath, "is newly created.")

    def runOne(self, srcFile): #srcFile.v
        print("Now in runOne()")
        #yosysBlif=runYosys(srcFile, self.outputPath)
        if self.Type == "base":
            abcResFile=runAbcBase(srcFile,self.restoreClkScript,6,self.outputPath)
        else: 
            abcResFile=runAbcHllut(srcFile, self.libFile,self.restoreClkScript,self.K,self.outputPath)
        #odinResFile = runYosys(srcFile, outputPath)
        #abcResFile = runAbc(odinResFile, self.restoreClkScript, self.K)
        #runVpr(abcResFile, self.archFile, self.chanWidth)
        print(archFile)
        print("%s is done" % (srcFile))
            
    def runDsdLib(self, srcPath):
        dsdLib(self.Type, srcPath, self.libFile,self.preMatchFile,self.K,self.outputPath)
    
    def runSrcPath(self, srcPath, outputPath=".",Type="base"):
        print("Now in runSrcPath()")

        #parameters for Pool
        flagPool = True
        nProcs = 30
        chunksize = 1

        if os.path.isdir(outputPath):
            print(outputPath, "exists.")
        else:
            os.mkdir(outputPath)
            print(outputPath, "is newly created.")

        targetFiles = []
        for path,dirs,files in os.walk(srcPath):
            for fi in files:
                netlistName, fileExt = os.path.splitext(fi)
                if fileExt == '.v':
                    targetFiles.append(os.path.join(srcPath, fi))
                if fileExt == '.blif':
                    targetFiles.append(os.path.join(srcPath, fi))
        print(targetFiles)

        worker = WorkerFactory(self, outputPath)
        
        if flagPool:
            with Pool(processes = nProcs) as pool:
                pool.map(worker, targetFiles, chunksize)
        else:
            for srcFile in targetFiles:
                worker(srcFile)


    def parseResult(self, resPath, outputPath='.'):
        print("Now in parseResult()")
        if os.path.isdir(outputPath):
            print(outputPath, "exists.")
        else:
            os.mkdir(outputPath)
            print(outputPath, "is newly created.")
        '''resBlifPath = os.path.join(outputPath, "odinBlif")
        if os.path.isdir(resBlifPath):
            print(resBlifPath, "exists.")
        else:
            os.mkdir(resBlifPath)
            print(resBlifPath, "is newly created.")
        resFile = os.path.join(outputPath, "parseResult.csv")'''

        targetNetlists = []
        for path,dirs,files in os.walk(resPath):
            for dir in dirs:
                targetNetlists.append(dir)

        resDataMap = dict() 
        for netlist in targetNetlists:
            print("\n====================\n")
            targetPath = os.path.join(resPath, netlist)
            parseData = ResData(netlist)
            
            '''cmd = "mv %s/*.odin.blif %s/%s.odin.blif" \
                % (targetPath, resBlifPath, netlist)
            print(cmd)
            if flagLinux:
                os.system(cmd)'''

            '''with open(os.path.join(targetPath, "odin.out")) as f:
                line = f.readline()
                while line:
                    searchObj = re.search(r'Odin II took (\S+) seconds', line)
                    if searchObj:
                        #print("odinRuntime = ", searchObj.group(1))
                        parseData.odinRuntime = float(searchObj.group(1))
                        break
                    line = f.readline()'''
            
            with open(os.path.join(targetPath, "abc.out")) as f:
                line = f.readline()
                while line:
                    searchObj = re.search(r'\s+nd\s*=\s*(\d+).*lev\s*=\s*(\d+)', line)
                    if searchObj:
                        #print("nd = ", searchObj.group(1))
                        parseData.abcNplb = int(searchObj.group(1))
                        #print("lev = ", searchObj.group(2))
                        parseData.abcLev = int(searchObj.group(2))
                        line = f.readline()
                        continue
                    '''searchObj = re.search(r'total time used: (\S*)', line)
                    if searchObj:
                        #print("abcRuntime = ", searchObj.group(1))
                        parseData.abcRuntime = float(searchObj.group(1))
                        break'''
                    line = f.readline()

            """ with open(os.path.join(targetPath, "vpr.out")) as f:
                line = f.readline()
                flagVprSuccess = False
                while line:
                    searchObj = re.search(r'Netlist',line)
                    
                    if searchObj:
                        searchObj1 = re.search(r'Netlist clb blocks: (\d+)', line)
                        if searchObj1:
                            #print("vprNclb = ", searchObj1.group(1))
                            parseData.vprNclb = int(searchObj1.group(1))
                            line = f.readline()
                            continue
                    searchObj = re.search(r'Best routing used a channel width factor of (\d+)', line)
                    if searchObj:
                        #print("channelWidth = ", searchObj.group(1))
                        parseData.chanWidth = searchObj.group(1)
                        line = f.readline()
                        continue
                    searchObj = re.search(r'Total used logic block area: (\S+)', line)
                    if searchObj:
                        #print("vprAreaClb = ", searchObj.group(1))
                        parseData.vprAreaClb = searchObj.group(1)
                        line = f.readline()
                        continue
                    searchObj = re.search(r'Total routing area: (\S+),', line)
                    if searchObj:
                        #print("vprAreaRouting = ", searchObj.group(1))
                        parseData.vprAreaRouting = searchObj.group(1)
                        line = f.readline()
                        continue
                    searchObj = re.search(r'Final geomean non-virtual intra-domain period: (\S+) ns', line)
                    if searchObj:
                        #print("vprDelay = ", searchObj.group(1))
                        parseData.vprDelay = float(searchObj.group(1))
                        line = f.readline()
                        continue
                    searchObj = re.search(r'VPR succeeded', line)
                    if searchObj:
                        #print(line)
                        flagVprSuccess = True
                        line = f.readline()
                        continue
                    searchObj = re.search(r'The entire flow of VPR took (\S+) seconds', line)
                    if searchObj:
                        #print("vprRuntime = ", searchObj.group(1))
                        parseData.vprRuntime = float(searchObj.group(1))
                        break
                    line = f.readline()
                if not flagVprSuccess:
                    print("%s VPR Failed!!!!" % (parseData.netlistName))
                #parseData.flowRuntime = parseData.odinRuntime + parseData.abcRuntime + parseData.vprRuntime
                #print("Flow runtime: ", parseData.flowRuntime)
             """
            resDataMap[parseData.netlistName] = parseData
        
        csv=Type+"dsp_res.csv"
        csvFile = os.path.join(outputPath, csv)
        with open(csvFile, 'w') as f:
            f.write("netlist, abcNplb, abcLev, vprDelay, vprAreaClb, vprAreaRouting, vprNclb,vprtime\n")
            for key in resDataMap:
                d = resDataMap[key]
                line = "%s, %d, %d, %f, %s, %s, %d, %f\n" \
                    % (d.netlistName, d.abcNplb, d.abcLev, d.vprDelay, d.vprAreaClb, d.vprAreaRouting, d.vprNclb, d.vprRuntime)
                f.write(line)
    
    def runOdinWrap(self,srcPath,outputPath="."):
        if os.path.isdir(outputPath):
            print(outputPath, "exists.")
        else:
            os.mkdir(outputPath)
            print(outputPath, "is newly created.")
        targetFiles = []
        for path,dirs,files in os.walk(srcPath):
            for fi in files:
                netlistName, fileExt = os.path.splitext(fi)
                if fileExt == '.v':
                    targetFiles.append(os.path.join(srcPath, fi))
                else:
                    print("error, srcfile is not a verilog file")
        print(targetFiles)
        for srcFile in targetFiles:
            runOdin(srcFile,self.archFile,self.configTemplate,outputPath)

            
class WorkerFactory(object):
    def __init__(self, flow, outputPath):
        self.flow = flow
        self.outputPath = outputPath
        
    def __call__(self, srcFile):
        start = time.perf_counter()
        _, fileName = os.path.split(srcFile)
        tmplist = fileName.split('.')
        if tmplist[-1] == 'v':
            netlistName = fileName[:-2]
            self.flow.runOne(srcFile)
        elif tmplist[-1] == 'blif':
            if tmplist[-2] == 'odin':
                netlistName = fileName[:-10]
            else:
                netlistName = fileName[:-5]
            self.flow.runOne(srcFile)
        else:
            print("Error in worker(): invalid file extention: %s" % (tmplist[-1]))
            exit()
        end = time.perf_counter()
        print("Flow for %s runtime: %s Seconds"  % (srcFile, end-start))
    
if __name__ == "__main__":
    parser =argparse.ArgumentParser()
    parser.add_argument('-Type', metavar='Type', type=str, help='The type of PLB')
    args=parser.parse_args()
    Type=args.Type
    start = time.perf_counter()
    print("Now in vtrFlow.py")
    if flagLinux:
        outputPath = resPath+"/"+Type+"_dsp_result"
        configFile = inputPath+"/config.xml"
        parseOutputPath = resPath+"/result"
        odinOutputPath=resPath+"/blif/"
    else:
        vtrFlowPath = "."
        outputPath = "result"
    if Type == "base":
        archFile= inputPath+"/arch/baseline.xml"
        vprK=6
    elif Type == "andlut":
        archFile= inputPath+"/arch/andlut.xml"
        vprK=7
    elif Type == "andandlut":
        archFile= inputPath+"/arch/andandlut.xml"
        vprK=8
    elif Type == "Jason":
        archFile= inputPath+"/arch/Jason.xml"
        vprK=7
    elif Type == "lut2lut":
        archFile= inputPath+"/arch/lut2lut.xml"
        vprK=7
    elif Type == "andlut2":
        archFile= inputPath+"/arch/andlut2.xml"
        vprK=7
    elif Type == "lut2lut2":
        archFile= inputPath+"/arch/lut2lut2.xml"
        vprK=8
    elif Type == "xorlut":
        archFile= inputPath+"/arch/xorlut.xml"
        vprK=7
    else:
        archFile= inputPath+"/arch/baseline.xml"
        vprK=7

    libFile = resPath+"/dsdResult/"+Type+"match.dsd"
    if os.path.isdir(resPath+"/dsdResult/"):
        print(resPath+"/dsdResult/", "exists.")
    else:
        os.mkdir(resPath+"/dsdResult/")
        print(resPath+"/dsdResult/", "is newly created.")
    preMatchFile =  resPath+"/dsdResult/"+Type+".dsd"    
    srcPath = inputPath+"/blif/"
    srcFile=srcPath+fileName
    verisrcPath=inputPath+"/verilog/"
    srcPathdsd = inputPath+"/blif/"
    restoreClkScript =vprFlowPath + "/scripts/restore_multiclock_latch.pl"
    flow = VtrFlow(Type=Type,archFile=archFile,configTemplate=configFile,restoreClkScript=restoreClkScript,libFile=libFile,preMatchFile=preMatchFile,K=vprK, chanWidth=channel_width,outputPath=outputPath)
    if BuildDsdFlag:
        flow.runDsdLib(srcPathdsd)
    if RunOneFileFlag:
        flow.runOne(srcFile)
    if RunOdinFlag:
        flow.runOdinWrap(verisrcPath,outputPath=odinOutputPath)
    if RunSrcPathFlag:
        flow.runSrcPath(srcPath, outputPath,Type)
    if RunParseResFlag:
        flow.parseResult(outputPath, parseOutputPath)
    end = time.perf_counter()
    print("Running time: %s Seconds"  % (end-start))