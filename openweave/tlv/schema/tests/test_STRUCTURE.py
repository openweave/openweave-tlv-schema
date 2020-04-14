import unittest

import sys
import os
import io

from .testutils import TLVSchemaTestCase

class Tests(TLVSchemaTestCase):
    
    def test_STRUCTURE_DuplicateFieldNames(self):
        schemaText = '''
                     test-struct => STRUCTURE
                     {
                         field-a : INTEGER,
                         field-b : INTEGER,
                         field-a : STRING,
                     }
                     '''
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate field in STRUCTURE type: field-a')

    def test_STRUCTURE_DuplicateFieldNames_InFieldGroup(self):
        schemaText = '''
                     test-field-group => FIELD GROUP
                     {
                         field-a : INTEGER,
                         field-b : INTEGER,
                         field-a : STRING,
                     }
                     '''
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate field in FIELD GROUP type: field-a')

    def test_STRUCTURE_DuplicateFieldNames_BeforeFieldGroup(self):
        schemaText = '''
                     test-struct => STRUCTURE
                     {
                         field-a : INTEGER,
                         field-b : INTEGER,
                         includes test-field-group,
                     }
                     
                     test-field-group => FIELD GROUP
                     {
                         field-a : STRING,
                     }
                     '''
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate field in STRUCTURE type: field-a')

    def test_STRUCTURE_DuplicateFieldNames_AfterFieldGroup(self):
        schemaText = '''
                     test-struct => STRUCTURE
                     {
                         includes test-field-group,
                         field-a : INTEGER,
                         field-b : INTEGER,
                     }
                     
                     test-field-group => FIELD GROUP
                     {
                         field-a : STRING,
                     }
                     '''
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate field in STRUCTURE type: field-a')

    def test_STRUCTURE_DuplicateFieldNames_InReferencedFieldGroup(self):
        # In this test, there should only be one error related to the FIELD GROUP
        # having a duplicate field.  There should NOT be an error related to the
        # STRUCTURE that includes the FIELD GROUP with the duplicate field.
        schemaText = '''
                     test-field-group => FIELD GROUP
                     {
                         field-a : INTEGER,
                         field-b : INTEGER,
                         field-a : STRING,
                     }

                     test-struct => STRUCTURE
                     {
                         includes test-field-group
                     }
                     '''
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate field in FIELD GROUP type: field-a')

    def test_STRUCTURE_DisallowFIELDGROUP(self):
        schemaText = '''
                     test-struct => STRUCTURE
                     {
                         field-a : FIELD GROUP { },
                     }
                     '''
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'FIELD GROUP type not allowed')
        schemaText = '''
                     test-struct => STRUCTURE
                     {
                         field-a : test-field-group,
                     }
                     test-field-group => FIELD GROUP { }
                     '''
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'FIELD GROUP type not allowed')

if __name__ == '__main__':
    unittest.main()
