import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fdialog
import os
import sys
import copy
import time

sys.path.insert(1, 'utils')
from comm_handler import CommHandler
from get_files import get_save_path, load_yaml, save_yaml


class PressureControlGui:
    def __init__(self):
        self.config = None
        self.pressures = None
        # Get the desired save path from save_paths.yaml
        self.traj_folder = get_save_path(which='traj_built')
        self.config_folder = get_save_path(which='config')
        self.data_base= get_save_path(which='preferred')
        self.curr_flag_file = os.path.join(self.traj_folder,"last_sent.txt")

        self.settings = load_yaml(os.path.join(self.config_folder,'gui',"settings.yaml"))

        self.file_types = self.settings['file_types']
        self.color_scheme = self.settings['color_scheme']

        self.curr_config_file={'basename':None, 'dirname': os.path.join(self.config_folder, 'control')}

    def get_config(self, filename):
        try:
            config = load_yaml(filename)
            if isinstance(config, dict):
                if config.get('channels'):
                    basename = os.path.basename(filename)
                    self.status_bar.config(text = 'New config "%s" loaded'%(basename))
                    self.config=config
                    return True
                else:
                    self.status_bar.config(text ='Incorrect config format')
                    return False
            else:
                self.status_bar.config(text ='Incorrect config format')
                return False
            
        except:
            self.status_bar.config(text ='New config was not loaded')
            raise
            return False



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


    def send_config(self):
        self.status_bar.config(text ='Sending config...')
        print(self.config)        
        self.status_bar.config(text ='Sent config!')



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

            print(slider_num, scale_value)
        except tk.TclError:
            pass


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
            foreground="black",
            width=10,
            height=3,
            font=12)

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
        btn = ttk.Button(fr_buttons, text = 'Exit',
                        command = self.window.destroy,
                        width=10)

        button.grid(row=1, column=0, sticky="ew", padx=5)
        button2.grid(row=1, column=1, sticky="ew", padx=5)
        btn.grid(row=1, column=2, sticky="ew", padx=5)

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


    def del_control_sender(self):
        try:
            self.fr_send_btns.destroy()
        except:
            pass
        

    def init_pressure_editor(self):
        fr_sliders = tk.Frame(self.fr_sidebar, bd=2)
        fr_sliders.grid(row=99, column=0, sticky="ns", pady=20)
        self.init_sliders(fr_sliders)


    def init_sliders(self, fr_sliders):
        self.channels=[]
        for i in range(8):
            spinval = tk.DoubleVar()
            spinval.set(3.0)
            cb = lambda name, index, val, i=i: self.slider_changed(i)
            spinval.trace("w",cb)
            scale = tk.Scale(fr_sliders, variable=spinval,
                orient=tk.VERTICAL, length=130,
                from_=50.0, to=0.0, resolution=0.1,
                state="normal", activebackground=self.color_scheme['primary_active'], troughcolor=self.color_scheme['primary'],
                )
            scale.grid(row=2, column=i, sticky="ew", padx=5)

            spin = ttk.Spinbox(fr_sliders,
                width=7,
                from_=0.0, to=50.0, increment=0.1,
                textvariable=spinval
                )
            spin.grid(row=4, column=i, sticky="ew", padx=5, pady=10)
            #spin.set(3.0)

            label_title = tk.Label(fr_sliders, text="%d"%(i), width=2, font=('Arial', 20, 'bold'))
            label_max = tk.Label(fr_sliders, text="Top", width=7)
            label_min = tk.Label(fr_sliders, text="Bot", width=7)
            label_title.grid(row=0, column=i, sticky="s", pady=0)
            label_max.grid(row=1, column=i, sticky="s", pady=0)
            label_min.grid(row=3, column=i, sticky="n", pady=0)

            

            self.channels.append([scale, spin, spinval, label_max, label_min])
        
        def update_sliders(self):
            
            self.channels


if __name__ == "__main__":
    gui = PressureControlGui()
    gui.init_gui({})