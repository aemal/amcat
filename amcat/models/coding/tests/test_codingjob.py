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
from amcat.models import CodedArticle, CodingJob, create_codingjob_batches
from amcat.tools import amcattest

class TestCodingJob(amcattest.AmCATTestCase):
    def test_create(self):
        """Can we create a codingjob with articles?"""
        from amcat.models.project import Project
        p = amcattest.create_test_project()
        j = amcattest.create_test_job(project=p)
        self.assertIsNotNone(j)
        self.assertEqual(j.project, Project.objects.get(pk=p.id))
        j.articleset.add(amcattest.create_test_article())
        j.articleset.add(amcattest.create_test_article())
        j.articleset.add(amcattest.create_test_article())
        self.assertEqual(1+3, len(j.articleset.articles.all()))

    def test_post_create(self):
        job = amcattest.create_test_job(10)
        self.assertEqual(CodedArticle.objects.filter(codingjob=job).count(), 10)

    def test_create_codingjob_batches(self):
        a = amcattest.create_test_set(10)

        cj = CodingJob()
        cj.project = a.project
        cj.name = "foo"
        cj.unitschema = amcattest.create_test_schema(project=a.project)
        cj.articleschema = amcattest.create_test_schema(isarticleschema=True, project=a.project)
        cj.coder = amcattest.create_test_user()
        cj.insertuser = amcattest.create_test_user()

        arts = a.articles.all().values_list("id", flat=True)

        cjs = create_codingjob_batches(cj, arts, 2)
        self.assertEqual(5, len(cjs))

        cjs = create_codingjob_batches(cj, arts, 3)
        self.assertEqual(4, len(cjs))


