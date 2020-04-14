#
#    Copyright (c) 2020 Google LLC.
#    All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

#
#    @file
#      Code for parsing and interpreting Weave TLV Schemas. 
#

import sys
import os
import io

from lark import Lark
from collections import defaultdict

from .ast import *
from .transformer import _SchemaTransformer

class WeaveTLVSchema(object):
    EBNFFileName = 'tlv-schema-ebnf.txt'
    
    _schemaParser = None
    
    def __init__(self):
        if WeaveTLVSchema._schemaParser is None:
            scriptDir = os.path.dirname(os.path.realpath(__file__))
            with open(os.path.join(scriptDir, WeaveTLVSchema.EBNFFileName), "r") as s:
                schemaSyntax = s.read()
                WeaveTLVSchema._schemaParser = Lark(schemaSyntax, start='file', propagate_positions=True)
        self._schemaFiles = []
        self._vendors = defaultdict(list)
        self._namespaces = defaultdict(list)
        self._profiles = defaultdict(list)
        self._typeDefs = defaultdict(list)

    def loadSchemaFromStream(self, stream, fileName=None):
        if fileName is None:
            if hasattr(stream, 'name'):
                fileName = stream.name
            else:
                fileName = '(stream)'
        schemaText = stream.read()
        schemaTree = WeaveTLVSchema._schemaParser.parse(schemaText)
        schemaFile = _SchemaTransformer(fileName=fileName, schemaText=schemaText).transform(schemaTree)
        self._schemaFiles.append(schemaFile)
        self._indexNodes(schemaFile)
        return schemaFile
    
    def loadSchemaFromFile(self, fileName):
        with open(fileName, "r") as f:
            return self.loadSchemaFromStream(f, fileName)

    def loadSchemaFromString(self, s, fileName='(string)'):
        with io.StringIO(s) as f:
            return self.loadSchemaFromStream(f, fileName)

    def validate(self):
        errs = []
        self._resolveTypeReferences(errs)
        self._checkNodeErrors(errs)
        return errs
    
    def allNodes(self, classinfo=object):
        '''Iterate for all nodes and their descendants, if they are instances of classinfo'''
        for schemaFile in self._schemaFiles:
            for node in schemaFile.allNodes():
                if isinstance(node, classinfo):
                    yield node

    def allFiles(self):
        '''Iterate for schema files'''
        for schemaFile in self._schemaFiles:
            yield schemaFile

    def _indexNodes(self, schemaFile):
        for node in schemaFile.allNodes(Vendor):
            self._vendors[node.name].append(node)
        for node in schemaFile.allNodes(Namespace):
            self._namespaces[node.fullyQualifiedName].append(node)
        for node in schemaFile.allNodes(Profile):
            self._profiles[node.fullyQualifiedName].append(node)
        for node in schemaFile.allNodes(TypeDef):
            self._typeDefs[node.fullyQualifiedName].append(node)

    def _checkDuplicates(self, errs):
        # TODO: finish this
        for likeNamedVendorDefs in self._vendors.values():
            pass

    def _checkNodeErrors(self, errs):
        for node in self.allNodes():
            node.checkErrors(errs)

    def _resolveTypeReferences(self, errs):
        # NOTE: this algorithm is designed to always re-evaluate all type references, even
        # if they have been previously resolved.  This allows the function to be called a
        # second time, after loading a new schema which changes the resolution of some
        # types. 
        visitedNodes = [ ]
        for refNode in self.allNodes((ReferencedType, StructureIncludes)):
            visitedNodes.clear()
            while True:
                visitedNodes.append(refNode)
                typeDefNode = self._resolveTypeName(refNode.targetName, refNode)
                if typeDefNode is None:
                    errs.append(SchemaError(msg='Invalid type reference: %s' % refNode.targetName,
                                            detail='The given type name could not be resolved',
                                            sourceRef=refNode.sourceRef))
                    break
                elif isinstance(typeDefNode.type, ReferencedType):
                    if typeDefNode.type in visitedNodes:
                        errs.append(SchemaError(msg='Circular type reference: %s' % refNode.targetName,
                                                detail='The given type reference ultimately refers to itself',
                                                sourceRef=refNode.nameSourceRef))
                        break
                    refNode = typeDefNode.type
                else:
                    visitedNodes[0].targetType = typeDefNode.type
                    break

    def _resolveTypeName(self, typeName, baseNode):
        while baseNode is not None:
            nsNode = baseNode.containingNamespaceNode()
            if nsNode is not None:
                fqTypeName = nsNode.fullyQualifiedName + '.' + typeName
            else:
                fqTypeName = typeName
            typeDefs = self._typeDefs.get(fqTypeName, None)
            if typeDefs is not None:
                return typeDefs[0]
            baseNode = nsNode
        return None







