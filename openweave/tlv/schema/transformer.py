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
#      Code for converting a Lark parse trees into a Weave TLV Schema AST. 
#

import copy
from decimal import Decimal

from lark import Tree, Token, v_args 
from lark.visitors import Transformer

from .node import *
from .error import *

class _SchemaTransformer(Transformer):
    def __init__(self, schemaFile):
        Transformer.__init__(self)
        self.schemaFile = schemaFile

    # ----- general rule handlers
    
    @v_args(meta=True)
    def file(self, children, meta):
        self.schemaFile.sourceRef = SourceRef.fromMeta(self.schemaFile, meta)
        self.schemaFile.statements = self._popTree(children, expectedName='statements').children
        assert len(children) == 0
        self._attachDocsToNodes(self.schemaFile.statements)
        return self.schemaFile

    @v_args(meta=True)
    def namespace_def(self, children, meta):
        node = Namespace(SourceRef.fromMeta(self.schemaFile, meta))
        (node.docs, node.docsSourceRef) = self._popOptionalDocs(children)
        (node.name, node.nameSourceRef) = self._popName(children, allowScopedName=True)
        node.statements = self._popTree(children, expectedName='statements').children
        assert len(children) == 0
        self._attachDocsToNodes(node.statements)
        self._setParent(node.statements, node)
        while True:
            names = node.name.rsplit('.', maxsplit=1)
            if len(names) == 1:
                break
            node.name = names[1]
            node.parent = Namespace(node.sourceRef)
            node.parent.name = names[0]
            node.parent.nameSourceRef = node.nameSourceRef
            node.parent.statements = [ node ]
            node = node.parent
        return node

    @v_args(meta=True)
    def using_stmt(self, children, meta):
        node = Using(SourceRef.fromMeta(self.schemaFile, meta))
        (node.targetName, node.targetNameSourceRef) = self._popName(children, allowScopedName=True)
        assert len(children) == 0
        return node

    @v_args(meta=True)
    def vendor_def(self, children, meta):
        node = Vendor(SourceRef.fromMeta(self.schemaFile, meta))
        (node.docs, node.docsSourceRef) = self._popOptionalDocs(children)
        (node.name, node.nameSourceRef) = self._popName(children)
        node.quals = self._popOptionalQualList(children)
        assert len(children) == 0
        self._setParent(node.quals, node)
        return node

    @v_args(meta=True)
    def profile_def(self, children, meta):
        node = Profile(SourceRef.fromMeta(self.schemaFile, meta))
        (node.docs, node.docsSourceRef) = self._popOptionalDocs(children)
        (node.name, node.nameSourceRef) = self._popName(children)
        node.quals = self._popOptionalQualList(children)
        if len(children) == 1:
            node.statements = self._popTree(children, expectedName='statements').children
        else:
            node.statements = []
        assert len(children) == 0
        self._attachDocsToNodes(node.statements)
        self._setParent(node.quals, node)
        self._setParent(node.statements, node)
        return node

    @v_args(meta=True)
    def message_def(self, children, meta):
        node = Message(SourceRef.fromMeta(self.schemaFile, meta))
        (node.docs, node.docsSourceRef) = self._popOptionalDocs(children)
        (node.name, node.nameSourceRef) = self._popName(children)
        node.quals = self._popOptionalQualList(children)
        if len(children) > 0:
            child = children.pop(0)
            if isinstance(child, TypeNode):
                node.payload = child
            else:
                assert child.data == 'containing_nothing'
                node.emptyPayload = True
        assert len(children) == 0
        self._setParent(node.quals, node)
        if isinstance(node.payload, SchemaNode):
            self._setParent(node.payload, node)
        return node

    @v_args(meta=True)
    def status_code_def(self, children, meta):
        node = StatusCode(SourceRef.fromMeta(self.schemaFile, meta))
        (node.docs, node.docsSourceRef) = self._popOptionalDocs(children)
        (node.name, node.nameSourceRef) = self._popName(children)
        node.quals = self._popOptionalQualList(children)
        assert len(children) == 0
        self._setParent(node.quals, node)
        return node

    @v_args(meta=True)
    def type_def(self, children, meta):
        node = TypeDef(SourceRef.fromMeta(self.schemaFile, meta))
        (node.docs, node.docsSourceRef) = self._popOptionalDocs(children)
        (node.name, node.nameSourceRef) = self._popName(children)
        node.quals = self._popOptionalQualList(children, 0)
        node.type = self._popTypeNode(children)
        assert len(children) == 0
        self._setParent(node.quals, node)
        self._setParent(node.type, node)
        return node

    # ----- qualifier handlers

    @v_args(meta=True)
    def extensible(self, children, meta):
        return Extensible(SourceRef.fromMeta(self.schemaFile, meta))

    @v_args(meta=True)
    def optional(self, children, meta):
        return Optional(SourceRef.fromMeta(self.schemaFile, meta))

    @v_args(meta=True)
    def private(self, children, meta):
        return Private(SourceRef.fromMeta(self.schemaFile, meta))

    @v_args(meta=True)
    def invariant(self, children, meta):
        return Invariant(SourceRef.fromMeta(self.schemaFile, meta))

    @v_args(meta=True)
    def nullable(self, children, meta):
        return Nullable(SourceRef.fromMeta(self.schemaFile, meta))

    @v_args(meta=True)
    def tag_order(self, children, meta):
        return TagOrder(SourceRef.fromMeta(self.schemaFile, meta))

    @v_args(meta=True)
    def schema_order(self, children, meta):
        return SchemaOrder(SourceRef.fromMeta(self.schemaFile, meta))

    @v_args(meta=True)
    def any_order(self, children, meta):
        return AnyOrder(SourceRef.fromMeta(self.schemaFile, meta))

    @v_args(meta=True)
    def range_8bits(self, children, meta):
        return Range(SourceRef.fromMeta(self.schemaFile, meta), width=8)

    @v_args(meta=True)
    def range_16bits(self, children, meta):
        return Range(SourceRef.fromMeta(self.schemaFile, meta), width=16)

    @v_args(meta=True)
    def range_32bits(self, children, meta):
        return Range(SourceRef.fromMeta(self.schemaFile, meta), width=32)

    @v_args(meta=True)
    def range_64bits(self, children, meta):
        return Range(SourceRef.fromMeta(self.schemaFile, meta), width=64)

    @v_args(meta=True)
    def range_from_to(self, children, meta):
        (lowerBound, unused) = self._popIntOrDecimal(children, 'range lower bound')
        (upperBound, unused) = self._popIntOrDecimal(children, 'range upper bound')
        assert len(children) == 0
        return Range(SourceRef.fromMeta(self.schemaFile, meta), lowerBound=lowerBound, upperBound=upperBound)

    @v_args(meta=True)
    def length_exact(self, children, meta):
        (n, unused) = self._popInt(children)
        assert len(children) == 0
        return Length(SourceRef.fromMeta(self.schemaFile, meta), lowerBound=n, upperBound=n)

    @v_args(meta=True)
    def length_from_to(self, children, meta):
        (lowerBound, unused) = self._popInt(children)
        if len(children) == 1:
            (upperBound, unused) = self._popInt(children)
        else:
            upperBound = None
        assert len(children) == 0
        return Length(SourceRef.fromMeta(self.schemaFile, meta), lowerBound=lowerBound, upperBound=upperBound)

    @v_args(meta=True)
    def context_tag(self, children, meta):
        (tagNum, unused) = self._popInt(children, desc='context tag')
        assert len(children) == 0
        return Tag(SourceRef.fromMeta(self.schemaFile, meta), tagNum=tagNum)

    @v_args(meta=True)
    def profile_tag_int(self, children, meta):
        (profileId, unused) = self._popInt(children, desc='profile id')
        (tagNum, unused) = self._popInt(children, desc='profile tag')
        assert len(children) == 0
        return Tag(SourceRef.fromMeta(self.schemaFile, meta), tagNum=tagNum, profile=profileId)

    @v_args(meta=True)
    def profile_tag_name(self, children, meta):
        assert len(children) > 0
        if isinstance(children[0], Token) and children[0].type == 'STAR':
            profile = '*'
            children.pop(0)
        else: 
            (profile, unused) = self._popName(children, allowScopedName=True)
        (tagNum, unused) = self._popInt(children, desc='profile tag')
        assert len(children) == 0
        return Tag(SourceRef.fromMeta(self.schemaFile, meta), tagNum=tagNum, profile=profile)

    @v_args(meta=True)
    def anon_tag(self, children, meta):
        return Tag(SourceRef.fromMeta(self.schemaFile, meta))

    @v_args(meta=True)
    def id(self, children, meta):
        (idNum, unused) = self._popInt(children, desc='id')
        assert len(children) == 0
        return Id(SourceRef.fromMeta(self.schemaFile, meta), idNum=idNum)

    @v_args(meta=True)
    def id_int_scope(self, children, meta):
        (vendorNum, unused) = self._popInt(children, desc='id')
        (idNum, unused) = self._popInt(children, desc='id')
        assert len(children) == 0
        return Id(SourceRef.fromMeta(self.schemaFile, meta), idNum=idNum, vendor=vendorNum)

    @v_args(meta=True)
    def id_name_scope(self, children, meta):
        (vendor, unused) = self._popName(children, allowScopedName=True)
        (idNum, unused) = self._popInt(children, desc='id')
        assert len(children) == 0
        return Id(SourceRef.fromMeta(self.schemaFile, meta), idNum=idNum, vendor=vendor)

    # ----- type handlers

    @v_args(meta=True)
    def signed_integer_type(self, children, meta):
        return self._newIntTypeNode(SignedIntegerType, children, meta)

    @v_args(meta=True)
    def unsigned_integer_type(self, children, meta):
        return self._newIntTypeNode(UnsignedIntegerType, children, meta)

    @v_args(meta=True)
    def enum_value(self, children, meta):
        node = IntegerEnumValue(SourceRef.fromMeta(self.schemaFile, meta))
        (node.name, node.nameSourceRef) = self._popName(children)
        (node.value, node.valueSourceRef) = self._popInt(children)
        assert len(children) == 0
        return node

    @v_args(meta=True)
    def float_type(self, children, meta):
        return self._newSimpleTypeNode(FloatType, children, meta)

    @v_args(meta=True)
    def bool_type(self, children, meta):
        return self._newSimpleTypeNode(BooleanType, children, meta)

    @v_args(meta=True)
    def string_type(self, children, meta):
        return self._newSimpleTypeNode(StringType, children, meta)

    @v_args(meta=True)
    def byte_string_type(self, children, meta):
        return self._newSimpleTypeNode(ByteStringType, children, meta)

    @v_args(meta=True)
    def null_type(self, children, meta):
        return self._newSimpleTypeNode(NullType, children, meta)

    @v_args(meta=True)
    def any_type(self, children, meta):
        return self._newSimpleTypeNode(AnyType, children, meta)

    @v_args(meta=True)
    def structure_type(self, children, meta):
        node = StructureType(SourceRef.fromMeta(self.schemaFile, meta))
        node.quals = self._popOptionalQualList(children, 0)
        if len(children) != 0:
            node.members = self._popTree(children, expectedName='structure_members').children
            assert len(children) == 0
        self._attachDocsToNodes(node.members)
        self._setParent(node.quals, node)
        self._setParent(node.members, node)
        return node

    @v_args(meta=True)
    def structure_field_def(self, children, meta):
        node = StructureField(SourceRef.fromMeta(self.schemaFile, meta))
        (node.name, node.nameSourceRef) = self._popName(children)
        node.quals = self._popOptionalQualList(children, 0)
        node.type = self._popTypeNode(children)
        assert len(children) == 0
        self._setParent(node.quals, node)
        self._setParent(node.type, node)
        return node

    @v_args(meta=True)
    def structure_includes(self, children, meta):
        node = StructureIncludes(SourceRef.fromMeta(self.schemaFile, meta))
        (node.targetName, unused) = self._popName(children, allowScopedName=True)
        return node

    @v_args(meta=True)
    def field_group_type(self, children, meta):
        node = FieldGroupType(SourceRef.fromMeta(self.schemaFile, meta))
        node.quals = self._popOptionalQualList(children, 0)
        if len(children) != 0:
            node.members = self._popTree(children, expectedName='structure_members').children
            assert len(children) == 0
        self._attachDocsToNodes(node.members)
        self._setParent(node.quals, node)
        self._setParent(node.members, node)
        return node

    @v_args(meta=True)
    def choice_type(self, children, meta):
        node = ChoiceType(SourceRef.fromMeta(self.schemaFile, meta))
        node.quals = self._popOptionalQualList(children, 0)
        if len(children) != 0:
            node.alternates = self._popTree(children, expectedName='choice_alternates').children
            assert len(children) == 0
        self._attachDocsToNodes(node.alternates)
        self._setParent(node.alternates, node)
        return node

    @v_args(meta=True)
    def named_choice_alt(self, children, meta):
        node = ChoiceAlternate(SourceRef.fromMeta(self.schemaFile, meta))
        (node.name, node.nameSourceRef) = self._popName(children)
        node.quals = self._popOptionalQualList(children)
        node.type = self._popTypeNode(children)
        assert len(children) == 0
        self._setParent(node.quals, node)
        self._setParent(node.type, node)
        return node

    @v_args(meta=True)
    def unnamed_choice_alt(self, children, meta):
        node = ChoiceAlternate()
        node.type = self._popTypeNode(children)
        node.sourceRef = copy.copy(node.type.sourceRef)
        assert len(children) == 0
        self._setParent(node.type, node)
        return node
    
    @v_args(meta=True)
    def uniform_array_type(self, children, meta):
        node = ArrayType(SourceRef.fromMeta(self.schemaFile, meta))
        node.quals = self._popOptionalQualList(children, 0)
        node.elemType = self._popTypeNode(children)
        assert len(children) == 0
        self._setParent(node.quals, node)
        self._setParent(node.elemType, node)
        return node

    @v_args(meta=True)
    def pattern_array_type(self, children, meta):
        node = ArrayType(SourceRef.fromMeta(self.schemaFile, meta))
        node.quals = self._popOptionalQualList(children, 0)
        if len(children) != 0:
            node.elemTypePattern = self._popTree(children, expectedName='linear_type_pattern').children
            assert len(children) == 0
        else:
            node.elemTypePattern = []
        self._attachDocsToNodes(node.elemTypePattern)
        # TODO: normalize patterns with single unnamed element type to uniform arrays with range constraints?? 
        self._setParent(node.quals, node)
        self._setParent(node.elemTypePattern, node)
        return node

    @v_args(meta=True)
    def uniform_list_type(self, children, meta):
        node = ListType(SourceRef.fromMeta(self.schemaFile, meta))
        node.quals = self._popOptionalQualList(children, 0)
        node.elemType = self._popTypeNode(children)
        assert len(children) == 0
        self._setParent(node.quals, node)
        self._setParent(node.elemType, node)
        return node

    @v_args(meta=True)
    def pattern_list_type(self, children, meta):
        node = ListType(SourceRef.fromMeta(self.schemaFile, meta))
        node.quals = self._popOptionalQualList(children, 0)
        if len(children) != 0:
            node.elemTypePattern = self._popTree(children, expectedName='linear_type_pattern').children
            assert len(children) == 0
        else:
            node.elemTypePattern = []
        self._attachDocsToNodes(node.elemTypePattern)
        # TODO: normalize patterns with single unnamed element type to uniform arrays with range constraints?? 
        self._setParent(node.quals, node)
        self._setParent(node.elemTypePattern, node)
        return node

    @v_args(meta=True)
    def named_ltp_elem(self, children, meta):
        (name, nameSourceRef) = self._popName(children)
        quals = self._popOptionalQualList(children, 0)
        node = self.unnamed_ltp_elem(children, meta)
        node.name = name
        node.nameSourceRef = nameSourceRef
        node.quals = quals
        self._setParent(node.quals, node)
        return node
    
    @v_args(meta=True)
    def unnamed_ltp_elem(self, children, meta):
        node = LinearTypePatternElement()
        node.type = self._popTypeNode(children)
        node.sourceRef = copy.copy(node.type.sourceRef)
        if len(children) == 1:
            (node.lowerBound, node.upperBound, quantSourceRef) = self._popQuantifier(children)
            node.sourceRef.setEnd(quantSourceRef)
        else:
            node.lowerBound = 1
            node.upperBound = 1
        assert len(children) == 0
        self._setParent(node.type, node)
        return node

    @v_args(meta=True)
    def referenced_type(self, children, meta):
        node = ReferencedType(SourceRef.fromMeta(self.schemaFile, meta))
        (node.targetName, unused) = self._popName(children, allowScopedName=True)
        assert len(children) == 0
        return node

    # ----- private methods
    
    def _parseInt(self, valStr, desc='integer', sourceRef=None):
        try:
            return int(valStr, 0)
        except ValueError: 
            raise WeaveTLVSchemaError('Invalid %s value: %s' % (desc, valStr), sourceRef=sourceRef)

    def _parseDecimal(self, valStr, desc='decimal', sourceRef=None):
        try:
            val = Decimal(valStr)
        except ValueError:
            raise WeaveTLVSchemaError('Invalid %s value: %s' % (desc, valStr), sourceRef=sourceRef)
        # normalize to int if possible
        intVal = int(val)
        if intVal == val:
            val = intVal
        return val

    def _popName(self, children, allowScopedName=False):
        nameTree = self._popTree(children, 'name')
        nameSourceRef = SourceRef.fromMeta(self.schemaFile, nameTree.meta)
        nameComponents = []
        for nameToken in nameTree.children:
            assert isinstance(nameToken, Token)
            if nameToken.type == 'UNQUOTED_NAME':
                nameComponents.append(nameToken.value)
            else:
                assert nameToken.type == 'QUOTED_NAME'
                assert nameToken.value[0] == '"' and nameToken.value[-1] == '"'
                nameComponents.append(nameToken.value[1:-1])
        nameVal = '.'.join(nameComponents)
        if len(nameComponents) > 1 and not allowScopedName:
            raise WeaveTLVSchemaError(msg='Invalid name: %s' % (nameVal),
                                      detail='Scoped name not allowed in this context',
                                      sourceRef=nameSourceRef)
        return (nameVal, nameSourceRef)

    def _popOptionalQualList(self, children, pos=0):
        if len(children) > pos and isinstance(children[pos], Tree) and children[pos].data == 'qualifier_list':
            return children.pop(pos).children
        else:
            return []

    def _popQuantifier(self, children):
        assert len(children) > 0 and isinstance(children[0], Tree)
        quantNode = children.pop(0)
        sourceRef = SourceRef.fromMeta(self.schemaFile, quantNode.meta)
        name = quantNode.data
        if name == 'quant_0_or_1':
            return (0, 1, sourceRef)
        if name == 'quant_0_or_more':
            return (0, None, sourceRef)
        if name == 'quant_1_or_more':
            return (1, None, sourceRef)
        if name == 'quant_exactly_n':
            (n, unused) = self._popInt(quantNode.children, desc='quantifier')
            assert len(quantNode.children) == 0
            return (n, n, sourceRef)
        assert name == 'quant_range'
        (n, unused) = self._popInt(quantNode.children, desc='quantifier')
        (m, unused) = self._popInt(quantNode.children, desc='quantifier')
        assert len(quantNode.children) == 0
        return (n, m, sourceRef)

    def _popOptionalDocs(self, children, pos=0):
        if len(children) > pos and isinstance(children[pos], Token) and (children[pos].type == 'DOCS' or children[pos].type == 'POSTFIX_DOCS'):
            docsToken = children.pop(pos)
            docsSourceRef = SourceRef.fromToken(self.schemaFile, docsToken)
            return (docsToken.value, docsSourceRef)
        else:
            return (None, None)

    def _popTypeNode(self, children):
        assert len(children) > 0 and isinstance(children[0], TypeNode)
        return children.pop(0)
    
    def _popTree(self, children, expectedName):
        assert len(children) > 0 and isinstance(children[0], Tree) and children[0].data == expectedName
        return children.pop(0)
    
    def _popToken(self, children, expectedName):
        assert len(children) > 0 and isinstance(children[0], Token) and children[0].type == expectedName
        return children.pop(0)

    def _popInt(self, children, desc='integer'):
        valToken = self._popToken(children, 'INT')
        sourceRef = SourceRef.fromToken(self.schemaFile, valToken)
        val = self._parseInt(valToken, desc=desc, sourceRef=sourceRef)
        return (val, sourceRef)

    def _popIntOrDecimal(self, children, desc='numeric'):
        assert len(children) > 0 and isinstance(children[0], Token)
        valToken = children.pop(0)
        sourceRef = SourceRef.fromToken(self.schemaFile, valToken)
        if valToken.type == 'INT':
            val = self._parseInt(valToken, desc=desc, sourceRef=sourceRef)
        else:
            assert valToken.type == 'DECIMAL' 
            val = self._parseDecimal(valToken, desc=desc, sourceRef=sourceRef)
        return (val, sourceRef)
        
    def _newSimpleTypeNode(self, nodeType, children, meta):
        node = nodeType()
        node.sourceRef = SourceRef.fromMeta(self.schemaFile, meta)
        node.quals = self._popOptionalQualList(children, 0)
        assert len(children) == 0
        self._setParent(node.quals, node)
        return node

    def _newIntTypeNode(self, nodeType, children, meta):
        node = nodeType()
        node.sourceRef = SourceRef.fromMeta(self.schemaFile, meta)
        node.quals = self._popOptionalQualList(children, 0)
        if len(children) == 1:
            node.values = self._popTree(children, expectedName='enum_def').children
            self._attachDocsToNodes(node.values)
        else:
            assert len(children) == 0
            node.values = []
        self._setParent(node.quals, node)
        self._setParent(node.values, node)
        return node

    def _setParent(self, nodeOrNodes, parent):
        if nodeOrNodes is not None:
            if isinstance(nodeOrNodes, SchemaNode):
                nodeOrNodes.parent = parent
            else:
                for node in nodeOrNodes:
                    assert isinstance(node, SchemaNode)
                    node.parent = parent
        
    def _attachDocsToNodes(self, nodes):
        
        # Iterate through the given items, which are expected to be a mix of SchemaNodes
        # and LARK tokens matching documentation comments (DOCS or POSTFIX_DOCS).  Whenever
        # a documentation token is encountered, remove it from the list and attach the
        # associated text to the next/previous SchemaNode, but only if that node implements
        # the HasDocumentation mixin.  If the node does not allow documentation, or if there
        # is no next/previous node, simply ignore the documentation token (which is fitting,
        # as it is styled as a comment).
        # 
        i = 0;
        while i < len(nodes):
            if isinstance(nodes[i], Token):
                tokenName = nodes[i].type
                if tokenName == 'DOCS':
                    (docs, docsSourceRef) = self._popOptionalDocs(nodes, pos=i)
                    if len(nodes) > i and isinstance(nodes[i], HasDocumentation):
                        nodes[i].docs = docs
                        nodes[i].docsSourceRef = docsSourceRef
                    continue
                if tokenName == 'POSTFIX_DOCS':
                    (docs, docsSourceRef) = self._popOptionalDocs(nodes, pos=i)
                    if len(nodes) > 0 and isinstance(nodes[i-1], HasDocumentation):
                        # TODO: maybe throw error if both docs and postfix_docs present?
                        nodes[i-1].docs = docs
                        nodes[i-1].docsSourceRef = docsSourceRef
                    continue
            i += 1

