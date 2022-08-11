from multiprocessing.sharedctypes import Value
import numpy as np
import os
from pathlib import Path
import platform
import time
import tempfile
from shutil import copyfile

#we will generate the _kernel-opencl.c file when importing
from distutils.sysconfig import get_python_inc

TotalAllocs=0

MASKID={}
MASKID['ALLV']=0x0000000001
MASKID['Vx']  =0x0000000002
MASKID['Vy']  =0x0000000004
MASKID['Vz']  =0x0000000008
MASKID['Sigmaxx'] =0x0000000010
MASKID['Sigmayy'] =0x0000000020
MASKID['Sigmazz'] =0x0000000040
MASKID['Sigmaxy'] =0x0000000080
MASKID['Sigmaxz'] =0x0000000100
MASKID['Sigmayz'] =0x0000000200
MASKID['Pressure']=0x0000000400
MASKID['SEL_RMS']=0x0000000001
MASKID['SEL_PEAK']=0x0000000002

class StaggeredFDTD_3D_With_Relaxation_BASE():
    def __init__(self, arguments, extra_params={}):
        global NumberSelRMSPeakMaps # Is it necessary to keep these global anymore?
        global NumberSelSensorMaps
        global TotalAllocs
        global AllC
        
        IncludeDir=str(Path(__file__).parent.absolute())+os.sep


        if (type(arguments)!=dict):
            raise TypeError( "The input parameter must be a dictionary")

        for key in arguments.keys():
            if type(arguments[key])==np.ndarray:
                if np.isfortran(arguments[key])==False:
                    #print "StaggeredFDTD_3D: Converting ndarray " + key + " to Fortran convention";
                    arguments[key] = np.asfortranarray(arguments[key])
            elif type(arguments[key])!=str:
                arguments[key]=np.array((arguments[key]))

        if arguments['DT'].dtype==np.dtype('float32'):
            dtype=np.float32
        elif extra_params["BACKEND"] == "METAL":
            raise SystemError("Metal backend only supports single precision")
        else:
            dtype=np.float64

        gpu_kernelSrc=IncludeDir+'_gpu_kernel.c'
        index_src=IncludeDir+'_indexing.h'


        td = 'float'
        if dtype is np.float64:
            td='double'
        extra_params['td'] = td
    
        t0=time.time()
        
        NumberSelRMSPeakMaps=0
        NumberSelSensorMaps=0
        TotalAllocs=0
        
        outparams = self._PrepParamsForKernel(arguments)
        
        #we prepare the kernel code

        self._PostInitScript(arguments, extra_params)
        
        if extra_params["BACKEND"] == "OPENCL":
            SCode = extra_params["SCode"]
            with open(index_src) as f:
                SCode+=f.readlines()
        else:
            SCode = []
            AllC = ''

        LParamFloat = ['DT']
        LParamInt=["N1","N2", "N3", "Limit_I_low_PML", "Limit_J_low_PML", "Limit_K_low_PML", "Limit_I_up_PML","Limit_J_up_PML",\
                "Limit_K_up_PML","SizeCorrI","SizeCorrJ","SizeCorrK","PML_Thickness","NumberSources", "LengthSource","ZoneCount",\
                "SizePMLxp1","SizePMLyp1","SizePMLzp1","SizePML","SizePMLxp1yp1zp1","NumberSensors","TimeSteps","SelRMSorPeak",\
                "SelMapsRMSPeak", "IndexRMSPeak_ALLV","IndexRMSPeak_Vx","IndexRMSPeak_Vy", "IndexRMSPeak_Vz", "IndexRMSPeak_Sigmaxx",\
                "IndexRMSPeak_Sigmayy","IndexRMSPeak_Sigmazz","IndexRMSPeak_Sigmaxy","IndexRMSPeak_Sigmaxz","IndexRMSPeak_Sigmayz",\
                "IndexRMSPeak_Pressure","NumberSelRMSPeakMaps","SelMapsSensors","IndexSensor_ALLV","IndexSensor_Vx","IndexSensor_Vy",\
                "IndexSensor_Vz","IndexSensor_Sigmaxx","IndexSensor_Sigmayy","IndexSensor_Sigmazz","IndexSensor_Sigmaxy",\
                "IndexSensor_Sigmaxz","IndexSensor_Sigmayz","IndexSensor_Pressure","NumberSelSensorMaps","SensorSubSampling",
                "SensorStart"]
        LParamArray=['InvDXDTplus','DXDTminus','InvDXDTplushp','DXDTminushp']
        assert(len(outparams)==(len(LParamFloat)+len(LParamInt)+len(LParamArray)))
        for k in LParamFloat:
            self._InitSymbol(outparams,k,td,SCode)
        for k in LParamInt:
            self._InitSymbol(outparams,k,'unsigned int',SCode)
        for k in LParamArray:
            self._InitSymbolArray(outparams,k,td,SCode)

        if extra_params["BACKEND"] == "OPENCL":
            with open(gpu_kernelSrc) as f:
                SCode+=f.readlines()
            AllC=''
            for l in SCode:
                AllC+=l
            if platform.system() != 'Windows': 
                arguments['PI_OCL_PATH']=IncludeDir+'pi_ocl' # Unused for Metal
        
        

        # Check here for OpenCL on x86-64 Mac Devices
        if extra_params['BACKEND'] == 'OPENCL' and platform.system() =='Darwin' and 'arm64' not in platform.platform() and False:
            print("Executing with C backend...")
            self._OpenCL_86_64(arguments, AllC)
            t0=time.time()-t0
            print ('Time to run low level FDTDStaggered_3D =', t0)
            AllC = ''
            return

        N1=arguments['N1']
        N2=arguments['N2']
        N3=arguments['N3']
                    
        # Might need to change the order to C for Swift, we'll see.
        if extra_params['BACKEND'] == 'METAL':
            ord = 'C'
        else:
            ord = 'F'

        ArrayResCPU={}
        for k in ['Sigma_xx','Sigma_yy','Sigma_zz','Pressure']:
            ArrayResCPU[k]=np.zeros((N1,N2,N3),dtype,order=ord)
        for k in ['Sigma_xy','Sigma_xz','Sigma_yz']:
            ArrayResCPU[k]=np.zeros((N1+1,N2+1,N3+1),dtype,order=ord)
        ArrayResCPU['Vx']=np.zeros((N1+1,N2,N3),dtype,order=ord)
        ArrayResCPU['Vy']=np.zeros((N1,N2+1,N3),dtype,order=ord)
        ArrayResCPU['Vz']=np.zeros((N1,N2,N3+1),dtype,order=ord)

        if 	(arguments['SelRMSorPeak'] &  MASKID['SEL_PEAK']) and (arguments['SelRMSorPeak'] &  MASKID['SEL_RMS']):
            #both peak and RMS
            updims=2 
        else:
            updims=1

        ArrayResCPU['SqrAcc']=np.zeros((N1,N2,N3,outparams['NumberSelRMSPeakMaps'],updims),dtype,order=ord)
        Ns=1
        NumberSnapshots=arguments['SnapshotsPos'].size
        NumberSensors=arguments['IndexSensorMap'].size
        if NumberSnapshots>0:
            Ns=NumberSnapshots
        ArrayResCPU['Snapshots']=np.zeros((N1,N2,Ns),dtype,order=ord)
        TimeSteps=arguments['TimeSteps']
        SensorSubSampling=arguments['SensorSubSampling']
        SensorStart=arguments['SensorStart']
        ArrayResCPU['SensorOutput']=np.zeros((NumberSensors,int(TimeSteps/SensorSubSampling)+1-SensorStart,outparams['NumberSelSensorMaps']),dtype,order=ord)
        
        self._InitiateCommands(AllC)

        ArraysGPUOp={}
        for k in ['LambdaMiuMatOverH','LambdaMatOverH','MiuMatOverH','TauLong','OneOverTauSigma','TauShear','InvRhoMatH',\
                    'Ox','Oy','Oz','SourceFunctions','IndexSensorMap','SourceMap','MaterialMap']:            
            self._CreateAndCopyFromMXVarOnGPU(k,ArraysGPUOp,arguments)
        for k in ['V_x_x','V_y_x','V_z_x']:
            self._ownGpuCalloc(k,td,outparams['SizePMLxp1'],ArraysGPUOp)
        for k in ['V_x_y','V_y_y','V_z_y']:
            self._ownGpuCalloc(k,td,outparams['SizePMLyp1'],ArraysGPUOp)
        for k in ['V_x_z','V_y_z','V_z_z']:
            self._ownGpuCalloc(k,td,outparams['SizePMLzp1'],ArraysGPUOp)
        for k in ['Sigma_x_xx','Sigma_y_xx','Sigma_z_xx','Sigma_x_yy','Sigma_y_yy','Sigma_z_yy','Sigma_x_zz','Sigma_y_zz','Sigma_z_zz']:
            self._ownGpuCalloc(k,td,outparams['SizePML'],ArraysGPUOp)
        for k in ['Sigma_x_xy','Sigma_y_xy','Sigma_x_xz','Sigma_z_xz','Sigma_y_yz','Sigma_z_yz']:
            self._ownGpuCalloc(k,td,outparams['SizePMLxp1yp1zp1'],ArraysGPUOp)
        for k in ['Rxx','Ryy','Rzz']:
            self._ownGpuCalloc(k,td,ArrayResCPU['Sigma_xx'].size,ArraysGPUOp)
        for k in ['Rxy','Rxz','Ryz']:
            self._ownGpuCalloc(k,td,ArrayResCPU['Sigma_xy'].size,ArraysGPUOp)
        if extra_params['BACKEND'] == 'OPENCL':
            for k in ['Vx','Vy','Vz','Sigma_xx','Sigma_yy','Sigma_zz','Pressure','Sigma_xy','Sigma_xz','Sigma_yz','Snapshots','SensorOutput','SqrAcc']:
                self._ownGpuCalloc(k,td,ArrayResCPU[k].size,ArraysGPUOp)
        else:
            for k in ['Vx','Vy','Vz','Sigma_xx','Sigma_yy','Sigma_zz','Pressure','Sigma_xy','Sigma_xz','Sigma_yz','Snapshots']:
                self._ownGpuCalloc(k,td,ArrayResCPU[k].size,ArraysGPUOp)
            for k in ['SensorOutput','SqrAcc']:
                self._CreateAndCopyFromMXVarOnGPU(k, ArraysGPUOp, ArrayResCPU)

        self._PreExecuteScript(arguments, ArraysGPUOp)

        self._Execution(arguments, ArrayResCPU, ArraysGPUOp)
            
        t0=time.time()-t0
        print ('Time to run low level FDTDStaggered_3D =', t0)

        AllC=''
        
        return

    def _PostInitScript(self, arguments):
        raise NotImplementedError("This block must be implemented in a child class!")

    def _InitSymbol(self, IP,_NameVar,td,SCode=[]):
        raise NotImplementedError("This block must be implemented in a child class!")
    
    def _InitSymbolArray(self, IP,_NameVar,td,SCode=[]):
        raise NotImplementedError("This block must be implemented in a child class!")
    
    def _ownGpuCalloc(self, Name,ctx,td,dims,ArraysGPUOp,flags):
        raise NotImplementedError("This block must be implemented in a child class")
    
    def _CreateAndCopyFromMXVarOnGPU(self, Name,ctx,ArraysGPUOp,ArrayResCPU,flags):
        raise NotImplementedError("This block must be implemented in a child class")
    
    def _PrepParamsForKernel(self, arguments):
        global NumberSelRMSPeakMaps
        global NumberSelSensorMaps


        copyParams=['DT','N1','N2','N3','SensorSubSampling','SensorStart','LengthSource','TimeSteps',\
                'SelRMSorPeak','SelMapsRMSPeak','SelMapsSensors','InvDXDTplus','DXDTminus','InvDXDTplushp','DXDTminushp']
        outparams={}
        for c in copyParams:
            outparams[c]=arguments[c]
            
        outparams['PML_Thickness']=arguments['PMLThickness']
            
        outparams['NumberSources']=arguments['SourceFunctions'].shape[0]
        outparams['ZoneCount']=arguments['SPP_ZONES']
        outparams['NumberSensors']=arguments['IndexSensorMap'].size
        
        
        outparams['Limit_I_low_PML']=outparams['PML_Thickness']-1
        outparams['Limit_I_up_PML']=arguments['N1']-outparams['PML_Thickness']
        outparams['Limit_J_low_PML']=outparams['PML_Thickness']-1
        outparams['Limit_J_up_PML']=arguments['N2']-outparams['PML_Thickness']
        outparams['Limit_K_low_PML']=outparams['PML_Thickness']-1
        outparams['Limit_K_up_PML']=arguments['N3']-outparams['PML_Thickness']

        outparams['SizeCorrI']=arguments['N1']-2*outparams['PML_Thickness']
        outparams['SizeCorrJ']=arguments['N2']-2*outparams['PML_Thickness']
        outparams['SizeCorrK']=arguments['N3']-2*outparams['PML_Thickness']

        #//The size of the matrices where the PML is valid depends on the size of the PML barrier
        outparams['SizePML']= arguments['N1']*arguments['N2']*arguments['N3'] - outparams['SizeCorrI']*outparams['SizeCorrJ']*outparams['SizeCorrK']+1
        outparams['SizePMLxp1']= (arguments['N1']+1)*(arguments['N2'])*(arguments['N3']) - outparams['SizeCorrI']*outparams['SizeCorrJ']*outparams['SizeCorrK']+1
        outparams['SizePMLyp1']= arguments['N1']*(arguments['N2']+1)*arguments['N3'] - outparams['SizeCorrI']*outparams['SizeCorrJ']*outparams['SizeCorrK']+1
        outparams['SizePMLzp1']= arguments['N1']*(arguments['N2'])*(arguments['N3']+1) - outparams['SizeCorrI']*outparams['SizeCorrJ']*outparams['SizeCorrK']+1
        outparams['SizePMLxp1yp1zp1']= (arguments['N1']+1)*(arguments['N2']+1)*(arguments['N3']+1) - outparams['SizeCorrI']*outparams['SizeCorrJ']*outparams['SizeCorrK']+1

        for k in ['ALLV','Vx','Vy','Vz','Sigmaxx','Sigmayy','Sigmazz','Sigmaxy','Sigmaxz','Sigmayz','Pressure']:
            outparams['IndexRMSPeak_'+k]=0
            outparams['IndexSensor_'+k]=0
            if arguments['SelMapsRMSPeak'] & MASKID[k]:
                outparams['IndexRMSPeak_'+k]=NumberSelRMSPeakMaps
                NumberSelRMSPeakMaps+=1
            if arguments['SelMapsSensors'] & MASKID[k]:
                outparams['IndexSensor_'+k]=NumberSelSensorMaps
                NumberSelSensorMaps+=1
        outparams['NumberSelRMSPeakMaps']=NumberSelRMSPeakMaps
        outparams['NumberSelSensorMaps']=NumberSelSensorMaps
        return outparams

    def _Execution(self, arguments):
        raise NotImplementedError("This block must be implemented in a child class")
    
    def _Return(self):
        return self.Results