#!/usr/bin/env python3ests

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

#
#   @file
#         Tool for working with Weave TLV schemas.
#


import sys
import os
import argparse
from .obj import WeaveTLVSchema

scriptName = os.path.basename(sys.argv[0])

class _UsageError(Exception):
    pass

class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise _UsageError('{0}: {1}'.format(self.prog, message))

class _ValidateCommand(object):
    
    name = 'validate'
    summary = 'Validate the syntax and consistency of a TLV schema'
    help = ('{0} validate : {1}\n'
            '\n'
            'Usage:\n'
            '  {0} validate [options...] {{schema-files...}}\n'
            '\n'
            '  -s|--silent\n'
            '    Do not display results (exit code indicates the number of errors).\n'
        ).format(scriptName, summary)

    def run(self, args):
        argParser = _ArgumentParser(prog='{0} {1}'.format(scriptName, self.name),
                                    add_help=False)
        argParser.add_argument('-s', '--silent', action='store_true')
        argParser.add_argument('files', nargs='*')
        args = argParser.parse_args(args)
        
        if len(args.files) == 0:
            raise _UsageError('{0} {1}: Please specify one or more schema files'.format(scriptName, self.name))
        
        schema = WeaveTLVSchema()
        
        for schemaFileName in args.files:
            if not os.path.exists(schemaFileName):
                raise _UsageError('{0} {1}: Schema file not found: {0}\n'.format(scriptName, self.name, schemaFileName))
            schema.loadSchemaFromFile(schemaFileName)

        errs = schema.validate()
        
        if not args.silent:
            if len(errs) == 0:
                print('Validation completed successfully')
            else:
                detailShown = {}
                for err in errs:
                    withDetail = False
                    if err.detail is not None:
                        withDetail = not detailShown.get(err.detail, False)
                        if withDetail:
                            detailShown[err.detail] = True
                    print("%s\n" % err.format(withDetail=withDetail), file=sys.stderr)
        
        return len(errs)

class _DumpCommand(object):
    
    name = 'dump'
    summary = 'Dump the syntax tree for a TLV schema'
    help = ('{0} dump : {1}\n'
            '\n'
            'Usage:\n'
            '  {0} dump {{schema-files...}}\n'
        ).format(scriptName, summary)

    def run(self, args):
        argParser = _ArgumentParser(prog='{0} {1}'.format(scriptName, self.name),
                                         add_help=False)
        argParser.add_argument('files', nargs='*')
        args = argParser.parse_args(args)
        
        if len(args.files) == 0:
            raise _UsageError('{0} {1}: Please specify one or more schema files'.format(scriptName, self.name))
        
        schema = WeaveTLVSchema()
        
        for schemaFileName in args.files:
            if not os.path.exists(schemaFileName):
                raise _UsageError('{0} {1}: Schema file not found: {0}\n'.format(scriptName, self.name, schemaFileName))
            schema.loadSchemaFromFile(schemaFileName)
            
        for schemaFile in schema.allFiles():
            schemaFile.summarize(sys.stdout)
            
        return 0

class _UnitTestCommand(object):
    
    name = 'unittest'
    summary = 'Run unit tests on the TLV schema code'
    help = ('{0} unittest : {1}\n'
            '\n'
            'Usage:\n'
            '  {0} unittest [options...] [test-names...]\n'
            '\n'
            '  -v|--verbosity [int]\n'
            '    Test progress verbosity (defaults to 2).\n'
        ).format(scriptName, summary)

    def run(self, args):
        argParser = _ArgumentParser(prog='{0} {1}'.format(scriptName, self.name), add_help=False)
        argParser.add_argument('-v', '--verbosity', type=int, default=2)
        argParser.add_argument('testnames', nargs=argparse.REMAINDER, default=[])
        args = argParser.parse_args(args)

        import unittest
        from . import tests
        
        if len(args.testnames) > 0:
            selectedTests = unittest.defaultTestLoader.loadTestsFromNames(args.testnames, module=tests)
        else:
            selectedTests = unittest.defaultTestLoader.loadTestsFromModule(tests)

        runner = unittest.TextTestRunner(verbosity=int(args.verbosity))
        result = runner.run(selectedTests)
        
        return len(result.errors)

class _HelpCommand(object):
    
    name = 'help'
    summary = 'Display usage information'

    @property
    def help(self):
        maxWidth = max((len(c.name) for c in self.availCommands))
        commandSummary = ''.join(( '\n  {0:<{width}} - {1}'.format(c.name, c.summary, width=maxWidth) for c in self.availCommands ))
        return ('{0} : A tool for working with Weave TLV Schemas\n'
                '\n'
                'Usage:\n'
                '  {0} {{command}} [options] ...\n'
                '\n'
                'Available commands:{1}\n'
                '\n'
                'Run "{0} help <command>" for additional help.\n'
            ).format(scriptName, commandSummary)
    
    def __init__(self, availCommands):
        self.availCommands = availCommands

    def run(self, args):
        topic = args[0] if len(args) > 0 else 'help'
        topic = topic.lower()
        for command in self.availCommands:
            if topic == command.name:
                print(command.help)
                break
        else:
            raise _UsageError('Unrecognized help topic: {0}'.format(topic))
        
        return 0

def main():

    try:

        # Construct a list of the available commands.
        commands = [
            _ValidateCommand(),
            _DumpCommand(),
            _UnitTestCommand()
        ]
        commands.append(_HelpCommand(availCommands=commands))

        # Parse the command name argument, along with arguments for the command.
        argParser = _ArgumentParser(prog=scriptName, add_help=False)
        argParser.add_argument('-h', '--help', nargs='?', const='help')
        argParser.add_argument('commandName', nargs='?')
        argParser.add_argument('commandArgs', nargs=argparse.REMAINDER, default=[])
        args = argParser.parse_args()

        # Allow the user to invoke the help command using -h or --help.
        if args.help is not None:
            args.commandName = 'help'
            args.commandArgs = [ args.help ]
        
        # Fail if no command was given.
        if args.commandName is None:
            raise _UsageError('Please specify a command, or run "{0} help" for a list of available commands.'.format(scriptName))

        # Run the specified command.
        commandNameLC = args.commandName.lower()
        for command in commands:
            if commandNameLC == command.name:
                command.run(args.commandArgs)
                break
        else:
            raise _UsageError('Unrecognized command: {1}\nRun "{0} help" for a list of available commands.'.format(scriptName, args.commandName))

    except _UsageError as ex:
        print(str(ex), file=sys.stderr)
        return -1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
