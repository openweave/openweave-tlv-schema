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
#         Unit tests for MESSAGE definitions.
#

import unittest

from ..node import ArrayType, SignedIntegerType
from .testutils import TLVSchemaTestCase

class Test_MESSAGE(TLVSchemaTestCase):
    
    def test_MESSAGE(self):
        schemaText = '''
                     profile1 => PROFILE [ id 42 ]
                     {
                         msg1 => MESSAGE [ id 1 ]
                         msg2 => MESSAGE [ id 2 ] CONTAINING NOTHING
                         msg3 => MESSAGE [ id 3 ] CONTAINING ARRAY OF STRING
                         msg4 => MESSAGE [ id 4 ] CONTAINING payload
                         
                         payload => INTEGER
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)
        profile1 = tlvSchema.getProfile('profile1')
        msg1 = profile1.getMessage('msg1')
        self.assertEqual(msg1.id, 1)
        self.assertIsNone(msg1.payload)
        self.assertFalse(msg1.emptyPayload)
        msg2 = profile1.getMessage('msg2')
        self.assertEqual(msg2.id, 2)
        self.assertIsNone(msg2.payload)
        self.assertTrue(msg2.emptyPayload)
        msg3 = profile1.getMessage('msg3')
        self.assertEqual(msg3.id, 3)
        self.assertIsInstance(msg3.payloadType, ArrayType)
        self.assertFalse(msg3.emptyPayload)
        msg4 = profile1.getMessage('msg4')
        self.assertEqual(msg4.id, 4)
        self.assertIsInstance(msg4.payloadType, SignedIntegerType)
        self.assertFalse(msg4.emptyPayload)

    def test_MESSAGE_NoId(self):
        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         msg1 => MESSAGE
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'id qualifier missing')

        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         msg1 => MESSAGE [ ]
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'id qualifier missing')

        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         msg1 => MESSAGE [ ] CONTAINING INTEGER
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'id qualifier missing')

    def test_MESSAGE_BadId(self):
        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         msg1 => MESSAGE [ id 0x1000 ]
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         msg1 => MESSAGE [ id -1 ]
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         msg1 => MESSAGE [ id 256 ]
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         msg1 => MESSAGE [ id 1:1 ]
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

    def test_MESSAGE_NonUniqueId(self):
        schemaText = '''
                     profile1 => PROFILE [ id 42 ]
                     {
                         msg1 => MESSAGE [ id 1 ]
                         msg2 => MESSAGE [ id 2 ] CONTAINING NOTHING
                         msg3 => MESSAGE [ id 1 ] CONTAINING ARRAY OF STRING // ERROR: id not unique
                     }
                     profile2 => PROFILE [ id 24 ]
                     {
                         msg1 => MESSAGE [ id 1 ] // Not an error; different profile
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate message id: 1')

    def test_MESSAGE_NotInProfile(self):
        schemaText = '''
                     profile1 => PROFILE [ id 42 ]
                     {
                         msg1 => MESSAGE [ id 1 ]
                     }
                     msg2 => MESSAGE [ id 2 ] // ERROR: not in PROFILE
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'MESSAGE definition not within PROFILE definition')

        schemaText = '''
                     profile1 => PROFILE [ id 42 ]
                     {
                         msg1 => MESSAGE [ id 1 ]
                         namespace ns1
                         {
                             msg2 => MESSAGE [ id 2 ] // ERROR: not directly in PROFILE
                         }
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'MESSAGE definition not within PROFILE definition')

if __name__ == '__main__':
    unittest.main()
