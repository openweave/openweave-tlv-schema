import unittest

from .testutils import TLVSchemaTestCase

class Tests(TLVSchemaTestCase):
    
    def test_LIST_DuplicateElementNames(self):
        schemaText = '''
                     test-list => LIST
                     {
                         elem-a : INTEGER,
                         elem-b : INTEGER,
                                  FLOAT,
                         elem-a : STRING,
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate item in LIST type: elem-a')

    def test_LIST_DisallowFIELDGROUP(self):
        schemaText = '''
                     test-list => LIST
                     {
                         elem-a : INTEGER,
                         elem-b : INTEGER,
                                  FIELD GROUP { },
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertEqual(len(errs), 1)
        self.assertError(errs, 'FIELD GROUP type not allowed')
        schemaText = '''
                     test-list => LIST
                     {
                         elem-a : INTEGER,
                         elem-b : INTEGER,
                                  test-field-group,
                     }
                     test-field-group => FIELD GROUP { }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertEqual(len(errs), 1)
        self.assertError(errs, 'FIELD GROUP type not allowed')

if __name__ == '__main__':
    unittest.main()
