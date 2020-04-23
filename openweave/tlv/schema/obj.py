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

from .node import *
from .node import _addSchemaError
from .transformer import _SchemaTransformer

class WeaveTLVSchema(object):
    EBNFFileName = 'tlv-schema-ebnf.txt'
    
    _schemaParser = None
    
    _defaultSchema = '''
common => VENDOR [ id 0 ] 
'''
    
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
        self._defaultSchemaLoaded = False

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

    def loadDefaultSchema(self):
        if not self._defaultSchemaLoaded:        
            self.loadSchemaFromString(self._defaultSchema, fileName='(default)')
            self._defaultSchemaLoaded = True

    def validate(self):
        '''Check the loaded schema files for syntactical and structural errors and
           return a list of exceptions describing any errors found.'''
        self.loadDefaultSchema()
        errs = []
        self._resolveTypeReferences(errs)
        self._resolveVendorReferences(errs)
        self._resolveProfileReferences(errs)
        for node in self.allNodes():
            node.validate(errs)
        self._checkInconsistentVendorIds(errs)
        self._checkInconsistentProfileIds(errs)
        self._checkUniqueProfileIds(errs)
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

    def getTypeDef(self, typeName):
        typeDefList = self._typeDefs.get(typeName, None)
        if typeDefList is not None:
            return typeDefList[0]
        return None

    def getProfile(self, profileName):
        profileList = self._profiles.get(profileName, None)
        if profileList is not None:
            return profileList[0]
        return None

    def getVendor(self, vendorName):
        vendorList = self._vendors.get(vendorName, None)
        if vendorList is not None:
            return vendorList[0]
        return None
    
    # ----- Private Members

    def _indexNodes(self, schemaFile):
        for node in schemaFile.allNodes(Vendor):
            self._vendors[node.name].append(node)
        for node in schemaFile.allNodes(Namespace):
            self._namespaces[node.fullyQualifiedName].append(node)
        for node in schemaFile.allNodes(Profile):
            self._profiles[node.fullyQualifiedName].append(node)
        for node in schemaFile.allNodes(TypeDef):
            self._typeDefs[node.fullyQualifiedName].append(node)

    def _checkInconsistentVendorIds(self, errs):
        '''Check that all VENDOR definitions with the same name have the same vendor id'''
        for likeNamedVendors in self._vendors.values():
            # Ignore vendor definitions without ids.  These are errors that are detected elsewhere.
            likeNamedVendors = [ v for v in likeNamedVendors if v.id is not None ]
            if len(likeNamedVendors) == 0:
                continue
            id = likeNamedVendors[0].id
            for vendor in likeNamedVendors:
                if vendor.id != id:
                    _addSchemaError(errs, msg='inconsistent vendor id: 0x%04X (%d)' % (vendor.id, vendor.id),
                                    detail='VENDOR definitions with the same name must declare the same vendor id',
                                    sourceRef=vendor.sourceRef)

    def _checkInconsistentProfileIds(self, errs):
        '''Check that all PROFILE definitions with the same name have the same profile id'''
        for likeNamedProfiles in self._profiles.values():
            # Ignore profile definitions without ids.  These are errors that are detected elsewhere.
            likeNamedProfiles = [ p for p in likeNamedProfiles if p.id is not None ]
            if len(likeNamedProfiles) == 0:
                continue
            id = likeNamedProfiles[0].id
            for profile in likeNamedProfiles:
                if profile.id != id:
                    _addSchemaError(errs, msg='inconsistent profile id: 0x%08X (%d)' % (profile.id, profile.id),
                                    detail='PROFILE definitions with the same name must declare the same profile id',
                                    sourceRef=profile.sourceRef)

    def _checkUniqueProfileIds(self, errs):
        '''Check that all PROFILE definitions with different names have distinct profile ids'''
        profilesById = {}
        for profile in self.allNodes(Profile):
            # Ignore profile definitions without ids. These are errors that are detected elsewhere.
            if profile.id is None:
                continue
            otherProfile = profilesById.get(profile.id, None)
            if otherProfile is not None:
                if profile.fullyQualifiedName != otherProfile.fullyQualifiedName:
                    _addSchemaError(errs, msg='non-unique profile id: 0x%08X (%d)' % (profile.id, profile.id),
                                    detail='PROFILE definitions with distinct names must have distinct profile ids',
                                    sourceRef=profile.sourceRef)
            else:
                profilesById[profile.id] = profile

    def _resolveTypeReferences(self, errs):
        '''Resolve the type names in all type reference nodes (e.g. ReferencedType and
           StructureIncludes) to the corresponding TypeDef nodes and the associated
           Type node.'''

        # NOTE: this algorithm is designed to always re-evaluate all type references, even
        # if they have been previously resolved.  This allows the function to be called a
        # second time, after loading a new schema which changes the resolution of some
        # types. 
        
        # For each node that represents a reference to a type, attempt to resolve the
        # type name to a corresponding TypeDef node and attach the TypeDef node to the
        # referencing node. Generate errors for any names that cannot be resolved.        
        for refNode in self.allNodes((ReferencedType, StructureIncludes)):
            refNode.targetTypeDef = self._resolveTypeName(refNode.targetName, refNode)
            if refNode.targetTypeDef is None:
                _addSchemaError(errs, msg='invalid type reference: %s' % refNode.targetName,
                                detail='the given type name could not be resolved',
                                sourceRef=refNode.sourceRef)
                
        # For each node that represents a reference to a type, follow the chain of TypeDef
        # nodes to the final one (the one that is not itself a type reference), and attach
        # the Type node to the referencing node.  Ignore any type references that were
        # unresolved by the above loop.  Generate an error if a circular type reference
        # chain is encountered.
        for refNode in self.allNodes((ReferencedType, StructureIncludes)):
            visitedRefNodes = [ ]
            while refNode.targetTypeDef is not None:
                visitedRefNodes.append(refNode)
                if isinstance(refNode.targetTypeDef.type, ReferencedType):
                    if refNode.targetTypeDef.type in visitedRefNodes:
                        _addSchemaError(errs, msg='circular type reference: %s' % refNode.targetName,
                                        detail='the given type reference ultimately refers to itself',
                                        sourceRef=refNode.nameSourceRef)
                        break
                    refNode = refNode.targetTypeDef.type
                else:
                    visitedRefNodes[0].targetType = refNode.targetTypeDef.type
                    break
                
    def _resolveTypeName(self, typeName, baseNode):
        '''Resolve a target type name to corresponding TypeDef node, interpreting relative
           type names in relation to a given base node.'''
        # For each namespace node that is a parent of the base node, in ascending order,
        # compose a fully-qualified type name using the target type name and the FQ name
        # of the namespace. Add the target type name itself to the end of this list.
        nsNodes = baseNode.allParentNodes(Namespace)
        fqTypeNames = [n.fullyQualifiedName + '.' + typeName for n in nsNodes]
        fqTypeNames.append(typeName)
        # Search for and return the first type definition whose fully-qualified name
        # matches one of the possible names, or None if no match found.
        for fqTypeName in fqTypeNames:
            typeDef = self.getTypeDef(fqTypeName)
            if typeDef is not None:
                return typeDef
        return None

    def _resolveVendorReferences(self, errs):
        for idNode in self.allNodes(Id):
            if not isinstance(idNode.parent, Profile):
                continue
            if isinstance(idNode.vendor, str):
                idNode.vendorNode = self.getVendor(idNode.vendor)
                if idNode.vendorNode is None:
                    _addSchemaError(errs, msg='invalid vendor reference: %s' % idNode.vendor,
                                    detail='a VENDOR definition with the specified name could not be found',
                                    sourceRef=idNode.sourceRef)

    def _resolveProfileReferences(self, errs):
        for tagNode in self.allNodes(Tag):
            if isinstance(tagNode.profile, str):
                if tagNode.profile == '*':
                    tagNode.profileNode = tagNode.nextParentNode(Profile)
                    if tagNode.profileNode is None:
                        _addSchemaError(errs, msg='invalid reference to current profile',
                                        detail='a current profile reference (*) must appear within a PROFILE definition',
                                        sourceRef=tagNode.sourceRef)
                else:
                    tagNode.profileNode = self.getProfile(tagNode.profile)
                    if tagNode.profileNode is None:
                        _addSchemaError(errs, msg='invalid profile reference: %s' % tagNode.profile,
                                        detail='a PROFILE definition with the specified name could not be found',
                                        sourceRef=tagNode.sourceRef)
                    
            



