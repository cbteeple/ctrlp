import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fdialog
import os
import sys
import copy
import time
from serial.tools import list_ports
#import matplotlib.pyplot as plt
import seaborn as sns
import threading

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



class popupWindow(object):
    def __init__(self,master, comm_options=None, hw_options=None):
        if comm_options is None:
            comm_options=self.get_ports()
        if hw_options is None:
            hw_options = []
        baud_options = [110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200, 128000, 256000]
        top=self.top=tk.Toplevel(master)
        top.title('Serial Config')
        self.fr = tk.Frame(top, bd=2)
        self.fr.pack()
        self.comvar = tk.StringVar()
        self.hwvar = tk.StringVar()
        self.baudvar = tk.StringVar()
        self.l=tk.Label(self.fr, text='Choose a Device:', width=30)
        self.l.grid(row=0, column=0, sticky='ew', pady=5, padx=10)

        self.e=ttk.OptionMenu(self.fr, self.hwvar, hw_options[0], *hw_options)
        self.e.grid(row=1, column=0, sticky='ew', pady=5, padx=10)
        self.e=ttk.OptionMenu(self.fr, self.comvar, comm_options[0], *comm_options)
        self.e.grid(row=2, column=0, sticky='ew', pady=5, padx=10)
        self.e=ttk.OptionMenu(self.fr, self.baudvar, 115200, *baud_options)
        self.e.grid(row=3, column=0, sticky='ew', pady=5, padx=10)

        self.b=ttk.Button(self.fr,text='Ok',command=self.cleanup, width=30)
        self.b.grid(row=99, column=0, sticky='ew', pady=5, padx=10)

    def get_ports(self):
        ports = list(list_ports.comports())
        comports = []
        for p in ports:
            comports.append(p.device)
        return comports

    def cleanup(self):
        self.comports=[self.comvar.get()]
        self.baudrate=self.baudvar.get()
        self.hw_profile = self.hwvar.get()
        self.top.destroy()


class PressureControlGui:
    def __init__(self):
        self.config = None
        self.pressures = None
        self.ctrlp = None
        self.read_thread = None
        self.send_thread = None
        # Get the desired save path from save_paths.yaml
        self.traj_folder = get_save_path(which='traj_built')
        self.config_folder = get_save_path(which='config')
        self.data_base= get_save_path(which='preferred')
        self.curr_flag_file = os.path.join(self.traj_folder,"last_sent.txt")

        self.load_settings()
        self.curr_config_file={'basename':None, 'dirname': os.path.join(self.config_folder, 'control')}



    def connect_to_controller(self, hw_profile=None, devices=None):
        self.ctrlp = CommHandler()
        if hw_profile is None or devices is None:
            self.ctrlp.read_serial_settings()
        else:
            self.ctrlp.set_serial_settings(hw_profile=hw_profile,devices=devices)
        self.ctrlp.initialize()
        time.sleep(2.0)
        
        self.run_read_thread = True
        self.read_thread = threading.Thread(target=self.read_data)
        self.read_thread.start()

        self.ctrlp.send_command("echo",1)
        self.ctrlp.send_command("speed",200)
        self.ctrlp.send_command("cont",1)
        #self.ctrlp.send_command("echo",0)
        self.ctrlp.send_command("on",None)


    def start_pressure_thread(self):
        if self.send_thread is None:
            self.run_read_thread = True
            self.send_thread = threading.Thread(target=self.set_pressure_threaded)
            self.send_thread.start()






    def load_settings(self, filename="default.yaml"):
        self.settings = load_yaml(os.path.join(self.config_folder,'gui',filename))

        hw_path = os.path.join(self.config_folder,'hardware')
        self.hw_options = [f for f in os.listdir(hw_path) if os.path.isfile(os.path.join(hw_path, f))]

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
            self.root.title(f"Pressure Control Interface | Config Editor - {basename}")
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
        self.root.title(f"Pressure Control Interface | Config Editor - {os.path.basename(filepath)}")


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

            #if self.livesend.get():
            #    self.set_pressure()

            #print(slider_num, scale_value)
        except tk.TclError:
            pass
        except IndexError:
            pass


    def _set_pressure(self):
        press = copy.deepcopy(self.curr_pressures)
        press.insert(0, self.transition_speed.get())

        if self.ctrlp:
            self.ctrlp.send_command("set",press)
        
        #print(press)

    def set_pressure(self):
        if self.livesend.get():
            return
        else:
            self._set_pressure()
            return


    def set_data_stream(self):
        if self.live_data.get():
            self.ctrlp.send_command("on",None)
        else:
            self.ctrlp.send_command("off",None)


    def read_data(self):
        while self.run_read_thread:
            line=self.ctrlp.read_all()
            if line:
                print(line)

    
    def set_pressure_threaded(self):
        while self.run_read_thread:
            if self.livesend.get():
                self._set_pressure()
            time.sleep(0.1)
            


    def get_serial_setup(self):
        self.connect_btn['state']='disabled'
        self.w=popupWindow(self.root, hw_options=self.hw_options)
        self.root.wait_window(self.w.top)
        print(self.w.hw_profile)
        print(self.w.baudrate)
        print(self.w.comports)
        self.connect_btn['state']='normal'
        self.connect_to_controller(hw_profile=self.w.hw_profile, devices=self.w.comports,)


    def init_gui(self, config):
        # Make a new window
        self.root = tk.Tk()
        self.root.title("Pressure Control Interface")
        self.root.rowconfigure(0, minsize=200, weight=1)
        self.root.columnconfigure(1, minsize=200, weight=1)

        # Build the text pane, but button pane, and the slider pane
        self.txt_edit = tk.Text(self.root)
        self.txt_edit.grid(row=0, column=1, sticky="nsew")
        
        self.fr_sidebar = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        self.status_bar = tk.Label(self.fr_sidebar, text="Hello!",
            foreground=self.color_scheme['secondary_normal'],
            width=10,
            height=3,
            font=('Arial',12))

        self.fr_sidebar.grid(row=0, column=0, sticky="ns")
        self.status_bar.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        self.init_control_editor(config)

        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.root.mainloop()


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
        #                command = self.root.destroy,
        #                width=10)

        button.grid(row=1, column=0, sticky="ew", padx=5)
        button2.grid(row=1, column=1, sticky="ew", padx=5)
        #btn.grid(row=1, column=2, sticky="ew", padx=5)

        fr_buttons.grid(row=1, column=0, sticky="ns")


    def init_control_sender(self):
        self.fr_send_btns = tk.Frame(self.fr_sidebar, bd=2)
        self.fr_send_btns.grid(row=2, column=0, sticky="ns", pady=20)

        button = ttk.Button(self.fr_send_btns,
            text="Send Config",
            command=self.send_config,
        )
        button.grid(row=0, column=1, sticky="ew", padx=5)

        button2 = ttk.Button(self.fr_send_btns,
            text="Open Sliders",
            command=self.init_pressure_editor,
        )
        button2.grid(row=0, column=2, sticky="ew", padx=5)

        self.connect_btn = ttk.Button(self.fr_send_btns,
            text="Connect Controller",
            command=self.get_serial_setup,
        )

        self.connect_btn.grid(row=0, column=0, sticky="ew", padx=5)


    def del_control_sender(self):
        try:
            self.fr_send_btns.destroy()
        except:
            pass
        

    def del_sliders(self):
        try:
            self.fr_sliders.destroy()
            self.fr_slider_btns.destroy()
            for chan in self.channels:
                for item in chan:
                    item.destroy()
        except:
            pass


    def set_graph_colors(self):
        self.graph_palette = {}
        graph_colors = self.color_scheme['graph']
        for color_key in graph_colors:
            palette = graph_colors[color_key].get('palette',None)
            args = graph_colors[color_key].get('args', {})
            if isinstance(palette, list):
                self.graph_palette[color_key] = palette
            elif isinstance(palette, str):
                if palette == "hls":
                    self.graph_palette[color_key] = sns.hls_palette(self.num_channels, **args)
                elif palette == "husl":
                    self.graph_palette[color_key] = sns.husl_palette(self.num_channels, **args)
                elif palette == "dark":
                    self.graph_palette[color_key] = sns.dark_palette(self.num_channels, **args)
                elif palette == "light":
                    self.graph_palette[color_key] = sns.light_palette(self.num_channels, **args)
                elif palette == "diverging":
                    self.graph_palette[color_key] = sns.diverging_palette(self.num_channels, **args)
                elif palette == "diverging":
                    self.graph_palette[color_key] = sns.diverging_palette(self.num_channels, **args)
                elif palette == "blend":
                    self.graph_palette[color_key] = sns.blend_palette(self.num_channels, **args)
                elif palette == "xkcd":
                    self.graph_palette[color_key] = sns.xkcd_palette(self.num_channels, **args)
                elif palette == "crayon":
                    self.graph_palette[color_key] = sns.crayon_palette(self.num_channels, **args)
                elif palette == "mpl":
                    self.graph_palette[color_key] = sns.mpl_palette(self.num_channels, **args)
                else:
                    self.graph_palette[color_key] = sns.color_palette(palette, self.num_channels)
            else:
                self.graph_palette[color_key] = sns.color_palette("bright", self.num_channels)

        sns.set_palette(self.graph_palette['primary'])


    def init_pressure_editor(self):
        self.del_sliders()

        self.set_graph_colors()

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


        self.live_data = tk.IntVar()
        self.live_data.set(1)
        cb = lambda name, index, val: self.set_data_stream()
        self.live_data.trace("w",cb)
        button3 = ttk.Checkbutton(self.fr_slider_btns,
            text="Data Stream",
            variable=self.live_data,
        )

        button3.grid(row=0, column=3, sticky="ew", padx=5)

        self.fr_sliders = tk.Frame(self.fr_sidebar, bd=2)
        self.fr_sliders.grid(row=98, column=0, sticky="ns", pady=20)
        self.init_sliders(self.fr_sliders)

        self.start_pressure_thread()


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


    def on_window_close(self):
        if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.shutdown()
            self.root.destroy()
            

    def shutdown(self):
        try:
            self.run_read_thread = False
        except:
            pass


if __name__ == "__main__":
    gui = PressureControlGui()
    try:
        if len(sys.argv)==2:
            gui.load_settings(sys.argv[1])
        gui.init_gui({})
    except KeyboardInterrupt:
        gui.on_window_close()