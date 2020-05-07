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
#         Unit tests for reference types.
#

import unittest

from .testutils import TLVSchemaTestCase
from ..node import ReferencedType, TypeDef, SignedIntegerType

class Test_Refs(TLVSchemaTestCase):
    
    def test_Refs(self):
        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 [0] : i,
                     }
                     c => CHOICE OF
                     {
                         alt1 : i,
                     }
                     a1 => ARRAY OF i
                     a2 => ARRAY
                     {
                         i
                     }
                     l1 => LIST OF i
                     l2 => LIST
                     {
                         i
                     }
                     x => i
                     i => INTEGER
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)
        
        def assertRefType(refType):
            self.assertIsInstance(refType, ReferencedType)
            self.assertIsInstance(refType.targetTypeDef, TypeDef)
            self.assertEqual(refType.targetTypeDef.name, "i")
            self.assertIsInstance(refType.targetType, SignedIntegerType)
        
        s = tlvSchema.getTypeDef('s').targetType
        refType = s.getField('f1').type
        assertRefType(refType)

        c = tlvSchema.getTypeDef('c').targetType
        refType = c.getAlternate('alt1').type
        assertRefType(refType)

        a1 = tlvSchema.getTypeDef('a1').targetType
        refType = a1.elemType
        assertRefType(refType)

        a2 = tlvSchema.getTypeDef('a2').targetType
        refType = a2.elemTypePattern[0].type
        assertRefType(refType)

        l1 = tlvSchema.getTypeDef('l1').targetType
        refType = l1.elemType
        assertRefType(refType)

        l2 = tlvSchema.getTypeDef('l2').targetType
        refType = l2.elemTypePattern[0].type
        assertRefType(refType)

        refType = tlvSchema.getTypeDef('x').type
        assertRefType(refType)

    def test_Refs_UndefinedTypeName(self):
        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 [0] : u,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid type reference: u')

        schemaText = '''
                     c => CHOICE OF
                     {
                         alt1 : u,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid type reference: u')

        schemaText = '''
                     a1 => ARRAY OF u
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid type reference: u')

        schemaText = '''
                     a2 => ARRAY
                     {
                         u
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid type reference: u')

        schemaText = '''
                     l1 => LIST OF u
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid type reference: u')

        schemaText = '''
                     l2 => LIST
                     {
                         u
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid type reference: u')

        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 : CHOICE OF
                         {
                             alt1 : u
                         }
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 2)
        self.assertError(errs, 'invalid type reference: u')
        self.assertError(errs, 'missing tag on STRUCTURE type field: f1')

        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 : CHOICE OF
                         {
                             alt1 : x
                         }
                     }
                     x [0] => u
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid type reference: u')

    def test_Refs_CircularRefs(self):
        schemaText = '''
                     x => x
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'circular type reference: x')

        schemaText = '''
                     a => b
                     b => c
                     c => d
                     d => e
                     e => f
                     f => a
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 6)
        self.assertError(errs, 'circular type reference: a')
        self.assertError(errs, 'circular type reference: b')
        self.assertError(errs, 'circular type reference: c')
        self.assertError(errs, 'circular type reference: d')
        self.assertError(errs, 'circular type reference: e')
        self.assertError(errs, 'circular type reference: f')


if __name__ == '__main__':
    unittest.main()
