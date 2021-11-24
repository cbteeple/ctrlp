import sys
import os
import copy

from helper_utils import flatten_dict



class ConfigHandler:
    def __init__(self, command_handler):
        self.command_handler = command_handler


    # Parse the config
    def parse_config(self, config):
        self.config={}
        self.config_flat={}

        self.num_channels = config.get("channels", {}).get('num_channels', None)

        if isinstance(config, dict):
            for key in config:
                if key == "max_pressure" or key == "min_pressure":
                    self.config[key]=self.expand_pressure_limits(config[key])
                elif key == "PID":
                    self.config["PID"] = config["PID"]
                    self.config["PID"]['values']=self.expand_pid(config[key])
                else:
                    self.config[key] = config[key]


        self.config_flat = flatten_dict(self.config)
        
        return self.config


    # Expand the pressure limit values
    def expand_pressure_limits(self, value):
        if isinstance(value, list):
            return value
        else:
            if self.num_channels is not None:
                return [value]*self.num_channels
            else:
                return []


    # Expand the PID values
    def expand_pid(self, value):
        all_equal = value.get('all_equal', True)
        values = value.get('values', True)
        if all_equal:
            out=[]
            for i in range(self.num_channels):
                out.append(copy.deepcopy(values))
            return out
        else:
            return values


    # Generate a list of commands to send to the pressure controller
    def get_commands(self):
        cmd_list = []

        for key in self.config_flat:
            cmd = self.command_handler.get_cmd_name(key)

            if cmd is None:
                pass##print("Incorrect Command: %s"%(key))
            else:
                if key == "PID/values":
                    for p_idx, row in enumerate(self.config_flat[key]):
                        row.insert(0,p_idx)
                        cmd_list.append({'cmd':cmd,'args':row})

                else:
                    cmd_list.append({'cmd':cmd,'args':self.config_flat[key]})
                
        return cmd_list


    # Do a soft shutdown
    def shutdown(self):
        pass


    # Upon object deletion, shut down the serial handler
    def __del__(self): 
        self.shutdown()


