#!/usr/bin/env python

import time
import sys
import os
import pickle
import yaml

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
        self.time = []
        self.setpoint = []
        self.measured = []
        self.master_pressure = []


    # Read in the raw data
    def _load_raw_data(self, filename):
        fulfile=os.path.join(self.data_path,filename)
        print(fulfile)
        # If filename exists, open it
        with open(fulfile,'r') as f:
            line = f.readline()
            while line:
                line = line.strip()
                self._parse_line(line)
                line = f.readline()
            


    def _parse_line(self, line):
        # If first character is underscore, store that in the "echo" list
        # Else - the line must contain data
            # Split line by tabs
            # Convert first item from ms to sec and store in "time" list
            # If second item is 0, store the rest of the line in "setpoint" list
            # Elif second item is 1, store the rest of the line in "measured" list
            # Elif second item is 2, store the rest of the line in "master_pressure" list
        print(line)

    def _parse_one(self, filename):
        # open the data and parse it
        self._load_raw_data(filename)
        
        # save parsed data in a better format


    def save_data(self, filename, extension='.pkl'):
        out = dict()
        out['echo'] = self.echo
        out['time'] = self.time
        out['setpoint'] = self.setpoint
        out['measured'] = self.measured
        out['master_pressure'] = self.master_pressure

        # Save the data in a file
        pass



    def parse_data(self, filenames):
        if isinstance(filenames, list):
            for filename in filenames:
                self._parse_one(filename)
                
        elif isinstance(filenames, str):
            self._parse_one(filenames)
        else:
            print("ERROR: Please give the data parser one filename or a list of filenames")

if __name__ == '__main__':
    parser = DataParser()
    parser.parse_data('example/setpoint_traj_demo_0000.txt')