#!/usr/bin/env python3

#
#   Copyright (c) 2020 Google LLC.
#   All rights reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

#
#   @file
#         Script for building the openweave-tlv-schema source distribution.
#

import os
from datetime import datetime
import getpass
from setuptools import setup

packageName = 'openweave-tlv-schema'
packageVer = '1.0'

# Allow package name to be overridden in the environment.
packageName = os.environ.get('PACKAGE_NAME', packageName)

# Allow package version to be overridden in the environment.
packageVer = os.environ.get('PACKAGE_VERSION', packageVer)

# If building under Travis, assume that this is a developer version, and use
# the Travis build number as the development version number.
if 'TRAVIS_BUILD_NUMBER' in os.environ:
    packageVer = '%s.dev%s' % (packageVer, os.environ['TRAVIS_BUILD_NUMBER'])

# Generate a description string with information on how/when the package
# was built. 
if 'TRAVIS_BUILD_NUMBER' in os.environ:
    buildDescription = 'Built by Travis CI on %s\n- Build: %s/#%s\n- Build URL: %s\n- Branch: %s\n- Commit: %s\n' % (
                            datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                            os.environ['TRAVIS_REPO_SLUG'],
                            os.environ['TRAVIS_BUILD_NUMBER'],
                            os.environ['TRAVIS_BUILD_WEB_URL'],
                            os.environ['TRAVIS_BRANCH'],
                            os.environ['TRAVIS_COMMIT'])
else:
    buildDescription = 'Built by %s on %s\n' % (
                            getpass.getuser(),
                            datetime.now().strftime('%Y/%m/%d %H:%M:%S'))

setup(
    name=packageName,
    version=packageVer,
    description='Python-based libraries and tools for working with Weave TLV schemas.',
    long_description=buildDescription,
    author='Google LLC',
    url='https://github.com/openweave/openweave-tlv-schema',
    license='Apache',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    python_requires='>=3.6',
    packages=[
        'openweave.tlv.schema',
        'openweave.tlv.schema.tests',
    ],
    package_data={
        'openweave.tlv.schema':[
            'tlv-schema-ebnf.txt',
            'LICENSE.txt'
        ]
    },
    scripts=[
        'weave-tlv-schema'              # Install the TLV schema tool as an executable script in the 'bin' directory.
    ],
    install_requires=[
        'lark-parser'
    ],
)
