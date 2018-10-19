"""
Copyright (C) 2018 IAIK TU Graz (data@iaik.tugraz.at)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

@version 1.1

"""

import setuptools
from datagui import DATAGUI_VERSION

def readme():
    with open('README.md') as f:
        return f.read()

setuptools.setup(
      name='datagui',
      version=DATAGUI_VERSION,
      description='Graphical user interface for the DATA tool',
      long_description=readme(),
      url='https://github.com/IAIK/DATA-GUI',
      author='IAIK, Graz University of Technology',
      author_email='data@iaik.tugraz.at',
      license='GPLv3+',
      classifiers=[
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
      ],
      keywords='data gui memory side-channel analysis',
      packages=['datagui', 'datagui/package', 'datagui/package/ui', 'datagui/package/model', 'datastub'],
      install_requires=[
          'qscintilla>=2.10.3, <3',
          'qtconsole>=4.3.1',
          'pgzero>=1.2',
          'pyqt5>=5.10.1, <6',
          'pyqtgraph>=0.10.0',
          'pyserial>=3.4',
          'fs>=2.1.0',
          'sip>=4.19.8'
      ],
      scripts=['bin/datagui'],
      include_package_data=True,
      zip_safe=False)
