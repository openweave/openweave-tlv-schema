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
#         Test tool for Weave TLV Schema code.
#

import sys
import os

from openweave.tlv.schema import WeaveTLVSchema

if len(sys.argv) < 2:
    sys.stderr.write('Please specify one or more schema files\n')
    sys.exit(-1)

WeaveTLVSchema = WeaveTLVSchema()

for schemaFileName in sys.argv[1:]:

    if not os.path.exists(schemaFileName):
        sys.stderr.write('Input file not found: %s\n' % schemaFileName)
        sys.exit(-1)
    
    WeaveTLVSchema.loadSchemaFromFile(schemaFileName)
    
for schemaFile in WeaveTLVSchema.allFiles():
    print(schemaFile.dump())

print('----------')

errs = WeaveTLVSchema.validate()

if len(errs) == 0:
    print('All file parsed successfully')
else:
    print('Errors = %s' % errs)
