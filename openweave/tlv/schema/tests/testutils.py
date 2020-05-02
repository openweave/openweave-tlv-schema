import unittest

import sys
import os
import io

from openweave.tlv.schema import WeaveTLVSchema
from openweave.tlv.schema.error import WeaveTLVSchemaError

class TLVSchemaTestCase(unittest.TestCase):

    @staticmethod
    def loadValidate(schemaText):
        tlvSchema = WeaveTLVSchema()
        errs = []
        try:
            tlvSchema.loadSchemaFromString(schemaText)
        except WeaveTLVSchemaError as err:
            errs.append(err)
        errs += tlvSchema.validate()
        return (tlvSchema, errs)
    
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

