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
#         Unit tests for LIST types.
#

import unittest

from .testutils import TLVSchemaTestCase

class Test_LIST(TLVSchemaTestCase):
    
    def test_LIST_DuplicateElementNames(self):
        schemaText = '''
                     test-list => LIST
                     {
                         elem-a : INTEGER,
                         elem-b : INTEGER,
                                  FLOAT,
                         elem-a : STRING,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate item in LIST type: elem-a')

    def test_LIST_DisallowFIELDGROUP(self):
        schemaText = '''
                     test-list => LIST
                     {
                         elem-a : INTEGER,
                         elem-b : INTEGER,
                                  FIELD GROUP { },
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertEqual(len(errs), 1)
        self.assertError(errs, 'FIELD GROUP type not allowed')
        schemaText = '''
                     test-list => LIST
                     {
                         elem-a : INTEGER,
                         elem-b : INTEGER,
                                  test-field-group,
                     }
                     test-field-group => FIELD GROUP { }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertEqual(len(errs), 1)
        self.assertError(errs, 'FIELD GROUP type not allowed')

if __name__ == '__main__':
    unittest.main()
