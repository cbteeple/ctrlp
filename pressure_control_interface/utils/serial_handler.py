import serial
import time
from datetime import datetime
import sys
import os
import yaml


class SerialHandler:
    def __init__(self):
        self.serial_settings = None
        self.s = None


    def initialize(self, devname=None, baudrate=None, ser=None):
        if devname is not None and baudrate is not None:
            self.s = serial.Serial(devname,baudrate)
        elif ser is not None:
            self.s = ser
        elif self.serial_settings is not None:
            self.s = serial.Serial(self.serial_settings["devname"], self.serial_settings["baudrate"])
        else:
            self.s = None
            raise ValueError("SerialHandler expects either a devname and baudrate, or and existing serial object")


    # Get serial settings from a file
    def read_serial_settings(self, file=None):
        if file is None:
            file_path = os.path.dirname(os.path.realpath(__file__))
            file=os.path.join(file_path,"..","config","comms","serial_config.yaml")
        with open(file) as f:
            # use safe_load instead of load
            serial_settings = yaml.safe_load(f)
            f.close()

        self.serial_settings = serial_settings
        return serial_settings


    # Set serial settings directly
    def get_serial_settings(self):
        return self.serial_settings


    # Set serial settings directly
    def set_serial_settings(self, devname, baudrate):
        self.serial_settings={'devname':devname, 'baudrate':baudrate}


    # Send commands out
    def send_command(self, command, values=None, format="%0.5f"):
        txt = command
        if values is not None:
            print("%s \t %s"%(command, values))
            if isinstance(values, list):
                if values:
                    for val in values:
                        txt+= ";"+format%(val)
            else:
                txt+=";"+format%(values)
        print(txt)
        cmd = txt+'\n'
        self.s.write(cmd.encode())


    # Send a raw string out
    def send_string(self, string, eol='\n'):
        string+=eol
        self.s.write(string.encode())


    # Read one line
    def read_line(self, display=False):
        out=None
        if self.s.in_waiting:  # Or: while ser.inWaiting():
            out= self.s.readline().decode().strip()

        if out is not None and display:
            print(out)

        return out


    def read_all(self, display=False):
        out = []
        while self.s.in_waiting:  # Or: while ser.inWaiting():
            out.append(self.s.readline().decode().strip())

        if len(out) ==0:
            return None
        else:
            if display:
                print(out)
            return out


    # Upon shutdown, close the serial instance
    def shutdown(self):
        if self.s is not None:
            self.s.close()


    # Upon object deletion, shut down the serial handler
    def __del__(self): 
        self.shutdown()