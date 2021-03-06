###########################################################################
#          (C) Vrije Universiteit, Amsterdam (the Netherlands)            #
#                                                                         #
# This file is part of AmCAT - The Amsterdam Content Analysis Toolkit     #
#                                                                         #
# AmCAT is free software: you can redistribute it and/or modify it under  #
# the terms of the GNU Affero General Public License as published by the  #
# Free Software Foundation, either version 3 of the License, or (at your  #
# option) any later version.                                              #
#                                                                         #
# AmCAT is distributed in the hope that it will be useful, but WITHOUT    #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or   #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public     #
# License for more details.                                               #
#                                                                         #
# You should have received a copy of the GNU Affero General Public        #
# License along with AmCAT.  If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

"""
Configuration options to change how AmCAT uses elastic
"""
import os
import sys

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

# Host/port on which elastic can be reached:
ES_HOST = os.environ.get("AMCAT_ES_HOST", 'localhost')
ES_PORT = os.environ.get("AMCAT_ES_PORT", 9200)

# Emulate Django behaviour by prepending index name with 'test_' if running
ES_TEST_INDEX = "test_amcat"
ES_PROD_INDEX = "amcat"

ES_INDEX = os.environ.get('AMCAT_ES_INDEX', ES_TEST_INDEX if TESTING else ES_PROD_INDEX)
ES_ARTICLE_DOCTYPE = 'article'

ES_MAPPING_STRING_OPTIONS = {
    "type": "string",
    "omit_norms": True
}

ES_MAPPING_SIMPLE_STRING_OPTIONS = {
    "type": "string",
    "omit_norms": True,
    "include_in_all": "false"
}

#              TODO: possibly interesting global options to consider
#              "_source" : {"enabled" : false}
#              "_routing" : {"required" : True, "path" : "mediumid"}
#              "_timestamp" : {"enabled" : true, "path" : "date"}

ES_MAPPING = {
    "properties": {
        "id": {"type": "long"},
        "text": ES_MAPPING_STRING_OPTIONS,
        "headline": ES_MAPPING_STRING_OPTIONS,
        "byline": ES_MAPPING_STRING_OPTIONS,
        "medium": ES_MAPPING_SIMPLE_STRING_OPTIONS,
        "creator": ES_MAPPING_SIMPLE_STRING_OPTIONS,
        "section": ES_MAPPING_SIMPLE_STRING_OPTIONS,
        "uuid": ES_MAPPING_SIMPLE_STRING_OPTIONS,
        "page": {"type": "long"},
        "addressee": ES_MAPPING_SIMPLE_STRING_OPTIONS,
        "url": ES_MAPPING_SIMPLE_STRING_OPTIONS,
        "metastring": ES_MAPPING_SIMPLE_STRING_OPTIONS,
        "length": {"type": "long"},
        "externalid": {"type": "long"},
        "date": {
            "type": "date",
            "format": "dateOptionalTime"
        },
        "mediumid": {"type": "long"},
        "projectid": {"type": "long"},
        "parentid": {"type": "long"},
        "sets": {"type": "long"},
        "hash": {
            "type": "string",
            "index": "not_analyzed",
        },
        "uuid": {
            "type": "string",
            "index": "not_analyzed",
        },
    },
}
ES_SETTINGS = {"analysis": {
        "analyzer": {
            "default": {
                "type": "custom",
                "tokenizer": "unicode_letters_digits",
                "filter": [
                    "icu_folding"
                    ]
                }
            },
        "tokenizer": {
            "unicode_letters_digits": {
                "type": "pattern",
                "pattern": "[^\\p{L}\\p{M}\\p{N}]",
                "lowercase": "true"
                }
            }
        }
    }


def _get_use_legacy_hash():
    use = os.environ.get("AMCAT_ES_LEGACY_HASH", None)
    if use is not None:
        return use.strip() in ("1", "Y", "ON")

ES_USE_LEGACY_HASH_FUNCTION = _get_use_legacy_hash()
