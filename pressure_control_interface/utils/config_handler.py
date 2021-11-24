import sys
import os
import collections

#from comm_handler import build_cmd_string

def flatten_dict(d, parent_key='', sep='/'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


class ConfigHandler:
    def __init__(self, comm_handler):
        self.comm_handler = comm_handler


    def parse_config(self, config):
        self.config={}
        self.config_flat={}

        self.num_channels = config.get("channels", {}).get('num_channels', None)

        if isinstance(config, dict):
            for key in config:
                if key == "max_pressure" or key == "min_pressure":
                    self.config[key]=self.expand_pressure_limits(config[key])
                elif key == "PID":
                    self.config[key]=self.expand_pid(config[key])
                else:
                    self.config[key] = config[key]


        self.config_flat = flatten_dict(self.config)
        
        return self.config


    def expand_pressure_limits(self, value):
        if isinstance(value, list):
            return value
        else:
            if self.num_channels is not None:
                return [value]*self.num_channels
            else:
                return []


    def expand_pid(self, value):
        all_equal = value.get('all_equal', True)
        values = value.get('values', True)
        if all_equal:
            return [values]*self.num_channels
        else:
            return values


    def get_commands(self):
        cmd_list = []

        for key in self.config_flat:
            self.config_flat[key]

        return cmd_list



    # Do a soft shutdown
    def shutdown(self):
        pass


    # Upon object deletion, shut down the serial handler
    def __del__(self): 
        self.shutdown()


