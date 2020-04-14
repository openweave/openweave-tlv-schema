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
#      Objects representing Weave TLV Schemas as an AST.
#

import os
import itertools
from decimal import Decimal

from .error import WeaveTLVSchemaError as SchemaError

# ----- Mixin Classes for SchemaNodes

class HasName(object):
    '''Mixin for SchemaNodes that have human-readable text names'''

    def __init__(self, *args, **kwargs):
        super(HasName, self).__init__(*args, **kwargs)
        self.name = None
        self.nameSourceRef = None

    @property
    def _displayName(self):
        return self.name
    
class HasScopedName(HasName):
    '''Mixin for named SchemaNodes whose names are scoped by namespaces'''
    
    def __init__(self, *args, **kwargs):
        super(HasScopedName, self).__init__(*args, **kwargs)
        self._namespaceName = None
    
    @property
    def namespaceName(self):
        if self._namespaceName is None:
            containingNSNode = self.containingNamespaceNode()
            if containingNSNode is not None:
                self._namespaceName = containingNSNode.fullyQualifiedName
            else:
                self._namespaceName = ''
        return self._namespaceName

    @property
    def fullyQualifiedName(self):
        nsName = self.namespaceName
        if len(nsName) > 0:
            return nsName + '.' + self.name
        else:
            return self.name

    @property
    def _displayName(self):
        return self.fullyQualifiedName

class HasQualifiers(object):
    '''Mixin for SchemaNodes that can have qualifiers'''
    
    def __init__(self, *args, **kwargs):
        super(HasQualifiers, self).__init__(*args, **kwargs)
        self.quals = []

    def getQualifier(self, cls):
        for qual in self.quals:
            if isinstance(qual, cls):
                return qual
        return None
    
    def checkErrors(self, errs):
        super(HasQualifiers, self).checkErrors(errs)
        # Check that all qualifiers are allowed
        allowedQuals = self.__class__._allowedQualifiers
        for qual in self.quals:
            if not isinstance(qual, allowedQuals):
                errMsg = '%s not allowed on %s' % (qual.schemaConstruct, self.schemaConstruct)
                errs.append(SchemaError(msg=errMsg, sourceRef=qual.sourceRef))
        # Look for duplicate qualifiers
        qualTypesSeen = {}
        for qual in self.quals:
            qualType = qual.schemaConstruct
            if qualType not in qualTypesSeen:
                qualTypesSeen[qualType] = True
            else:
                errMsg = 'duplicate qualifier'
                errDetail = 'only one %s allowed on %s' % (qualType, self.schemaConstruct)
                errs.append(SchemaError(msg=errMsg, detail=errDetail, sourceRef=qual.sourceRef))

    def allChildNodes(self):
        for node in super(HasQualifiers, self).allChildNodes():
            yield node
        for node in self.quals:
            yield node

class HasDocumentation(object):
    '''Mixin for SchemaNodes that can have documentation'''
    
    def __init__(self, *args, **kwargs):
        super(HasDocumentation, self).__init__(*args, **kwargs)
        self.docs = None
        self.docsSourceRef = None

    def _summarizeDocs(self, maxLen=50):
        docsSum = self.docs
        docsSum = (docsSum[:maxLen] + '...') if len(docsSum) > maxLen else docsSum
        docsSum = docsSum.replace(u'\\', u'\\\\')
        docsSum = docsSum.replace(u'\n', u'\\n')
        docsSum = docsSum.replace(u'\r', u'\\r')
        docsSum = docsSum.replace(u'\t', u'\\t')
        return docsSum

# ----- SchemaNode Base Classes

class SchemaNode(object):
    '''Base class for all Weave Schema nodes'''
    
    def __init__(self, sourceRef=None):
        super(SchemaNode, self).__init__()
        self.sourceRef = sourceRef
        self.parent = None
        
    @property
    def schemaConstruct(self):
        '''Returns a descriptive string for the schema construct represented by this node'''
        return type(self)._schemaConstruct

    def allParentNodes(self):
        '''Iterate all parent nodes of this node in ascending order'''
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def allChildNodes(self):
        '''Iterate all immediate child nodes of this node'''
        return iter(())

    def allNodes(self, classinfo=object):
        '''Iterate for all nodes, including this node and all its descendants, if they are instances of classinfo'''
        if isinstance(self, classinfo):
            yield self
        for childNode in self.allChildNodes():
            if not hasattr(childNode, 'allNodes'):
                print('self is %s' % self)
                print('childNode is %s' % childNode)
            for node in childNode.allNodes(classinfo):
                if isinstance(node, classinfo):
                    yield node

    def containingNamespaceNode(self):
        '''Returns the immediately containing namespace node, or None
           if the this node is not within a namespace node.'''
        return next(filter(lambda e : isinstance(e, Namespace), self.allParentNodes()), None)

    def checkErrors(self, errs):
        '''Check the node for syntactical and structural errors and
           add exceptions describing any errors found to the given list'''
        pass

    def dump(self, level=0, prefix='', indent='  '):
        res = self._dump(level, indent)
        res[0] = prefix + res[0]
        return ('\n'+prefix).join(res)

    def _dump(self, level=0, indent='  '):
        res = [ '%s%s: %s' % (level*indent, type(self).__name__, self._displayName)]
        level += 1
        res.append('%spos: %s' % (level*indent, self.sourceRef.posStr()))
        if isinstance(self, HasDocumentation) and self.docs is not None:
            res.append('%sdocs: %s' % (level*indent, self._summarizeDocs()))
        if isinstance(self, HasQualifiers):
            res += self._dumpList(self.quals, name='quals', level=level, indent=indent)
        return res

    def _dumpList(self, lst, name, level=0, indent='  '):
        curIndent = level*indent
        if lst:
            res = [ '%s%s: (%d) [' % (curIndent, name, len(lst)) ]
            level += 1
            for x in lst:
                res += x._dump(level, indent)
            res.append('%s]' % (curIndent))
        else:
            res = [ '%s%s: -' % (curIndent, name) ]
        return res
    
    def _checkIsNotFieldGroup(self, node, errs):
        '''Confirm that node is not a FieldGroupType or reference to such'''
        if isinstance(node, ReferencedType):
            node = node.targetType
        if isinstance(node, FieldGroupType):
            errs.append(SchemaError(msg='FIELD GROUP type not allowed',
                                    detail='a FIELD GROUP type cannot appear within a %s' % self.schemaConstruct,
                                    sourceRef=self.sourceRef))

    def _checkUniqueNames(self, nodes, nodeDesc, errs):
        '''Confirm all nodes in the given list have distinct names'''
        nameSeen = {}
        for node in nodes:
            if node.name is not None:
                if not node.name in nameSeen:
                    nameSeen[node.name] = True
                else:
                    errs.append(SchemaError(msg='duplicate %s in %s: %s' % (nodeDesc, self.schemaConstruct, node.name),
                                            detail='%ss within a %s must have unique names' % (nodeDesc, self.schemaConstruct),
                                            sourceRef=node.nameSourceRef))

    @property
    def _displayName(self):
        return ''

class QualifierNode(SchemaNode):
    '''Base class for all SchemaNodes representing qualifiers'''
    pass
        
class TypeNode(SchemaNode):
    '''Base class for SchemaNodes representing types'''
    pass

class IntegerTypeNode(HasQualifiers, TypeNode):
    '''Base class for SchemaNotes that represent integer types'''

    def __init__(self, sourceRef=None):
        super(IntegerTypeNode, self).__init__(sourceRef)
        self.values = [] 

    def _dump(self, level=0, indent='  '):
        res = super(IntegerTypeNode, self)._dump(level, indent)
        if self.values:
            res += self._dumpList(self.values, 'values', level=level+1, indent=indent)
        return res

class SequencedTypeNode(HasQualifiers, TypeNode):
    '''Base class for SchemaNodes representing ARRAY or LIST types'''

    def __init__(self, sourceRef=None):
        super(SequencedTypeNode, self).__init__(sourceRef)
        self.elemType = None
        self.elemTypePattern = None

    def allChildNodes(self):
        for node in super(SequencedTypeNode, self).allChildNodes():
            yield node
        if self.elemType is not None:
            yield self.elemType
        elif self.elemTypePattern is not None:
            for patternElem in self.elemTypePattern:
                yield patternElem
            
    def checkErrors(self, errs):
        super(SequencedTypeNode, self).checkErrors(errs)
        # for uniform array/list...
        if self.elemType is not None:
            # Confirm element type is not FIELD GROUP or reference to such.
            self._checkIsNotFieldGroup(self.elemType, errs)
        # for pattern array/list...
        else:
            # Confirm element types are not FIELD GROUPs or references to such.
            for node in self.elemTypePattern:
                self._checkIsNotFieldGroup(node.type, errs)
            # Confirm all named items have distinct names.
            self._checkUniqueNames(self.elemTypePattern, 'item', errs)

    def _dump(self, level=0, indent='  '):
        res = super(SequencedTypeNode, self)._dump(level, indent)
        level += 1
        if self.elemType is not None:
            res.append('%selemType:' % (level*indent))
            res += self.elemType._dump(level+1, indent)
        elif self.elemTypePattern is not None:
            res += self._dumpList(self.elemTypePattern, 'elemTypePattern', level=level, indent=indent)
        return res

class StructuredTypeNode(HasQualifiers, TypeNode):
    '''Base class for SchemaNodes representing STRUCTURE or FIELD GROUP types'''

    def __init__(self, sourceRef=None):
        super(StructuredTypeNode, self).__init__(sourceRef)
        self.members = []

    def allChildNodes(self):
        for node in super(StructuredTypeNode, self).allChildNodes():
            yield node
        for node in self.members:
            yield node
            
    def allFields(self):
        for member in self.members:
            if isinstance(member, StructureIncludes):
                if isinstance(member.targetType, FieldGroupType):
                    for field in member.targetType.allFields():
                        yield field
            elif isinstance(member, StructureField):
                yield member
            
    def checkErrors(self, errs):
        super(StructuredTypeNode, self).checkErrors(errs)
        self._checkDuplicateIncludes(errs)
        self._checkDuplicateFieldNames(errs)

    def _dump(self, level=0, indent='  '):
        res = super(StructuredTypeNode, self)._dump(level, indent)
        level += 1
        res += self._dumpList(self.members, 'members', level=level, indent=indent)
        return res
    
    def _checkDuplicateIncludes(self, errs):
        '''Check for multiple includes statements that include the same FIELD GROUP'''
        includedFieldGroups = []
        for m in self.members:
            if isinstance(m, StructureIncludes):
                fg = m.targetType
                if not fg in includedFieldGroups:
                    includedFieldGroups.append(fg)
                else:
                    errs.append(SchemaError(msg='duplicate includes statement',
                                            detail='the includes statement references a FIELD GROUP that has already been included',
                                            sourceRef=m.sourceRef))
        
    def _checkDuplicateFieldNames(self, errs):
        '''Confirm all fields have distinct names, including fields incorporated
           via "includes" statements.'''
        fieldsSeen = {}
        for (field, fieldIncludeStmt) in self._allFieldsWithIncludeStatement():
            if not field.name in fieldsSeen:
                fieldsSeen[field.name] = field
            elif field.parent == self or field.parent != fieldsSeen[field.name].parent:
                if fieldIncludeStmt == None:
                    sourceRef = field.nameSourceRef
                else:
                    sourceRef = fieldIncludeStmt.sourceRef
                errs.append(SchemaError(msg='duplicate field in %s: %s' % (self.schemaConstruct, field.name),
                                          detail='fields within a %s type must have unique names' % self.schemaConstruct,
                                          sourceRef=sourceRef))
        
    def _allFieldsWithIncludeStatement(self):
        for m in self.members:
            if isinstance(m, StructureIncludes):
                if isinstance(m.targetType, FieldGroupType):
                    for field in m.targetType.allFields():
                        yield (field, m)
            elif isinstance(m, StructureField):
                yield (m, None)

# ----- General SchemaNodes

class SchemaFile(SchemaNode):
    '''Represents a file or other textual source of Weave Schema'''

    _schemaConstruct = 'schema file'
    
    def __init__(self, fileName, schemaText):
        super(SchemaFile, self).__init__()
        self.fileName = fileName
        self.schemaText = schemaText
        self.statements = None
        
    def allChildNodes(self):
        for node in super(SchemaFile, self).allChildNodes():
            yield node
        for node in self.statements:
            yield node

    def _dump(self, level=0, indent='  '):
        res = super(SchemaFile, self)._dump(level, indent)
        res += self._dumpList(self.statements, name='statements', level=level+1, indent=indent)
        return res

    @property
    def _displayName(self):
        return self.fileName

# ----- Qualifier SchemaNodes

class Extensible(QualifierNode):
    '''Represents an extensible qualifier'''
    _schemaConstruct = 'extensible qualifier'

class Optional(QualifierNode):
    '''Represents an optional qualifier'''
    _schemaConstruct = 'optional qualifier'

class Private(QualifierNode):
    '''Represents a private qualifier'''
    _schemaConstruct = 'private qualifier'

class Invariant(QualifierNode):
    '''Represents an invariant qualifier'''
    _schemaConstruct = 'invariant qualifier'

class Nullable(QualifierNode):
    '''Represents a nullable qualifier'''
    _schemaConstruct = 'nullable qualifier'

class TagOrder(QualifierNode):
    '''Represents a tag-order qualifier'''
    _schemaConstruct = 'tag-order qualifier'

class SchemaOrder(QualifierNode):
    '''Represents a schema-order qualifier'''
    _schemaConstruct = 'schema-order qualifier'

class AnyOrder(QualifierNode):
    '''Represents an any-order qualifier'''
    _schemaConstruct = 'any-order qualifier'

class Range(QualifierNode):
    '''Represents a range qualifier'''

    _schemaConstruct = 'range qualifier'

    def __init__(self, sourceRef=None, lowerBound=None, upperBound=None, width=None):
        super(Range, self).__init__(sourceRef)
        self.lowerBound = lowerBound
        self.upperBound = upperBound
        self.width = width
        
    def checkErrors(self, errs):
        super(Range, self).checkErrors(errs)
        # Check that upperBound >= lowerBound 
        if self.width is None:
            if self.lowerBound is not None and self.upperBound is not None:
                if self.upperBound < self.lowerBound:
                    errs.append(SchemaError(msg='upper bound of range qualifier must be >= lower bound',
                                            sourceRef=self.sourceRef))
        # Check range constraints based on parent type...
        if isinstance(self.parent, FloatType):
            # Verify only 32/64bit widths on FLOAT type
            if self.width is not None and self.width < 32:
                errs.append(SchemaError(msg='only 32bit and 64bit range qualifiers allowed on FLOAT type',
                                        sourceRef=self.sourceRef))
        elif isinstance(self.parent, IntegerTypeNode):
            # Verify only integer bounds on INTEGER types
            if isinstance(self.lowerBound, Decimal) or isinstance(self.upperBound, Decimal):  
                errMsg = 'bounds values for range qualifier on %s must be integers' % self.parent.schemaConstruct
                errs.append(SchemaError(msg=errMsg,
                                        sourceRef=self.sourceRef))

    @property
    def _displayName(self):
        if self.width is not None:
            return 'width %d' % (self.width)
        else:
            return '%s to %s' % (str(self.lowerBound), str(self.upperBound))

class Length(QualifierNode):
    '''Represents a length qualifier'''

    _schemaConstruct = 'length qualifier'

    def __init__(self, sourceRef=None, lowerBound=None, upperBound=None):
        super(Length, self).__init__(sourceRef)
        self.lowerBound = lowerBound
        self.upperBound = upperBound

    def checkErrors(self, errs):
        super(Length, self).checkErrors(errs)
        # Check that lowerBound and upperBound >= 0 
        if self.lowerBound < 0 or (self.upperBound is not None and self.upperBound < 0):
            errs.append(SchemaError(msg='bounds of length qualifier must be >= 0',
                                    sourceRef=self.sourceRef))
        # Check that upperBound >= lowerBound 
        if self.upperBound is not None and self.upperBound < self.lowerBound:
            errs.append(SchemaError(msg='upper bound of length qualifier must be >= lower bound',
                                    sourceRef=self.sourceRef))

    @property
    def _displayName(self):
        return '%s to %s' % (str(self.lowerBound), str(self.upperBound))

class Tag(QualifierNode):
    '''Represents a tag qualifier'''

    _schemaConstruct = 'tag qualifier'
    
    def __init__(self, sourceRef=None, tagNum=None, profile=None):
        super(Tag, self).__init__(sourceRef)
        self.tagNum = tagNum
        self.profile = profile
        
    @property
    def isAnonTag(self):
        return self.tagNum is None and self.profile is None

    @property
    def _displayName(self):
        if self.isAnonTag:
            return 'anon'
        elif self.profile is not None:
            return '%s:%s' % (self.profile, self.tagNum)
        else:
            return '%s' % (self.tagNum)

class Id(QualifierNode):
    '''Represents an id qualifier'''

    _schemaConstruct = 'id qualifier'
    
    def __init__(self, sourceRef=None, idNum=None, vendor=None):
        super(Id, self).__init__(sourceRef)
        self.idNum = idNum
        self.vendor = vendor

    @property
    def _displayName(self):
        if self.vendor is not None:
            return '%s:%s' % (self.vendor, self.idNum)
        else:
            return '%s' % (self.idNum)

# ----- Definition SchemaNodes

class Namespace(HasScopedName, HasDocumentation, SchemaNode):
    '''Represents a namespace definition'''

    _schemaConstruct = 'namespace definition'

    def __init__(self, sourceRef=None):
        super(Namespace, self).__init__(sourceRef)
        self.statements = None
    
    def allChildNodes(self):
        for node in super(Namespace, self).allChildNodes():
            yield node
        for node in self.statements:
            yield node

    def _dump(self, level=0, indent='  '):
        res = super(Namespace, self)._dump(level, indent)
        res += self._dumpList(self.statements, name='statements', level=level+1, indent=indent)
        return res

class Vendor(HasName, HasQualifiers, HasDocumentation, SchemaNode):
    '''Represents a VENDOR definition'''

    _schemaConstruct = 'VENDOR definition'
    _allowedQualifiers = (Id)

    def checkErrors(self, errs):
        super(Vendor, self).checkErrors(errs)
        # Confirm that VENDOR is not within a namespace or PROFILE
        if self.containingNamespaceNode() is not None:
            errs.append(SchemaError(msg='VENDOR definition not at global scope',
                                      detail='VENDOR definitions may not appear within a namespace or PROFILE definition',
                                      sourceRef=self.sourceRef))
        # Confirm that id qualifier is present
        idQual = self.getQualifier(Id)
        if idQual is None:
            errs.append(SchemaError(msg='id qualifier missing on VENDOR definition',
                                    sourceRef=self.sourceRef))
        else:
            # Confirm that the given id value is correctly structured and in range.
            if idQual.vendor is not None or idQual.idNum < 0 or idQual.idNum > 65535:
                errs.append(SchemaError(msg='invalid id value for VENDOR definition',
                                        detail='id value for VENDOR must be a single integer in the range 0-65535',
                                        sourceRef=idQual.sourceRef))

class Profile(HasQualifiers, Namespace):
    '''Represents a PROFILE definition'''

    _schemaConstruct = 'PROFILE definition'
    _allowedQualifiers = (Id)

    def __init__(self, sourceRef=None):
        super(Profile, self).__init__(sourceRef)

    def checkErrors(self, errs):
        super(Profile, self).checkErrors(errs)
        # Disallow nesting of PROFILES
        parentProfile = next(filter(lambda e:isinstance(e, Profile), self.allParentNodes()), None)
        if parentProfile is not None:
            errs.append(SchemaError(msg='nested PROFILE definition',
                                    detail='PROFILE definitions may not appear within other PROFILE definitions',
                                    sourceRef=self.sourceRef))
        # Confirm that id qualifier is present
        idQual = self.getQualifier(Id)
        if idQual is None:
            errs.append(SchemaError(msg='id qualifier missing on PROFILE definition',
                                    sourceRef=self.sourceRef))
        else:
            # Confirm that the given id value is correctly structured and in range.
            if idQual.vendor is None:
                if idQual.idNum < 0 or idQual.idNum > 0xFFFFFFFF:
                    errs.append(SchemaError(msg='invalid profile id for PROFILE definition',
                                            detail='profile ids must be in the range 0-0xFFFFFFFF',
                                            sourceRef=idQual.sourceRef))
            else:
                if isinstance(idQual.vendor, int) and (idQual.vendor < 0 or idQual.vendor > 65535):
                    errs.append(SchemaError(msg='invalid vendor id for PROFILE definition',
                                            detail='vendor id must be in the range 0-65535',
                                            sourceRef=idQual.sourceRef))
                if idQual.idNum < 0 or idQual.idNum > 65535:
                    errs.append(SchemaError(msg='invalid profile number for PROFILE definition',
                                            detail='profile numbers must be in the range 0-65535',
                                            sourceRef=idQual.sourceRef))

class Message(HasScopedName, HasQualifiers, HasDocumentation, SchemaNode):
    '''Represents a MESSAGE definition'''

    _schemaConstruct = 'MESSAGE definition'
    _allowedQualifiers = (Id)

    def __init__(self, sourceRef=None):
        super(Message, self).__init__(sourceRef)
        self.payload = None
        self.emptyPayload = False

    def allChildNodes(self):
        for node in super(Message, self).allChildNodes():
            yield node
        if self.payload is not None:
            yield self.payload

    def checkErrors(self, errs):
        super(Message, self).checkErrors(errs)
        # Confirm that MESSAGE is directly within a PROFILE definition
        if not isinstance(self.parent, Profile):
            errs.append(SchemaError(msg='MESSAGE definition not witin PROFILE definition',
                                      detail='MESSAGE definitions must appear directly within a PROFILE definition',
                                      sourceRef=self.sourceRef))
        # Confirm that id qualifier is present
        idQual = self.getQualifier(Id)
        if idQual is None:
            errs.append(SchemaError(msg='id qualifier missing on MESSAGE definition',
                                    sourceRef=self.sourceRef))
        else:
            # Confirm that the given id value is correctly structured and in range.
            if idQual.vendor is not None or idQual.idNum < 0 or idQual.idNum > 255:
                errs.append(SchemaError(msg='invalid id value for MESSAGE definition',
                                        detail='id value for MESSAGE must be a single integer in the range 0-255',
                                        sourceRef=idQual.sourceRef))

    def _dump(self, level=0, indent='  '):
        res = super(Message, self)._dump(level, indent)
        level += 1
        if self.payload:
            res.append('%spayload:' % (level*indent))
            res += self.payload._dump(level+1, indent)
        elif self.emptyPayload:
            res.append('%spayload: empty' % (level*indent))
        else:
            res.append('%spayload: not defined' % (level*indent))
        return res

class StatusCode(HasScopedName, HasQualifiers, HasDocumentation, SchemaNode):
    '''Represents a STATUS CODE definition'''
    
    _schemaConstruct = 'STATUS CODE definition'
    _allowedQualifiers = (Id)

    def checkErrors(self, errs):
        super(StatusCode, self).checkErrors(errs)
        # Confirm that STATUS CODE is directly within a PROFILE definition
        if not isinstance(self.parent, Profile):
            errs.append(SchemaError(msg='STATUS CODE definition not witin PROFILE definition',
                                      detail='STATUS CODE definitions must appear directly within a PROFILE definition',
                                      sourceRef=self.sourceRef))
        # Confirm that id qualifier is present
        idQual = self.getQualifier(Id)
        if idQual is None:
            errs.append(SchemaError(msg='id qualifier missing on STATUS CODE definition',
                                    sourceRef=self.sourceRef))
        else:
            # Confirm that the given id value is correctly structured and in range.
            if idQual.vendor is not None or idQual.idNum < 0 or idQual.idNum > 65535:
                errs.append(SchemaError(msg='invalid id value for STATUS CODE definition',
                                        detail='id value for STATUS CODE must be a single integer in the range 0-65535',
                                        sourceRef=idQual.sourceRef))


class TypeDef(HasScopedName, HasQualifiers, HasDocumentation, SchemaNode):
    '''Represents a type definition'''

    _schemaConstruct = 'type definition'
    _allowedQualifiers = (Tag)

    def __init__(self, sourceRef=None):
        super(TypeDef, self).__init__(sourceRef)
        self.type = None

    def allChildNodes(self):
        for node in super(TypeDef, self).allChildNodes():
            yield node
        if self.type is not None:
            yield self.type

    def _dump(self, level=0, indent='  '):
        res = super(TypeDef, self)._dump(level, indent)
        level += 1
        res.append('%stype:' % (level*indent))
        res += self.type._dump(level+1, indent)
        return res

# ----- Statement SchemaNodes

class Using(SchemaNode):
    '''Represents a using statement'''

    _schemaConstruct = 'using statement'

    def __init__(self, sourceRef=None):
        super(Using, self).__init__(sourceRef)
        self.targetName = None
        self.targetNameSourceRef = None
        self.fullyQualifiedTargetName = None

    @property
    def _displayName(self):
        return self.targetName

# ----- Type SchemaNodes

class FloatType(HasQualifiers, TypeNode):
    '''Represents a FLOAT type'''
    _schemaConstruct = 'FLOAT type'
    _allowedQualifiers = (Range, Nullable)
    
class BooleanType(HasQualifiers, TypeNode):
    '''Represents a BOOLEAN type'''
    _schemaConstruct = 'BOOLEAN type'
    _allowedQualifiers = (Nullable)

class StringType(HasQualifiers, TypeNode):
    '''Represents a STRING type'''
    _schemaConstruct = 'STRING type'
    _allowedQualifiers = (Length, Nullable)

class ByteStringType(HasQualifiers, TypeNode):
    '''Represents a BYTE STRING type'''
    _schemaConstruct = 'BYTE STRING type'
    _allowedQualifiers = (Length, Nullable)

class NullType(HasQualifiers, TypeNode):
    '''Represents a NULL type'''
    _schemaConstruct = 'NULL type'
    _allowedQualifiers = ()

class AnyType(HasQualifiers, TypeNode):
    '''Represents an ANY pseudo-type'''
    _schemaConstruct = 'ANY type'
    _allowedQualifiers = ()

class SignedIntegerType(IntegerTypeNode):
    '''Represents a SIGNED INTEGER type'''
    _schemaConstruct = 'SIGNED INTEGER type'
    _allowedQualifiers = (Range, Nullable)

class UnsignedIntegerType(IntegerTypeNode):
    '''Represents a UNSIGNED INTEGER type'''
    _schemaConstruct = 'UNSIGNED INTEGER type'
    _allowedQualifiers = (Range, Nullable)

class StructureType(StructuredTypeNode):
    '''Represents a STRUCTURE type'''

    _schemaConstruct = 'STRUCTURE type'
    _allowedQualifiers = (Extensible, TagOrder, SchemaOrder, AnyOrder, Private, Invariant, Nullable)
    
    def checkErrors(self, errs):
        super(StructureType, self).checkErrors(errs)
        self._checkOneOrderQual(errs)

    def _checkOneOrderQual(self, errs):
        '''Confirm only one of schema-order, tag-order, any-order applied to STRUCTURE'''
        orderQualSeen = False
        for qual in self.quals:
            if isinstance(qual, (SchemaOrder, TagOrder, AnyOrder)):
                if not orderQualSeen:
                    orderQualSeen = True
                else:
                    errs.append(SchemaError(msg='multiple order qualifiers',
                                            detail='only one order qualifier allowed on a STRUCTURE type',
                                            sourceRef=qual.sourceRef))

class FieldGroupType(StructuredTypeNode):
    '''Represents a FIELD GROUP pseudo-type'''
    _schemaConstruct = 'FIELD GROUP type'
    _allowedQualifiers = ()

class ChoiceType(HasQualifiers, TypeNode):
    '''Represents a CHOICE OF pseudo-type'''

    _schemaConstruct = 'CHOICE OF type'
    _allowedQualifiers = (Nullable)

    def __init__(self, sourceRef=None):
        super(ChoiceType, self).__init__(sourceRef)
        self.alternates = []

    def allChildNodes(self):
        for node in super(ChoiceType, self).allChildNodes():
            yield node
        for node in self.alternates:
            yield node
            
    def checkErrors(self, errs):
        super(ChoiceType, self).checkErrors(errs)
        # Confirm all named alternates have distinct names
        # TODO: this can only be done *after* normalization
        nameSeen = {}
        for node in self.alternates:
            if node.name is not None:
                if not node.name in nameSeen:
                    nameSeen[node.name] = True
                else:
                    errs.append(SchemaError(msg='duplicate CHOICE OF alternate',
                                            detail='alternates within a CHOICE OF type must have unique names',
                                            sourceRef=node.nameSourceRef))

    def _dump(self, level=0, indent='  '):
        res = super(ChoiceType, self)._dump(level, indent)
        level += 1
        res += self._dumpList(self.alternates, 'alternates', level=level, indent=indent)
        return res

class ArrayType(SequencedTypeNode):
    '''Represents an ARRAY / ARRAY OF type'''
    _schemaConstruct = 'ARRAY type'
    _allowedQualifiers = (Length, Nullable)

class ListType(SequencedTypeNode):
    '''Represents a LIST / LIST OF type'''
    _schemaConstruct = 'LIST type'
    _allowedQualifiers = (Length, Nullable)

class ReferencedType(TypeNode):
    '''Represents a type that is a reference to another type'''

    _schemaConstruct = 'type reference'

    def __init__(self, sourceRef=None):
        super(ReferencedType, self).__init__(sourceRef)
        self.targetName = None
        self.targetType = None

    def _dump(self, level=0, indent='  '):
        res = super(ReferencedType, self)._dump(level, indent)
        level += 1
        res.append('%sreferencedName: %s' % (level*indent, self.targetName))
        return res

# ----- SchemaNodes Representing Components of Types

class IntegerEnumValue(HasName, HasDocumentation, SchemaNode):
    '''Represents an individual enumerated value associated with an INTEGER type.'''

    _schemaConstruct = 'enumerated value'
    
    def __init__(self, sourceRef=None):
        super(IntegerEnumValue, self).__init__(sourceRef)
        self.value = None
        self.valueSourceRef = None

    def checkErrors(self, errs):
        super(IntegerEnumValue, self).checkErrors(errs)
        # TODO: Check value is in range for integer type

    @property
    def _displayName(self):
        return '%s = %d' % (self.name, self.value)

class StructureField(HasName, HasQualifiers, HasDocumentation, SchemaNode):
    '''Represents an individual field within a STRUCTURE or FIELD GROUP type.'''

    _schemaConstruct = 'STRUCTURE or FIELD GROUP field'
    _allowedQualifiers = (Tag, Optional)

    def __init__(self, sourceRef=None):
        super(StructureField, self).__init__(sourceRef)
        self.type = None

    def allChildNodes(self):
        for node in super(StructureField, self).allChildNodes():
            yield node
        if self.type is not None:
            yield self.type

    def checkErrors(self, errs):
        super(StructureField, self).checkErrors(errs)
        self._checkIsNotFieldGroup(self.type, errs)

    def _dump(self, level=0, indent='  '):
        res = super(StructureField, self)._dump(level, indent)
        level += 1
        res.append('%stype:' % (level*indent))
        res += self.type._dump(level+1, indent)
        return res

class StructureIncludes(SchemaNode):
    '''Represents an includes statement within a STRUCTURE or FIELD GROUP type.'''

    _schemaConstruct = 'STRUCTURE includes statement'

    def __init__(self, sourceRef=None):
        super(StructureIncludes, self).__init__(sourceRef)
        self.targetName = None
        self.targetType = None

    def checkErrors(self, errs):
        super(StructureIncludes, self).checkErrors(errs)
        # Check that target names a FIELD GROUP
        if self.targetType is not None and not isinstance(self.targetType, FieldGroupType):
            errs.append(SchemaError(msg='Invalid target for includes statement',
                                    detail='An includes statement within a STRUCTURE or FIELD GROUP must refer to a FIELD GROUP type',
                                    sourceRef=self.sourceRef))

    @property
    def _displayName(self):
        return self.targetName
    
class ChoiceAlternate(HasName, HasQualifiers, HasDocumentation, SchemaNode):
    '''Represents a type alternate within a CHOICE type.'''

    _schemaConstruct = 'CHOICE alternate'
    _allowedQualifiers = (Tag)

    def __init__(self, sourceRef=None):
        super(ChoiceAlternate, self).__init__(sourceRef)
        self.type = None

    def allChildNodes(self):
        for node in super(ChoiceAlternate, self).allChildNodes():
            yield node
        if self.type is not None:
            yield self.type

    def checkErrors(self, errs):
        super(ChoiceAlternate, self).checkErrors(errs)
        # TODO: Check that type is not FIELD GROUP

    def _dump(self, level=0, indent='  '):
        res = super(ChoiceAlternate, self)._dump(level, indent)
        level += 1
        res.append('%stype:' % (level*indent))
        res += self.type._dump(level+1, indent)
        return res

    @property
    def _displayName(self):
        return self.name if self.name is not None else '(unnamed)'

class LinearTypePatternElement(HasName, HasQualifiers, HasDocumentation, SchemaNode):
    '''Represents a single type element within a linear type pattern.'''

    _schemaConstruct = 'linear type pattern element'
    _allowedQualifiers = (Tag)

    def __init__(self, sourceRef=None):
        super(LinearTypePatternElement, self).__init__(sourceRef)
        self.type = None
        self.lowerBound = None
        self.upperBound = None

    def allChildNodes(self):
        for node in super(LinearTypePatternElement, self).allChildNodes():
            yield node
        if self.type is not None:
            yield self.type

    def _dump(self, level=0, indent='  '):
        res = super(LinearTypePatternElement, self)._dump(level, indent)
        level += 1
        res.append('%slowerBound: %s' % (level*indent, self.lowerBound))
        res.append('%supperBound: %s' % (level*indent, self.upperBound))
        res.append('%stype:' % (level*indent))
        res += self.type._dump(level+1, indent)
        return res

    @property
    def _displayName(self):
        return self.name if self.name is not None else '(unnamed)'

# ----- Supporting Classes / Functions

class SourceRef(object):
    '''Identifies a source of schema (e.g. a file), and start / end text positions within that source.'''

    def __init__(self, source, startLine, startCol, startPos, endLine, endCol, endPos):
        self.source = source
        self.startLine = startLine
        self.startCol = startCol
        self.startPos = startPos
        self.endLine = endLine
        self.endCol = endCol
        self.endPos = endPos

    def setstart(self, otherSourceRef):
        self.startLine = otherSourceRef.startLine
        self.startCol = otherSourceRef.startCol
        self.startPos = otherSourceRef.startPos

    def setEnd(self, otherSourceRef):
        self.endLine = otherSourceRef.endLine
        self.endCol = otherSourceRef.endCol
        self.endPos = otherSourceRef.endPos
        
    def posStr(self):
        return '%d:%d-%d:%d %d-%d' % (self.startLine, self.startCol, self.endLine, self.endCol,
                                      self.startPos, self.endPos)

    @staticmethod
    def fromMeta(source, meta):
        if meta is None:
            return None
        return SourceRef(source, 
                         startLine=meta.line, startCol=meta.column, startPos=meta.start_pos,
                         endLine=meta.end_line, endCol=meta.end_column, endPos=meta.end_pos)

    @staticmethod
    def fromToken(source, token):
        if token is None:
            return None
        endPos = token.pos_in_stream + len(token.value)
        return SourceRef(source, 
                         startLine=token.line, startCol=token.column, startPos=token.pos_in_stream,
                         endLine=token.end_line, endCol=token.end_column, endPos=endPos)

        
