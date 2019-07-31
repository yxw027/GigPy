#! /usr/bin/env python
#################################################################
###  This program is part of PyGPS  v2.0                      ### 
###  Copy Right (c): 2019, Yunmeng Cao                        ###  
###  Author: Yunmeng Cao                                      ###                                                          
###  Email : ymcmrs@gmail.com                                 ###
###  Univ. : King Abdullah University of Science & Technology ###   
#################################################################

import numpy as np
import os
import sys  
import subprocess
import getopt
import time
import glob
import argparse
from pykrige import OrdinaryKriging
import random
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import h5py

import random
import pykrige
from pykrige import OrdinaryKriging
from pykrige import variogram_models

import matlab.engine
#######################################################

def read_hdf5(fname, datasetName=None, box=None):
    # read hdf5
    with h5py.File(fname, 'r') as f:
        data = f[datasetName][:]
        atr = dict(f.attrs)
        
    return data, atr

def write_gps_h5(datasetDict, out_file, metadata=None, ref_file=None, compression=None):
    #output = 'variogramStack.h5'
    'lags                  1 x N '
    'semivariance          M x N '
    'sills                 M x 1 '
    'ranges                M x 1 '
    'nuggets               M x 1 '
    
    if os.path.isfile(out_file):
        print('delete exsited file: {}'.format(out_file))
        os.remove(out_file)

    print('create HDF5 file: {} with w mode'.format(out_file))
    dt = h5py.special_dtype(vlen=np.dtype('float64'))

    
    with h5py.File(out_file, 'w') as f:
        for dsName in datasetDict.keys():
            data = datasetDict[dsName]
            ds = f.create_dataset(dsName,
                              data=data,
                              compression=compression)
        
        for key, value in metadata.items():
            f.attrs[key] = str(value)
            #print(key + ': ' +  value)
    print('finished writing to {}'.format(out_file))
        
    return out_file  
 
#########################################################################

INTRODUCTION = '''
#############################################################################
   Copy Right(c): 2019, Yunmeng Cao   @PyGPS v2.0
   
   Variogram model estimation of the GPS tropospheric measurements.
'''

EXAMPLE = '''
    Usage:
            gps_variogram_modeling.py gps_aps_variogram.h5 
            gps_variogram_modeling.py gps_aps_variogram.h5  --model gaussian
            gps_variogram_modeling.py gps_pwv_variogram.h5  --max-length 150 --model spherical

##############################################################################
'''


def cmdLineParse():
    parser = argparse.ArgumentParser(description='Check common busrts for TOPS data.',\
                                     formatter_class=argparse.RawTextHelpFormatter,\
                                     epilog=INTRODUCTION+'\n'+EXAMPLE)

    parser.add_argument('input_file',help='input file name (e.g., gps_aps_variogram.h5).')
    parser.add_argument('-m','--model', dest='model', default='spherical',
                      help='variogram model used to fit the variance samples')
    parser.add_argument('--max-length', dest='max_length',type=float, metavar='NUM',
                      help='used bin ratio for mdeling the structure model.')
    parser.add_argument('-o','--out_file', dest='out_file', metavar='FILE',
                      help='name of the output file')

    inps = parser.parse_args()

    return inps

################################################################################    
    
    
def main(argv):
    
    inps = cmdLineParse() 
    FILE = inps.input_file
    
    date,meta = read_hdf5(FILE, datasetName='date')
    variance_tzd = read_hdf5(FILE, datasetName='Semivariance')[0]
    variance_wzd = read_hdf5(FILE, datasetName='Semivariance_wzd')[0]
 
    Lags = read_hdf5(FILE, datasetName='Lags')[0]
    
    if inps.max_length:
        max_lag = inps.max_length
    else:
        max_lag = max(lag) + 0.001
    meta['max_length'] = max_lag
    r0 = np.asarray(1/2*max_lag)
    range0 = r0.tolist()
    
    datasetDict = dict()
    datasetDict['Lags'] = Lags
    
    if inps.out_file:
        OUT = os.path.out_file
    elif 'pwv' in os.path.basename(FILE):
        OUT = 'gps_pwv_variogramModel.h5'
    else:
        OUT = 'gps_aps_variogramModel.h5'
    
    eng = matlab.engine.start_matlab()
    
    row,col = variance_tzd.shape
    model_parameters = np.zeros((row,4),dtype='float32')   # sill, range, nugget, Rs
    model_parameters_wzd = np.zeros((row,4),dtype='float32')   # sill, range, nugget, Rs
    for i in range(row):
        lag = Lags[i,:]
        LL0 = lag[lag < max_lag]
        
        S0 = variance_tzd[i,:]
        SS0 = S0[lag < max_lag]
        sill0 = max(SS0)
        sill0 = sill0.tolist()
       
        LLm = matlab.double(LL0.tolist())
        SSm = matlab.double(SS0.tolist())
       
        tt = eng.variogramfit(LLm,SSm,range0,sill0,[],'nugget',0.00001,'model',inps.model)
        model_parameters[i,:] = np.asarray(tt)
        #print(model_parameters[i,3])
        
        S0 = variance_wzd[i,:]
        SS0 = S0[lag < max_lag]
        sill0 = max(SS0)
        sill0 = sill0.tolist()
       
        LLm = matlab.double(LL0.tolist())
        SSm = matlab.double(SS0.tolist())
       
        tt = eng.variogramfit(LLm,SSm,range0,sill0,[],'nugget',0.00001,'model',inps.model)
        model_parameters_wzd[i,:] = np.asarray(tt)
        #print(model_parameters_wzd[i,3])
        
    meta['variogram_model'] = inps.model
    #meta['elevation_model'] = meta['elevation_model']    
    #del meta['model']
    
    datasetNames = ['date','gps_name','gps_lat','gps_lon','gps_height','hzd','wzd','tzd','wzd_turb_trend','tzd_turb_trend','wzd_turb','tzd_turb','station','tzd_elevation_parameter', 'wzd_elevation_parameter','tzd_trend_parameter', 'wzd_trend_parameter']
    
    datasetDict = dict()
    for dataName in datasetNames:
        datasetDict[dataName] = read_hdf5(FILE,datasetName=dataName)[0]
    
    datasetDict['tzd_variogram_parameter'] = model_parameters  
    datasetDict['wzd_variogram_parameter'] = model_parameters_wzd  
    eng.quit()
    write_gps_h5(datasetDict, OUT, metadata=meta, ref_file=None, compression=None) 
    
    sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[:])
