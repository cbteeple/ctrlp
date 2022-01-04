import serial
import time
from datetime import datetime
import sys
import os
import yaml
import csv
import re
from multiprocessing import Process


from .validate_commands import CommandValidator
from .helper_utils import all_equal



class CommandHandler:
    def __init__(self, comm_list):
        self.comm_list = comm_list

        self.validators = []
        self.num_chans = []
        self.cmd_specs = []
        for settings in self.comm_list:
            self.num_chans.append(settings['num_channels'])
            self.cmd_specs.append(settings['cmd_spec'])

            self.validators.append(CommandValidator(settings["cmd_spec"], settings["num_channels"]))


    def get_cmd_spec(self, cmd, by_config_name=False):
        commands=[]
        for validator in self.validators:
            command = validator.get_spec(cmd, by_config_name)
            commands.append(command)

        return commands

    def get_cmd_name(self, config_name):
        commands = self.get_cmd_spec(config_name, by_config_name=True)
        cmd_names=[]
        for cmd in commands:
            if cmd is not None:
                cmd_names.append(cmd['cmd'])
        
        if len(cmd_names)==0:
            return None
        
        if all_equal(cmd_names):
            return cmd_names[0]
        else:
            raise ValueError('Multiple commands retrieved for the same config_name "%s". Resolve conflicts in command spec definitions.'%(config_name))



    def split_command(self, command, values, format="%0.3f"):
        commands_out=[]
        for idx,_ in enumerate(self.comm_list):
            spec = self.validators[idx].get_spec(command)

            if spec is None:
                split_how = None
            else:
                split_how = spec.get('split_how',None)

            split_idx = None
            switch_idx = None

            # If we are not splitting the command, send the same thing to each controller
            if split_how == None:
                commands_out.append({'command':command, 'values':values})

            # If we are splitting the command, determine how
            else:
                if isinstance(values,list) or isinstance(values,tuple):
                    values = list(values)
                    
                    if len(values) ==0:
                        commands_out.append({'command':command, 'values':values})
                        continue

                    split_how_single = split_how.get('single_arg',None)
                    if spec['num_args'][0] == len(values):
                        if split_how_single is None:
                            commands_out.append({'command':command, 'values':values})
                        elif 'channel' in split_how_single:
                            channel = 0
                            split_idx = eval(split_how_single)
                        
                        elif 'idx' in split_how_single:
                            channel = 0
                            switch_idx = int(re.match('.*?([0-9]+)$', split_how_single).group(1))
                        else:
                            commands_out.append(None)

                    
                    else:
                        split_how_multi = split_how.get('multi_arg',None)

                        if split_how_multi is None:
                            commands_out.append({'command':command, 'values':values})
                        elif 'channel' in split_how_multi:
                            channel = 0
                            split_idx = eval(split_how_multi)
                        
                        elif 'idx' in split_how_multi:
                            channel = 0
                            switch_idx = int(re.match('.*?([0-9]+)$', split_how_single).group(1))
                        else:
                            commands_out.append(None)
                else:
                    commands_out.append({'command':command, 'values':values})

            max_chan = sum(self.num_chans[0:idx+1])
            min_chan = sum(self.num_chans[0:idx])

            if split_idx is not None:
                curr_vals = values[0:split_idx]

                if len(values) >=max_chan+split_idx:
                    curr_vals.extend(values[min_chan+split_idx:max_chan+split_idx])
                
                else:
                    curr_vals.extend(values[min_chan+split_idx:])

                commands_out.append({'command':command, 'values':curr_vals})

            elif switch_idx is not None:
                if values[switch_idx] < max_chan and values[switch_idx] >= min_chan:
                    values[switch_idx] = float(values[switch_idx]) - min_chan
                    commands_out.append({'command':command, 'values':values})
                else:
                    commands_out.append(None)

        return commands_out




class CommHandler:
    def __init__(self):
        self.serial_settings = None
        self.s = None


    def initialize(self, devname=None, baudrate=None, ser=None):
        if devname is not None and baudrate is not None:
            self.s = [serial.Serial(devname,baudrate, timeout=0)]
        elif ser is not None:
            self.s = [ser]
        elif self.serial_settings is not None:
            self.s = []
            for settings in self.serial_settings:
                self.s.append(serial.Serial(settings["devname"], settings["baudrate"], timeout=0))
        else:
            self.s = None
            raise ValueError("CommHandler expects either a devname and baudrate, or and existing serial object")


        self.command_handler=CommandHandler(self.serial_settings)
        self.validator = []
        self.loggers   = []
        for idx, settings in enumerate(self.serial_settings):
            validator_curr = self.command_handler.validators[idx]
            self.validator.append(validator_curr)
            self.loggers.append(DataSaver(settings,validator_curr))
                


    # Get serial settings from a file
    def read_serial_settings(self, file=None):
        file_path = os.path.dirname(os.path.realpath(__file__))
        if file is None:
            file=os.path.join(file_path,"..","config","comms","comms_config.yaml")
        with open(file) as f:
            # use safe_load instead of load
            hardware_settings = yaml.safe_load(f)
            f.close()

        hw_file = hardware_settings.get('hardware')
        devnames = hardware_settings.get('devnames')

        hw_fullfile=os.path.join(file_path,"..","config","hardware",hw_file+".yaml")
        with open(hw_fullfile) as f:
            # use safe_load instead of load
            serial_settings = yaml.safe_load(f)
            f.close()

        for idx, obj in enumerate(serial_settings):
            obj['devname'] = devnames[idx]

            if obj.get('type', None) is None:
                obj['type'] = 'pressure'

        self.serial_settings = serial_settings
        return serial_settings


    # Set serial settings directly
    def set_serial_settings(self, settings=None, hw_profile=None, devices=None):
        if settings is None:
            if hw_profile is not None and devices is not None:
                file_path = os.path.dirname(os.path.realpath(__file__))
                hw_fullfile=os.path.join(file_path,"..","config","hardware",hw_profile)
                with open(hw_fullfile) as f:
                    # use safe_load instead of load
                    settings = yaml.safe_load(f)

                for idx, obj in enumerate(settings):
                    obj['devname'] = devices[idx]

                    if obj.get('type', None) is None:
                        obj['type'] = 'pressure'
        
        self.serial_settings = settings
        return settings


    # Set serial settings directly
    def get_serial_settings(self):
        return self.serial_settings


    # Send commands out
    def send_command(self, command, values=None, format="%0.3f"):
        cmd_obj = self.command_handler.split_command(command, values)

        cmd = []
        for cmd_curr, validator in zip(cmd_obj, self.validator):
            if cmd_curr is None:
                cmd.append(None)
            else:
                cmd.append(validator.build_cmd_string(cmd_curr['command'], cmd_curr['values'], format) )
            


        #print(cmd, len(cmd))

        for ser, cmd_curr in zip(self.s,cmd):
            if cmd_curr is not None:
                ser.write(cmd_curr.encode())

                        

    # Send a raw string out
    def send_string(self, string, eol='\n'):
        string+=eol

        for ser in self.s:
            ser.write(string.encode())


    # Read one line
    def read_line(self, display=False, raw=False):
        out=[None]*len(self.s)

        for idx,ser in enumerate(self.s):
            curr_line = None
            if ser.in_waiting:  # Or: while ser.inWaiting():
                curr_line = ser.readline().decode().strip()
                out[idx] = curr_line
            
            if curr_line is not None and display:
                print(curr_line)
        
        if out == [None]*len(self.s):
            return None

        elif raw:
            return out

        else:
            new_out = []
            for idx,_ in enumerate(out):
                line = self.validator[idx].process_line(out[idx])
                if line is None:
                    new_out.append(None)
                
                else:
                    new_out.append(line[0])

            if new_out == [None]*len(self.s):
                return None
            
            return new_out 


    def read_all(self, display=False, raw=False):
        out = []

        new_line = []
        while new_line != None:  # Or: while ser.inWaiting():
            new_line = self.read_line(display, raw)

            if new_line is not None:
                out.append(new_line)

        if len(out) ==0:
            return None
        else:
            return out


    def save_init(self, filename, filetype='csv'):
        for idx,logger in enumerate(self.loggers):
            file, file_extension = os.path.splitext(filename)
            logger.save_init(file+"_%02d"%(idx)+file_extension,filetype)


    def save_data_lines(self,data_lines):
        for line in data_lines:
            self.save_data_line(line)

    def save_data_line(self,data_line):
        for idx, _ in enumerate(self.serial_settings):
            self.loggers[idx].save_data_line(data_line[idx]) 


    # Upon shutdown, close the serial instance
    def shutdown(self):
        if self.s is not None:
            for ser in self.s:
                ser.close()
        for logger in self.loggers:
            logger.shutdown()


    # Upon object deletion, shut down the serial handler
    def __del__(self): 
        self.shutdown()



class DataSaver:
    def __init__(self, serial_settings, validator):
        self.serial_settings = serial_settings
        self.validator = validator

        self.out_file = None
        self.file_writer = None


    def save_init(self, filename, filetype='csv'):
        num_channels = self.serial_settings['num_channels']

        data_to_save = self.validator.cmd_data['types'].keys()
        data_flat_labels = ['time']
        data_labels      = ['time']
        data_lens        = [1]

        for data_type in data_to_save:
            curr_type = self.validator.cmd_data['types'][data_type]

            curr_label = curr_type['label']
            curr_len   = curr_type['length']

            if curr_len == 'num_channels':
                curr_len = num_channels

            data_labels.append(curr_label)
            data_lens.append(curr_len)

            if curr_len>1:
                for idx in range(curr_len):
                    data_flat_labels.append(curr_label+"[%d]"%(idx))
            else:
                data_flat_labels.append(curr_label)


        data_labels.extend(['_command', '_args'])
        data_flat_labels.extend(['_command', '_args'])
        data_lens.extend([1,1])
        self.data_to_save = data_to_save
        self.data_labels = data_labels
        self.data_lens = data_lens
        self.data_flat_labels = data_flat_labels


        self.out_file = open(filename, "w+")
        self.file_writer = csv.writer(self.out_file)
        self.file_writer.writerow(self.data_flat_labels)


    def save_data_lines(self,data_lines):
        for line in data_lines:
            self.save_data_line(line)


    def save_data_line(self,data_line):
        try:
            if data_line is None:
                return

            data=[]
            for idx,key in enumerate(self.data_labels):
    
                expected_len = self.data_lens[idx]
                dat = data_line.get(key,None)
                if isinstance(dat, list):
                    for curr_dat in dat:
                        data.append(curr_dat)

                    if expected_len > len(dat):
                        for idx in range(expected_len-len(dat)):
                            data.append("")

                    if expected_len < len(dat):
                        print("data array is longer than we expected")

                elif dat is not None:
                    data.append(dat)
                else:
                    for idx in range(expected_len):
                        data.append("")
            self.file_writer.writerow(data)
        except IOError:
            print("I/O error")


    # Upon shutdown, close the serial instance
    def shutdown(self):
        if self.out_file is not None:
            self.out_file.close()


    def __del__(self): 
        self.shutdown()