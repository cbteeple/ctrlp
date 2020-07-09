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

    # Read in the trajectory and store it in a list of arrays
    def load_raw_data(self, filename):
        pass

    def save_data(self, filename, extension='.pkl'):
        pass


    def _parse_one(self, filename):
        # open the data
        # parse data
        # save parsed data
        print(filename)



    def parse_data(self, filenames):
        if isinstance(filenames, list):
            for filename in filenames:
                self._parse_one(filename)
                
        elif isinstance(filenames, str):
            self._parse_one(filenames)
        else:
            print("ERROR: Please give the data parser one filename or a list of filenames")

if __name__ == '__main__':
    d = DataParser()