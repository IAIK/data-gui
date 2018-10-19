#!/bin/bash

#########################################################################
# Copyright (C) 2018 IAIK TU Graz (data@iaik.tugraz.at)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#########################################################################
# @file release.sh
# @brief Sets up a Python virtual environment.
# @author Samuel Weiser <samuel.weiser@iaik.tugraz.at>
# @license This project is released under the GNU GPLv3 License.
# @version 1.1
#########################################################################

#------------------------------------------------------------------------
# Check version number
#------------------------------------------------------------------------
VER=$(python -c 'from datagui import DATAGUI_VERSION; print(DATAGUI_VERSION)')
export TAR=dist/datagui-${VER}.tar.gz

if [[ -f "${TAR}" ]]; then
  echo "Release ${VER} already exists in ${TAR}"
  echo "Increment version number in datagui/__init__.py"
  exit 1
fi

#------------------------------------------------------------------------
# Check whether parent repository is on 'master'
#------------------------------------------------------------------------
pushd ..
if ! [[ "$(git rev-parse --abbrev-ref HEAD)" == "master" ]]; then
  echo "Parent DATA repo must be on master branch. since DATA GUI"
  echo "This ensures that a DATA GUI package only include released"
  echo "DATA files."
  exit 1
fi
popd

#------------------------------------------------------------------------
# Update version number in all license headers
#------------------------------------------------------------------------
UNTRACKED=$(git status --porcelain | grep -e "^??")
if ! [[ -z "${UNTRACKED}" ]]; then
  echo "You have untracked files. Track them or add them to .gitignore!"
  echo "${UNTRACKED}"
  exit 1
fi

echo "Setting version number"
for f in `git ls-files`; do
  grep "@version" $f > /dev/null
  if [[ "$?" -eq "0" ]]; then
    echo "Setting version number in $f"
    # search for '@version' string and 
    # replace the following version number with ${VER}
    # xxx can be digits and dots
    sed -i "s/\(@version\s\+\)[.0-9]\+/\1${VER}/g" $f
  fi
done

#------------------------------------------------------------------------
# Create fresh environment
#------------------------------------------------------------------------
ENV=.pyenv
rm -rf ${ENV}
LOAD_PYENV_INTERPRETER=/usr/bin/python3.5
virtualenv -p ${LOAD_PYENV_INTERPRETER} ${ENV}
source ${ENV}/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools

#------------------------------------------------------------------------
# Package DATA GUI
#------------------------------------------------------------------------
python setup.py sdist

#------------------------------------------------------------------------
# Try to install and run package
#------------------------------------------------------------------------
pip install "${TAR}"
datagui
