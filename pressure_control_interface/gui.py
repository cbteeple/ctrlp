import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fdialog
import os
import sys
import copy
import time
#import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(1, 'utils')
from comm_handler import CommHandler
from get_files import get_save_path, load_yaml, save_yaml


def _from_rgb(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    rgb_int = [0]*3
    for i, color in enumerate(rgb):
        rgb_int[i] = int(color*255)
    return "#%02x%02x%02x" % tuple(rgb_int)


class PressureControlGui:
    def __init__(self):
        self.config = None
        self.pressures = None
        # Get the desired save path from save_paths.yaml
        self.traj_folder = get_save_path(which='traj_built')
        self.config_folder = get_save_path(which='config')
        self.data_base= get_save_path(which='preferred')
        self.curr_flag_file = os.path.join(self.traj_folder,"last_sent.txt")

        self.load_settings()
        self.curr_config_file={'basename':None, 'dirname': os.path.join(self.config_folder, 'control')}


    def load_settings(self, filename="default.yaml"):
        self.settings = load_yaml(os.path.join(self.config_folder,'gui',filename))
        self.file_types = self.settings['file_types']
        self.color_scheme = self.settings['color_scheme']

    def get_config(self, filename):
        try:
            config = load_yaml(filename)
            if isinstance(config, dict):
                if config.get('channels'):
                    basename = os.path.basename(filename)
                    self.status_bar.config(text = 'New config "%s" loaded'%(basename))
                    return config
                else:
                    self.status_bar.config(text ='Incorrect config format')
                    return False
            else:
                self.status_bar.config(text ='Incorrect config format')
                return False
            
        except:
            self.status_bar.config(text ='New config was not loaded')
            return False


    def parse_config(self, config):
        self.config={}

        self.num_channels = config.get("channels", {}).get('num_channels', None)
        self.curr_pressures = [0.0]*self.num_channels

        if isinstance(config, dict):
            for key in config:
                if key == "max_pressure" or key == "min_pressure":
                    self.config[key]=self.expand_pressure_limits(config[key])
                elif key == "PID":
                    self.config[key]=self.expand_pid(config[key])
                else:
                    self.config[key] = config[key]


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


    def send_config(self):
        self.status_bar.config(text ='Sending config...')
        print(self.config)        
        self.status_bar.config(text ='Sent config!')


    def open_config_file(self):
        """Open a file for editing."""
        filepath = fdialog.askopenfilename(
            filetypes=self.file_types,
            initialdir=self.curr_config_file['dirname'],
            initialfile=self.curr_config_file['basename']
        )
        if not filepath:
            return
        new_config = False
        if filepath.endswith(".yaml"):
            new_config = self.get_config(filepath)
        if new_config:
            self.parse_config(new_config)
            basename = os.path.basename(filepath)
            self.curr_config_file['basename'] = basename
            self.curr_config_file['dirname'] = os.path.dirname(filepath)
            self.init_control_sender()
            #self.init_pressure_editor()
            self.txt_edit.delete("1.0", tk.END)
            with open(filepath, "r") as input_file:
                text = input_file.read()
                self.txt_edit.insert(tk.END, text)
            self.window.title(f"Pressure Control Interface | Config Editor - {basename}")
        else:
            self.del_control_sender()

    def save_config_file(self):
        """Save the current file as a new file."""

        filepath = fdialog.asksaveasfilename(
            defaultextension="txt",
            filetypes=self.file_types,
            initialdir=self.curr_config_file['dirname'],
            initialfile=self.curr_config_file['basename']
        )
        if not filepath:
            return
        with open(filepath, "w") as output_file:
            text = self.txt_edit.get(1.0, tk.END)
            output_file.write(text)
        
        self.curr_config_file['basename'] = os.path.basename(filepath)
        self.curr_config_file['dirname'] = os.path.dirname(filepath)
        self.window.title(f"Pressure Control Interface | Config Editor - {os.path.basename(filepath)}")


    def slider_changed(self, slider_num):
        try:
            #self.channels[slider_num][1].set(val)
            scalevar = self.channels[slider_num][2]
            scale_value=round(scalevar.get(), 2)

            scale = self.channels[slider_num][0]
            box = self.channels[slider_num][0]

            scalevar.set(scale_value)
            scale.set(scale_value)
            box.set(scale_value)

            self.curr_pressures[slider_num] = scale_value

            if self.livesend.get():
                self.set_pressure()

            #print(slider_num, scale_value)
        except tk.TclError:
            pass


    def set_pressure(self):
        press = copy.deepcopy(self.curr_pressures)
        press.insert(0, self.transition_speed.get())
        print(press)


    def init_gui(self, config):
        # Make a new window
        self.window = tk.Tk()
        self.window.title("Pressure Control Interface")
        self.window.rowconfigure(0, minsize=200, weight=1)
        self.window.columnconfigure(1, minsize=200, weight=1)

        # Build the text pane, but button pane, and the slider pane
        self.txt_edit = tk.Text(self.window)
        self.fr_sidebar = tk.Frame(self.window, relief=tk.RAISED, bd=2)
        self.status_bar = tk.Label(self.fr_sidebar, text="Hello!",
            foreground=self.color_scheme['secondary_normal'],
            width=10,
            height=3,
            font=('Arial',12))

        self.fr_sidebar.grid(row=0, column=0, sticky="ns")
        self.status_bar.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        self.init_control_editor(config)
        self.window.mainloop()


    def init_control_editor(self, config):
        fr_buttons = tk.Frame(self.fr_sidebar,  bd=2)

        button = ttk.Button(fr_buttons,
            text="Open Config",
            width=20,
            command=self.open_config_file,
        )
        button2 = ttk.Button(fr_buttons,
            text="Save Config",
            width=20,
            command=self.save_config_file,
        )
        #btn = ttk.Button(fr_buttons, text = 'Exit',
        #                command = self.window.destroy,
        #                width=10)

        button.grid(row=1, column=0, sticky="ew", padx=5)
        button2.grid(row=1, column=1, sticky="ew", padx=5)
        #btn.grid(row=1, column=2, sticky="ew", padx=5)

        fr_buttons.grid(row=1, column=0, sticky="ns")
        self.txt_edit.grid(row=0, column=1, sticky="nsew")


    def init_control_sender(self):
        self.fr_send_btns = tk.Frame(self.fr_sidebar, bd=2)
        self.fr_send_btns.grid(row=2, column=0, sticky="ns", pady=20)

        button = ttk.Button(self.fr_send_btns,
            text="Send To Controller",
            command=self.send_config,
        )
        button.grid(row=0, column=0, sticky="ew", padx=5)

        button2 = ttk.Button(self.fr_send_btns,
            text="Open Pressure Control",
            command=self.init_pressure_editor,
        )
        button2.grid(row=0, column=1, sticky="ew", padx=5)


    def del_control_sender(self):
        try:
            self.fr_send_btns.destroy()
        except:
            pass
        

    def del_sliders(self):
        try:
            self.fr_sliders.destroy()
            self.fr_slider_btns.destroy()
        except:
            pass


    def init_pressure_editor(self):
        self.del_sliders()

        self.graph_palette = {}
        self.graph_palette['primary'] = sns.color_palette("bright", self.num_channels)
        self.graph_palette['primary_light'] = sns.color_palette("pastel", self.num_channels)
        sns.set_palette(self.graph_palette['primary'])

        self.livesend = tk.IntVar()
        self.livesend.set(0)
        self.transition_speed = tk.DoubleVar()
        self.transition_speed.set(self.config.get('transitions', 0.0))
        
        self.fr_slider_btns = tk.Frame(self.fr_sidebar, bd=2)
        self.fr_slider_btns.grid(row=99, column=0, sticky="ns", pady=5)

        button = ttk.Button(self.fr_slider_btns,
            text="Set Pressures",
            command=self.set_pressure,
        )

        button.grid(row=0, column=0, sticky="ew", padx=5)

        button2 = ttk.Checkbutton(self.fr_slider_btns,
            text="Send Pressures Live",
            variable=self.livesend,
        )

        button2.grid(row=0, column=1, sticky="ew", padx=5)

        spin = ttk.Spinbox(self.fr_slider_btns,
                width=6,
                from_=0.0, to=1000, increment=0.1,
                textvariable=self.transition_speed,
                font=('Arial', 14),
                )
        spin.grid(row=0, column=2, sticky="ew", padx=5)

        self.fr_sliders = tk.Frame(self.fr_sidebar, bd=2)
        self.fr_sliders.grid(row=98, column=0, sticky="ns", pady=20)
        self.init_sliders(self.fr_sliders)


    def init_sliders(self, fr_sliders):
        self.channels=[]
        for i in range(self.num_channels):
            # Get current info
            curr_max = self.config['max_pressure'][i]
            curr_min = self.config['min_pressure'][i]
            curr_on = self.config['channels']['states'][i]

            if curr_on:
                curr_state = "normal"
            else:
                curr_state = "disabled"

            # Create a variable to share with the slider and spinbox
            spinval = tk.DoubleVar()
            spinval.set(self.curr_pressures[i])
            cb = lambda name, index, val, i=i: self.slider_changed(i)
            spinval.trace("w",cb)

            # Create the slider
            #scale = tk.Scale(fr_sliders, variable=spinval,
            #    orient=tk.VERTICAL, length=130,
            #    from_=curr_max, to=curr_min, resolution=0.1,
            #    state=curr_state,
            #    font=('Arial', 12),
            #    activebackground=self.color_scheme['primary_'+curr_state],
            #    troughcolor=self.color_scheme['secondary_'+curr_state],
            #    )
            scale = tk.Scale(fr_sliders, variable=spinval,
                orient=tk.VERTICAL, length=130,
                from_=curr_max, to=curr_min, resolution=0.1,
                state=curr_state,
                font=('Arial', 12),
                activebackground=_from_rgb(self.graph_palette['primary_light'][i]),
                troughcolor=_from_rgb(self.graph_palette['primary'][i]),
                )
            scale.grid(row=2, column=i, sticky="ew", padx=5)

            # Create the spinbox
            spin = ttk.Spinbox(fr_sliders,
                width=5,
                from_=curr_min, to=curr_max, increment=0.1,
                textvariable=spinval, state=curr_state,
                font=('Arial', 12),
                )
            spin.grid(row=4, column=i, sticky="ew", padx=5, pady=10)

            # Add max and min labels
            label_title = tk.Label(fr_sliders, text="%d"%(i+1), width=2, font=('Arial', 20, 'bold'), state=curr_state)
            label_max = tk.Label(fr_sliders, text="%0.1f"%(curr_max), width=7, font=('Arial', 10), state=curr_state)
            label_min = tk.Label(fr_sliders, text="%0.1f"%(curr_min), width=7, font=('Arial', 10), state=curr_state)
            label_title.grid(row=0, column=i, sticky="s", pady=0)
            label_max.grid(row=1, column=i, sticky="s", pady=0)
            label_min.grid(row=3, column=i, sticky="n", pady=0)

            

            self.channels.append([scale, spin, spinval, label_max, label_min])
        
        def update_sliders(self):
            
            self.channels


if __name__ == "__main__":
    gui = PressureControlGui()
    if len(sys.argv)==2:
        gui.load_settings(sys.argv[1])
    gui.init_gui({})