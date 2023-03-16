"""Special pytest fixture configuration file.

This file automatically provides all fixtures defined in it to all
pytest tests in this directory and sub directories.

See https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files

pytest fixtures are used to initialize object for test functions. The
fixtures run for a function are based on the name of the argument to
the test function.

Scope = 'session' means that the fixture will be run onec and reused
for the whole test run session. The default scope is 'function' which
means that the fixture will be re-run for each test function.

"""
import pytest
from pathlib import Path
from browse.factory import create_web_app
import os

from tests import path_of_for_test


@pytest.fixture(scope='session')
def loaded_db():
    """Loads the testing db"""
    app = create_web_app()
    with app.app_context():
        from browse.services.database import models

        from . import populate_test_database
        populate_test_database(True, models)



@pytest.fixture(scope='session')
def app_with_db(loaded_db):
    """App setup with DB backends."""
    import browse.services.documents as documents
    from browse.services.listing import db_listing

    app = create_web_app()
    app.config.update({'DOCUMENT_LISTING_SERVICE': db_listing})
    app.config.update({'DOCUMENT_ABSTRACT_SERVICE': documents.db_docs})
    app.settings.DOCUMENT_ABSTRACT_SERVICE = documents.db_docs
    app.settings.DOCUMENT_LISTING_SERVICE = db_listing

    app.testing = True
    app.config['APPLICATION_ROOT'] = ''

    with app.app_context():
        import browse.services.documents as documents
        from browse.services.listing import db_listing
        from flask import g
        g.doc_service = documents.db_docs(app.settings, g)
        g.listing_service = db_listing(app.settings, g)

    return app


@pytest.fixture(scope='function')
def app_with_fake(loaded_db):
    """A browser client with fake listings and FS abs documents"""

    # This depends on loaded_db becasue the services.database needs the DB
    # to be loaded eventhough listings and abs are done via fake and FS.
    app = create_web_app()
    import browse.services.documents as documents
    import browse.services.listing as listing

    app.config.update({'DOCUMENT_LISTING_SERVICE': listing.fake})
    app.config.update({'DOCUMENT_ABSTRACT_SERVICE': documents.fs_docs})

    app.settings.DOCUMENT_ABSTRACT_SERVICE = documents.fs_docs
    app.settings.DOCUMENT_LISTING_SERVICE = listing.fake

    app.testing = True
    app.config['APPLICATION_ROOT'] = ''

    with app.app_context():
        from flask import g
        g.doc_service = documents.fs_docs(app.settings, g)
        g.listing_service = listing.fs_listing(app.settings, g)
        yield app


@pytest.fixture
def storage_prefix():
    return './tests/data/abs_files/'


@pytest.fixture(scope='function')
def app_with_test_fs(loaded_db):
    """A browser client with FS abs documents and listings"""

    # This depends on loaded_db becasue the services.database needs the DB
    # to be loaded eventhough listings and abs are done via FS.

    import browse.services.documents as documents
    import browse.services.listing as listing
    from browse.config import settings

    settings.DISSEMINATION_STORAGE_PREFIX = './tests/data/abs_files/'
    settings.DOCUMENT_ABSTRACT_SERVICE = documents.fs_docs
    settings.DOCUMENT_LISTING_SERVICE = listing.fs_listing
    settings.DOCUMENT_LISTING_PATH = "tests/data/abs_files/ftp"
    settings.DOCUMENT_LATEST_VERSIONS_PATH = "tests/data/abs_files/ftp"
    settings.DOCUMENT_ORIGNAL_VERSIONS_PATH = "tests/data/abs_files/orig"

    app = create_web_app()
    app.testing = True
    app.config['APPLICATION_ROOT'] = ''

    with app.app_context():
        from flask import g
        g.doc_service = documents.fs_docs(app.settings, g)
        g.listing_service = listing.fs_listing(app.settings, g)
        yield app

@pytest.fixture(scope='function')
def dbclient(app_with_db):
    """A browse app client with a test DB populated with fresh data.

    This is function so each test funciton gets an new app_context."""
    with app_with_db.app_context():
        yield app_with_db.test_client() # yield so the tests already have the app_context


@pytest.fixture(scope='function')
def client_with_fake_listings(app_with_fake):
    with app_with_fake.app_context():
        yield app_with_fake.test_client() # yield so the tests already have the app_context


@pytest.fixture(scope='function')
def client_with_test_fs(app_with_test_fs):
    with app_with_test_fs.app_context():
        yield app_with_test_fs.test_client() # yield so the tests already have the app_context


@pytest.fixture()
def unittest_add_db(request, dbclient):
    """Adds dbclient to the calling UnitTest object

    To use this add @pytest.mark.usefixtures("unittest_add_db") to the UnitTest TestCase class."""
    request.cls.dbclient = dbclient


@pytest.fixture()
def unittest_add_fake(request, client_with_fake_listings):
    """Adds client with fake listing data and FS abs data to the calling UnitTest object

    To use this add @pytest.mark.usefixtures("unittest_add_fake") to the UnitTest TestCase class."""
    request.cls.client = client_with_fake_listings


@pytest.fixture()
def abs_path() -> Path:
    """`Path` to the test abs files."""
    return Path(path_of_for_test('data/abs_files'))


#NOT A FIXTURE
def _app_with_db():
    import browse.services.documents as documents
    from browse.services.listing import db_listing

    app = create_web_app()
    app.config.update({'DOCUMENT_LISTING_SERVICE': db_listing})
    app.config.update({'DOCUMENT_ABSTRACT_SERVICE': documents.db_docs})

    app.settings.DOCUMENT_ABSTRACT_SERVICE = documents.db_docs
    app.settings.DOCUMENT_LISTING_SERVICE = db_listing
    app.testing = True
    app.config['APPLICATION_ROOT'] = ''
    return app



# #################### Integration test marker ####################
"""
Setup to mark integration tests.

https://docs.pytest.org/en/latest/example/simple.html
Mark integration tests like this:

@pytest.mark.integration
def test_something():
  ...
"""

def pytest_addoption(parser):
    parser.addoption(
        "--runintegration", action="store_true", default=False,
        help="run arxiv dissemination integration tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark tests as integration tests")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runintegration"):
        # --runintegration given in cli: do not skip integration tests
        return
    skip_integration = pytest.mark.skip(reason="need --runintegration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
