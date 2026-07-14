"""Route modules shared across the API apps.

Each router owns a slice of the surface so the app modules can compose only
the routes a given service needs:

* ``health``    — ``/health`` (mounted by every app)
* ``query``     — read side: ``/query``, ``GET /documents``, ``/config``
* ``ingestion`` — write side: ``/ingest`` + job routes, ``DELETE /documents/{file}``

``query`` never imports the ingestion router (or the Docling-backed job
runner), which is what keeps the query image free of the parsing stack.
"""
