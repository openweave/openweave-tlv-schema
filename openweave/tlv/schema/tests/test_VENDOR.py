import unittest

import sys
import os
import io

from .testutils import TLVSchemaTestCase

class Tests(TLVSchemaTestCase):
    
    def test_VENDOR(self):
        schemaText = '''
                     test-vendor-1 => VENDOR [ id 0 ]
                     test-vendor-2 => VENDOR [ id 1 ]
                     test-vendor-65535 => VENDOR [ id 65535 ]
                     '''
        errs = self.loadValidate(schemaText)
        self.assertNoErrors(errs)

    def test_VENDOR_NoId(self):
        schemaText = 'test-vendor-1 => VENDOR'
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'id qualifier missing')

        schemaText = 'test-vendor-1 => VENDOR [ ]'
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'id qualifier missing')

    def test_VENDOR_BadId(self):
        schemaText = 'test-vendor-1 => VENDOR [ id 65536 ]'
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

        schemaText = 'test-vendor-1 => VENDOR [ id -1 ]'
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

        schemaText = 'test-vendor-1 => VENDOR [ id 42:1 ]'
        errs = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')


if __name__ == '__main__':
    unittest.main()
