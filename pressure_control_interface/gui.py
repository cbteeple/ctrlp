import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fdialog
import os
import sys
import copy

sys.path.insert(1, 'utils')
from comm_handler import CommHandler
from get_files import get_save_path

colors={'primary':"#4fa6ff",
        'primary_active': "#c4e1ff"}


file_types = [("Trajectory Setup Files", "*.yaml"),
                   ("Trajectory Build Files", "*.traj"),
                   ("All Files", "*.*")]

def open_file():
    """Open a file for editing."""
    filepath = fdialog.askopenfilename(
        filetypes=file_types
    )
    if not filepath:
        return
    txt_edit.delete("1.0", tk.END)
    with open(filepath, "r") as input_file:
        text = input_file.read()
        txt_edit.insert(tk.END, text)
    window.title(f"Simple Text Editor - {filepath}")

def save_file():
    """Save the current file as a new file."""
    filepath = fdialog.asksaveasfilename(
        defaultextension="txt",
        filetypes=file_types
    )
    if not filepath:
        return
    with open(filepath, "w") as output_file:
        text = txt_edit.get(1.0, tk.END)
        output_file.write(text)
    window.title(f"Simple Text Editor - {filepath}")

def slider_changed(slider_num):
    try:
        #scales[slider_num][1].set(val)
        scalevar = scales[slider_num][2]
        scale_value=round(scalevar.get(), 2)

        scale = scales[slider_num][0]
        box = scales[slider_num][0]

        scalevar.set(scale_value)
        scale.set(scale_value)
        box.set(scale_value)

        print(slider_num, scale_value)
    except tk.TclError:
        pass


data_back=True
save_data = True

# Get the desired save path from save_paths.yaml
traj_folder = get_save_path(which='traj_built')
data_base= get_save_path(which='preferred')
curr_flag_file = os.path.join(traj_folder,"last_sent.txt")


window = tk.Tk()
window.title("Simple Text Editor")
window.rowconfigure(0, minsize=200, weight=1)
window.columnconfigure(1, minsize=200, weight=1)


txt_edit = tk.Text(window)
fr_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
fr_sliders = tk.Frame(fr_buttons, bd=2)

greeting = tk.Label(fr_buttons, text="Hello, Tkinter",
    foreground="white",
    background="black",
    width=10,
    height=10 )

button = ttk.Button(fr_buttons,
    text="Open File",
    width=25,
    command=open_file,
)
button2 = ttk.Button(fr_buttons,
    text="Save File",
    width=25,
    command=save_file,
)
btn = ttk.Button(fr_buttons, text = 'Exit',
                command = window.destroy,
                width=25,)

scales=[]
for i in range(8):
    spinval = tk.DoubleVar()
    spinval.set(3.0)
    cb = lambda name, index, val, i=i: slider_changed(i)
    spinval.trace("w",cb)
    scale = tk.Scale(fr_sliders, variable=spinval,
        orient=tk.VERTICAL, length=130,
        from_=50.0, to=0.0, resolution=0.1,
        state="normal", activebackground=colors['primary_active'], troughcolor=colors['primary'],
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

    

    scales.append([scale, spin, spinval])

greeting.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
button.grid(row=1, column=0, sticky="ew", padx=5)
button2.grid(row=2, column=0, sticky="ew", padx=5)
btn.grid(row=3, column=0, sticky="ew", padx=5)
fr_sliders.grid(row=99, column=0, sticky="ns", pady=20)

fr_buttons.grid(row=0, column=0, sticky="ns")
txt_edit.grid(row=0, column=1, sticky="nsew")
window.mainloop()