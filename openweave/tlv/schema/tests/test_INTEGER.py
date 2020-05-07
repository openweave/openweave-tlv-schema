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
#         Unit tests for INTEGER types.
#

import unittest

from .testutils import TLVSchemaTestCase

class Test_INTEGER(TLVSchemaTestCase):

    def test_INTEGER_EnumeratedValues(self):
        schemaText = '''
                     int => INTEGER
                     {
                         v0 = 0,
                         v1 = 1,
                         v2 = 2,
                         v3 = 9223372036854775807,
                         v4 = -9223372036854775808,
                         v5 = 0x7FFFFFFFFFFFFFFF,
                         v6 = -0x7FFFFFFFFFFFFFFF,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)

        schemaText = '''
                     int => UNSIGNED INTEGER
                     {
                         v0 = 0,
                         v1 = 1,
                         v2 = 2,
                         v3 = 18446744073709551615,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)

    def test_INTEGER_EnumeratedValues_OutOfRange_Default(self):
        schemaText = '''
                     int => INTEGER
                     {
                         too-small = -9223372036854775809,
                         too-big = 9223372036854775808,
                         just-right-1 = -9223372036854775808,
                         just-right-2 = 0,
                         just-right-3 = 9223372036854775807,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 2)
        self.assertError(errs, 'enumerated integer value out of range: 9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: -9223372036854775809')

        schemaText = '''
                     int => UNSIGNED INTEGER
                     {
                         too-small-1 = -1,
                         too-small-2 = -9223372036854775809,
                         too-big-1 = 18446744073709551616,
                         too-big-2 = 184467440737095516160,
                         just-right-1 = 0,
                         just-right-2 = 9223372036854775808,
                         just-right-3 = 18446744073709551615,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 4)
        self.assertError(errs, 'enumerated integer value out of range: -1')
        self.assertError(errs, 'enumerated integer value out of range: -9223372036854775809')
        self.assertError(errs, 'enumerated integer value out of range: 18446744073709551616')
        self.assertError(errs, 'enumerated integer value out of range: 184467440737095516160')

    def test_INTEGER_EnumeratedValues_OutOfRange_8Bit(self):
        schemaText = '''
                     int => INTEGER [ range 8bit ]
                     {
                         too-small-1 = -9223372036854775809,
                         too-small-2 = -65535,
                         too-small-3 = -129,
                         too-big-1 = 9223372036854775808,
                         too-big-2 = 65535,
                         too-big-3 = 128,
                         just-right-1 = 0,
                         just-right-2 = 127,
                         just-right-3 = -128,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 6)
        self.assertError(errs, 'enumerated integer value out of range: 9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: -65535')
        self.assertError(errs, 'enumerated integer value out of range: -129')
        self.assertError(errs, 'enumerated integer value out of range: 9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: 65535')
        self.assertError(errs, 'enumerated integer value out of range: 128')

        schemaText = '''
                     int => UNSIGNED INTEGER [ range 8bit ]
                     {
                         too-small-1 = -9223372036854775809,
                         too-small-2 = -65535,
                         too-small-3 = -129,
                         too-big-1 = 9223372036854775808,
                         too-big-2 = 65535,
                         too-big-3 = 256,
                         just-right-1 = 0,
                         just-right-2 = 127,
                         just-right-3 = 255,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 6)
        self.assertError(errs, 'enumerated integer value out of range: 9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: -65535')
        self.assertError(errs, 'enumerated integer value out of range: -129')
        self.assertError(errs, 'enumerated integer value out of range: 9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: 65535')
        self.assertError(errs, 'enumerated integer value out of range: 256')

    def test_INTEGER_EnumeratedValues_OutOfRange_16Bit(self):
        schemaText = '''
                     int => INTEGER [ range 16bit ]
                     {
                         too-small-1 = -9223372036854775809,
                         too-small-2 = -4294967295,
                         too-small-3 = -32769,
                         too-big-1 = 9223372036854775808,
                         too-big-2 = 65535,
                         too-big-3 = 32768,
                         just-right-1 = 0,
                         just-right-2 = 32767,
                         just-right-3 = -32768,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 6)
        self.assertError(errs, 'enumerated integer value out of range: -9223372036854775809')
        self.assertError(errs, 'enumerated integer value out of range: -4294967295')
        self.assertError(errs, 'enumerated integer value out of range: -32769')
        self.assertError(errs, 'enumerated integer value out of range: 9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: 65535')
        self.assertError(errs, 'enumerated integer value out of range: 32768')

        schemaText = '''
                     int => UNSIGNED INTEGER [ range 16bit ]
                     {
                         too-small-1 = -9223372036854775809,
                         too-small-2 = -65535,
                         too-small-3 = -1,
                         too-big-1 = 9223372036854775808,
                         too-big-2 = 4294967295,
                         too-big-3 = 65536,
                         just-right-1 = 0,
                         just-right-2 = 32768,
                         just-right-3 = 65535,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 6)
        self.assertError(errs, 'enumerated integer value out of range: -9223372036854775809')
        self.assertError(errs, 'enumerated integer value out of range: -65535')
        self.assertError(errs, 'enumerated integer value out of range: -1')
        self.assertError(errs, 'enumerated integer value out of range: 9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: 4294967295')
        self.assertError(errs, 'enumerated integer value out of range: 65536')

    def test_INTEGER_EnumeratedValues_OutOfRange_32Bit(self):
        schemaText = '''
                     int => INTEGER [ range 32bit ]
                     {
                         too-small-1 = -18446744073709551616,
                         too-small-2 = -9223372036854775808,
                         too-small-3 = -2147483649,
                         too-big-1 = 18446744073709551616,
                         too-big-2 = 9223372036854775808,
                         too-big-3 = 2147483648,
                         just-right-1 = 0,
                         just-right-2 = 2147483647,
                         just-right-3 = -2147483648,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 6)
        self.assertError(errs, 'enumerated integer value out of range: -18446744073709551616')
        self.assertError(errs, 'enumerated integer value out of range: -9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: -2147483649')
        self.assertError(errs, 'enumerated integer value out of range: 18446744073709551616')
        self.assertError(errs, 'enumerated integer value out of range: 9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: 2147483648')

        schemaText = '''
                     int => UNSIGNED INTEGER [ range 32bit ]
                     {
                         too-small-1 = -18446744073709551616,
                         too-small-2 = -9223372036854775808,
                         too-small-3 = -1,
                         too-big-1 = 184467440737095516160,
                         too-big-2 = 18446744073709551616,
                         too-big-3 = 4294967296,
                         just-right-1 = 0,
                         just-right-2 = 2147483648,
                         just-right-3 = 4294967295,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 6)
        self.assertError(errs, 'enumerated integer value out of range: -18446744073709551616')
        self.assertError(errs, 'enumerated integer value out of range: -9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: -1')
        self.assertError(errs, 'enumerated integer value out of range: 184467440737095516160')
        self.assertError(errs, 'enumerated integer value out of range: 18446744073709551616')
        self.assertError(errs, 'enumerated integer value out of range: 4294967296')

    def test_INTEGER_EnumeratedValues_OutOfRange_64bit(self):
        schemaText = '''
                     int => INTEGER [ range 64bit ]
                     {
                         too-small = -9223372036854775809,
                         too-big = 9223372036854775808,
                         just-right-1 = -9223372036854775808,
                         just-right-2 = 0,
                         just-right-3 = 9223372036854775807,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 2)
        self.assertError(errs, 'enumerated integer value out of range: 9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: -9223372036854775809')

        schemaText = '''
                     int => UNSIGNED INTEGER [ range 64bit ]
                     {
                         too-small-1 = -1,
                         too-small-2 = -9223372036854775809,
                         too-big-1 = 18446744073709551616,
                         too-big-2 = 184467440737095516160,
                         just-right-1 = 0,
                         just-right-2 = 9223372036854775808,
                         just-right-3 = 18446744073709551615,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 4)
        self.assertError(errs, 'enumerated integer value out of range: -1')
        self.assertError(errs, 'enumerated integer value out of range: -9223372036854775809')
        self.assertError(errs, 'enumerated integer value out of range: 18446744073709551616')
        self.assertError(errs, 'enumerated integer value out of range: 184467440737095516160')


    def test_INTEGER_EnumeratedValues_OutOfRange_UpperLower(self):
        schemaText = '''
                     int => INTEGER [ range -42..87265838912 ]
                     {
                         too-small-1 = -9223372036854775809,
                         too-small-2 = -9223372036854775808,
                         too-small-3 = -43,
                         too-big-1 = 9223372036854775808,
                         too-big-2 = 9223372036854775807,
                         too-big-3 = 87265838913,
                         just-right-1 = -42,
                         just-right-2 = -10,
                         just-right-3 = 0,
                         just-right-4 = 42,
                         just-right-5 = 87265838912,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 6)
        self.assertError(errs, 'enumerated integer value out of range: -9223372036854775809')
        self.assertError(errs, 'enumerated integer value out of range: -9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: -43')
        self.assertError(errs, 'enumerated integer value out of range: 9223372036854775808')
        self.assertError(errs, 'enumerated integer value out of range: 9223372036854775807')
        self.assertError(errs, 'enumerated integer value out of range: 87265838913')

        schemaText = '''
                     int => UNSIGNED INTEGER [ range 42..87265838912 ]
                     {
                         too-small-1 = -1,
                         too-small-2 = 0,
                         too-small-2 = 41,
                         too-big-1 = 87265838913,
                         too-big-2 = 18446744073709551616,
                         too-big-3 = 184467440737095516160,
                         just-right-1 = 42,
                         just-right-2 = 100,
                         just-right-3 = 87265838912,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 6)
        self.assertError(errs, 'enumerated integer value out of range: -1')
        self.assertError(errs, 'enumerated integer value out of range: 0')
        self.assertError(errs, 'enumerated integer value out of range: 41')
        self.assertError(errs, 'enumerated integer value out of range: 87265838913')
        self.assertError(errs, 'enumerated integer value out of range: 18446744073709551616')
        self.assertError(errs, 'enumerated integer value out of range: 184467440737095516160')

if __name__ == '__main__':
    unittest.main()
