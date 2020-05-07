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
#         Unit tests for STRUCTURE types.
#

import unittest

from .testutils import TLVSchemaTestCase

class Test_STRUCTURE(TLVSchemaTestCase):
    
    def test_STRUCTURE_DuplicateFieldNames(self):
        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 [0] : INTEGER,
                         f2 [1] : INTEGER,
                         f1 [2] : STRING,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate field in STRUCTURE type: f1')

    def test_STRUCTURE_DuplicateFieldNames_InFieldGroup(self):
        schemaText = '''
                     fg => FIELD GROUP
                     {
                         f1 [0] : INTEGER,
                         f2 [1] : INTEGER,
                         f1 [2] : STRING,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate field in FIELD GROUP type: f1')

    def test_STRUCTURE_DuplicateFieldNames_BeforeFieldGroup(self):
        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 [0] : INTEGER,
                         f2 [1] : INTEGER,
                         includes fg,
                     }
                     
                     fg => FIELD GROUP
                     {
                         f1 [2] : STRING,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate field in STRUCTURE type: f1')

    def test_STRUCTURE_DuplicateFieldNames_AfterFieldGroup(self):
        schemaText = '''
                     s => STRUCTURE
                     {
                         includes fg,
                         f1 [0] : INTEGER,
                         f2 [1] : INTEGER,
                     }
                     
                     fg => FIELD GROUP
                     {
                         f1 [2] : STRING,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate field in STRUCTURE type: f1')

    def test_STRUCTURE_DuplicateFieldNames_InReferencedFieldGroup(self):
        # In this test, there should only be one error related to the FIELD GROUP
        # having a duplicate field.  There should NOT be an error related to the
        # STRUCTURE that includes the FIELD GROUP with the duplicate field.
        schemaText = '''
                     fg => FIELD GROUP
                     {
                         f1 [0] : INTEGER,
                         f2 [1] : INTEGER,
                         f1 [2] : STRING,
                     }

                     s => STRUCTURE
                     {
                         includes fg
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate field in FIELD GROUP type: f1')

    def test_STRUCTURE_DisallowFIELDGROUP(self):
        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 [0] : FIELD GROUP { },
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'FIELD GROUP type not allowed')
        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 [0] : fg,
                     }
                     fg => FIELD GROUP { }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'FIELD GROUP type not allowed')

    def test_STRUCTURE_DuplicateTags(self):
        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 [0] : INTEGER,
                         f2 [1] : INTEGER,
                         f3 [0] : STRING,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate tag in STRUCTURE type: 0 (context-specific)')

    def test_STRUCTURE_DuplicateTags_InFieldGroup(self):
        schemaText = '''
                     fg => FIELD GROUP
                     {
                         f1 [0] : INTEGER,
                         f2 [1] : INTEGER,
                         f3 [0] : STRING,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate tag in FIELD GROUP type: 0 (context-specific)')

    def test_STRUCTURE_DuplicateTags_BeforeFieldGroup(self):
        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 [0] : INTEGER,
                         f2 [1] : INTEGER,
                         includes fg,
                     }
                     
                     fg => FIELD GROUP
                     {
                         f3 [0] : STRING,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate tag in STRUCTURE type: 0 (context-specific)')

    def test_STRUCTURE_DuplicateTags_AfterFieldGroup(self):
        schemaText = '''
                     s => STRUCTURE
                     {
                         includes fg,
                         f1 [0] : INTEGER,
                         f2 [1] : INTEGER,
                     }
                     
                     fg => FIELD GROUP
                     {
                         f3 [1] : STRING,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate tag in STRUCTURE type: 1 (context-specific)')

    def test_STRUCTURE_DuplicateTags_InReferencedFieldGroup(self):
        # TODO: this test should produce a single error related to the FIELD GROUP
        # having a duplicate field.  However the code to eliminate duplicate errors
        # in this case is TBD.
        schemaText = '''
                     fg => FIELD GROUP
                     {
                         f1 [0] : INTEGER,
                         f2 [1] : INTEGER,
                         f3 [0] : STRING,
                     }

                     s => STRUCTURE
                     {
                         includes fg
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 2)
        self.assertError(errs, 'duplicate tag in FIELD GROUP type: 0 (context-specific)')
        self.assertError(errs, 'duplicate tag in STRUCTURE type: 0 (context-specific)')

    def test_STRUCTURE_MissingTags(self):
        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 [0] : INTEGER,
                         f2     : STRING, // this field is missing a tag
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'missing tag on STRUCTURE type field: f2')

    def test_STRUCTURE_MissingTags_ChoiceAlternate(self):
        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 : CHOICE OF
                         {
                             alt1 : STRUCTURE // this alternate does not declare a tag
                             {
                                 f1 [0] : NULL
                             },
                             alt2 [0] : INTEGER
                         }
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'missing tag on STRUCTURE type field: f1')

    def test_STRUCTURE_possibleTags(self):
        schemaText = '''
                     s => STRUCTURE
                     {
                         f1 : c1,
                         f2 [6] : CHOICE OF
                         {
                             alt6 : BOOLEAN,
                             alt7 : STRING
                         },
                         f3 [0:1] : c1
                     }
                     c1 => CHOICE OF
                     {
                         alt1 [1] : STRING,
                         CHOICE OF
                         {
                             alt2 [2] : BOOLEAN
                         },
                         CHOICE OF
                         {
                             alt3 [3] : INTEGER,
                             CHOICE OF
                             {
                                 alt4 [4] : ARRAY OF ANY
                             },
                             c2
                         },
                     }
                     c2 [0x1234:5] => CHOICE OF
                     {
                         alt5 [42] : FLOAT
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)
        s = tlvSchema.getTypeDef('s').targetType
        # field f1
        possibleTags = s.getField('f1').possibleTags
        self.assertEqual(len(possibleTags), 5)
        possibleTags = [ tag.asTuple() if tag is not None else None for tag in possibleTags ]
        self.assertIn((None, 1), possibleTags)  # tag for alt1
        self.assertIn((None, 2), possibleTags)  # tag for alt2
        self.assertIn((None, 3), possibleTags)  # tag for alt3
        self.assertIn((None, 4), possibleTags)  # tag for alt4
        self.assertIn((0x1234, 5), possibleTags)# tag for alt5
        # field f2
        possibleTags = s.getField('f2').possibleTags
        self.assertEqual(len(possibleTags), 1)
        self.assertEqual(possibleTags[0].asTuple(), (None, 6))
        # field f3
        possibleTags = s.getField('f3').possibleTags
        self.assertEqual(len(possibleTags), 1)
        self.assertEqual(possibleTags[0].asTuple(), (0, 1))

if __name__ == '__main__':
    unittest.main()
