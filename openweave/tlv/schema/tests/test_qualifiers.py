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
#         Unit tests for schema qualifiers.
#

import unittest

from .testutils import TLVSchemaTestCase

class Test_Qualifiers(TLVSchemaTestCase):
    
    _quals = ['extensible',
              'optional',
              'private',
              'invariant',
              'nullable',
              'tag-order',
              'schema-order',
              'any-order',
              'range 0..100',
              'length 0..100',
              'tag 42',
              'id 42']
    
    _qualNames = [ qual.split(' ', 1)[0] for qual in _quals ]

    _allQuals = ', '.join(_quals)

    def _checkQualifierNotAllowedErrors(self, errs, allowedQuals, construct):
        errText = ", ".join((str(err) for err in errs))
        for qual in self._qualNames:
            qualAllowed = qual in allowedQuals
            qualAccepted = not (('%s qualifier not allowed' % qual) in errText)
            if qualAccepted and not qualAllowed:
                self.fail('%s qualifier unexpectedly *allowed* on %s' % (qual, construct))
            elif not qualAccepted and qualAllowed:
                self.fail('%s qualifier unexpectedly *disallowed* on %s' % (qual, construct))
    
    def test_Qualifiers_AllowedQualifiers_TypeDef(self):
        schemaText = 'test [ %s ] => INTEGER' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('tag'),
            construct='Type definition')

    def test_Qualifiers_AllowedQualifiers_VENDOR(self):
        schemaText = 'test => VENDOR [ %s ]' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('id'),
            construct='VENDOR definition')

    def test_Qualifiers_AllowedQualifiers_PROFILE(self):
        schemaText = 'test => PROFILE [ %s ]' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('id'),
            construct='PROFILE definition')

    def test_Qualifiers_AllowedQualifiers_MESSAGE(self):
        schemaText = '''
                      profile1 => PROFILE [ id 1 ]
                      {
                          test => MESSAGE [ %s ]
                      }
                      ''' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('id'),
            construct='MESSAGE definition')

    def test_Qualifiers_AllowedQualifiers_STATUS_CODE(self):
        schemaText = '''
                      profile1 => PROFILE [ id 1 ]
                      {
                          test => STATUS CODE [ %s ]
                      }
                      ''' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('id'),
            construct='STATUS CODE definition')

    def test_Qualifiers_AllowedQualifiers_STRUCTURE(self):
        schemaText = 'test => STRUCTURE [ %s ] { }' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('extensible', 'private', 'nullable', 'invariant', 'tag-order', 'schema-order', 'any-order'),
            construct='STRUCTURE type')

    def test_Qualifiers_AllowedQualifiers_FIELD_GROUP(self):
        schemaText = 'test => FIELD GROUP [ %s ] { }' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=(),
            construct='FIELD GROUP type')

    def test_Qualifiers_AllowedQualifiers_ARRAY(self):
        schemaText = 'test => ARRAY [ %s ] { }' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('nullable', 'length'),
            construct='ARRAY type')

    def test_Qualifiers_AllowedQualifiers_ARRAY_OF(self):
        schemaText = 'test => ARRAY [ %s ] OF ANY' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('nullable', 'length'),
            construct='ARRAY OF type')

    def test_Qualifiers_AllowedQualifiers_LIST(self):
        schemaText = 'test => LIST [ %s ] { }' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('nullable', 'length'),
            construct='LIST type')

    def test_Qualifiers_AllowedQualifiers_LIST_OF(self):
        schemaText = 'test => LIST [ %s ] OF ANY' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('nullable', 'length'),
            construct='LIST OF type')

    def test_Qualifiers_AllowedQualifiers_CHOICE_OF(self):
        schemaText = 'test => CHOICE [ %s ] OF { }' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('nullable'),
            construct='CHOICE OF type')

    def test_Qualifiers_AllowedQualifiers_INTEGER(self):
        schemaText = 'test => INTEGER [ %s ]' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('nullable', 'range'),
            construct='INTEGER type')

    def test_Qualifiers_AllowedQualifiers_UNSIGNED_INTEGER(self):
        schemaText = 'test => UNSIGNED INTEGER [ %s ]' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('nullable', 'range'),
            construct='UNSIGNED INTEGER type')

    def test_Qualifiers_AllowedQualifiers_FLOAT(self):
        schemaText = 'test => FLOAT [ %s ]' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('nullable', 'range'),
            construct='FLOAT type')

    def test_Qualifiers_AllowedQualifiers_BOOLEAN(self):
        schemaText = 'test => BOOLEAN [ %s ]' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('nullable'),
            construct='BOOLEAN type')

    def test_Qualifiers_AllowedQualifiers_STRING(self):
        schemaText = 'test => STRING [ %s ]' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('nullable', 'length'),
            construct='STRING type')

    def test_Qualifiers_AllowedQualifiers_BYTE_STRING(self):
        schemaText = 'test => BYTE STRING [ %s ]' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('nullable', 'length'),
            construct='BYTE STRING type')

    def test_Qualifiers_AllowedQualifiers_ANY(self):
        schemaText = 'test => ANY [ %s ]' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=(),
            construct='ANY type')

    def test_Qualifiers_AllowedQualifiers_NULL(self):
        schemaText = 'test => NULL [ %s ]' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=(),
            construct='NULL type')

    def test_Qualifiers_AllowedQualifiers_Fields(self):
        schemaText = '''
                     test => STRUCTURE
                     {
                         field1 [ %s ] : INTEGER
                     }
                     ''' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('tag', 'optional'),
            construct='STRUCTURE field')

        schemaText = '''
                     test => FIELD GROUP
                     {
                         field1 [ %s ] : INTEGER
                     }
                     ''' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('tag', 'optional'),
            construct='FIELD GROUP field')

    def test_Qualifiers_AllowedQualifiers_Elements(self):
        schemaText = '''
                     test => ARRAY
                     {
                         elem1 [ %s ] : INTEGER
                     }
                     ''' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=(),
            construct='ARRAY element')

        schemaText = '''
                     test => LIST
                     {
                         elem1 [ %s ] : INTEGER
                     }
                     ''' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('tag'),
            construct='LIST element')

    def test_Qualifiers_AllowedQualifiers_Alternates(self):
        schemaText = '''
                     test => CHOICE OF
                     {
                         alt1 [ %s ] : INTEGER
                     }
                     ''' % self._allQuals
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self._checkQualifierNotAllowedErrors(errs, 
            allowedQuals=('tag'),
            construct='CHOICE alternate')

    def test_Qualifiers_DuplicateQualifiers(self):
        schemaText = 'test => STRUCTURE [ extensible, extensible ] { }'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertEqual(len(errs), 1, msg='Expected 1 error');
        self.assertError(errs, 'duplicate qualifier');

    def test_Qualifiers_RangeArguments(self):
        schemaText = '''
                     test => ARRAY
                     {
                         INTEGER [ range 0..1 ],
                         INTEGER [ range 0..18446744073709551618 ],
                         INTEGER [ range -100..100 ],
                         INTEGER [ range -100.0..100.00000000 ],
                         INTEGER [ range -18446744073709551618..18446744073709551618 ],
                         INTEGER [ range -18446744073709551618..-18446744073709551616 ],
                         INTEGER [ range 8bit ],
                         INTEGER [ range 16bit ],
                         INTEGER [ range 32bit ],
                         INTEGER [ range 64bit ],
                         UNSIGNED INTEGER [ range 0..1 ],
                         UNSIGNED INTEGER [ range 0..18446744073709551618 ],
                         UNSIGNED INTEGER [ range -100..100 ],
                         UNSIGNED INTEGER [ range -18446744073709551618..18446744073709551618 ],
                         UNSIGNED INTEGER [ range -18446744073709551618..-18446744073709551616 ],
                         UNSIGNED INTEGER [ range 8bit ],
                         UNSIGNED INTEGER [ range 16bit ],
                         UNSIGNED INTEGER [ range 32bit ],
                         UNSIGNED INTEGER [ range 64bit ],
                         FLOAT [ range 0..1 ],
                         FLOAT [ range 0..18446744073709551618 ],
                         FLOAT [ range -100..100 ],
                         FLOAT [ range -100.5..100.5 ],
                         FLOAT [ range -18446744073709551618..18446744073709551618 ],
                         FLOAT [ range -18446744073709551618..-18446744073709551616 ],
                         FLOAT [ range -18446744073709551618.5..18446744073709551618.00007 ],
                         FLOAT [ range 32bit ],
                         FLOAT [ range 64bit ]
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)
        
        schemaText = 'test => INTEGER [ range 1..0 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'must be >=')
        
        schemaText = 'test => INTEGER [ range 100..-100 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'must be >=')

        schemaText = 'test => INTEGER [ range 0..1.5 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'must be integers')
        
        schemaText = 'test => FLOAT [ range 8bit ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'only 32bit and 64bit range')

        schemaText = 'test => FLOAT [ range 16bit ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'only 32bit and 64bit range')

    def test_Qualifiers_LengthArguments(self):
        schemaText = '''
                     test => ARRAY
                     {
                         STRING [ length 42 ],
                         STRING [ length 0..1 ],
                         STRING [ length 100..18446744073709551618 ],
                         STRING [ length 0.. ],
                         BYTE STRING [ length 0 ],
                         BYTE STRING [ length 0..1 ],
                         BYTE STRING [ length 100..18446744073709551618 ],
                         BYTE STRING [ length 100.. ],
                         ARRAY [ length 18446744073709551618 ] OF BOOLEAN,
                         ARRAY [ length 1..1 ] OF BOOLEAN,
                         ARRAY [ length 100..18446744073709551618 ] OF NULL,
                         ARRAY [ length 0..0 ] { ANY * },
                         ARRAY [ length 18446744073709551618.. ] { },
                         LIST [ length 1 ] OF ANY,
                         LIST [ length 100..101 ] OF INTEGER,
                         LIST [ length 100..18446744073709551618 ] OF BYTE STRING,
                         LIST [ length 18446744073709551618..18446744073709551618 ] { },
                         LIST [ length 1.. ] OF STRUCTURE { },
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)

        schemaText = 'test => STRING [ length 1..0 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'must be >= lower bound')

        schemaText = 'test => STRING [ length -1..0 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'must be >= 0')

        schemaText = 'test => STRING [ length 0..-1 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 2)
        self.assertError(errs, 'must be >= 0')
        self.assertError(errs, 'must be >= lower bound')


if __name__ == '__main__':
    unittest.main()
