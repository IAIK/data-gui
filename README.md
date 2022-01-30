# ![DATA GUI icon][icon] DATA GUI

This DATA GUI is an extension for the Differential Address Trace Analysis (DATA) 
tool. It provides a better representation of the results given by the
DATA tool and improves the usability for analysing binaries and source code to 
find potentially critical address leakage.

For further information on DATA have a look at the [code][data_github]
or check out the corresponding [Usenix Security 2018][usenix]
paper.

## Setup
### Installation

DATA GUI has been tested on Ubuntu 16.04 using python 3.5.2 and pip 18.0.
You can install DATA GUI via the packages provided in the `dist` folder.
We recommend to set up a virtual environment. To do so:

```
sudo apt-get install virtualenv libcxb-xinerama0 libxcb-xinerama0-dev libxcb-image0 libxcb-keysyms, libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0 libxcb-icccm4
virtualenv -p /usr/bin/python3 .pyenv
source .pyenv/bin/activate
pip install -U setuptools pip click scipy sklearn
pip install dist/datagui-x.x.tar.gz
```

### Development Installation

If you want to contribute to the development of DATA GUI, use the 
script `analysis/pyenv.sh` in the main DATA repository and source the
virtual environment `analysis/.pyenv/bin/activate`.

### Running
Once installed in a python environment, you can invoke the DATA GUI 
directly from the commandline by calling

* `datagui`

The GUI needs two mandatory files in order to run.
The required files are located in the results directory of the DATA tool: 

* `result_*.pickle` (contains all leakage results)
* `framework.zip`   (contains the corresponding binary and assembler files)

When starting DATA GUI, it asks for those two files in a dialog window. 
Alternatively, one can provide these files as commandline arguments:

* `datagui <path_to_.pickle> <path_to_framework.zip>`
   
**NOTE:** It is important that the .pickle and the .zip file correspond 
to the same analysis run of the same algorithm (e.g., results/rsa).
Otherwise the GUI is not able to display the content correctly.
The `framework.zip` is the same for phase1, phase2 and phase3.

## Application Overview
![GUI screenshot][screenshot]

DATA GUI allows simple and intuitive navigation through the discovered leakage. Several
items are clickable and will synchronize the views to facilitate fast navigation.
If available, corresponding assembler and source code is visualized.

To record progress in analyzing a certain algorithm, DATA GUI supports flags and user comments.
By default, all leaks are marked with a warning symbol, indicating potential leakage and requiring
analyst's action. One can mark leaks as uncritical (checkmark), critical, or ignore it (trash).
Also, one can add text comments to describe the leak in more detail.
To save the progress, choose File \ Save pickle.

### Leakage Views

The **call hierarchy** displays leakage within their execution contexts.
Since the same leak could occur multiple times under different contexts, 
the **call hierarchy** is perfect for identifying leaks in a specific context.
Functions in the **call hierarchy** can be right-clicked to navigate not only
to the call site but also to the caller site. This is useful to discern
whether a particular function is invoked with potentially secret arguments.

The **library hierarchy** groups leaks by libraries and functions. 
When clicking on a library hierachy leak, it might correspond to multiple
leaks within different execution contexts. One has to choose a specific execution context in this case.

The **leak view** lists all leaks corresponding to the current selection.
When coming from the **library hierarchy** or a source code or assembler tab, 
a leak might correspond to different execution contexts. In this case, the leak's icon
shows the most urgent leak. E.g., if in one context the leak is marked as okay and 
in another context the leak is marked as dangerous, the leak will be displayed as dangerous. 

The **assembler** and **source code** tabs show the precise location at which leakage occurs. 
When clicking on a source code line, the GUI navigates to the corresponding leak. 
It is possible that different leaks point to the same source code line. In this case the 
source code icons simply overlap and the GUI navigates to the first corresponding leak.
Note that source code might not be available in case debug information is missing in the binary.
Also, assembler might be unavailable in the case of dynamically generated code. 

# License
Copyright (C) 2018 Institute of Applied Information Processing and Communications (IAIK, Graz University of Technology)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public [License](./LICENSE)
along with this program. If not, see <http://www.gnu.org/licenses/>.

For more permissive commercial licenses, please contact [us](mailto:data@iaik.tugraz.at).

# Credits
The GUI was developed by Lukas Bodner.

[icon]: datagui/resources/icons/window_icon_small.png
[data_github]: https://github.com/Fraunhofer-AISEC/DATA
[usenix]: https://www.usenix.org/conference/usenixsecurity18/presentation/weiser
[venv]: https://virtualenv.pypa.io/en/stable/
[pyenv]: pyenv.sh
[setup]: setup.py
[screenshot]: doc/gui_screenshot.png
