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
#      Weave TLV Schema errors. 
#

import os

class WeaveTLVSchemaError(Exception):
    def __init__(self, msg, detail=None, sourceRef=None):
        super(WeaveTLVSchemaError, self).__init__(msg)
        self.detail = detail
        self.sourceRef = sourceRef
        
    def format(self, withTextMarker=True, withDetail=True):
        res = 'ERROR: ' + str(self)
        if withDetail and self.detail is not None:
            res = res + "\nNOTE: " + self.detail
        if self.sourceRef:
            res = '%s: %s' % (self.sourceRef.filePosStr(), res)
            if withTextMarker:
                res += '\n\n' + self.sourceRef.lineSummaryStr()
        return res
    
class AmbiguousTagError(Exception):
    pass
