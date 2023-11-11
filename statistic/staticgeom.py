import sys
sys.path.append(".")
import math

def str2float(item):
    if 'e' not in item:
        return float(item)
    itemVec = item.split('e')
    num = float(itemVec[0])
    exp = 1
    if itemVec[1][0] == '+':
        exp = 10 ** int(itemVec[1][1:])
    else:
        exp = 0.1 ** int(itemVec[1][1:])

    return num * exp

koiosList = "clstm_like.small.v     dla_like.small.v   robot_rl.v                  tiny_darknet_like.small.v \
attention_layer.v    complex_dsp_include.v  eltwise_layer.v    softmax.v                   tpu_like.medium.v \
bnn.v                conv_layer.v           gemm_layer.v       spmv.v                      tpu_like.small.v \
clstm_like.large.v   conv_layer_hls.v       lstm.v             test.v \
clstm_like.medium.v  dla_like.medium.v      reduction_layer.v  tiny_darknet_like.medium.v" 

""" vtrList = "LU32PEEng.v  bgm.v            diffeq2.v           mkSMAdapter4B.v                  raygentop.v    stereovision0.v \
LU64PEEng.v  blob_merge.v     koios               multiclock_output_and_latch.v    sha.v          stereovision1.v \
LU8PEEng.v   boundtop.v       mcml.v              multiclock_reader_writer.v       single_ff.v    stereovision2.v \
and_latch.v  ch_intrinsics.v  mkDelayWorker32B.v  multiclock_separate_and_latch.v  single_wire.v  stereovision3.v \
arm_core.v   diffeq1.v        mkPktMerge.v        or1200.v                         spree.v"
 """
vtrList = "arm_core.v  blob_merge.v boundtop.v ch_intrinsics.v \
    diffeq1.v diffeq2.v  LU8PEEng.v  mkDelayWorker32B.v   mkPktMerge.v   \
    mkSMAdapter4B.v     or1200.v   raygentop.v   sha.v    stereovision0.v  \
    stereovision1.v stereovision2.v stereovision3.v   "
    
if __name__ == "__main__": 
    
    # insert your files here
    fileList = ["/home/uixbyu/testfpga/testfpga/FinalWork/result/basedsp_res.csv","/home/uixbyu/testfpga/testfpga/FinalWork/result/andandlutdsp_res.csv",\
                "/home/uixbyu/testfpga/testfpga/FinalWork/result/lut2lut2dsp_res.csv"]
    # fileList = ["./basedspfull_res.csv","./andlutdspfull_res.csv","./andandlutdspfull_res.csv","./Jasondspfull_res.csv","./lut2lutdspfull_res.csv","lut2lut2dspfull_res.csv"]
    #fileList = ["./basedspfull_res.csv","./andlutdspfull_res.csv"]
    """ fileList = ["/home/uixbyu/testfpga/testfpga/yosysAbcVpr/result/basedspfull_res.csv","/home/uixbyu/testfpga/testfpga/weight/result/andlutdspfull_res.csv","/home/uixbyu/testfpga/testfpga/weight/result/lut2lutdspfull_res.csv","/home/uixbyu/testfpga/testfpga/weight/result/Jasondspfull_res.csv","/home/uixbyu/testfpga/testfpga/weight/result/xorlutdspfull_res.csv" ,"/home/uixbyu/testfpga/testfpga/weight/result/andandlutdspfull_res.csv",\
    "/home/uixbyu/testfpga/testfpga/weight/result/lut2lut2dspfull_res.csv","/home/uixbyu/testfpga/testfpga/weight/result/andlut2dspfull_res.csv"] """
    # insert your baseline here
    #fileBase = "/home/uixbyu/testfpga/testfpga/yosysAbcVpr/result/basedspfull_res.csv"
    fileBase = "/home/uixbyu/testfpga/testfpga/FinalWork/result/basedsp_res.csv"
    #fileBase = "./base300_res.csv"

    # insert your carelist // ignore this if empty
    #careFiles = vtrList + koiosList
    careFiles = vtrList
    # careFiles = "LU32PEEng.odin.blif  arm_core.odin.blif  blob_merge.odin.blif  mcml.odin.blif              mkPktMerge.odin.blif     or1200.odin.blif     sha.odin.blif    stereovision0.odin.blif  stereovision2.odin.blif \
    #         LU8PEEng.odin.blif   bgm.odin.blif       boundtop.odin.blif    mkDelayWorker32B.odin.blif  mkSMAdapter4B.odin.blif  raygentop.odin.blif  spree.odin.blif  stereovision1.odin.blif  stereovision3.odin.blif"
    
    # insert average mode 0/1/2 for ol/arithmetic/geometry
    mode = 2
    
    lineVec = careFiles.split()
    carelist = []
    for file in lineVec:
        carelist.append(file.split(".")[0])
        carelist.append(file.split(".")[0]+".small")
        carelist.append(file.split(".")[0]+".medium")
        carelist.append(file.split(".")[0]+".large")

    results = []
    params = []
    names = []
    names.append("__avg__")
    with open(fileBase, 'r') as fi:
        bench = {}
        line = fi.readline()
        lineVec = line.replace('\n','').replace(' ','').split(",")
        for item in lineVec[1:]:
            params.append(item)
        while line:
            line = fi.readline()
            if len(line) == 0:
                continue
            lineVec = line.replace('\n','').replace(' ','').split(",")
            if len(carelist) > 0 and lineVec[0] not in carelist:
                print("MESSAGE: " + lineVec[0] + " of " + fileList[0] + " not in carelist, ignored")
                continue
            bench[lineVec[0]]={}
            names.append(lineVec[0])
            if len(params) != len(lineVec)-1:
                print("ERROR: " + lineVec[0] + " in " + fileList[0] + " length error")
            for idy in range(1, len(lineVec)):
                bench[lineVec[0]][params[idy-1]] = str2float(lineVec[idy])
        results.append(bench)
        
    

    for file in fileList:
        if file == fileBase:
            continue
        with open(file, 'r') as fi:
            bench = {}
            thisparams = []
            line = fi.readline()
            lineVec = line.replace('\n','').replace(' ','').split(",")
            for item in lineVec[1:]:
                thisparams.append(item)
            while line:
                line = fi.readline()
                if len(line) == 0:
                    continue
                lineVec = line.replace('\n','').replace(' ','').split(",")
                if lineVec[0] not in names:
                    print("MESSAGE: " + lineVec[0] + " of " + file + " not in baseline, ignored")
                    continue
                bench[lineVec[0]]={}
                for idy in range(1, len(lineVec)):
                    bench[lineVec[0]][thisparams[idy-1]] = str2float(lineVec[idy])
        results.append(bench)

    data = []

    for idx in range(1, len(results)):
        benchdata = {}
        parsum = [0.0] * len(params)
        parnum = [0] * len(params)
        for bench in results[idx]:
            benchdata[bench] = []
            for idy in range(0, len(params)):
                param = params[idy]
                if param not in results[idx][bench] or param not in results[0][bench] \
                   or results[idx][bench][param] == 0 or results[0][bench][param] == 0:
                    benchdata[bench].append(-2.0)
                else:
                    deviation = results[idx][bench][param] / results[0][bench][param] - 1
                    benchdata[bench].append(deviation)
                    parnum[idy]+=1
                    parsum[idy]+=deviation
        benchdata["__avg__"] = []
        if mode == 2:
            for idy in range(0, len(params)):
                dataCompare = 1
                dataBase = 1
                dataNum = 0
                for bench in results[idx]:
                    param = params[idy]
                    if param not in results[idx][bench] or param not in results[0][bench] \
                        or results[idx][bench][param] == 0 or results[0][bench][param] == 0:
                        dataCompare += 0
                        dataBase += 0
                    else:
                        if param == "vprAreaRouting" or param == "vprAreaClb":
                            #print (results[idx][bench][param]/100000)
                            tempdata=results[idx][bench][param]/10000000000
                            tempbase=results[0][bench][param]/10000000000
                            dataCompare *= tempdata
                            dataBase *= tempbase
                        dataCompare *= results[idx][bench][param]
                        """ if param == "vprAreaRouting" or param == "vprAreaClb":
                            print ("%s database= %s"  %(param,dataBase))
                            print ("%s datacompare= %s"  %(param,dataCompare)) """
                        dataBase *= results[0][bench][param]
                        dataNum += 1
                benchdata["__avg__"].append(dataCompare**(1.0/dataNum) / dataBase**(1.0/dataNum) - 1)
        elif mode == 1:
            for idy in range(0, len(params)):
                dataCompare = 0
                dataBase = 0
                dataNum = 0
                for bench in results[idx]:
                        param = params[idy]
                        if param not in results[idx][bench] or param not in results[0][bench] \
                            or results[idx][bench][param] == 0 or results[0][bench][param] == 0:
                            dataCompare += 0
                            dataBase += 0
                        else:
                            dataCompare += results[idx][bench][param]
                            dataBase += results[0][bench][param]
                            dataNum += 1
                benchdata["__avg__"].append(dataCompare / dataBase - 1)
        else:
            for idy in range(0, len(params)):
                if parnum[idy] == 0:
                    benchdata["__avg__"].append(-2.0)
                else:
                    benchdata["__avg__"].append(parsum[idy]/parnum[idy])
        data.append(benchdata)
    #log=open('./baseNoTune.csv','w+')
    log=open('./baseWithTune.csv','w+')
    """ print(file=log)
    for param in params:
        print(param,end=" ",file=log)
    print(file=log) """
    for idx in range(0, len(data)):
        print("=============  "+fileList[1+idx]+"  ============",file=log)
        print(file=log)
        print("netlist",end=", ",file=log)
        for param in params:
            print(param,end=", ",file=log)
        print(file=log)
        for name in names:
            if name not in data[idx]:
                continue
            print(name,end=" , ",file=log)
            print(' ' * (30 - len(name)),end="",file=log)
            for idy in range(0, len(params)):
                if(data[idx][name][idy] == -2.0):
                    print("null",end=", ",file=log)
                else:
                    print(round(data[idx][name][idy] * 100, 2),end=", ",file=log)
            print(file=log)
        print(file=log)
