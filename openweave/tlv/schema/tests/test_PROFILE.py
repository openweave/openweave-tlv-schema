import unittest

from .testutils import TLVSchemaTestCase

class Tests(TLVSchemaTestCase):
    
    def test_PROFILE(self):
        schemaText = '''
                     profile1 => PROFILE [ id 0 ] { }
                     profile2 => PROFILE [ id 0x235A:1 ] { }
                     profile3 => PROFILE [ id Nest:65535 ]
                     Nest => VENDOR [ id 0x235A ]
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertNoErrors(errs)

    def test_PROFILE_NoId(self):
        schemaText = 'profile1 => PROFILE'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'id qualifier missing')

        schemaText = 'profile1 => PROFILE [ ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'id qualifier missing')

        schemaText = 'profile1 => PROFILE [ ] { foo => INTEGER }'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'id qualifier missing')

    def test_PROFILE_BadId(self):
        schemaText = 'profile1 => PROFILE [ id 0x100000000 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

        schemaText = 'profile1 => PROFILE [ id -1 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid id value')

        schemaText = 'profile1 => PROFILE [ id 65536:1 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid vendor id value')

        schemaText = 'profile1 => PROFILE [ id -1:1 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid vendor id value')

        schemaText = 'profile1 => PROFILE [ id 0:65536 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid profile number value')

        schemaText = 'profile1 => PROFILE [ id 0:-1 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid profile number value')

    def test_PROFILE_BadVendorReference(self):
        schemaText = 'profile1 => PROFILE [ id unknown:0 ]'
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid vendor reference')

        schemaText = '''
                     profile1 => PROFILE [ id VeNDoR1:0 ]
                     vendor1 => VENDOR [ id 1 ]
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'invalid vendor reference')

    def test_PROFILE_InconsistentId(self):
        schemaText = '''
                     profile1 => PROFILE [ id 0x12345678 ]
                     profile2 => PROFILE [ id 0x87654321 ]
                     profile1 => PROFILE [ id 42 ]             // ERROR: inconsistent id
                     profile2 => PROFILE [ id 0x87654321 ]
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 1)
        self.assertError(errs, 'inconsistent profile id: 0x0000002A (42)')

    def test_PROFILE_NonUniqueId(self):
        schemaText = '''
                     profile1 => PROFILE [ id 0x12345678 ]
                     profile2 => PROFILE [ id 0x12345678 ]        // ERROR: Id not unique
                     profile3 => PROFILE [ id 0xFEDCBA98 ]
                     namespace ns1
                     {
                         profile3 => PROFILE [ id 0xFEDCBA98 ]    // ERROR: Id not unique
                     }
                     '''
        (tlvSchema, errs) = self.loadValidate(schemaText)
        self.assertErrorCount(errs, 2)
        self.assertError(errs, 'non-unique profile id: 0x12345678 (305419896)')
        self.assertError(errs, 'non-unique profile id: 0xFEDCBA98 (4275878552)')

if __name__ == '__main__':
    unittest.main()
