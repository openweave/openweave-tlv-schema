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

from decimal import Decimal
import io
import itertools
import os
import re

from .error import WeaveTLVSchemaError, AmbiguousTagError


# ----- Utility functions

def _addSchemaError(errs, msg, detail=None, sourceRef=None):
    errs.append(WeaveTLVSchemaError(msg=msg, detail=detail, sourceRef=sourceRef))

# ----- Mixin Classes for SchemaNodes

class HasName(object):
    '''Mixin for SchemaNodes that have human-readable text names'''

    def __init__(self, *args, **kwargs):
        super(HasName, self).__init__(*args, **kwargs)
        self.name = None
        self.nameSourceRef = None

    @property
    def effectiveName(self):
        '''The effective name of the schema node.
           If the node was assigned a name in the schema, this is the assigned name
           (the same value as self.name).
           If the node wasn't assigned a name, by default a None is returned.  However,
           in some cases the node type may override this and return an automatically
           generated name instead.'''
        if self.name is not None:
            return self.name
        else:
            return 'element-%d' % (self.parent.elemTypePattern.index(self) + 1)

    @property
    def _summaryTitle(self):
        name = self.name if self.name is not None else '(unnamed)'
        return '%s: %s' % (type(self).__name__, name)
    
class HasScopedName(HasName):
    '''Mixin for named SchemaNodes whose names are scoped by namespaces'''
    
    def __init__(self, *args, **kwargs):
        super(HasScopedName, self).__init__(*args, **kwargs)
        self._namespaceName = None
    
    @property
    def namespaceName(self):
        if self._namespaceName is None:
            containingNSNode = self.nextParentNode(Namespace)
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

    def isInNamespace(self, nsName):
        nodeNsName = self.namespaceName
        return (nsName == '' or 
                nodeNsName == nsName or 
                (nodeNsName.startswith(nsName) and nodeNsName[len(nsName)] == '.'))

    @property
    def _summaryTitle(self):
        return '%s: %s' % (type(self).__name__, self.fullyQualifiedName)

class HasType(object):
    '''Mixin for SchemaNodes that have an underlying type'''
    
    def __init__(self, *args, **kwargs):
        super(HasType, self).__init__(*args, **kwargs)
        self.type = None
    
    @property
    def targetType(self):
        '''The type node to which the underlying type ultimately refers.
           If the underlying type is a ReferencedType, the returned node is the ultimate
           target type of the referenced type.
           Otherwise, the returned node is the underlying type node itself.'''
        if isinstance(self.type, ReferencedType):
            return self.type.targetType
        else:
            return self.type

    def allChildNodes(self):
        for node in super(HasType, self).allChildNodes():
            yield node
        if self.type is not None:
            yield self.type

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
    
    def validate(self, errs):
        super(HasQualifiers, self).validate(errs)
        # Check that all qualifiers are allowed
        allowedQuals = self._allowedQualifiers
        for qual in self.quals:
            if not isinstance(qual, allowedQuals):
                errMsg = '%s not allowed on %s' % (qual.schemaConstruct, self.schemaConstruct)
                _addSchemaError(errs, msg=errMsg, sourceRef=qual.sourceRef)
        # Look for duplicate qualifiers
        qualTypesSeen = {}
        for qual in self.quals:
            qualType = qual.schemaConstruct
            if qualType not in qualTypesSeen:
                qualTypesSeen[qualType] = True
            else:
                errMsg = 'duplicate qualifier'
                errDetail = 'only one %s allowed on %s' % (qualType, self.schemaConstruct)
                _addSchemaError(errs, msg=errMsg, detail=errDetail, sourceRef=qual.sourceRef)

    def allChildNodes(self):
        for node in super(HasQualifiers, self).allChildNodes():
            yield node
        for node in self.quals:
            yield node

class HasTag(object):
    '''Mixin for SchemaNodes that can have an assigned tag'''
    
    def __init__(self, *args, **kwargs):
        super(HasTag, self).__init__(*args, **kwargs)
        self._possibleTags = None

    @property
    def tag(self):
        '''The tag qualifier assigned to the node in its schema definition.
           If no tag was assigned, a None is returned.'''
        return self.getQualifier(Tag)
    
    @property
    def effectiveTag(self):
        '''The effective tag qualifier for the schema node.
           If a tag qualifier is attached directly to the schema node, that tag is returned.
           If the node has an underlying type which is a reference to a type definition
           that has an associated default tag, the default tag is returned.
           If the underlying type is a CHOICE OF with only a single possible tag, that
           tag is returned.
           If the underlying type is a CHOICE OF with multiple possible tags, an
           AmbiguousTagError is raised.
           If no tag has been specified, either directly or indirectly, a None is
           returned.'''
        possibleTags = self.possibleTags
        if len(possibleTags) == 0:
            return None
        elif len(possibleTags) == 1:
            return possibleTags[0]
        else:
            raise AmbiguousTagError()
    
    @property
    def possibleTags(self):
        '''A list of all possible tag qualifiers for the schema node.
           If a tag qualifier is attached directly to the node, the list will consist
           of that tag alone.
           If the schema node has an underlying type which is a reference to a type
           definition with an associated default tag, the list will consist of the default
           tag.
           If the underlying type is a CHOICE OF, the list will contain the default tags
           associated with each of the possible choice alternates. In this case, the list
           will additionally include a None element if one or more of the alternates does
           not have a default tag.
           If no tag has been specified, either directly or indirectly, an empty list is
           returned.'''
        if self._possibleTags is None:
            tag = self.tag
            underlyingType = None
            if tag is None and isinstance(self, HasType):
                underlyingType = self.type
                if isinstance(underlyingType, ReferencedType):
                    tag = self.type.effectiveTag
                    underlyingType = self.type.targetType
            if tag is not None:
                self._possibleTags = [ tag ]
            elif isinstance(underlyingType, ChoiceType):
                self._possibleTags = underlyingType.possibleTags
            else:
                self._possibleTags = []
        return self._possibleTags

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

    def allParentNodes(self, classinfo=object):
        '''Iterate all parent nodes of this node, in ascending order, if they are instances of classinfo'''
        node = self.parent
        while node is not None:
            if isinstance(node, classinfo):
                yield node
            node = node.parent
            
    def nextParentNode(self, classinfo=object):
        '''Return the most immediate parent of this node that is an instance of classinfo, or None
           if no such parent exists.'''
        return next(self.allParentNodes(classinfo), None)

    def allChildNodes(self):
        '''Iterate all immediate child nodes of this node'''
        return iter(())

    def allNodes(self, classinfo=object):
        '''Iterate for all nodes, including this node and all its descendants, if they are instances of classinfo'''
        if isinstance(self, classinfo):
            yield self
        for childNode in self.allChildNodes():
            for node in childNode.allNodes(classinfo):
                if isinstance(node, classinfo):
                    yield node

    def validate(self, errs):
        '''Check the node for syntactical and structural errors and
           add exceptions describing any errors found to the given list'''
        pass

    def summarize(self, output=None, level=0, indent='  '):
        genString = (output is None)
        if genString:
            output = io.StringIO()
        self._summarize(output, level, indent)
        return output.getvalue() if genString else output
        
    def _summarize(self, output, level, indent):
        curIndent = indent*level
        output.write('%s%s\n' % (curIndent, self._summaryTitle))
        output.write('%s%spos: %s\n' % (curIndent, indent, self.sourceRef.posStr()))
        if isinstance(self, HasDocumentation) and self.docs is not None:
            output.write('%s%sdocs: %s\n' % (curIndent, indent, self._summarizeDocs()))
        if isinstance(self, HasQualifiers):
            self._summarizeList(output, self.quals, name='quals', level=level+1, indent=indent)
        
    @property
    def _summaryTitle(self):
        return '%s:' % (type(self).__name__) 

    @staticmethod
    def _summarizeList(output, lst, name, level=0, indent='  '):
        curIndent = level*indent
        if lst:
            output.write('%s%s: (%d) [\n' % (curIndent, name, len(lst)))
            for x in lst:
                x._summarize(output, level+1, indent)
            output.write('%s]\n' % (curIndent))
        else:
            output.write('%s%s: -\n' % (curIndent, name))

    def _checkIsNotFieldGroup(self, node, errs):
        '''Confirm that node is not a FieldGroupType or reference to such'''
        if isinstance(node, ReferencedType):
            node = node.targetType
        if isinstance(node, FieldGroupType):
            _addSchemaError(errs, msg='FIELD GROUP type not allowed',
                            detail='a FIELD GROUP type cannot appear within a %s' % self.schemaConstruct,
                            sourceRef=self.sourceRef)

    def _checkUniqueNames(self, nodes, nodeDesc, errs):
        '''Confirm all nodes in the given list have distinct names'''
        nameSeen = {}
        for node in nodes:
            if node.name is not None:
                if not node.name in nameSeen:
                    nameSeen[node.name] = True
                else:
                    _addSchemaError(errs, msg='duplicate %s in %s: %s' % (nodeDesc, self.schemaConstruct, node.name),
                                    detail='%ss within a %s must have unique names' % (nodeDesc, self.schemaConstruct),
                                    sourceRef=node.nameSourceRef)

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
        self._upperBound = None
        self._lowerBound = None

    def allChildNodes(self):
        for node in super(IntegerTypeNode, self).allChildNodes():
            yield node
        for node in self.values:
            yield node

    def isInRange(self, val):
        if self._upperBound is None:
            range = self.getQualifier(Range)
            width = range.width if range is not None else 64
            if width is not None:
                width = range.width if range is not None else 64
                if isinstance(self, SignedIntegerType):
                    self._lowerBound = (2 ** (width - 1)) * -1
                    self._upperBound = (2 ** (width - 1)) - 1
                else:
                    assert isinstance(self, UnsignedIntegerType)
                    self._lowerBound = 0
                    self._upperBound = (2 ** width) - 1
            else:
                self._lowerBound = range.lowerBound
                self._upperBound = range.upperBound
        return (val >= self._lowerBound) and (val <= self._upperBound)

    def _summarize(self, output, level, indent):
        super(IntegerTypeNode, self)._summarize(output, level, indent)
        if self.values:
            self._summarizeList(output, self.values, 'values', level=level+1, indent=indent)

class SequencedTypeNode(HasQualifiers, TypeNode):
    '''Base class for SchemaNodes representing ARRAY or LIST types'''

    def __init__(self, sourceRef=None):
        super(SequencedTypeNode, self).__init__(sourceRef)
        self.elemType = None
        self.elemTypePattern = None

    @property
    def isUniform(self):
        '''True if the node represents a uniform ARRAY or LIST.'''
        return self.elemType is not None

    @property
    def targetElemType(self):
        '''For a uniform ARRAY or LIST, the type node to which the underlying element type
           ultimately refers.  If the element type is a ReferencedType, the returned node
           is the ultimate target type of the referenced type.  If it is some other type,
           the element type node itself is returned.  If the node is a pattern ARRAY or
           LIST a None is returned.'''
        if self.isUniform:
            if isinstance(self.elemType, ReferencedType):
                return self.elemType.targetType
            else:
                return self.elemType

    def allChildNodes(self):
        for node in super(SequencedTypeNode, self).allChildNodes():
            yield node
        if self.elemType is not None:
            yield self.elemType
        elif self.elemTypePattern is not None:
            for patternElem in self.elemTypePattern:
                yield patternElem
            
    def allTypePatternElements(self):
        if self.elemTypePattern is not None:
            for elem in self.elemTypePattern:
                yield elem
    
    def getElement(self, elemName):
        return next((e for e in self.allTypePatternElements() if e.name == elemName), None)
        
    def validate(self, errs):
        super(SequencedTypeNode, self).validate(errs)
        # for uniform array/list...
        if self.isUniform:
            # Confirm element type is not FIELD GROUP or reference to such.
            self._checkIsNotFieldGroup(self.elemType, errs)
        # for pattern array/list...
        else:
            # Confirm element types are not FIELD GROUPs or references to such.
            for node in self.elemTypePattern:
                self._checkIsNotFieldGroup(node.type, errs)
            # Confirm all named items have distinct names.
            self._checkUniqueNames(self.elemTypePattern, 'item', errs)

    def _summarize(self, output, level, indent):
        super(SequencedTypeNode, self)._summarize(output, level, indent)
        level += 1
        if self.isUniform:
            output.write('%selemType:\n' % (level*indent))
            self.elemType._summarize(output, level+1, indent)
        elif self.elemTypePattern is not None:
            self._summarizeList(output, self.elemTypePattern, 'elemTypePattern', level=level, indent=indent)

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
        '''Enumerates all StructureField nodes associated with the current node,
           either directly or via an includes statement.'''
        for member in self.members:
            if isinstance(member, StructureIncludes):
                if isinstance(member.targetType, FieldGroupType):
                    for field in member.targetType.allFields():
                        yield field
            elif isinstance(member, StructureField):
                yield member
    
    def allMembers(self, classinfo=object):
        '''Enumerates all members of the current node, if they are instances of classinfo.'''
        for member in self.members:
            if isinstance(member, classinfo):
                yield member
        
    def allFieldsWithIncludes(self):
        '''Enumerates all StructureField nodes associated with the current node, and their a
           corresponding StructureIncludes node, if any.
           Each result is a tuple of the StructureField node and the StructureIncludes node or None.'''
        for m in self.members:
            if isinstance(m, StructureIncludes):
                if isinstance(m.targetType, FieldGroupType):
                    for field in m.targetType.allFields():
                        yield (field, m)
            elif isinstance(m, StructureField):
                yield (m, None)

    def getField(self, fieldName):
        return next((f for f in self.allFields() if f.name == fieldName), None)
        
    def validate(self, errs):
        super(StructuredTypeNode, self).validate(errs)
        self._checkDuplicateIncludes(errs)
        self._checkDuplicateFieldNames(errs)
        self._checkMissingOrInvalidTags(errs)
        self._checkDuplicateTags(errs)

    def _summarize(self, output, level, indent):
        super(StructuredTypeNode, self)._summarize(output, level, indent)
        self._summarizeList(output, self.members, 'members', level=level+1, indent=indent)
    
    def _checkDuplicateIncludes(self, errs):
        '''Check for multiple includes statements that include the same FIELD GROUP'''
        includedFieldGroups = []
        for m in self.members:
            if isinstance(m, StructureIncludes):
                fg = m.targetType
                if not fg in includedFieldGroups:
                    includedFieldGroups.append(fg)
                else:
                    _addSchemaError(errs, msg='duplicate includes statement',
                                    detail='the includes statement references a FIELD GROUP that has already been included',
                                    sourceRef=m.sourceRef)
        
    def _checkDuplicateFieldNames(self, errs):
        '''Confirm all fields have distinct names, including fields incorporated
           via "includes" statements.'''
        fieldsSeen = {}
        for (field, fieldIncludeStmt) in self.allFieldsWithIncludes():
            if not field.name in fieldsSeen:
                fieldsSeen[field.name] = field
            elif field.parent == self or field.parent != fieldsSeen[field.name].parent:
                if fieldIncludeStmt == None:
                    sourceRef = field.nameSourceRef
                else:
                    sourceRef = fieldIncludeStmt.sourceRef
                _addSchemaError(errs, msg='duplicate field in %s: %s' % (self.schemaConstruct, field.name),
                                detail='fields within a %s must have unique names' % self.schemaConstruct,
                                sourceRef=sourceRef)

    def _checkMissingOrInvalidTags(self, errs):
        '''Confirm all fields have valid tags'''
        # NOTE: This logic only checks fields declared directly within the STRUCTURE
        # or FIELD GROUP.  Fields declared within included FIELD GROUPs are check when that
        # FIELD GROUP is checked.
        for member in self.members:
            if isinstance(member, StructureField):
                possibleTags = member.possibleTags
                if len(possibleTags) == 0 or None in possibleTags:
                    if isinstance(member.targetType, ChoiceType):
                        _addSchemaError(errs, msg='missing tag on %s field: %s' % (self.schemaConstruct, member.name),
                                        detail='all CHOICE OF alternates within a %s field must declare an associated tag' % self.schemaConstruct,
                                        sourceRef=member.sourceRef)
                    else:
                        _addSchemaError(errs, msg='missing tag on %s field: %s' % (self.schemaConstruct, member.name),
                                        detail='fields within a %s must declare an associated tag' % self.schemaConstruct,
                                        sourceRef=member.sourceRef)
                if any((tag.isAnonTag for tag in possibleTags if tag is not None)):
                    _addSchemaError(errs, msg='invalid use of anonymous tag',
                                    detail='fields within a %s cannot declare an anonymous tag' % self.schemaConstruct,
                                    sourceRef=member.sourceRef)

    def _checkDuplicateTags(self, errs):
        '''Confirm all fields have distinct tags, including fields incorporated
           via "includes" statements.'''
        tagsSeen = {}
        for (field, fieldIncludeStmt) in self.allFieldsWithIncludes():
            # For all the possible tags associated with the current field...
            # (a field can have multiple possible tags when its underlying type
            # is a CHOICE OF).
            for tag in field.possibleTags:
                # Ignore cases where an alternate in a CHOICE OF field has no tag.
                # This error is detected by the _checkMissingOrInvalidTags() method.
                if tag is None:
                    continue
                # Look for a previous field that uses the same tag.  Skip to the next tag
                # if no such field is found. 
                matchingField = tagsSeen.get(tag.asTuple(), None)
                if matchingField is None:
                    continue
                # At this point we have found a duplicate tag.
                # TODO: Avoid reporting the same error twice, e.g. in the case a structure
                # includes a field group which contains fields with duplicate tags.
                if fieldIncludeStmt is not None:
                    sourceRef = fieldIncludeStmt.sourceRef
                elif tag.parent == field:
                    sourceRef = tag.sourceRef
                else:
                    sourceRef = field.sourceRef
                _addSchemaError(errs, msg='duplicate tag in %s: %s' % (self.schemaConstruct, tag),
                                detail='fields within a %s must have unique tags' % self.schemaConstruct,
                                sourceRef=sourceRef)
            # Include all possible tags in set of seen tags.
            for tag in field.possibleTags:
                if tag is not None:
                    tagsSeen[tag.asTuple()] = field

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

    def _summarize(self, output, level, indent):
        super(SchemaFile, self)._summarize(output, level, indent)
        self._summarizeList(output, self.statements, name='statements', level=level+1, indent=indent)

    @property
    def _summaryTitle(self):
        return '%s: %s' % (type(self).__name__, self.fileName)

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
        self.width = width
        if width is not None:
            self.lowerBound = None
            self.upperBound = None
        else:
            self.lowerBound = lowerBound
            self.upperBound = upperBound

    def validate(self, errs):
        super(Range, self).validate(errs)
        # Check that upperBound >= lowerBound 
        if self.width is None:
            if self.lowerBound is not None and self.upperBound is not None:
                if self.upperBound < self.lowerBound:
                    _addSchemaError(errs, msg='upper bound of range qualifier must be >= lower bound',
                                    sourceRef=self.sourceRef)
        # Check range constraints based on parent type...
        if isinstance(self.parent, FloatType):
            # Verify only 32/64bit widths on FLOAT type
            if self.width is not None and self.width < 32:
                _addSchemaError(errs, msg='only 32bit and 64bit range qualifiers allowed on FLOAT type',
                                sourceRef=self.sourceRef)
        elif isinstance(self.parent, IntegerTypeNode):
            # Verify only integer bounds on INTEGER types
            if isinstance(self.lowerBound, Decimal) or isinstance(self.upperBound, Decimal):  
                errMsg = 'bounds values for range qualifier on %s must be integers' % self.parent.schemaConstruct
                _addSchemaError(errs, msg=errMsg,
                                sourceRef=self.sourceRef)

    @property
    def _summaryTitle(self):
        if self.width is not None:
            return '%s: width %d' % (type(self).__name__, self.width)
        else:
            return '%s: %s to %s' % (type(self).__name__, str(self.lowerBound), str(self.upperBound))

class Length(QualifierNode):
    '''Represents a length qualifier'''

    _schemaConstruct = 'length qualifier'

    def __init__(self, sourceRef=None, lowerBound=None, upperBound=None):
        super(Length, self).__init__(sourceRef)
        self.lowerBound = lowerBound
        self.upperBound = upperBound

    def validate(self, errs):
        super(Length, self).validate(errs)
        # Check that lowerBound and upperBound >= 0 
        if self.lowerBound < 0 or (self.upperBound is not None and self.upperBound < 0):
            _addSchemaError(errs, msg='bounds of length qualifier must be >= 0',
                            sourceRef=self.sourceRef)
        # Check that upperBound >= lowerBound 
        if self.upperBound is not None and self.upperBound < self.lowerBound:
            _addSchemaError(errs, msg='upper bound of length qualifier must be >= lower bound',
                            sourceRef=self.sourceRef)

    @property
    def _summaryTitle(self):
        return '%s: %s to %s' % (type(self).__name__, str(self.lowerBound), str(self.upperBound))

class Tag(QualifierNode):
    '''Represents a tag qualifier'''

    _schemaConstruct = 'tag qualifier'
    
    def __init__(self, sourceRef=None, tagNum=None, profile=None):
        super(Tag, self).__init__(sourceRef)
        self.tagNum = tagNum
        self.profile = profile
        self.profileNode = None

    @property
    def profileId(self):
        if self.profileNode is not None:
            return self.profileNode.id
        return self.profile

    @property
    def isAnonTag(self):
        return self.tagNum is None and self.profile is None

    @property
    def isContextSpecificTag(self):
        return self.tagNum is not None and self.profile is None

    @property
    def isProfileSpecificTag(self):
        return self.tagNum is not None and self.profile is not None

    def asTuple(self):
        return (self.profileId, self.tagNum)

    @property
    def _summaryTitle(self):
        return '%s: %s' % (type(self).__name__, self)

    def __str__(self):
        if self.isAnonTag:
            return 'anon'
        elif self.profile is not None:
            return '%s:%s (profile-specific)' % (self.profile, self.tagNum)
        else:
            return '%s (context-specific)' % (self.tagNum)

class Id(QualifierNode):
    '''Represents an id qualifier'''

    _schemaConstruct = 'id qualifier'
    
    def __init__(self, sourceRef=None, idNum=None, vendor=None):
        super(Id, self).__init__(sourceRef)
        self.idNum = idNum
        self.vendor = vendor
        self.vendorNode = None

    @property
    def vendorId(self):
        if self.vendorNode is not None:
            return self.vendorNode.id
        return self.vendor

    @property
    def _summaryTitle(self):
        return '%s: %s' % (type(self).__name__, self)

    def __str__(self):
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
    
    @property
    def isLeafNamespace(self):
        return not any(True for _ in self.allStatements(Namespace)) 
        
    def allChildNodes(self):
        for node in super(Namespace, self).allChildNodes():
            yield node
        for node in self.statements:
            yield node

    def allStatements(self, classinfo=object):
        for stmt in self.statements:
            if isinstance(stmt, classinfo):
                yield stmt

    def _summarize(self, output, level, indent):
        super(Namespace, self)._summarize(output, level, indent)
        self._summarizeList(output, self.statements, name='statements', level=level+1, indent=indent)

class Vendor(HasName, HasQualifiers, HasDocumentation, SchemaNode):
    '''Represents a VENDOR definition'''

    _schemaConstruct = 'VENDOR definition'
    _allowedQualifiers = (Id)

    def __init__(self, sourceRef=None):
        super(Vendor, self).__init__(sourceRef)
        self._id = None
    
    @property
    def id(self):
        if self._id is None:
            idQual = self.getQualifier(Id)
            if idQual is not None:
                self._id = idQual.idNum 
        return self._id

    def validate(self, errs):
        super(Vendor, self).validate(errs)
        # Confirm that VENDOR is not within a namespace or PROFILE
        if self.nextParentNode(Namespace) is not None:
            _addSchemaError(errs, msg='VENDOR definition not at global scope',
                            detail='VENDOR definitions may not appear within a namespace or PROFILE definition',
                            sourceRef=self.sourceRef)
        # Confirm that id qualifier is present
        idQual = self.getQualifier(Id)
        if idQual is None:
            _addSchemaError(errs, msg='id qualifier missing on VENDOR definition',
                            sourceRef=self.sourceRef)
        else:
            # Confirm that the given id value is correctly structured and in range.
            if idQual.vendor is not None or idQual.idNum < 0 or idQual.idNum > 65535:
                _addSchemaError(errs, msg='invalid id value for VENDOR definition',
                                detail='id value for VENDOR must be a single integer in the range 0-65535',
                                sourceRef=idQual.sourceRef)

class Profile(HasQualifiers, Namespace):
    '''Represents a PROFILE definition'''

    _schemaConstruct = 'PROFILE definition'
    _allowedQualifiers = (Id)

    def __init__(self, sourceRef=None):
        super(Profile, self).__init__(sourceRef)
        self._id = None

    @property
    def id(self):
        if self._id is None:
            idQual = self.getQualifier(Id)
            if idQual is not None:
                vendorId = idQual.vendorId
                if vendorId is None:
                    self._id = idQual.idNum
                elif isinstance(vendorId, int):
                    self._id = (vendorId << 16) + idQual.idNum
        return self._id

    def validate(self, errs):
        super(Profile, self).validate(errs)
        self._checkNestedProfiles(errs)
        self._checkInvalidOrMissingId(errs)
        self._checkDuplicateMessageIds(errs)
        self._checkDuplicateStatusCodeIds(errs)

    def getMessage(self, name):
        for msg in self.allStatements(Message):
            if msg.name == name:
                return msg
        return None

    def getStatusCode(self, name):
        for msg in self.allStatements(StatusCode):
            if msg.name == name:
                return msg
        return None
    
    def _checkNestedProfiles(self, errs):
        '''Verify no nesting of PROFILES'''
        parentProfile = next((n for n in self.allParentNodes() if isinstance(n, Profile)), None)
        if parentProfile is not None:
            _addSchemaError(errs, msg='nested PROFILE definition',
                            detail='PROFILE definitions may not appear within other PROFILE definitions',
                            sourceRef=self.sourceRef)
    
    def _checkInvalidOrMissingId(self, errs):
        '''Verify that the id qualifier is present and valid'''
        idQual = self.getQualifier(Id)
        if idQual is None:
            _addSchemaError(errs, msg='id qualifier missing on PROFILE definition',
                            sourceRef=self.sourceRef)
        else:
            # Confirm that the given id value is correctly structured and in range.
            if idQual.vendor is None:
                if idQual.idNum < 0 or idQual.idNum > 0xFFFFFFFF:
                    _addSchemaError(errs, msg='invalid id value for PROFILE definition',
                                    detail='profile ids must be in the range 0-0xFFFFFFFF',
                                    sourceRef=idQual.sourceRef)
            else:
                if isinstance(idQual.vendor, int) and (idQual.vendor < 0 or idQual.vendor > 65535):
                    _addSchemaError(errs, msg='invalid vendor id value for PROFILE definition',
                                    detail='vendor id must be in the range 0-65535',
                                    sourceRef=idQual.sourceRef)
                if idQual.idNum < 0 or idQual.idNum > 65535:
                    _addSchemaError(errs, msg='invalid profile number value for PROFILE definition',
                                    detail='profile numbers must be in the range 0-65535',
                                    sourceRef=idQual.sourceRef)

    def _checkDuplicateMessageIds(self, errs):
        msgsById = {}
        for msg in self.allStatements(Message):
            # Ignore message definitions without ids.  These are errors that are detected elsewhere.
            if msg.id is None:
                continue
            prevMsg = msgsById.get(msg.id, None)
            if prevMsg is not None:
                _addSchemaError(errs, msg='duplicate message id: %s' % msg.id,
                                detail='ids assigned to messages in the PROFILE definition must be unique',
                                sourceRef=msg.sourceRef)
            else:
                msgsById[msg.id] = msg

    def _checkDuplicateStatusCodeIds(self, errs):
        statusCodesById = {}
        for sc in self.allStatements(StatusCode):
            # Ignore status code definitions without ids.  These are errors that are detected elsewhere.
            if sc.id is None:
                continue
            prevSC = statusCodesById.get(sc.id, None)
            if prevSC is not None:
                _addSchemaError(errs, msg='duplicate status code id: %s' % sc.id,
                                detail='ids assigned to status codes in the PROFILE definition must be unique',
                                sourceRef=sc.sourceRef)
            else:
                statusCodesById[sc.id] = sc

class Message(HasScopedName, HasQualifiers, HasType, HasDocumentation, SchemaNode):
    '''Represents a MESSAGE definition'''

    _schemaConstruct = 'MESSAGE definition'
    _allowedQualifiers = (Id)

    def __init__(self, sourceRef=None):
        super(Message, self).__init__(sourceRef)
        self.emptyPayload = False
    
    @property
    def id(self):
        idQual = self.getQualifier(Id)
        if idQual is not None:
            return idQual.idNum
        else:
            return None

    @property
    def payloadType(self):
        return self.type
        
    @property
    def targetPayloadType(self):
        return self.targetType
        
    def validate(self, errs):
        super(Message, self).validate(errs)
        # Confirm that MESSAGE is directly within a PROFILE definition
        if not isinstance(self.parent, Profile):
            _addSchemaError(errs, msg='MESSAGE definition not within PROFILE definition',
                            detail='MESSAGE definitions must appear directly within a PROFILE definition',
                            sourceRef=self.sourceRef)
        # Confirm that id qualifier is present
        idQual = self.getQualifier(Id)
        if idQual is None:
            _addSchemaError(errs, msg='id qualifier missing on MESSAGE definition',
                            sourceRef=self.sourceRef)
        else:
            # Confirm that the given id value is correctly structured and in range.
            if idQual.vendor is not None or idQual.idNum < 0 or idQual.idNum > 255:
                _addSchemaError(errs, msg='invalid id value for MESSAGE definition',
                                detail='id value for MESSAGE must be a single integer in the range 0-255',
                                sourceRef=idQual.sourceRef)

    def _summarize(self, output, level, indent):
        super(Message, self)._summarize(output, level, indent)
        level += 1
        if self.type:
            output.write('%spayload:\n' % (level*indent))
            self.type._summarize(output, level+1, indent)
        elif self.emptyPayload:
            output.write('%spayload: empty\n' % (level*indent))
        else:
            output.write('%spayload: not defined\n' % (level*indent))

class StatusCode(HasScopedName, HasQualifiers, HasDocumentation, SchemaNode):
    '''Represents a STATUS CODE definition'''
    
    _schemaConstruct = 'STATUS CODE definition'
    _allowedQualifiers = (Id)

    @property
    def id(self):
        idQual = self.getQualifier(Id)
        if idQual is not None:
            return idQual.idNum
        else:
            return None
        
    def validate(self, errs):
        super(StatusCode, self).validate(errs)
        # Confirm that STATUS CODE is directly within a PROFILE definition
        if not isinstance(self.parent, Profile):
            _addSchemaError(errs, msg='STATUS CODE definition not within PROFILE definition',
                            detail='STATUS CODE definitions must appear directly within a PROFILE definition',
                            sourceRef=self.sourceRef)
        # Confirm that id qualifier is present
        idQual = self.getQualifier(Id)
        if idQual is None:
            _addSchemaError(errs, msg='id qualifier missing on STATUS CODE definition',
                            sourceRef=self.sourceRef)
        else:
            # Confirm that the given id value is correctly structured and in range.
            if idQual.vendor is not None or idQual.idNum < 0 or idQual.idNum > 65535:
                _addSchemaError(errs, msg='invalid id value for STATUS CODE definition',
                                detail='id value for STATUS CODE must be a single integer in the range 0-65535',
                                sourceRef=idQual.sourceRef)


class TypeDef(HasScopedName, HasQualifiers, HasType, HasTag, HasDocumentation, SchemaNode):
    '''Represents a type definition'''

    _schemaConstruct = 'type definition'
    _allowedQualifiers = (Tag)

    def _summarize(self, output, level, indent):
        super(TypeDef, self)._summarize(output, level, indent)
        level += 1
        output.write('%stype:\n' % (level*indent))
        self.type._summarize(output, level+1, indent)

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
    def _summaryTitle(self):
        return '%s: %s' % (type(self).__name__, self.targetName)

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
    
    def validate(self, errs):
        super(StructureType, self).validate(errs)
        self._checkOneOrderQual(errs)

    def _checkOneOrderQual(self, errs):
        '''Confirm only one of schema-order, tag-order, any-order applied to STRUCTURE'''
        orderQualSeen = False
        for qual in self.quals:
            if isinstance(qual, (SchemaOrder, TagOrder, AnyOrder)):
                if not orderQualSeen:
                    orderQualSeen = True
                else:
                    _addSchemaError(errs, msg='multiple order qualifiers',
                                    detail='only one order qualifier allowed on a STRUCTURE type',
                                    sourceRef=qual.sourceRef)

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
        self._possibleTags = None

    @property
    def possibleTags(self):
        '''A list of the tags associated with all possible leaf alternates of the Choice type.
           The list will include a None if one or more of the alternates does not have an
           assigned tag.'''
        if self._possibleTags is None:
            tagSet = {}
            for (_, _, defaultTag) in self.allLeafAlternatesWithNamesAndTags():
                if defaultTag is not None:
                    tagSet[defaultTag.asTuple()] = defaultTag
                else:
                    tagSet[None] = None
            self._possibleTags = list(tagSet.values())
            # if none of the alternates have a tag, then simply return an empty list, rather
            # than a list containing a single None.
            if len(self._possibleTags) == 1 and self._possibleTags[0] is None:
                self._possibleTags = []
        return self._possibleTags

    def allChildNodes(self):
        for node in super(ChoiceType, self).allChildNodes():
            yield node
        for node in self.alternates:
            yield node

    def allLeafAlternatesWithNamesAndTags(self):
        '''Enumerates all leaf ChoiceAlternate nodes of the current ChoiceType node, including
           any contained within nested ChoiceType nodes.  For each such node it returns 3-tuple
           containing: 1) the chain of ChoiceAlternate nodes leading to the leaf node, 2) the
           effective name of the node and 3) the effective default tag for the node.'''
        for altChain in self.allLeafAlternateChains():
            defaultTag = None
            for alt in reversed(altChain):
                defaultTag = alt.tag
                if defaultTag is None and isinstance(alt.type, ReferencedType):
                    defaultTag = alt.type.effectiveTag
                if defaultTag is not None:
                    break
            yield (altChain, altChain[0].name, defaultTag)

    def allLeafAlternateChains(self, superiorAltChain=[], followTypeRefs=True):
        '''Enumerates all leaf ChoiceAlternate nodes of the current ChoiceType node, as well
           as those contained within nested ChoiceType nodes, along with a list of the non-leaf
           ChoiceAlternate nodes leading up to the current ChoiceType.
           Each result returned by the generator is an array, where the first element is the
           leaf alternate and the remaining elements (if any) are the non-leaf alternates
           leading to the leaf alternate, given in ascending order.  As such, the last element
           in each array is always a ChoiceAlternate node that resides immediately within the
           current ChoiceType node.'''
        for alt in self.alternates:
            altChain = superiorAltChain.copy()
            altChain.insert(0, alt)
            if alt.isLeafAlternate:
                yield altChain
            elif followTypeRefs or isinstance(alt.type, ChoiceType):
                yield from alt.targetType.allLeafAlternateChains(superiorAltChain=altChain, 
                                                                 followTypeRefs=followTypeRefs)

    def getAlternate(self, altName):
        return next((a for a in self.alternates if a.name == altName), None)

    def validate(self, errs):
        super(ChoiceType, self).validate(errs)
        self._checkDuplicateAlternateNames(errs)

    def _checkDuplicateAlternateNames(self, errs):
        '''Confirm all alternates immediately within the ChoiceType have distinct names.'''
        nameSeen = {}
        for node in self.alternates:
            if node.name is not None:
                if not node.name in nameSeen:
                    nameSeen[node.name] = True
                else:
                    _addSchemaError(errs, msg='duplicate CHOICE OF alternate',
                                    detail='alternates within a CHOICE OF type must have unique names',
                                    sourceRef=node.nameSourceRef)

    def _summarize(self, output, level, indent):
        super(ChoiceType, self)._summarize(output, level, indent)
        self._summarizeList(output, self.alternates, 'alternates', level=level+1, indent=indent)

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
        self.targetTypeDef = None
        self.targetType = None

    @property
    def effectiveTag(self):
        '''The effective tag associated with the referenced type definition.
           If the referenced type definition has a default tag, that tag is returned.
           If the referenced type definition is itself another type reference,
           the chain of type references if followed until a default tag is
           found.
           In the case no such tag is found, a None is returned.
        '''
        node = self
        while True:
            if node.targetTypeDef is None:
                return None
            tag = node.targetTypeDef.tag
            if tag is not None:
                return tag
            node = node.targetTypeDef.type
            if not isinstance(node, ReferencedType):
                return None

    def _summarize(self, output, level, indent):
        super(ReferencedType, self)._summarize(output, level, indent)
        output.write('%sreferencedName: %s\n' % ((level+1)*indent, self.targetName))

# ----- SchemaNodes Representing Components of Types

class IntegerEnumValue(HasName, HasDocumentation, SchemaNode):
    '''Represents an individual enumerated value associated with an INTEGER type.'''

    _schemaConstruct = 'enumerated value'
    
    def __init__(self, sourceRef=None):
        super(IntegerEnumValue, self).__init__(sourceRef)
        self.value = None
        self.valueSourceRef = None

    def validate(self, errs):
        super(IntegerEnumValue, self).validate(errs)
        # Check value is in range for integer type
        if not self.parent.isInRange(self.value):
            _addSchemaError(errs, msg='enumerated integer value out of range: %s' % self.value,
                            sourceRef=self.valueSourceRef)

    @property
    def _summaryTitle(self):
        return '%s: %s = %d' % (type(self).__name__, self.name, self.value)

class StructureField(HasName, HasQualifiers, HasType, HasTag, HasDocumentation, SchemaNode):
    '''Represents an individual field within a STRUCTURE or FIELD GROUP type.'''

    _schemaConstruct = 'STRUCTURE or FIELD GROUP field'
    _allowedQualifiers = (Tag, Optional)

    def __init__(self, sourceRef=None):
        super(StructureField, self).__init__(sourceRef)

    def validate(self, errs):
        super(StructureField, self).validate(errs)
        self._checkIsNotFieldGroup(self.type, errs)

    def _summarize(self, output, level, indent):
        super(StructureField, self)._summarize(output, level, indent)
        level += 1
        output.write('%stype:\n' % (level*indent))
        self.type._summarize(output, level+1, indent)

class StructureIncludes(SchemaNode):
    '''Represents an includes statement within a STRUCTURE or FIELD GROUP type.'''

    _schemaConstruct = 'STRUCTURE includes statement'

    def __init__(self, sourceRef=None):
        super(StructureIncludes, self).__init__(sourceRef)
        self.targetName = None
        self.targetTypeDef = None
        self.targetType = None

    def validate(self, errs):
        super(StructureIncludes, self).validate(errs)
        # Check that target names a FIELD GROUP
        if self.targetType is not None and not isinstance(self.targetType, FieldGroupType):
            _addSchemaError(errs, msg='invalid target for includes statement',
                            detail='an includes statement within a STRUCTURE or FIELD GROUP must refer to a FIELD GROUP type',
                            sourceRef=self.sourceRef)

    @property
    def _summaryTitle(self):
        return '%s: %s' % (type(self).__name__, self.targetName)
    
class ChoiceAlternate(HasName, HasQualifiers, HasType, HasTag, HasDocumentation, SchemaNode):
    '''Represents a type alternate within a CHOICE type.'''

    _schemaConstruct = 'CHOICE alternate'
    _allowedQualifiers = (Tag)

    @property
    def isLeafAlternate(self):
        '''True if the alternate is a leaf alternate.
           A _leaf alternate_ is a ChoiceAlternate node that does not itself refer to another
           ChoiceType.  Conversely, a _non-leaf alternate_ is a ChoiceAlternate that does refer
           to another ChoiceType.'''
        return not isinstance(self.targetType, ChoiceType)

    @property
    def effectiveName(self):
        '''The effective name of the alternate.
           If the alternate was assigned a name in the schema, this is the assigned name.
           If the alternate was not assigned a name, this is the string 'alternate-n', where 
           n is the numeric position of the alternate within the enclosing ChoiceType,
           starting with 1.'''
        if self.name is not None:
            return self.name
        else:
            return 'alternate-%d' % (self.parent.alternates.index(self) + 1)

    def validate(self, errs):
        super(ChoiceAlternate, self).validate(errs)
        self._checkIsNotFieldGroup(self.type, errs)

    def _summarize(self, output, level, indent):
        super(ChoiceAlternate, self)._summarize(output, level, indent)
        level += 1
        output.write('%stype:\n' % (level*indent))
        self.type._summarize(output, level+1, indent)

class LinearTypePatternElement(HasName, HasQualifiers, HasType, HasTag, HasDocumentation, SchemaNode):
    '''Represents a single type element within a linear type pattern.'''

    _schemaConstruct = 'linear type pattern element'
    # NOTE: _allowedQualifiers is dynamic for LinearTypePatternElement nodes. See
    # implementation below.

    def __init__(self, sourceRef=None):
        super(LinearTypePatternElement, self).__init__(sourceRef)
        self.lowerBound = None
        self.upperBound = None

    @property
    def effectiveName(self):
        '''The effective name of the element.
           If the element was assigned a name in the schema, this is the assigned name.
           If the element was not assigned a name, this is the string 'element-n', where 
           n is the numeric position of the element within the enclosing ArrayType/ListType,
           starting at 1.'''
        if self.name is not None:
            return self.name
        else:
            return 'element-%d' % (self.parent.elemTypePattern.index(self) + 1)

    @property
    def _allowedQualifiers(self):
        if isinstance(self.parent, ListType):
            return (Tag)
        else:
            assert isinstance(self.parent, ArrayType)
            return ()

    def _summarize(self, output, level, indent):
        super(LinearTypePatternElement, self)._summarize(output, level, indent)
        level += 1
        curIndent = level*indent
        output.write('%slowerBound: %s\n' % (curIndent, self.lowerBound))
        output.write('%supperBound: %s\n' % (curIndent, self.upperBound))
        output.write('%stype:\n' % (curIndent))
        self.type._summarize(output, level+1, indent)

# ----- Supporting Classes / Functions

class SourceRef(object):
    '''Identifies a source of schema (e.g. a file), and start / end text positions within that source.'''

    def __init__(self, schemaFile, startLine, startCol, startPos, endLine=None, endCol=None, endPos=None):
        self.schemaFile = schemaFile
        self.startLine = startLine
        self.startCol = startCol
        self.startPos = startPos
        self.endLine = endLine if endLine is not None else startLine
        self.endCol = endCol if endCol is not None else startCol
        self.endPos = endPos if endPos is not None else startPos

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

    def filePosStr(self):
        return '%s:%d:%d' % (self.schemaFile.fileName, self.startLine, self.startCol)

    def lineSummaryStr(self):
        schemaText = self.schemaFile.schemaText
        lineStart = schemaText.rfind('\n', 0, self.startPos)
        lineStart += 1
        lineEnd = schemaText.find('\n', self.startPos+1)
        if lineEnd < 0:
            lineEnd = len(schemaText)
        line = schemaText[lineStart:lineEnd]
        startPosIndent = schemaText[lineStart:self.startPos]
        startPosIndent = re.sub(r'\S', ' ', startPosIndent)
        return '%s\n%s^' % (line, startPosIndent)

    @staticmethod
    def fromMeta(schemaFile, meta):
        if meta is None:
            return None
        return SourceRef(schemaFile, 
                         startLine=meta.line, startCol=meta.column, startPos=meta.start_pos,
                         endLine=meta.end_line, endCol=meta.end_column, endPos=meta.end_pos)

    @staticmethod
    def fromToken(schemaFile, token):
        if token is None:
            return None
        endPos = token.pos_in_stream + len(token.value)
        return SourceRef(schemaFile, 
                         startLine=token.line, startCol=token.column, startPos=token.pos_in_stream,
                         endLine=token.end_line, endCol=token.end_column, endPos=endPos)

        
