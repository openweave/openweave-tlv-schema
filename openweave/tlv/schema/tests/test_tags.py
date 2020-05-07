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
#         Unit tests for tag qualifiers and tag handling.
#

import unittest

from ..node import TypeDef
from .testutils import TLVSchemaTestCase

class Test_Tags(TLVSchemaTestCase):

    def test_Tags_CurrentProfile(self):
        schemaText = '''
                     profile-1 => PROFILE [ id 0xABCD1234 ]
                     {
                       type-1 [ *:42 ] => INTEGER
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)
        typeDefNode = next(tlvSchema.allNodes(TypeDef))
        tagNode = typeDefNode.defaultTag
        self.assertEqual(tagNode.profileId, 0xABCD1234)
        self.assertEqual(tagNode.tagNum, 42)

    def test_Tags_BadProfileReference(self):
        schemaText = 'test [ undefined-profile:1 ] => INTEGER'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid profile reference')

        schemaText = 'test => STRUCTURE { field1 [ undefined-profile:1 ] : INTEGER }'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid profile reference')

        schemaText = 'test => LIST { field1 [ undefined-profile:1 ] : INTEGER }'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid profile reference')

        schemaText = 'test => CHOICE OF { field1 [ undefined-profile:1 ] : INTEGER }'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid profile reference')

        schemaText = 'test => FIELD GROUP { field1 [ undefined-profile:1 ] : INTEGER }'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid profile reference')

    def test_Tags_BadCurrentProfile(self):
        schemaText = 'test [ *:1 ] => INTEGER'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid reference to current profile')

        schemaText = '''
                     profile-1 => PROFILE [ id 42 ] { }
                     test [ *:1 ] => INTEGER
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid reference to current profile')

    def test_Tags_DefaultTags_TypeDef(self):
        schemaText = '''
                     type-1 [ 0x253A0000:1 ] => INTEGER
                     
                     namespace ns-1
                     {
                         type-2 => type-1
                         type-3 [ 0x12345678:3 ] => type-1
                     }
                     
                     vendor-1 => VENDOR [ id 0xAAAA ]
                     
                     profile-1 => PROFILE [ id vendor-1:0xBBBB ]
                     {
                         type-4 [ 4 ] => STRING
                         type-5 => type-1
                         type-6 => ns-1.type-2
                         type-7 => ns-1.type-3
                         type-8 [ *:8 ] => ns-1.type-2
                     } 
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)
        tag = tlvSchema.getTypeDef('type-1').defaultTag
        self.assertEqual(tag.profileId, 0x253A0000)
        self.assertEqual(tag.tagNum, 1)
        tag = tlvSchema.getTypeDef('ns-1.type-2').defaultTag
        self.assertEqual(tag.profileId, 0x253A0000)
        self.assertEqual(tag.tagNum, 1)
        tag = tlvSchema.getTypeDef('ns-1.type-3').defaultTag
        self.assertEqual(tag.profileId, 0x12345678)
        self.assertEqual(tag.tagNum, 3)
        tag = tlvSchema.getTypeDef('profile-1.type-4').defaultTag
        self.assertEqual(tag.profileId, None)
        self.assertEqual(tag.tagNum, 4)
        tag = tlvSchema.getTypeDef('profile-1.type-5').defaultTag
        self.assertEqual(tag.profileId, 0x253A0000)
        self.assertEqual(tag.tagNum, 1)
        tag = tlvSchema.getTypeDef('profile-1.type-6').defaultTag
        self.assertEqual(tag.profileId, 0x253A0000)
        self.assertEqual(tag.tagNum, 1)
        tag = tlvSchema.getTypeDef('profile-1.type-7').defaultTag
        self.assertEqual(tag.profileId, 0x12345678)
        self.assertEqual(tag.tagNum, 3)
        tag = tlvSchema.getTypeDef('profile-1.type-8').defaultTag
        self.assertEqual(tag.profileId, 0xAAAABBBB)
        self.assertEqual(tag.tagNum, 8)

    def test_Tags_DefaultTags_StructureFields(self):
        schemaText = '''
                     type-1 [ 0x253A0000:1 ] => INTEGER
                     
                     namespace ns-1
                     {
                         type-2 => type-1
                         type-3 [ 0x12345678:3 ] => type-1
                     }
                     
                     vendor-1 => VENDOR [ id 0xAAAA ]
                     
                     profile-1 => PROFILE [ id vendor-1:0xBBBB ]
                     {
                         type-4 [ 42 ] => STRING
                     
                         struct-1 => STRUCTURE
                         {
                             field-1 [ 1 ]    : type-1,
                             field-2 [ *:2 ]  : type-1,
                             field-3          : ns-1.type-2,
                             field-4          : ns-1.type-3,
                             
                             includes fg-1
                         }
                         
                         fg-1 => FIELD GROUP
                         {
                             field-5 [ 5 ]    : type-4,
                             field-6          : type-4
                         }
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)
        struct1 = tlvSchema.getTypeDef('profile-1.struct-1').type
        tag = struct1.getField('field-1').tag
        self.assertEqual(tag.profileId, None)
        self.assertEqual(tag.tagNum, 1)
        tag = struct1.getField('field-2').tag
        self.assertEqual(tag.profileId, 0xAAAABBBB)
        self.assertEqual(tag.tagNum, 2)
        tag = struct1.getField('field-3').tag
        self.assertEqual(tag.profileId, 0x253A0000)
        self.assertEqual(tag.tagNum, 1)
        tag = struct1.getField('field-4').tag
        self.assertEqual(tag.profileId, 0x12345678)
        self.assertEqual(tag.tagNum, 3)
        tag = struct1.getField('field-5').tag
        self.assertEqual(tag.profileId, None)
        self.assertEqual(tag.tagNum, 5)
        tag = struct1.getField('field-6').tag
        self.assertEqual(tag.profileId, None)
        self.assertEqual(tag.tagNum, 42)

    def test_Tags_DefaultTags_ListElements(self):
        schemaText = '''
                     type-1 [ 0x253A0000:1 ] => INTEGER
                     
                     namespace ns-1
                     {
                         type-2 => type-1
                         type-3 [ 0x12345678:3 ] => type-1
                     }
                     
                     vendor-1 => VENDOR [ id 0xAAAA ]
                     
                     profile-1 => PROFILE [ id vendor-1:0xBBBB ]
                     {
                         type-4 [ 42 ] => STRING
                     
                         list-1 => LIST
                         {
                             elem-1 [ 1 ]    : type-1,            // Tag should be context-specific 1
                             elem-2 [ *:2 ]  : type-1,            // Tag should be profile-specific 0xAAAABBBB:2
                             elem-3          : ns-1.type-2,       // Tag should be profile-specific 0x253A0000:1
                             elem-4          : ns-1.type-3,       // Tag should be profile-specific 0x12345678:3
                         }
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)
        list1 = tlvSchema.getTypeDef('profile-1.list-1').type
        tag = list1.getElement('elem-1').tag
        self.assertEqual(tag.profileId, None)
        self.assertEqual(tag.tagNum, 1)
        tag = list1.getElement('elem-2').tag
        self.assertEqual(tag.profileId, 0xAAAABBBB)
        self.assertEqual(tag.tagNum, 2)
        tag = list1.getElement('elem-3').tag
        self.assertEqual(tag.profileId, 0x253A0000)
        self.assertEqual(tag.tagNum, 1)
        tag = list1.getElement('elem-4').tag
        self.assertEqual(tag.profileId, 0x12345678)
        self.assertEqual(tag.tagNum, 3)

if __name__ == '__main__':
    unittest.main()
