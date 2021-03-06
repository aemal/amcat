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

import logging
import json
import re
from itertools import chain

from amcat.scripts.query.queryaction import NotInCacheError
from django.core.exceptions import ValidationError
from django.forms import ChoiceField, BooleanField, ModelChoiceField

from .aggregation import AggregationEncoder, aggregation_to_matrix, aggregation_to_csv
from amcat.models import CodedArticle
from amcat.models import CodingSchemaField, Code, CodingValue, Coding
from amcat.models import Medium, ArticleSet, CodingJob
from amcat.models.coding.codingschemafield import  FIELDTYPE_IDS
from amcat.scripts.forms.selection import get_all_schemafields
from amcat.scripts.query import QueryAction, QueryActionForm
from amcat.scripts.query.aggregation import AGGREGATION_FIELDS
from amcat.tools import aggregate_orm, aggregate_es
from amcat.tools.aggregate_orm import ORMAggregate
from amcat.tools.aggregate_orm.categories import POSTGRES_DATE_TRUNC_VALUES
from amcat.tools.keywordsearch import SelectionSearch, SearchQuery

log = logging.getLogger(__name__)


CODINGSCHEMAFIELD_RE = re.compile("^codingschemafield\((?P<id>[0-9]+)\)$")
AVERAGE_CODINGSCHEMAFIELD_RE = re.compile("^avg\((?P<id>[0-9]+)\)$")

MEDIUM_ERR = "Could not find medium with id={column} or name={column}"


def get_schemafield_choices(codingjobs, values=True):
    schemafields = get_all_schemafields(codingjobs).order_by("label").only("id", "label")
    article_fields = schemafields.filter(codingschema__isarticleschema=True)
    sentence_fields = schemafields.filter(codingschema__isarticleschema=False)

    for src, fields in [("Article field", article_fields), ("Sentence field", sentence_fields)]:
        category_fields = list(get_category_fields(fields))
        if category_fields:
            yield src, category_fields

def get_category_fields(fields):
    for field in fields:
        if field.fieldtype_id  == FIELDTYPE_IDS.CODEBOOK:
            yield "codingschemafield(%s)" % field.id, field.label

def get_average_fields(fields):
    for field in fields:
        if field.fieldtype_id in (FIELDTYPE_IDS.INT, FIELDTYPE_IDS.QUALITY):
            yield "avg(%s)" % field.id, "Average %s" % field.label

def get_value_fields(fields):
    yield "Average", list(get_average_fields(fields))
    yield "Count", [
        ("count(articles)", "Number of articles"),
        ("count(codings)", "Number of codings"),
        ("count(codingvalues)", "Number of coding values")
    ]


class CodingAggregationActionForm(QueryActionForm):
    primary_use_codebook = BooleanField(initial=False, required=False, label="Group codings using codebook")
    primary_group_mediums = ModelChoiceField(queryset=Medium.objects.all(), label="Group mediums using", required=False)
    primary = ChoiceField(choices=AGGREGATION_FIELDS, label="Aggregate on (primary)")
    primary_fill_zeroes = BooleanField(initial=True, required=False, label="Show empty dates as 0 (if interval selected)")

    secondary_use_codebook = BooleanField(initial=False, required=False, label="Group codings using codebook")
    secondary_group_mediums = ModelChoiceField(queryset=Medium.objects.all(), label="Group mediums using", required=False)
    secondary = ChoiceField(choices=(("", "------"),) + AGGREGATION_FIELDS, required=False, label="Aggregate on (secondary)")

    value1 = ChoiceField(label="First value", initial="count(articles)")
    value2 = ChoiceField(label="Second value", required=False, initial="")

    def __init__(self, *args, **kwargs):
        super(CodingAggregationActionForm, self).__init__(*args, **kwargs)

        assert self.codingjobs
        assert self.schemafields is not None

        value_choices = tuple(get_value_fields(self.schemafields))
        self.fields["value1"].choices = value_choices
        self.fields["value2"].choices = (("", "------"),) + value_choices

        schema_choices = tuple(get_schemafield_choices(self.codingjobs))
        self.fields["primary"].choices += schema_choices
        self.fields["secondary"].choices += schema_choices

        project_codebooks = self.project.get_codebooks()
        self.fields["primary_group_mediums"].queryset = project_codebooks
        self.fields["secondary_group_mediums"].queryset = project_codebooks

    def _clean_aggregation(self, field_name, prefix=None):
        field_value = self.cleaned_data[field_name]

        if not field_value:
            return None

        if field_value in POSTGRES_DATE_TRUNC_VALUES:
            return aggregate_orm.IntervalCategory(field_value, prefix=prefix)

        if field_value == "medium":
            codebook = self.cleaned_data["{}_group_mediums".format(field_name)]
            return aggregate_orm.MediumCategory(prefix=prefix, codebook=codebook, create_missing=True)

        if field_value == "articleset":
            return aggregate_orm.ArticleSetCategory(prefix=prefix)

        if field_value == "term":
            return aggregate_orm.TermCategory()

        # Test for schemafield
        match = CODINGSCHEMAFIELD_RE.match(field_value)
        if match:
            codingschemafield_id = int(match.groupdict()["id"])
            codingschemafield = CodingSchemaField.objects.get(id=codingschemafield_id)
            use_codebook = self.cleaned_data["{}_use_codebook".format(field_name)]
            codebook = codingschemafield.codebook if use_codebook else None
            return aggregate_orm.SchemafieldCategory(codingschemafield, codebook=codebook, prefix=prefix)

        raise ValidationError("Not a valid aggregation: %s." % field_value)

    def clean_primary(self):
        return self._clean_aggregation("primary", prefix="1")

    def clean_secondary(self):
        return self._clean_aggregation("secondary", prefix="3")

    def _clean_value(self, field_name, prefix=None):
        field_value = self.cleaned_data[field_name]

        if not field_value:
            return None

        if field_value == "count(articles)":
            return aggregate_orm.CountArticlesValue(prefix=prefix)

        if field_value == "count(codings)":
            return aggregate_orm.CountCodingsValue(prefix=prefix)

        if field_value == "count(codingvalues)":
            return aggregate_orm.CountCodingValuesValue(prefix=prefix)

        match = AVERAGE_CODINGSCHEMAFIELD_RE.match(field_value)
        if match:
            codingschemafield_id = int(match.groupdict()["id"])
            codingschemafield = CodingSchemaField.objects.get(id=codingschemafield_id)
            return aggregate_orm.AverageValue(codingschemafield, prefix=prefix)

        raise ValidationError("Not a valid value: %s." % field_value)

    def clean_value1(self):
        return self._clean_value("value1", prefix="2")

    def clean_value2(self):
        return self._clean_value("value2", prefix="4")

    def clean(self):
        output_type = self.cleaned_data["output_type"]
        primary = self.cleaned_data["primary"]
        secondary = self.cleaned_data["secondary"]
        value2 = self.cleaned_data["value2"]

        if primary and secondary and value2 and output_type != "text/json+aggregation+table":
            error_msg =  "When selecting two aggregations (primary and secondary), "
            error_msg += "you can only select one value."
            raise ValidationError(error_msg)

        return self.cleaned_data

def to_sortable_tuple(key):
    if isinstance(key, tuple):
        return tuple(map(to_sortable_tuple, key))
    elif isinstance(key, (Medium, ArticleSet, CodingJob)):
        return key.name.lower()
    elif isinstance(key, (Code, SearchQuery)):
        return key.label.lower()
    return key


def get_code_filter(codebook, codes, include_descendants):
    code_ids = set(code.id for code in codes)

    for code_id in code_ids:
        yield code_id

    if include_descendants:
        codebook.cache()
        flat_tree = chain.from_iterable(t.get_descendants() for t in codebook.get_tree())
        flat_tree = chain(flat_tree, codebook.get_tree())
        tree_items = [t for t in flat_tree if t.code_id in code_ids]

        for tree_item in tree_items:
            for descendant in tree_item.get_descendants():
                yield descendant.code_id


class CodingAggregationAction(QueryAction):
    output_types = (
        ("text/json+aggregation+barplot", "Bar plot"),
        ("text/json+aggregation+table", "Table"),
        ("text/json+aggregation+scatter", "Scatter plot"),
        ("text/json+aggregation+line", "Line plot"),
        ("text/json+aggregation+heatmap", "Heatmap"),
        ("text/csv", "CSV (Download)"),
    )
    form_class = CodingAggregationActionForm


    def run(self, form):
        self.monitor.update(1, "Executing query..")
        selection = SelectionSearch(form)
        try:
            aggregation, primary, secondary, categories, values = self.get_cache()
        except NotInCacheError:
            narticles = selection.get_count()
            self.monitor.update(10, "Found {narticles} articles. Aggregating..".format(**locals()))

            # Get aggregation
            codingjobs = form.cleaned_data["codingjobs"]
            primary = form.cleaned_data['primary']
            secondary = form.cleaned_data['secondary']
            value1 = form.cleaned_data['value1']
            value2 = form.cleaned_data['value2']

            article_ids = selection.get_article_ids()

            # This should probably happen in SelectionForm?
            coded_articles = CodedArticle.objects.all()
            coded_articles = coded_articles.filter(article__id__in=article_ids)
            coded_articles = coded_articles.filter(codingjob__id__in=codingjobs)

            coded_article_ids = set(coded_articles.values_list("id", flat=True))
            for field_name in ("1", "2", "3"):
                if not coded_article_ids:
                    break

                schemafield = form.cleaned_data["codingschemafield_{}".format(field_name)]
                schemafield_values = form.cleaned_data["codingschemafield_value_{}".format(field_name)]
                schemafield_include_descendants = form.cleaned_data["codingschemafield_include_descendants_{}".format(field_name)]

                if schemafield and  schemafield_values:
                    code_ids = get_code_filter(schemafield.codebook, schemafield_values, schemafield_include_descendants)
                    coding_values = CodingValue.objects.filter(coding__coded_article__id__in=coded_article_ids)
                    coding_values = coding_values.filter(field__id=schemafield.id)
                    coding_values = coding_values.filter(intval__in=code_ids)
                    coded_article_ids &= set(coding_values.values_list("coding__coded_article__id", flat=True))

            codings = Coding.objects.filter(coded_article__id__in=coded_article_ids)

            terms = selection.get_article_ids_per_query()
            orm_aggregate = ORMAggregate(codings, flat=False, terms=terms)
            categories = list(filter(None, [primary, secondary]))
            values = list(filter(None, [value1, value2]))
            aggregation = orm_aggregate.get_aggregate(categories, values)
            aggregation = sorted(aggregation, key=to_sortable_tuple)

            self.set_cache([aggregation, primary, secondary, categories, values])
        else:
            self.monitor.update(10, "Found in cache. Rendering..".format(**locals()))

        if form.cleaned_data.get("primary_fill_zeroes") and hasattr(primary, 'interval'):
            aggregation = list(aggregate_es.fill_zeroes(aggregation, primary, secondary))
        # Matrices are very annoying to construct in javascript due to missing hashtables. If
        # the user requests a table, we thus first convert it to a different format which should
        # be easier to render.
        if form.cleaned_data["output_type"] == "text/json+aggregation+table":
            aggregation = aggregation_to_matrix(aggregation, categories)

        if form.cleaned_data["output_type"] == "text/csv":
            return aggregation_to_csv(aggregation, categories, values)

        self.monitor.update(60, "Serialising..".format(**locals()))
        return json.dumps(aggregation, cls=AggregationEncoder, check_circular=False)


class AggregationColumnAction(QueryAction):
    pass
