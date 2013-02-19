from optparse import OptionParser

from pyramid.config import Configurator
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer

from terminal.db import engine, txn
from terminal.models import metadata, versions


ROUTES = {
    'dashboard': {
        'route': '/'
    },
    'advisories': {
        'route': '/advisories'
    },
    'services': {
        'route': '/services'
    }
}

STATIC_DIRS = ['css', 'js', 'img']

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('-p', '--port', default=8080, help="The port for the app server to listen on")
    parser.add_option('-r', '--reload', action='store_true', default=False, help='Enable code reloading')
    options, _ = parser.parse_args()

    # invoke Pyramid's scan to set up views
    config = Configurator()
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path('terminal:templates')
    for route_name, opts in ROUTES.iteritems():
        route_kwargs = opts.get('args', {})
        config.add_route(route_name, opts['route'], **route_kwargs)
    config.scan('terminal')

    for static_dir in STATIC_DIRS:
        config.add_static_view(static_dir, 'terminal:static/' + static_dir)

    # make a compatible WSGI app to serve with tornado
    app = config.make_wsgi_app()
    container = WSGIContainer(app)
    app_server = HTTPServer(container)

    io_loop = IOLoop.instance()

    app_server.listen(options.port)

    metadata.create_all(engine)

    # TODO: plug in more stuff here, like the things that collect information
    with txn(rw=True) as connection:
        connection.execute(versions.delete())

    io_loop.start()
