import unittest

import sys
import os
import io

from openweave.tlv.schema import WeaveTLVSchema

class TLVSchemaTestCase(unittest.TestCase):

    @staticmethod
    def loadValidate(schemaText):
        tlvSchema = WeaveTLVSchema()
        tlvSchema.loadSchemaFromString(schemaText)
        return tlvSchema.validate()
    
    def assertErrorCount(self, errs, count):
        if len(errs) != count:
            errSum = ''.join((('\n  ' + err.__repr__()) for err in errs))
            errMsg = 'Expected %d error%s, got %d%s' % (count, '' if count == 1 else 's', len(errs), errSum) 
            self.fail(errMsg);
        
    def assertNoErrors(self, errs):
        self.assertErrorCount(errs, 0)

    def assertError(self, errs, errText):
        for err in errs:
            if errText in str(err):
                return
        errSum = ''.join((('\n  ' + err.__repr__()) for err in errs))
        errMsg = 'Expected error with text "%s" not found in:%s' % (errText, errSum) 
        self.fail(errMsg);

