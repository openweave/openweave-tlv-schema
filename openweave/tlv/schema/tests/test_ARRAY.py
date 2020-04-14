import unittest

import sys
import os
import io

from .testutils import TLVSchemaTestCase

class Tests(TLVSchemaTestCase):
    
    def test_ARRAY_DuplicateElementNames(self):
        schemaText = '''
                     test-array => ARRAY
                     {
                         elem-a : INTEGER,
                         elem-b : INTEGER,
                                  FLOAT,
                         elem-a : STRING,
                     }
                     '''
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate item in ARRAY type: elem-a')

    def test_ARRAY_DisallowFIELDGROUP(self):
        schemaText = '''
                     test-array => ARRAY
                     {
                         elem-a : INTEGER,
                         elem-b : INTEGER,
                                  FIELD GROUP { },
                     }
                     '''
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'FIELD GROUP type not allowed')

        schemaText = '''
                     test-array => ARRAY
                     {
                         elem-a : INTEGER,
                         elem-b : INTEGER,
                                  test-field-group,
                     }
                     test-field-group => FIELD GROUP { }
                     '''
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'FIELD GROUP type not allowed')

if __name__ == '__main__':
    unittest.main()
