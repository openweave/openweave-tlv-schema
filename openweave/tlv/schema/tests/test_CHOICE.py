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
#         Unit tests for CHOICE OF pseudo-types.
#

import unittest

from .testutils import TLVSchemaTestCase

class Test_CHOICE(TLVSchemaTestCase):
    
    def test_CHOICE_allLeafAlternatesWithNamesAndTags(self):
        schemaText = '''
                     c1 => CHOICE OF
                     {
                         alt1 [0] : STRING,
                         CHOICE OF
                         {
                             alt2 [1] : BOOLEAN
                         },
                         CHOICE OF
                         {
                             alt3 : INTEGER,
                             CHOICE OF
                             {
                                 alt4 [4] : ARRAY OF ANY
                             },
                             c2
                         },
                     }
                     c2 [5] => CHOICE OF
                     {
                         alt5 [42] : FLOAT
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 0)
        c1 = tlvSchema.getTypeDef('c1').targetType
        c2 = tlvSchema.getTypeDef('c2').targetType
        allLeafAlts = list(c1.allLeafAlternatesWithNamesAndTags())
        self.assertEqual(len(allLeafAlts), 5)
        # Check first alternate
        (altChain, name, defaultTag) = allLeafAlts[0]
        self.assertEqual(len(altChain), 1)
        self.assertEqual(altChain[0], c1.alternates[0])
        self.assertEqual(name, 'alt1')
        self.assertIsNotNone(defaultTag)
        self.assertIsNone(defaultTag.profileId)
        self.assertEqual(defaultTag.tagNum, 0)
        # Check second alternate
        (altChain, name, defaultTag) = allLeafAlts[1]
        self.assertEqual(len(altChain), 2)
        self.assertEqual(altChain[0], c1.alternates[1].targetType.alternates[0])
        self.assertEqual(altChain[1], c1.alternates[1])
        self.assertEqual(name, 'alt2')
        self.assertIsNotNone(defaultTag)
        self.assertIsNone(defaultTag.profileId)
        self.assertEqual(defaultTag.tagNum, 1)
        # Check third alternate
        (altChain, name, defaultTag) = allLeafAlts[2]
        self.assertEqual(len(altChain), 2)
        self.assertEqual(name, 'alt3')
        self.assertEqual(altChain[0], c1.alternates[2].targetType.alternates[0])
        self.assertEqual(altChain[1], c1.alternates[2])
        self.assertIsNone(defaultTag)
        # Check forth alternate
        (altChain, name, defaultTag) = allLeafAlts[3]
        self.assertEqual(len(altChain), 3)
        self.assertEqual(altChain[0], c1.alternates[2].targetType.alternates[1].targetType.alternates[0])
        self.assertEqual(altChain[1], c1.alternates[2].targetType.alternates[1])
        self.assertEqual(altChain[2], c1.alternates[2])
        self.assertEqual(name, 'alt4')
        self.assertIsNotNone(defaultTag)
        self.assertIsNone(defaultTag.profileId)
        self.assertEqual(defaultTag.tagNum, 4)
        # Check fifth alternate
        (altChain, name, defaultTag) = allLeafAlts[4]
        self.assertEqual(len(altChain), 3)
        self.assertEqual(altChain[0], c2.alternates[0])
        self.assertEqual(altChain[1], c1.alternates[2].targetType.alternates[2])
        self.assertEqual(altChain[2], c1.alternates[2])
        self.assertEqual(name, 'alt5')
        self.assertIsNotNone(defaultTag)
        self.assertIsNone(defaultTag.profileId)
        self.assertEqual(defaultTag.tagNum, 5)

    def test_CHOICE_possibleTags(self):
        schemaText = '''
                     c1 => CHOICE OF
                     {
                         alt1 [1] : STRING,
                         CHOICE OF
                         {
                             alt2 [2] : BOOLEAN
                         },
                         CHOICE OF
                         {
                             alt3 : INTEGER,
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
        self.assertErrorCount(errs, 0)
        c1 = tlvSchema.getTypeDef('c1').targetType
        possibleTags = c1.possibleTags
        self.assertEqual(len(possibleTags), 5)
        possibleTags = [ tag.asTuple() if tag is not None else None for tag in possibleTags ]
        self.assertIn((None, 1), possibleTags)  # tag for alt1
        self.assertIn((None, 2), possibleTags)  # tag for alt2
        self.assertIn(None, possibleTags)       # no tag for alt3
        self.assertIn((None, 4), possibleTags)  # tag for alt4
        self.assertIn((0x1234, 5), possibleTags)# tag for alt5

if __name__ == '__main__':
    unittest.main()
