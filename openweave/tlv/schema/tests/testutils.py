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
#         Utility types for unit tests.
#

import unittest

import sys
import os
import io

from .. import WeaveTLVSchema
from ..error import WeaveTLVSchemaError

class TLVSchemaTestCase(unittest.TestCase):

    @staticmethod
    def loadValidate(schemaText):
        tlvSchema = WeaveTLVSchema()
        errs = []
        try:
            tlvSchema.loadSchemaFromString(schemaText)
        except WeaveTLVSchemaError as err:
            errs.append(err)
        errs += tlvSchema.validate()
        return (tlvSchema, errs)
    
    def assertErrorCount(self, errs, count):
        if len(errs) != count:
            errSum = ''.join((('\n  ' + err.__repr__()) for err in errs))
            errMsg = 'Expected %d error%s, got %d%s' % (count, '' if count == 1 else 's', len(errs), errSum) 
            self.fail(errMsg);
        
    def assertNoErrors(self, errs):
        self.assertErrorCount(errs, 0)

    def assertError(self, errs, errText):
        for err in errs:
            if errText in str(err):
                return
        errSum = ''.join((('\n  ' + err.__repr__()) for err in errs))
        errMsg = 'Expected error with text "%s" not found in:%s' % (errText, errSum) 
        self.fail(errMsg);

