# The openweave-tlv-schema Package

openweave-tlv-schema is a set of Python-based libraries and tools for working with Weave TLV schemas.
It is written in pure Python 3 and should work with any version of the language >= 3.6.


## Weave TLV Schema Language

The _Weave TLV Schema_ language provides a simple textual format for describing data and other
constructs typically used in Weave-based applications. Its primary use is to describe the
structure of data encoded in Weave TLV format, a compact binary data format targeting
constrained IoT devices.  However, TLV schemas can also describe higher level Weave constructs
such as Weave profiles, message types and status codes.  Emphasis is placed on the
inherent readability of the language, making it well suited for use in protocol documentation
and formal specifications.  Additionally, tools are provided for generating source code that
can be used when building Weave-based applications.


## Building and Installing

The openweave-tlv-schema package can be built using the supplied setup.py script:

    ./setup.py sdist
    
Install the package using pip3:

    pip3 install --user dist/openweave-tlv-schema-*.tar.gz
    
Alternatively, one can use the supplied Makefile to build and install:

    make install
    

## weave-tlv-schema Tool

The openweave-tlv-schema package includes a command-line tool called `weave-tlv-schema`.  The
`weave-tlv-schema` tool provides various commands for working with TLV schemas.  The `help`
command can be used to see a list of the available commands:

    $ ./weave-tlv-schema help
    weave-tlv-schema : A tool for working with Weave TLV Schemas
    
    Usage:
      weave-tlv-schema {command} [options] ...
    
    Available commands:
      validate - Validate the syntax and consistency of a TLV schema
      dump     - Dump the syntax tree for a TLV schema
      unittest - Run unit tests on the TLV schema code
      help     - Display usage information
    
    Run "weave-tlv-schema help <command>" for additional help.


### Validating Schemas

The `weave-tlv-schema validate` command can be used to check the correctness of a Weave TLV
schema:

    $ ./weave-tlv-schema validate examples/device-descriptor.txt 
    Validation completed successfully

If an error is found, the tool will produce detailed information about the nature and
location of the error:

    $ ./weave-tlv-schema validate ./examples/syntax-error.txt ./examples/schema-error.txt 
    ./examples/syntax-error.txt:4:26: ERROR: unexpected end of input
    NOTE: possibly missing }
    
        field-2 [1] : INTEGER,
                             ^
    
    ./examples/schema-error.txt:5:5: ERROR: duplicate field in STRUCTURE type: field-1
    NOTE: fields within a STRUCTURE type must have unique names
    
        field-1 [2] : STRING,   // bad field name
        ^


### Dumping a Parse Tree

The in-memory data structure (AST) representing a TLV schema can be summarized using the `weave-tlv-schema dump` command: 

    $ ./weave-tlv-schema dump examples/temp-sample.txt 
    SchemaFile: examples/temp-sample.txt
      pos: 1:1-5:2 0-119
      statements: (1) [
        TypeDef: temperature-sample
          pos: 1:1-5:2 0-119
          quals: -
          type:
            StructureType:
              pos: 1:23-5:2 22-119
              quals: -
              members: (2) [
                StructureField: timestamp
                  pos: 3:5-3:54 38-87
                  quals: (1) [
                    Tag: 1 (context-specific)
                      pos: 3:16-3:17 49-50
                  ]
                  type:
                    UnsignedIntegerType:
                      pos: 3:23-3:54 56-87
                      quals: (1) [
                        Range: width 32
                          pos: 3:41-3:53 74-86
                      ]
                StructureField: temperature
                  pos: 4:5-4:28 93-116
                  quals: (1) [
                    Tag: 2 (context-specific)
                      pos: 4:18-4:19 106-107
                  ]
                  type:
                    FloatType:
                      pos: 4:23-4:28 111-116
                      quals: -
              ]
      ]

### Using the API

The `WeaveTLVSchema` Python object provides programmatic access to the features of the openweave-tlv-schema package.
Using this API, developers can parse Weave TLV schemas to produce an in-memory representation of the schema (an AST)
which can then be queried for information:

```python
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
```

    $ python3 ./code-sample.py 
    temperature field is a FLOAT type with tag 2 (context-specific)

