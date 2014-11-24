# #########################################################################
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
from amcat.tools.keywordsearch import SelectionSearch
from .aggregation import AggregationActionForm
from amcat.scripts.query import QueryAction
from api.rest.get_token import get_token
import pyRserve

def tl(**d):
    "Create an R list (TaggedList) from a dictionary"
    return pyRserve.TaggedList(d.items())

class RAggregationAction(QueryAction):
    """
    Aggregate articles based on their properties. Make sure x_axis != y_axis.
    """
    output_types = (
        ("text/json+aggregation+table", "Table"),
        ("text/json+aggregation+graph", "Graph"),
        ("text/json+aggregation+heatmap", "Heatmap"),
        ("text/csv", "CSV (Download)"),
    )
    form_class = AggregationActionForm

    def run(self, form):
        filters = dict( SelectionSearch(form).get_filters())
        token = get_token(self.user).key
        replace = lambda d: form.cleaned_data['interval'] if d == 'date' else d
        x = replace(form.cleaned_data["x_axis"])
        y = replace(form.cleaned_data["y_axis"])
        self.monitor.update(1, "Connecting to R..")

        R = pyRserve.connect()
        try:
            self.monitor.update(10, "Performing query..")
            return R.r.aggregation_r("http://localhost:8000", token, x, y, tl(**filters))
        finally:
            R.close() #They claim it autocloses, but it doesn't seem to
