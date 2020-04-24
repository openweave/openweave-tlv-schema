import unittest

from .testutils import TLVSchemaTestCase

class Test_STATUS_CODE(TLVSchemaTestCase):
    
    def test_STATUS_CODE(self):
        schemaText = '''
                     profile1 => PROFILE [ id 42 ]
                     {
                         sc1 => STATUS CODE [ id 1 ]
                         sc2 => STATUS CODE [ id 2 ]
                         sc3 => STATUS CODE [ id 3 ]
                         sc4 => STATUS CODE [ id 4 ]
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)
        profile1 = tlvSchema.getProfile('profile1')
        sc1 = profile1.getStatusCode('sc1')
        self.assertEqual(sc1.id, 1)
        sc2 = profile1.getStatusCode('sc2')
        self.assertEqual(sc2.id, 2)
        sc3 = profile1.getStatusCode('sc3')
        self.assertEqual(sc3.id, 3)
        sc4 = profile1.getStatusCode('sc4')
        self.assertEqual(sc4.id, 4)

    def test_STATUS_CODE_NoId(self):
        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         sc1 => STATUS CODE
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'id qualifier missing')

        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         sc1 => STATUS CODE [ ]
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'id qualifier missing')

    def test_STATUS_CODE_BadId(self):
        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         sc1 => STATUS CODE [ id 0x1000000 ]
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         sc1 => STATUS CODE [ id -1 ]
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         sc1 => STATUS CODE [ id 65536 ]
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

        schemaText = '''profile1 => PROFILE [ id 42 ]
                     {
                         sc1 => STATUS CODE [ id 1:1 ]
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

    def test_STATUS_CODE_NonUniqueId(self):
        schemaText = '''
                     profile1 => PROFILE [ id 42 ]
                     {
                         sc1 => STATUS CODE [ id 1 ]
                         sc2 => STATUS CODE [ id 2 ]
                         sc3 => STATUS CODE [ id 1 ] // ERROR: id not unique
                     }
                     profile2 => PROFILE [ id 24 ]
                     {
                         sc1 => STATUS CODE [ id 1 ] // Not an error; different profile
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'duplicate status code id: 1')

    def test_STATUS_CODE_NotInProfile(self):
        schemaText = '''
                     profile1 => PROFILE [ id 42 ]
                     {
                         sc1 => STATUS CODE [ id 1 ]
                     }
                     sc2 => STATUS CODE [ id 2 ] // ERROR: not in PROFILE
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'STATUS CODE definition not within PROFILE definition')

        schemaText = '''
                     profile1 => PROFILE [ id 42 ]
                     {
                         sc1 => STATUS CODE [ id 1 ]
                         namespace ns1
                         {
                             sc2 => STATUS CODE [ id 2 ] // ERROR: not directly in PROFILE
                         }
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'STATUS CODE definition not within PROFILE definition')

if __name__ == '__main__':
    unittest.main()
