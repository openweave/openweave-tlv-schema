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
#         Unit tests for VENDOR definitions.
#

import unittest

from .testutils import TLVSchemaTestCase

class Test_VENDOR(TLVSchemaTestCase):
    
    def test_VENDOR(self):
        schemaText = '''
                     test-vendor-1 => VENDOR [ id 0 ]
                     test-vendor-2 => VENDOR [ id 1 ]
                     test-vendor-65535 => VENDOR [ id 65535 ]
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)

    def test_VENDOR_NoId(self):
        schemaText = 'test-vendor-1 => VENDOR'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'id qualifier missing')

        schemaText = 'test-vendor-1 => VENDOR [ ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'id qualifier missing')

    def test_VENDOR_BadId(self):
        schemaText = 'test-vendor-1 => VENDOR [ id 65536 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

        schemaText = 'test-vendor-1 => VENDOR [ id -1 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

        schemaText = 'test-vendor-1 => VENDOR [ id 42:1 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

    def test_VENDOR_InconsistentId(self):
        schemaText = '''
                     test-vendor-1 => VENDOR [ id 1 ]
                     test-vendor-2 => VENDOR [ id 2 ]
                     test-vendor-1 => VENDOR [ id 42 ] // Inconsistent
                     test-vendor-2 => VENDOR [ id 2 ]
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'inconsistent vendor id: 0x002A (42)')

if __name__ == '__main__':
    unittest.main()
