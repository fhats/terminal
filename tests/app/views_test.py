"""Just a set of basic coverage integration tests for the API.

Might be worth adding more end-to-end tests later, but right now since the API
is small this just tests a few cases vis-a-vis interacting with the database.
"""
import mock
from pyramid import httpexceptions
from pyramid import testing
from sqlalchemy import create_engine
import testify as T

from terminal.app import views
from terminal.db import txn
from terminal import models
from terminal.testing.terminal_test_case import TerminalTestCase


class ViewTestCase(TerminalTestCase):
    """Like a TerminalTestCase, but with a few utilities to make testing views
    more straightforward.
    """

    @T.setup_teardown
    def mock_db(self):
        in_memory_engine = create_engine("sqlite:///:memory:")
        models.metadata.create_all(in_memory_engine)
        with mock.patch('terminal.db.engine', in_memory_engine):
            yield


class DashboardTest(ViewTestCase):

    def test_dashboard_returns_context(self):
        expected_template_context = {}

        template_context = views.dashboard(testing.DummyRequest())

        T.assert_equal(template_context, expected_template_context)


class AdvisoriesTest(ViewTestCase):

    def test_empty_advisories(self):
        expected_advisories = []

        actual_advisories = views.advisories(testing.DummyRequest())

        T.assert_equal(actual_advisories, expected_advisories)

    def test_alert_advisory(self):
        expected_advisory = {
            'id': 1,
            'type': 'alert',
            'message': 'Test alert! Something bad is going down!'
        }

        with txn(rw=True) as connection:
            connection.execute(
                models.advisories.insert().values(**expected_advisory))

        actual_advisories = views.advisories(testing.DummyRequest())

        T.assert_in(expected_advisory, actual_advisories)

    def test_warning_advisory(self):
        expected_advisory = {
            'id': 1,
            'type': 'warning',
            'message': 'Test warning! Something bad might be going down!'
        }

        with txn(rw=True) as connection:
            connection.execute(
                models.advisories.insert().values(**expected_advisory))

        actual_advisories = views.advisories(testing.DummyRequest())

        T.assert_in(expected_advisory, actual_advisories)

    def test_info_advisory(self):
        expected_advisory = {
            'id': 1,
            'type': 'info',
            'message': 'Test info! Here\'s a thing!'
        }

        with txn(rw=True) as connection:
            connection.execute(
                models.advisories.insert().values(**expected_advisory))

        actual_advisories = views.advisories(testing.DummyRequest())

        T.assert_in(expected_advisory, actual_advisories)

    def test_sort_priority(self):
        advisory_info1 = {
            'id': 1,
            'type': 'info',
            'message': 'Some info message'
        }

        advisory_alert = {
            'id': 2,
            'type': 'alert',
            'message': 'Test alert! Something bad is going down!'
        }

        advisory_info2 = {
            'id': 3,
            'type': 'info',
            'message': 'Another info message! Clutter!'
        }

        advisory_warning = {
            'id': 4,
            'type': 'warning',
            'message': 'Test warning! Keep an eye out'
        }

        with txn(rw=True) as connection:
            for advisory in (advisory_info1,
                advisory_alert,
                advisory_info2,
                advisory_warning):

                connection.execute(
                    models.advisories.insert().values(**advisory))

        expected_advisories = [advisory_alert,
            advisory_warning,
            advisory_info1,
            advisory_info2]

        actual_advisories = views.advisories(testing.DummyRequest)

        T.assert_equal(expected_advisories, actual_advisories)


class ServicesTest(ViewTestCase):

    def test_empty_services(self):
        expected_services = {}

        actual_services = views.services(testing.DummyRequest())

        T.assert_equal(expected_services, actual_services)

    def test_single_service_single_version(self):
        version = {
            'name': 'foo',
            'env': 'production',
            'version': '1'
        }

        expected_services = {
            'foo': {
                'production': '1'
            }
        }

        with txn(rw=True) as connection:
            connection.execute(
                models.versions.insert().values(**version))

        actual_services = views.services(testing.DummyRequest())

        T.assert_equal(expected_services, actual_services)

    def test_single_service_multiple_versions(self):
        versions = [
            {
                'name': 'foo',
                'env': 'production',
                'version': '1'
            },
            {
                'name': 'foo',
                'env': 'stage',
                'version': '2'
            }
        ]

        expected_services = {
            'foo': {
                'production': '1',
                'stage': '2'
            }
        }

        with txn(rw=True) as connection:
            for version in versions:
                connection.execute(
                    models.versions.insert().values(**version))

        actual_services = views.services(testing.DummyRequest())

        T.assert_equal(expected_services, actual_services)

    def test_multiple_services_multiple_versions(self):
        versions = [
            {
                'name': 'foo',
                'env': 'production',
                'version': '1'
            },
            {
                'name': 'bar',
                'env': 'production',
                'version': '3243adae'
            },
            {
                'name': 'foo',
                'env': 'stage',
                'version': '2'
            },
            {
                'name': 'bar',
                'env': 'stage',
                'version': '912de190'
            }
        ]

        expected_services = {
            'foo': {
                'production': '1',
                'stage': '2'
            },
            'bar': {
                'production': '3243adae',
                'stage': '912de190'
            }
        }

        with txn(rw=True) as connection:
            for version in versions:
                connection.execute(
                    models.versions.insert().values(**version))

        actual_services = views.services(testing.DummyRequest())

        T.assert_equal(expected_services, actual_services)


class PutAdvisoryTest(ViewTestCase):

    def test_put_vanilla_advisory(self):
        expected_advisory = {
            'type': 'alert',
            'message': 'Test alert'
        }

        request = testing.DummyRequest()
        request.method = 'PUT'
        request.params = expected_advisory

        put_result = views.put_advisory(request)
        inserted_id = put_result['id']

        # Since the DB is reinitialized for every test, we can be pretty sure
        # that ID will always be 1
        T.assert_equal(inserted_id, 1)

        expected_advisory['id'] = 1

        with txn() as connection:
            result_set = connection.execute(
                models.advisories.select()).fetchall()

        T.assert_equal(len(result_set), 1)

        actual_advisory = dict(result_set[0].items())

        T.assert_equal(expected_advisory, actual_advisory)

    def test_put_bad_advisory_type(self):
        bad_advisory = {
            'type': 'HELLO WAT',
            'message': 'salty dane'
        }

        request = testing.DummyRequest()
        request.method = 'PUT'
        request.params = bad_advisory

        with T.assert_raises(httpexceptions.HTTPNotAcceptable):
            views.put_advisory(request)

        with txn() as connection:
            result_set = connection.execute(
                models.advisories.select()).fetchall()

        T.assert_equal(len(result_set), 0)


class DeleteAdvisoryTest(ViewTestCase):

    def test_delete_advisory(self):
        added_advisory = {
            'id': 1,
            'type': 'warning',
            'message': 'test warning'
        }

        with txn(rw=True) as connection:
            connection.execute(
                models.advisories.insert().values(**added_advisory))

        request = testing.DummyRequest()
        request.method = 'DELETE'
        request.params['id'] = 1
        views.delete_advisory(request)

        with txn() as connection:
            result_set = connection.execute(
                models.advisories.select()).fetchall()

        T.assert_equal(len(result_set), 0)

    def test_delete_non_existent_id(self):
        added_advisory = {
            'id': 1,
            'type': 'warning',
            'message': 'test warning'
        }

        with txn(rw=True) as connection:
            connection.execute(
                models.advisories.insert().values(**added_advisory))

        request = testing.DummyRequest()
        request.method = 'DELETE'
        request.params['id'] = 5

        with T.assert_raises(httpexceptions.HTTPNotFound):
            views.delete_advisory(request)

        with txn() as connection:
            result_set = connection.execute(
                models.advisories.select()).fetchall()

        T.assert_equal(len(result_set), 1)

    def test_delete_malformed_id(self):
        added_advisory = {
            'id': 1,
            'type': 'warning',
            'message': 'test warning'
        }

        with txn(rw=True) as connection:
            connection.execute(
                models.advisories.insert().values(**added_advisory))

        request = testing.DummyRequest()
        request.method = 'DELETE'
        request.params['id'] = 'a'

        with T.assert_raises(httpexceptions.HTTPNotAcceptable):
            views.delete_advisory(request)

        with txn() as connection:
            result_set = connection.execute(
                models.advisories.select()).fetchall()

        T.assert_equal(len(result_set), 1)
