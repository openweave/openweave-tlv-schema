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
#         Unit tests for basic syntax checking.
#

import unittest
import functools
import types

from .testutils import TLVSchemaTestCase

class Test_Syntax(TLVSchemaTestCase):
    
    _testCases = [
        ( 'TypeNames', [
            ('foo => INTEGER',                                              None),
            ('foo1 => INTEGER',                                             None),
            ('foo1b => INTEGER',                                            None),
            ('foo_ => INTEGER',                                             None),
            ('foo_b => INTEGER',                                            None),
            ('foo- => INTEGER',                                             None),
            ('foo-b => INTEGER',                                            None),
            ('_foo => INTEGER',                                             None),
            ('_foo_ => INTEGER',                                            None),
            ('_foo_b => INTEGER',                                           None),
            ('_ => INTEGER',                                                None),
            ('namespace ns { foo => INTEGER } ',                            None),
            ('namespace ns { foo1 => INTEGER } ',                           None),
            ('namespace ns { foo1b => INTEGER } ',                          None),
            ('namespace ns { foo_ => INTEGER } ',                           None),
            ('namespace ns { foo_b => INTEGER } ',                          None),
            ('namespace ns { foo- => INTEGER } ',                           None),
            ('namespace ns { foo-b => INTEGER } ',                          None),
            ('namespace ns { _foo => INTEGER } ',                           None),
            ('namespace ns { _foo_ => INTEGER } ',                          None),
            ('namespace ns { _foo_b => INTEGER } ',                         None),
            ('namespace ns { _ => INTEGER } ',                              None),
        ]),
        
        ( 'ContainedNames', [
            ('s => STRUCTURE { foo [0] : INTEGER } ',                       None),
            ('s => STRUCTURE { foo1 [1] : INTEGER } ',                      None),
            ('s => STRUCTURE { foo1b [2] : INTEGER } ',                     None),
            ('s => STRUCTURE { foo_ [3] : INTEGER } ',                      None),
            ('s => STRUCTURE { foo_b [4] : INTEGER } ',                     None),
            ('s => STRUCTURE { foo- [5] : INTEGER } ',                      None),
            ('s => STRUCTURE { foo-b [6] : INTEGER } ',                     None),
            ('s => STRUCTURE { _foo [7] : INTEGER } ',                      None),
            ('s => STRUCTURE { _foo_ [8] : INTEGER } ',                     None),
            ('s => STRUCTURE { _foo_b [9] : INTEGER } ',                    None),
            ('s => STRUCTURE { _ [10] : INTEGER } ',                        None),
        ]),
        
        ( 'KeywordNames', [
            ('"INTEGER" => NULL',                                           None),
            ('"SIGNED" => NULL',                                            None),
            ('"UNSIGNED" => NULL',                                          None),
            ('"STRING" => NULL',                                            None),
            ('"BOOLEAN" => NULL',                                           None),
            ('"BYTE" => NULL',                                              None),
            ('"NULL" => NULL',                                              None),
            ('"ANY" => NULL',                                               None),
            ('"CHOICE" => NULL',                                            None),
            ('"ARRAY" => NULL',                                             None),
            ('"LIST" => NULL',                                              None),
            ('"STRUCTURE" => NULL',                                         None),
            ('"FIELD" => NULL',                                             None),
            ('"GROUP" => NULL',                                             None),
            ('"OF" => NULL',                                                None),
            ('namespace "range"."INTEGER" { }',                             None),
        ]),

        ( 'NamespaceNames', [
            ('namespace ns { }',                                            None),
            ('namespace ns1 { }',                                           None),
            ('namespace ns1b { }',                                          None),
            ('namespace ns_ { }',                                           None),
            ('namespace ns_b { }',                                          None),
            ('namespace ns- { }',                                           None),
            ('namespace ns-b { }',                                          None),
            ('namespace _ns { }',                                           None),
            ('namespace _ns_ { }',                                          None),
            ('namespace _ns_b { }',                                         None),
            ('namespace _ { }',                                             None),
            ('namespace ns.ns { }',                                         None),
            ('namespace ns.ns1 { }',                                        None),
            ('namespace ns.ns1b { }',                                       None),
            ('namespace ns.ns_ { }',                                        None),
            ('namespace ns.ns_b { }',                                       None),
            ('namespace ns.ns- { }',                                        None),
            ('namespace ns.ns-b { }',                                       None),
            ('namespace ns._ns { }',                                        None),
            ('namespace ns._ns_ { }',                                       None),
            ('namespace ns._ns_b { }',                                      None),
            ('namespace ns._ { }',                                          None),
            ('namespace ns1.ns { }',                                        None),
            ('namespace ns1b.ns { }',                                       None),
            ('namespace ns_.ns { }',                                        None),
            ('namespace ns_b.ns { }',                                       None),
            ('namespace ns-.ns { }',                                        None),
            ('namespace ns-b.ns { }',                                       None),
            ('namespace _ns.ns { }',                                        None),
            ('namespace _ns_.ns { }',                                       None),
            ('namespace _ns_b.ns { }',                                      None),
            ('namespace _.ns { }',                                          None),
        ]),

        ( 'BadName', [
            ('-foo => INTEGER',                                             'invalid name: -foo'),
            ('"-foo" => INTEGER',                                           'invalid name: "-foo"'),
            ('8foo => INTEGER',                                             'unexpected numeric value: 8'),
            ('"8foo" => INTEGER',                                           'invalid name: "8foo"'),
            ('"+foo" => INTEGER',                                           'invalid name: "+foo"'),
            ('"foo|" => INTEGER',                                           'invalid name: "foo|"'),
            ('"" => INTEGER',                                               'unexpected input: ""'),
        ]),

        ( 'UnexpectedCharacter', [
            ('|foo => INTEGER',                                             'unexpected input: |'),
            ('foo| => INTEGER',                                             'unexpected input: |'),
            ('foo |=> INTEGER',                                             'unexpected input: |'),
            ('foo => |INTEGER',                                             'unexpected input: |'),
            ('foo => INTEGER|',                                             'unexpected input: |'),
            (',foo => STRUCTURE [tag-order] { }',                           'unexpected input: ,'),
            ('foo, => STRUCTURE [tag-order] { }',                           'unexpected input: ,'),
            ('foo ,=> STRUCTURE [tag-order] { }',                           'unexpected input: ,'),
            ('foo =>, STRUCTURE [tag-order] { }',                           'unexpected input: ,'),
            ('foo => ,STRUCTURE [tag-order] { }',                           'unexpected input: ,'),
            ('foo => STRUCTURE, [tag-order] { }',                           'unexpected input: ,'),
            ('foo => STRUCTURE ,[tag-order] { }',                           'unexpected input: ,'),
            ('foo => STRUCTURE [tag-order], { }',                           'unexpected input: ,'),
            ('foo => STRUCTURE [tag-order] ,{ }',                           'unexpected input: ,'),
            ('foo => STRUCTURE [tag-order] { },',                           'unexpected input: ,'),
        ]),

        ( 'UnexpectedKeyword', [
            ('length foo => INTEGER',                                       'unexpected keyword: length'),
            ('foo length => INTEGER',                                       'unexpected keyword: length'),
            ('foo => length INTEGER',                                       'unexpected keyword: length'),
            ('foo => INTEGER length',                                       'unexpected keyword: length'),
            ('ANY foo => STRUCTURE [tag-order] { f [0] : NULL }',           'unexpected keyword: ANY'),
            ('foo ANY => STRUCTURE [tag-order] { f [0] : NULL }',           'unexpected keyword: ANY'),
            ('foo => ANY STRUCTURE [tag-order] { f [0] : NULL }',           'unexpected keyword: STRUCTURE'),
            ('foo => STRUCTURE ANY [tag-order] { f [0] : NULL }',           'unexpected keyword: ANY'),
            ('foo => STRUCTURE [ANY tag-order] { f [0] : NULL }',           'unexpected keyword: ANY'),
            ('foo => STRUCTURE [tag-order ANY] { f [0] : NULL }',           'unexpected keyword: ANY'),
            ('foo => STRUCTURE [tag-order] ANY { f [0] : NULL }',           'unexpected keyword: ANY'),
            ('foo => STRUCTURE [tag-order] { ANY f [0] : NULL }',           'unexpected keyword: ANY'),
            ('foo => STRUCTURE [tag-order] { f ANY [0] : NULL }',           'unexpected keyword: ANY'),
            ('foo => STRUCTURE [tag-order] { f [ ANY 0] : NULL }',          'unexpected keyword: ANY'),
            ('foo => STRUCTURE [tag-order] { f [0 ANY] : NULL }',           'unexpected keyword: ANY'),
            ('foo => STRUCTURE [tag-order] { f [0] ANY : NULL }',           'unexpected keyword: ANY'),
            ('foo => STRUCTURE [tag-order] { f [0] : ANY NULL }',           'unexpected keyword: NULL'),
        ]),

        ( 'MissingInput', [
            ('foo',                                                         'unexpected end of input'),
            ('foo =>',                                                      'unexpected end of input'),
            ('foo => CHOICE',                                               'unexpected end of input'),
            ('foo => CHOICE { }',                                           'unexpected input: {'),
            ('foo => FIELD { }',                                            'unexpected input: {'),
            ('foo => PROFILE [ id 0',                                       'unexpected end of input'),
            ('foo => PROFILE [ id 0 ] {',                                   'unexpected end of input'),
            ('foo => PROFILE [ id 0 { }',                                   'unexpected input: {'),
            ('"foo => INTEGER',                                             'unterminated string'),
            ('"foo => INTEGER\n"bar" => INTEGER',                           'unterminated string'),
            ('foo => INTEGER { bar }',                                      'unexpected input: }'),
            ('foo => INTEGER { bar = }',                                    'unexpected input: }'),
            ('foo => INTEGER { bar =',                                      'unexpected end of input'),
            ('foo => INTEGER { bar = 42',                                   'unexpected end of input'),
        ]),
    
    ]

    def _runTest(self, schemaText, expectedErr):
        (tlvSchema, errs) = self.loadValidate(schemaText)
        if expectedErr is None:
            self.assertNoErrors(errs)
        else:
            self.assertErrorCount(errs, 1)
            self.assertError(errs, expectedErr)

    # At class definition time, dynamically add methods to the class for each of the
    # defined test cases.
    for (testGroupName, tests) in _testCases:
        for i in range(len(tests)):
            (schemaText, expectedErr) = tests[i]
            testMethodName = 'test_Syntax_%s_Case%02d' % (testGroupName, i+1)
            # This produces a function which, when called, calls _runTest() on a given 
            # instance of the test class, passing the current schema text and expected
            # error strings.
            def makeTestMethod(schemaText, expectedErr, _runTest=_runTest):
                def _callRunTest(self):
                    return _runTest(self, schemaText, expectedErr)
                return _callRunTest
            # Add a method to the class for running the current test case.
            vars()[testMethodName] = makeTestMethod(schemaText, expectedErr)

if __name__ == '__main__':
    unittest.main()
