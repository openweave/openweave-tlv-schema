#!/usr/bin/env python3

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
#         Package init file for openweave.tlv.schema.tests.
#


'''Implements unit test for Weave TLV Schema APIs.'''


from .test_ARRAY import Test_ARRAY
from .test_CHOICE import Test_CHOICE
from .test_INTEGER import Test_INTEGER
from .test_LIST import Test_LIST
from .test_MESSAGE import Test_MESSAGE
from .test_PROFILE import Test_PROFILE
from .test_qualifiers import Test_Qualifiers
from .test_STATUS_CODE import Test_STATUS_CODE
from .test_STRUCTURE import Test_STRUCTURE
from .test_syntax import Test_Syntax
from .test_tags import Test_Tags
from .test_VENDOR import Test_VENDOR
