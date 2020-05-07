#
#   Copyright (c) 2020 Google LLC.
#   All rights reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

'''
Classes for generating code based on Weave TLV Schemas.
'''

import os
import io
import re
import textwrap
from string import Formatter
import yaml

from .node import *

class CodeGenBase(object):
    '''Base class for objects that generate code based on Weave TLV Schemas'''
    
    def __init__(self, schema, outStream, config=None, templateFormatter=None):
        self.schema = schema
        self.outStream = outStream
        if config is None:
            defaultConfig = self._defaultConfig.copy()
            templates = defaultConfig['templates']
            for (name, val) in templates.items():
                templates[name] = textwrap.dedent(val)
            config = Config(defaultConfig)
        self.config = config
        if templateFormatter is None:
            templateFormatter = TemplateFormatter(self, config)
        self.templateFormatter = templateFormatter
        self._curNamespaceName = None
    
    def _isInTargetNamespace(self, node):
        targetNSList = self.config.getValue('target-namespaces')
        if targetNSList:
            if isinstance(node, Namespace):
                nodeNS = node.fullyQualifiedName
            else:
                nodeNS = node.namespaceName
            for targetNS in targetNSList:
                if nodeNS == targetNS or (nodeNS.startswith(targetNS) and nodeNS[len(targetNS)] =='.'):
                    return True
            return False
        else:
            return True

    def _translateName(self, schemaName, configContext=None, prefix='', capitalize=True):
        nameTranslations = self.config.getValue('name-translations', context=configContext)
        if nameTranslations is not None:
            for (match, sub) in nameTranslations.items():
                if schemaName == match:
                    return sub
        nameSplitPattern = self.config.getValue('name-split-pattern', context=configContext)
        words = re.split(nameSplitPattern, schemaName)
        if len(words) > 1 and len(words[0]) == 0:
            prefix = prefix + '_'
            words = words[1:]
        for i in range(len(words)):
            newWord = self._translateNameWord(words[i], configContext=configContext)
            if i > 0 or capitalize:
                newWord = self._capitalize(newWord)
            words[i] = newWord
        return prefix + ''.join(words)

    def _translateNameWord(self, word, configContext=None):
        wordTranslations = self.config.getValue('word-translations', context=configContext)
        if wordTranslations is not None:
            for (match, sub) in wordTranslations.items():
                if word == match:
                    return sub
        return word

    def _capitalize(self, s):
        if len(s) > 0:
            return s[0].capitalize() + s[1:]
        else:
            return s

    def _translateNamespace(self, nsName):
        if nsName is not None:
            nsNames = nsName.split('.')
            for i in range(len(nsNames)):
                leadingNSName = '.'.join(nsNames[:i])
                nsNames[i] = self._translateName(nsNames[i], configContext=leadingNSName, capitalize=True)
            nsPrefix = self.config.getValue('namespace-prefix')
            if nsPrefix:
                nsNames.insert(0, nsPrefix)
            return '.'.join(nsNames)
        return nsName

    def _write(self, s):
        if isinstance(s, list):
            for i in s:
                self._write(i)
        else:
            self.outStream.write(s)

    def _writeTemplate(self, templateName, configContext='', params=None):
        s = self.templateFormatter.format(templateName, configContext, params)
        self._write(s)

    def _getTemplateParam(self, name):
        return None

    def _writeStartEndNamespace(self, newNSName):
        newNSName = self._translateNamespace(newNSName)
        if self._curNamespaceName != newNSName:
            curNSNames = self._curNamespaceName.split('.') if self._curNamespaceName else []
            curNSCount = len(curNSNames)
            newNSNames = newNSName.split('.') if newNSName else []
            newNSCount = len(newNSNames)
            commonCount = 0
            while commonCount < curNSCount and commonCount < newNSCount:
                if curNSNames[commonCount] != newNSNames[commonCount]:
                    break
                commonCount += 1
            for nsName in reversed(curNSNames[commonCount:]):
                self._writeTemplate('namespace-end',
                                    params={
                                        'ns-name' : nsName })
            if commonCount < curNSCount and newNSCount > commonCount:
                self._write('\n')
            for nsName in newNSNames[commonCount:]:
                self._writeTemplate('namespace-start',
                                    params={
                                        'ns-name' : nsName })
            self._write('\n')
            self._curNamespaceName = newNSName

    _defaultConfig = { }
            

class Config(object):
    '''Contains configuration information used during code generation.'''
    
    def __init__(self, defaultConfig=None):
        self.configSets = {}
        if defaultConfig is not None:
            self.configSets[''] = defaultConfig.copy()
    
    def loadConfigFromFile(self, fileName):
        with open(fileName) as file:
            self.loadConfigFromStream(file)
        
    def loadConfigFromStream(self, stream):
        configValues = yaml.safe_load(stream)
        globalConfigValues = {}
        for (name, val) in configValues.items():
            if name.startswith('(') and name.endswith(')'):
                configSetName = name[1:-1]
                configSet = self.configSets.get(configSetName, None)
                if configSet is None:
                    configSet = {}
                    self.configSets[configSetName] = configSet 
                self._mergeConfig(configSet, val)
            else:
                globalConfigValues[name] = val
        self._mergeConfig(self.configSets[''], globalConfigValues)
    
    def getValue(self, name, context=None, defaultVal=None):
        splitName = name.split('.')
        for val in self._eachConfigSetByContext(context):
            for namePart in splitName:
                if isinstance(val, dict) and namePart in val:
                    val = val[namePart]
                else:
                    break
            else:
                return val
        return defaultVal

    def _mergeConfig(self, dest, src):
        for key in src:
            if key in dest and isinstance(src[key], dict) and isinstance(dest[key], dict):
                self._mergeConfig(dest[key], src[key])
            else:
                dest[key] = src[key]
        
    def _eachConfigSetByContext(self, context):
        if isinstance(context, list):
            for c in context:
                yield from self._eachConfigContext(c)
        else:
            if context is None:
                context = ''
            while True:
                if context in self.configSets:
                    yield self.configSets[context]
                if context == '':
                    break
                if '.' in context:
                    (context, _) = context.rsplit('.', 1)
                else:
                    context = ''


class TemplateFormatter(Formatter):
    '''Generates output text from a template string'''
    
    def __init__(self, codeGen, config):
        self.codeGen = codeGen
        self.config = config
        self._curConfigContext = None
        self._curTemplateName = None

    def format(self, templateName, configContext='', params=None):        
        template = self.config.getValue('templates.' + templateName, configContext)
        if template is None:
            raise KeyError('Template not found: ' + templateName)
        if params is None:
            params = {}
        self._curConfigContext = configContext
        self._curTemplateName = templateName
        try:
            return self.vformat(template, None, params)
        except ValueError as err:
            raise ValueError('%s in template %s' % (err, templateName)) from None
        
    def get_value(self, key, args, params):
        if not isinstance(key, int):
            if key in params:
                return params[key]
            v = self.codeGen._getTemplateParam(key)
            if v is not None:
                return v
            v = self.config.getValue(key, self._curConfigContext)
            if v is not None:
                return v
        else:
            key = '' if key == 0 else str(key)
        raise KeyError('Unable to resolve substitution in template %s: {%s}' % (self._curTemplateName, key))


class DefinitionsHeaderGenerator(CodeGenBase):
    '''Generates a C++ header file containing various numeric values derived from a Weave TLV Schema'''

    def __init__(self, schema, outStream, config=None, templateFormatter=None, outFileName=None):
        super(DefinitionsHeaderGenerator, self).__init__(schema, outStream, config, templateFormatter)
        self.outFileName = outFileName
    
    def generate(self):

        self._writeTemplate('header-start')
        self._writeTemplate('include-guard-start')
        
        # Get the names of all targeted namespaces, in sorted order. 
        targetNSNames = ( n.fullyQualifiedName for n in self.schema.allNodes(Namespace) 
                          if self._isInTargetNamespace(n) )
        targetNSNames = list(set(targetNSNames))
        targetNSNames.sort()
        
        for nsName in targetNSNames:
            
            # If the namespace corresponds to a PROFILE definition...
            profile = self.schema.getProfile(nsName)
            if profile is not None:
                
                # Write the profile id value.
                self._writeStartEndNamespace(nsName)
                self._writeProfileId(profile)

                # Write message type values for any messages associated with the profile.                 
                messages = [ m for m in self.schema.allNodes(Message)
                             if m.namespaceName == nsName ]
                if messages:
                    self._writeMessageTypes(profile, messages)
                    
                # Write any status code values associated with the profile.                 
                statusCodes = [ sc for sc in self.schema.allNodes(StatusCode)
                                if sc.namespaceName == nsName ] 
                if statusCodes:
                    self._writeStatusCodes(profile, statusCodes)

            # Find all Message or TypeDef nodes defined in the current namespace.
            typeNodes = [ n for n in self.schema.allNodes((Message, TypeDef)) 
                          if n.namespaceName == nsName ]
            
            # For each such node ...
            for typeNode in typeNodes:
                
                # Get the tag definitions associated with the node
                tagDefs = self.getTagDefinitions(typeNode)
                
                # Write tag definitions for the numeric values associated with the tags.
                numericTagDefs = [ tagDef for tagDef in tagDefs if not tagDef[1].isAnonTag ]
                if numericTagDefs:
                    self._writeStartEndNamespace(nsName)
                    self._writeTags(typeNode, numericTagDefs)

                # Get the enum definitions associated with the node
                enumDefs = self.getEnumDefinitions(typeNode)

                # Write the enum definitions, if any.                
                if enumDefs:
                    self._writeStartEndNamespace(nsName)
                    self._writeEnums(typeNode, enumDefs)

        # Close out the final C++ namespace
        self._writeStartEndNamespace(None)

        self._writeTemplate('include-guard-end')
        self._writeTemplate('header-end')

    def _writeProfileId(self, node):
        profileDefName = self._translateName(node.name, configContext=node.fullyQualifiedName)
        self._writeTemplate('profile-id-def',
                            configContext=node.fullyQualifiedName,
                            params={
                                'profile-name' : node.name,
                                'profile-def-name' : profileDefName,
                                'profile-id' : node.id })

    def _writeMessageTypes(self, profile, messages):
        # Sort messages by id
        messages.sort(key=lambda m: m.id)
        self._writeTemplate('message-type-section-start',
                            configContext=profile.fullyQualifiedName,
                            params={
                                'profile-name' : profile.name })
        for message in messages:
            messageDefName = self._translateName(message.name, message.fullyQualifiedName)
            self._writeTemplate('message-type-def', 
                                configContext=message.fullyQualifiedName,
                                params={ 
                                    'message-type-def-name' : messageDefName,
                                    'message-type-num' : message.id })
        self._writeTemplate('message-type-section-end', 
                            configContext=profile.fullyQualifiedName,
                            params={
                                'profile-name' : profile.name })
        
    def _writeStatusCodes(self, profile, statusCodes):
        # Sort status codes by numeric value
        statusCodes.sort(key=lambda m: m.id)
        self._writeTemplate('status-code-section-start', 
                            configContext=profile.fullyQualifiedName,
                            params={
                                'profile-name' : profile.name })
        for statusCode in statusCodes:
            messageDefName = self._translateName(statusCode.name, statusCode.fullyQualifiedName)
            self._writeTemplate('status-code-def', 
                                configContext=statusCode.fullyQualifiedName,
                                params={ 
                                    'status-code-def-name' : messageDefName,
                                    'status-code' : statusCode.id })
        self._writeTemplate('status-code-section-end', 
                            configContext=profile.fullyQualifiedName,
                            params={
                                'profile-name' : profile.name })
    
    def _writeTags(self, node, tagDefs):
        tagDefs.sort(key=lambda t: t[0])
        
        self._writeTemplate('tag-section-start', 
                            configContext=node.fullyQualifiedName,
                            params={
                                'type-name' : node.name,
                                'type-construct' : node.targetType.schemaConstruct })
        
        for (tagDefName, tag) in tagDefs:
            if tag.profileId is not None:
                self._writeTemplate('tag-profile-def', 
                                    configContext=node.fullyQualifiedName,
                                    params={ 
                                        'tag-def-name' : tagDefName,
                                        'profile-id' : tag.profileId })

            
            self._writeTemplate('tag-num-def', 
                                configContext=node.fullyQualifiedName,
                                params={ 
                                    'tag-def-name' : tagDefName,
                                    'tag-num' : tag.tagNum })

        self._writeTemplate('tag-section-end',
                            configContext=node.fullyQualifiedName,
                            params={
                                'type-name' : node.name,
                                'type-construct' : node.targetType.schemaConstruct })
    
    def _writeEnums(self, node, enumDefs):
        enumDefs.sort(key=lambda t: t[0])
        for (enumName, enumNode, enumConfigContext, valDefs) in enumDefs:

            self._writeTemplate('enum-section-start', 
                                configContext=enumConfigContext,
                                params={
                                    'enum-name' : enumName,
                                    'enum-construct' : enumNode.schemaConstruct })
        
            valDefs.sort(key=lambda t: t[3])
            for (valName, valNode, valConfigContext, val) in valDefs:
                self._writeTemplate('enum-val-def', 
                                    configContext=valConfigContext,
                                    params={ 
                                        'enum-val-name' : valName,
                                        'enum-val' : val })

            self._writeTemplate('enum-section-end',
                                configContext=enumConfigContext,
                                params={
                                    'enum-name' : enumName,
                                    'enum-construct' : enumNode.schemaConstruct })
    
    def getEnumDefinitions(self, node, enumName=None, configContext=None, enumDefs=None):
        
        if enumName is None:
            enumName = ''

        if configContext is None:
            configContext = node.namespaceName
    
        if enumDefs is None:
            enumDefs = [ ]
        
        # Attempt to get a name for the node. 
        # If the node type has an associated name, use that.
        # If the node is a uniform LIST type, treat it as if it had the
        # name "element".
        # Otherwise, presume it has no name.
        if isinstance(node, HasName):
            name = node.effectiveName
        elif isinstance(node, ListType) and node.isUniform:
            name = 'element'
        else:
            name = None
        
        # If the node has a name...
        if name is not None:

            # Form the configuration context for the node based on its name and the
            # containing config context.
            if configContext == '':
                configContext = name
            else:
                configContext = configContext + '.' + name

            # Translate the node's name into a suitable form for code.
            translatedName = self._translateName(name, configContext)

            # Form the full tag name for the node based on the translated name and containing
            # tag name.
            if enumName == '':
                enumName = translatedName
            else:
                enumName = enumName + '_' + translatedName

        # if the node is an IntegerType that has enumerated values...
        if isinstance(node, IntegerTypeNode) and len(node.values) > 0:
            
            valDefs = []
            
            # For each enumerated value associated with the integer...
            for valNode in node.values:
                
                # Form the configuration context for the value.
                valConfigContext = configContext + '.' + valNode.name

                # Translate the value's name into a suitable form for code.
                translatedValName = self._translateName(valNode.name, valConfigContext)

                # Generate a value definition.
                valDefs.append((enumName + '_' + translatedValName,
                                valNode,
                                valConfigContext,
                                valNode.value))
            
            # Generate the enum definition.
            enumDefs.append((enumName, node, configContext, valDefs))
            
        # Recurse into all child nodes of the current node.
        for childNode in node.allChildNodes():
            self.getEnumDefinitions(childNode, enumName, configContext, enumDefs)

        return enumDefs
        
    
    def getTagDefinitions(self, node, tagName=None, configContext=None, topNode=None, tagDefs=None):

        if tagName is None:
            tagName = ''

        if configContext is None:
            configContext = node.namespaceName
    
        if topNode is None:
            topNode = node
            
        if tagDefs is None:
            tagDefs = [ ]

        # Attempt to get a name for the node. 
        # If the node type has an associated name, use that.
        # If the node is a uniform LIST type, treat it as if it had the
        # name "element".
        # Otherwise, presume it has no name.
        if isinstance(node, HasName):
            name = node.effectiveName
        elif isinstance(node, ListType) and node.isUniform:
            name = 'element'
        else:
            name = None
        
        # If the node has a name...
        if name is not None:

            # Form the configuration context for the node based on its name and the
            # containing config context.
            if configContext == '':
                configContext = name
            else:
                configContext = configContext + '.' + name

            # Translate the node's name into a suitable form for code.
            translatedName = self._translateName(name, configContext)

            # Form the full tag name for the node based on the translated name and containing
            # tag name.
            if tagName == '':
                tagName = translatedName
            else:
                tagName = tagName + '_' + translatedName

        tag = None

        # If the node is a List type...
        if isinstance(node, ListType):
            
            # If the list is a uniform list whose underlying type is a reference to a
            # type definition with a default tag, generate a tag definition for the list's
            # element.  Based on the code above, this tag will have the name "element".
            if node.isUniform and isinstance(node.elemType, ReferencedType):
                tag = node.elemType.effectiveTag

        # If the node is one that can have an assigned tagged...
        elif isinstance(node, HasTag):
            
            # Generate a definition for the assigned tag, if present. If no assigned tag is
            # present, but the node's underlying type is a reference to a type definition
            # with a default tag, generate a definition based on the default tag.            
            tag = node.tag
            if tag is None and isinstance(node, HasType) and isinstance(node.type, ReferencedType):
                tag = node.type.effectiveTag
            
            # If the node is a ChoiceAlternate, suppress generation of the tag definition
            # if the containing ChoiceType is a child of some other node that determines the
            # alternate's tag (e.g. if the ChoiceType exists within a StructureField that declares
            # a tag). 
            if isinstance(node, ChoiceAlternate):
                for parent in node.allParentNodes():
                    if isinstance(parent, HasTag) and parent.tag is not None:
                        tag = None # suppress tag definition
                        break
                    if parent == topNode or not isinstance(parent, (ChoiceType, ChoiceAlternate)):
                        break

        # Generate the tag definition, as necessary.
        if tag is not None:
            tagDefs.append((tagName, tag))
        
        # Recurse into all child nodes of the current node.
        for childNode in node.allChildNodes():
            self.getTagDefinitions(childNode, tagName, configContext, topNode, tagDefs)

        return tagDefs

    def _getTemplateParam(self, name):
        if name == 'output-file-name':
            if self.outFileName:
                return os.path.basename(self.outFileName)
            else:
                return None
        if name == 'include-guard-name':
            if self.outFileName:
                guardName = self.outFileName
            else:
                guardName = self.schema.schemaFiles[-1].fileName
            guardName = os.path.basename(guardName)
            (guardName, _) = os.path.splitext(guardName)
            guardName = re.sub('\W+', '_', guardName)
            guardName = guardName.upper() + '_H'
            return guardName
        return CodeGenBase._getTemplateParam(self, name)

    _defaultConfig = {
        'name-split-pattern' : r'''[_-]+''',
    
        'indent' : '    ',
        
        'templates' : {

            'header-start' : """\
               /*
                *      This file was auto-generated by weave-tlv-schema.
                */

                """,
                
            'header-end' : '',
            
            'include-guard-start' : """\
                #ifndef {include-guard-name}
                #define {include-guard-name}
                
                """,
                
            'include-guard-end' : """\
                #endif // {include-guard-name}
                """,

            'namespace-start' : 'namespace {ns-name} {{\n',
            
            'namespace-end' : '}} // namespace {ns-name}\n',
            
            'profile-id-def' : """\
                /** Profile id for {profile-name}
                 */
                enum
                {{
                {indent}kProfileId_{profile-def-name} = 0x{profile-id:08X}
                }}

                """,

            'message-type-section-start' : """\
                /** Message types for {profile-name} profile
                 */
                enum
                {{
                """,

            'message-type-def' : '{indent}kMsgType_{message-type-def-name} = {message-type-num},\n',
            
            'message-type-section-end' : "}}\n\n",
            
            'status-code-section-start' : """\
                /** Status codes for {profile-name} profile
                 */
                enum
                {{
                """,

            'status-code-def' : '{indent}kStatusCode_{status-code-def-name} = {status-code},\n',
            
            'status-code-section-end' : "}}\n\n",
            
            'tag-section-start' : """\
                /** Tag values for {type-name} ({type-construct})
                 */
                enum
                {{
                """,
            
            'tag-section-end' : "}}\n\n",
        
            'tag-num-def' : '{indent}kTagNum_{tag-def-name} = {tag-num},\n',
           
            'tag-profile-def' : '{indent}kTagProfileId_{tag-def-name} = 0x{profile-id:08X},\n',
            
            'enum-section-start' : """\
                /** Enumerated values for {enum-name} ({enum-construct})
                 */
                enum
                {{
                """,

            'enum-val-def' : '{indent}kEnumVal_{enum-val-name} = {enum-val},\n',

            'enum-section-end' : "}}\n\n",
        },
    }

