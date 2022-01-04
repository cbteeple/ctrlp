# Ctrl-P: Hardware Interface
The low-level hardware control interface for controlling a Ctrl-P pressure control system.

## Versions
You can always keep up to date by using the version in the master branch. For previous stable versions, checkout the [releases](https://github.com/cbteeple/ctrlp/releases).

## Installation
### Install the release version
[This package is on pypi](https://pypi.org/project/ctrlp/), so anyone can install it with pip: `pip install ctrlp`

### Install the most-recent development version
1. Clone the package from the [github repo](https://github.com/cbteeple/ctrlp)
2. Navigate into the main folder (`cd ctrlp`)
3. `pip install -e .`


## Usage
[Instructions in the documentation](https://ctrl-p.cbteeple.com/top-level)

## About Ctrl-P
The Ctrl-P project is a full-stack pneumatic control system featuring smooth control of pressure at a high bandwidth.

Ctrl-P has four parts:
- [Arduino-Based Firmware](https://github.com/cbteeple/pressure_controller): Contains the low-level pressure control
- [Python Hardware Interface](https://github.com/cbteeple/ctrlp): The low-level device drivers and command handling via serial comms
- [Python Control Interface](https://github.com/cbteeple/pressure_control_interface): High-level handling of pressure trajectories in raw python
- [ROS Driver](https://github.com/cbteeple/pressure_control_cbt): High-level handling of pressure trajectories in ROS

Related Packages:
- [Pressure Controller Skills](https://github.com/cbteeple/pressure_controller_skills): Build complex parametric skills using straightforward definition files.
- [Visual Servoing](https://github.com/cbteeple/ihm_servoing): Example of setting up a realtime feedback controller.
