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
#########################################################################

VER=$(python -c 'from datagui import DATAGUI_VERSION; print(DATAGUI_VERSION)')
VER_ORIG=$VER

#------------------------------------------------------------------------
# Check whether parent repository is on 'master'
#------------------------------------------------------------------------
GUICI=$(git rev-parse HEAD)
GUIBRANCH=$(git rev-parse --abbrev-ref HEAD)
pushd ..
DATACI=$(git rev-parse HEAD)
DATABRANCH=$(git rev-parse --abbrev-ref HEAD)
DEVELOP=0
if ! [[ "${DATABRANCH}" == "master" ]] || ! [ "${GUIBRANCH}" == "master" ]]; then
  if ! [[ "$1" == "-f" ]]; then
    echo "GUI and DATA repo must be on master branch!"
    echo "This ensures that a DATA GUI package only include released"
    echo "DATA files."
    echo ""
    echo "To still continue for a development package, append -f"
    exit 1
  else
    DEVELOP=1
    VER="${VER}-DATA-${DATABRANCH}-${DATACI:0:7}-GUI-${GUIBRANCH}-${GUICI:0:7}"
    echo "Creating develop version: $VER"
  fi
fi
popd

#------------------------------------------------------------------------
# Check version number
#------------------------------------------------------------------------
export TAR=dist/datagui-${VER}.tar.gz

if [[ -f "${TAR}" ]]; then
  echo "Release ${VER} already exists in ${TAR}"
  echo "Increment version number in datagui/__init__.py"
  exit 1
fi

#------------------------------------------------------------------------
# Update version number in all license headers
#------------------------------------------------------------------------
UNTRACKED=$(git status --porcelain | grep -e "^??")
if ! [[ -z "${UNTRACKED}" ]]; then
  echo "You have untracked files. Track them or add them to .gitignore!"
  echo "${UNTRACKED}"
  exit 1
fi

UNCOMMITTED=$(git diff-index HEAD)
if ! [[ -z "${UNCOMMITTED}" ]]; then
  echo "You have uncommitted files. Commit or stash them!"
  echo "${UNCOMMITTED}"
  exit 1
fi

echo "Setting version number"
for f in `git ls-files`; do
  if [[ "$f" == "release.sh" ]]; then
    continue
  fi
  grep "@version" $f > /dev/null
  if [[ "$?" -eq "0" ]]; then
    echo "Setting version number in $f"
    # search for '@version' string and 
    # replace the following version number with ${VER}
    sed -i "s/\(@version\s*\).*/\1${VER}/g" $f
  fi
done

for f in `git ls-files`; do
  if [[ "$f" == "release.sh" ]]; then
    continue
  fi
  grep "DATAGUI_VERSION" $f > /dev/null
  if [[ "$?" -eq "0" ]]; then
    echo "Setting version number in $f"
    # search for 'DATAGUI_VERSION' string and 
    # replace the following version number with ${VER}
    sed -i "s/\(DATAGUI_VERSION\s*=\s*\).*/\1'${VER}'/g" $f
  fi
done

#------------------------------------------------------------------------
# Create fresh environment
#------------------------------------------------------------------------
set -e
ENV=.pyenv
rm -rf ${ENV}
LOAD_PYENV_INTERPRETER=/usr/bin/python3
virtualenv -p ${LOAD_PYENV_INTERPRETER} ${ENV}
source ${ENV}/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools
set +e

#------------------------------------------------------------------------
# Package DATA GUI
#------------------------------------------------------------------------
python setup.py sdist || retval=$?
if [[ "$retval" -ne "0" ]] || ! [[ -f "${TAR}" ]]; then
  echo "Failed to create python package"
  exit 1
fi

if [[ "${DEVELOP}" -eq "1" ]]; then
  echo "Reverting temporary @version changes"
  git checkout .
else
  echo "Please commit the @version changes"
fi

#------------------------------------------------------------------------
# Try to install and run package
#------------------------------------------------------------------------
pip install "${TAR}"
datagui
