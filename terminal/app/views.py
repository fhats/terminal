"""Contains the views for the application.

There's only one route which serves HTML: dashboard (/). All other views expose
an API into the application's data.

Most of the business logic for these views is contained in the views
themselves. Since this is a pretty straightforward CRUD API right now, they can
stay there; however, if the logic within the views grows much more it should
probably be refactored out into a separate place.
"""
from collections import defaultdict

from pyramid import httpexceptions
from pyramid.view import view_config
from pyramid.response import Response

from terminal import models
from terminal.db import txn


# Just to make it a little easier to sort by how important advisories are
ADVISORY_TYPES_TO_PRIORITIES = {
    'alert': 1,
    'warning': 2,
    'info': 3
}


@view_config(route_name='dashboard', request_method='GET', renderer='dashboard.jinja2')
def dashboard(request):
    return {}


@view_config(route_name='advisories', request_method='GET', renderer='json')
def advisories(request):
    """Returns a list of the current advisories sorted by severity.
    """
    with txn() as connection:
        result_set = connection.execute(models.advisories.select())
        results = [dict(row.items()) for row in result_set.fetchall()]

    results.sort(key=lambda advisory: ADVISORY_TYPES_TO_PRIORITIES[advisory['type']])

    return results


@view_config(route_name='services', request_method='GET', renderer='json')
def services(request):
    """Returns a list of services and their versions in different environments.
    """
    services = defaultdict(dict)

    with txn() as connection:
        result_set = connection.execute(models.versions.select()).fetchall()

    for row in result_set:
        result = dict(row.items())
        services[result['name']][result['env']] = result['version']

    return services


@view_config(route_name='advisories', request_method='PUT', renderer='json')
def put_advisory(request):
    """Provides an interface to add advisories.
    """
    advisory_info = {}
    advisory_info['type'] = request.params['type']
    advisory_info['message'] = request.params['message']

    if advisory_info['type'] not in models.ADVISORY_TYPES:
        raise httpexceptions.HTTPNotAcceptable()

    with txn(rw=True) as connection:
        result = connection.execute(models.advisories.insert().values(**advisory_info))

    return {'id': result.inserted_primary_key[0]}


@view_config(route_name='advisories', request_method='DELETE')
def delete_advisory(request):
    """Deletes an advisory specified by `ID`.
    """
    try:
        advisory_id = int(request.params['id'])
    except:
        raise httpexceptions.HTTPNotAcceptable()

    with txn(rw=True) as connection:
        result = connection.execute(
            models.advisories.delete().where(
                models.advisories.c.id == advisory_id
            )
        )

        if result.rowcount == 0:
            raise httpexceptions.HTTPNotFound()

    return Response()
