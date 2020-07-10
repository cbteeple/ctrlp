#!/usr/bin/env python

import time
import sys
import os
import pickle
import yaml
import numpy as np

with open("save_paths.yaml") as f:
    save_paths = yaml.safe_load(f)

data_base = save_paths['preferred']
if not os.path.exists(data_base):
    data_base = save_paths['default']
    if not os.path.exists(data_base):
        data_base = ""



class DataParser:
    def __init__(self, data_path = data_base):
        # set up stuff
        self.data_path = data_path
        self.echo = []
        self.setpoint = {'time': [], 'value':[]}
        self.measured = {'time': [], 'value':[]}
        self.master_pressure = {'time': [], 'value':[]}


    # Read in the raw data
    def _load_raw_data(self, filename):
        fulfile=os.path.join(self.data_path,filename)
        print(fulfile)
        # If filename exists, open it
        with open(fulfile,'r') as f:
            line = f.readline()
            cnt=1
            while line:
                line = line.strip()
                self._parse_line(line)
                line = f.readline()
                cnt+=1
                if cnt>10:
                    break
            


    def _parse_line(self, line):
        # If first character is underscore, store that in the "echo" list
        if line[0] == '_':
            self.echo.append(line[1:])
        
        # Else - the line must contain data
        else:
            # Split line by tabs and parse
            line_vec = line.split('\t')
            time_ms = int(line_vec[0])
            time_sec = float(time_ms)/1000.0
            data_type = int(line_vec[1])
            data = [float(x) for x in line_vec[2:]]

            # If second item is 0, store the rest of the line in "setpoint" list
            if data_type ==0:
                self.setpoint['time'].append(time_sec)
                self.setpoint['value'].append(data)

            # Elif second item is 1, store the rest of the line in "measured" list
            elif data_type ==1:
                self.measured['time'].append(time_sec)
                self.measured['value'].append(data)

            # Elif second item is 2, store the rest of the line in "master_pressure" list
            elif data_type ==2:
                self.master_pressure['time'].append(time_sec)
                self.master_pressure['value'].append(data)
            
            
    def parse_data(self, filename):
        if isinstance(filename, str):
            # open the data file and parse it
            self._load_raw_data(filename)
        else:
            print("ERROR: Please give the data parser one filename or a list of filenames")


    def save_data(self, filename):
        fullfile = os.path.join(self.data_path,filename)
        print(fullfile)
        out = dict()
        out['echo'] = self.echo
        out['setpoint'] = self.setpoint
        out['measured'] = self.measured
        out['master_pressure'] = self.master_pressure

        # Save the data in a file
        if filename[-4:] == '.pkl':
            with open(fullfile,'wb') as f:
                pickle.dump(out,f)

        elif filename[-5:] == '.yaml':
            with open(fullfile,'w') as f:
                yaml.dump(out,f)

        elif filename[-4:] == '.csv':
            out = []
            with open(fullfile,'w') as f:
                np.savetxt(f, out, delimiter=",")


if __name__ == '__main__':
    parser = DataParser()

    filenames = ['example/setpoint_traj_demo_0000.txt']
    for filename in filenames:
        parser.parse_data(filename)
        parser.save_data(filename.replace('.txt','.pkl'))