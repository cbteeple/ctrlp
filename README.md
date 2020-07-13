# Ctrl-P 2.0: Python Control Interface
The top-level control interface for controlling a Ctrl-P pressure control system.

## Dependencies
All dependencies are managed in the reqirements file.
`pip install -r requirements.txt`

- Various python libraries:
	- [scipy](https://www.scipy.org/) (`pip install scipy`)
	- [numpy](https://www.numpy.org/) (`pip install numpy`)
	- [matplotlib](https://matplotlib.org/) (`pip install matplotlib`)
	- [pynput](https://pypi.org/project/pynput/) (`pip install pynput`)
	- [yaml](https://pyyaml.org/wiki/PyYAMLDocumentation) (`pip install pyyaml`)
	- [sorotraj](https://pypi.org/project/sorotraj/) (`pip install sorotraj`)

## Usage
[Instructions in the documentation](https://ctrl-p.cbteeple.com/top-level)

## About Ctrl-P
The Ctrl-P project is a full-stack pneumatic control system featuring smooth control of pressure at a high bandwidth.

Ctrl-P has three parts:
- [Arduino-Based Firmware](https://github.com/cbteeple/pressure_controller)
- [Python Control Interface](https://github.com/cbteeple/pressure_control_interface)
- [ROS Driver](https://github.com/cbteeple/pressure_control_cbt)