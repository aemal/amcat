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
Model module containing the Article class representing documents in the
articles database table.
"""

from __future__ import unicode_literals, print_function, absolute_import

from amcat.tools.model import AmcatModel
from amcat.models.article import Article

from django.db import models

import logging
log = logging.getLogger(__name__)


class Interaction(AmcatModel):
    """
    Class representing a newspaper article
    """
    id = models.AutoField(primary_key=True)

    article = models.ForeignKey(Article, db_index=True)
    author = models.CharField(max_length=100, db_index=True)
    interaction = models.CharField(max_length=100, db_index=True)


    class Meta():
        db_table = 'articles_interactions'
        app_label = 'amcat'
    
