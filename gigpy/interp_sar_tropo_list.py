#! /usr/bin/env python
#################################################################
###  This program is part of PyGPS  v2.0                      ### 
###  Copy Right (c): 2019, Yunmeng Cao                        ###  
###  Author: Yunmeng Cao                                      ###                                                          
###  Email : ymcmrs@gmail.com                                 ###
###  Univ. : King Abdullah University of Science & Technology ###   
#################################################################
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import os
import re
import subprocess
import argparse
import numpy as np
import h5py
from pygps import elevation_models

import pygps._utilities as ut
from pykrige import OrdinaryKriging

from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
###############################################################
    
def cmdLineParse():
    parser = argparse.ArgumentParser(description='Generate high-resolution tropospheric product map for a list of SAR acquisitions',formatter_class=argparse.RawTextHelpFormatter,epilog=INTRODUCTION+'\n'+EXAMPLE)
    parser.add_argument('date_list', help='SAR acquisition date.')
    parser.add_argument('gps_file',help='input file name (e.g., gps_aps_variogram.h5).')
    parser.add_argument('geo_file',help='input geometry file name (e.g., geometryRadar.h5).')
    parser.add_argument('--type', dest='type', choices = {'tzd','wzd'}, default = 'tzd',help = 'type of the high-resolution tropospheric map.[default: tzd]')
    parser.add_argument('--method', dest='method', choices = {'kriging','weight_distance'},default = 'kriging',help = 'method used to interp the high-resolution map. [default: kriging]')
    parser.add_argument('-o','--out', dest='out_file', metavar='FILE',help='name of the prefix of the output file')
    parser.add_argument('--parallel', dest='parallelNumb', type=int, default=1, help='Enable parallel processing and Specify the number of processors.')
    parser.add_argument('--kriging-points-numb', dest='kriging_points_numb', type=int, default=20, help='Number of the closest points used for Kriging interpolation. [default: 20]')
       
    inps = parser.parse_args()

    return inps


INTRODUCTION = '''
##################################################################################
   Copy Right(c): 2019, Yunmeng Cao   @PyGPS v2.0
   
   Generate high-resolution GPS-based tropospheric maps (delays & water vapor) for InSAR Geodesy & meteorology.
'''

EXAMPLE = """Example:
  
  interp_sar_tropo_list.py date_list gps_file geometryRadar.h5 --type tzd
  interp_sar_tropo_list.py date_list gps_file geometryRadar.h5 --type wzd --parallel 8
  interp_sar_tropo_list.py date_list gps_file geometryRadar.h5 --method kriging -o 20190101_gps_aps_kriging.h5
  interp_sar_tropo_list.py date_list gps_file geometryRadar.h5 --method kriging --kriging-points-numb 15
  interp_sar_tropo_list.py date_list gps_file geometryRadar.h5 --method weight_distance
  interp_sar_tropo_list.py date_list gps_file geometryRadar.h5 --type tzd 
  interp_sar_tropo_list.py date_list gps_file geometryRadar.h5 --type wzd --parallel 4
  
###################################################################################
"""

###############################################################

def main(argv):
    
    inps = cmdLineParse()
    date_list_txt = inps.date_list
    gps_file = inps.gps_file
    geo_file = inps.geo_file
      
    date_list = np.loadtxt(date_list_txt,dtype=np.str)
    date_list = date_list.tolist()
    N=len(date_list)

    for i in range(N):
        out0 = date_list[i] + '_' + inps.type + '.h5'
        if not os.path.isfile(out0):
            #print('-------------------------------------------------------------')
            #print('Start to interpolate high-resolution map for date: %s' % date_list[i])
            call_str = 'interp_sar_tropo.py ' + date_list[i] + ' gps_aps_variogramModel.h5 ' + inps.geo_file + ' --type ' + inps.type + ' --method ' + inps.method + '  --kriging-points-numb ' + str(inps.kriging_points_numb) + ' --parallel ' + str(inps.parallelNumb)
            os.system(call_str)
    
    sys.exit(1)
    
###############################################################

if __name__ == '__main__':
    main(sys.argv[:])