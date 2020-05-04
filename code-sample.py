#!/usr/bin/env python3

import sys
from openweave.tlv.schema import WeaveTLVSchema

tlvSchema = WeaveTLVSchema()

# Load the schema file.
tlvSchema.loadSchemaFromFile('examples/temp-sample.txt')

# Verify that the schema is syntactically and structurally correct.
errs = tlvSchema.validate()
if len(errs) > 0:
    for err in errs:
        print("%s\n" % err.format(), file=sys.stderr)
    sys.exit(-1)

# Locate the temperature field within the temperature-sample STRUCTURE
# and print its type and tag.
tempSampleType = tlvSchema.getTypeDef('temperature-sample').targetType
tempField = tempSampleType.getField('temperature')
print('temperature field is a %s with tag %s' % (tempField.targetType.schemaConstruct, tempField.tag))
