#!/usr/bin/env python

import sorotraj
import os
import sys


setup_location = "traj_setup"
build_location  = "traj_built"


if __name__ == '__main__':
    if len(sys.argv)==2:
        traj = sorotraj.TrajBuilder()
        traj.load_traj_def(os.path.join(setup_location,sys.argv[1]))
        traj.save_traj(os.path.join(build_location,sys.argv[1]))

    else:
        print('make sure you give a filename')
        
        
        
        
        
        