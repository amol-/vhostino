About VHostino
-------------------------

vhostino is a virtual hosts manager for `Mozilla Circus <https://github.com/mozilla-services/circus>`_.

Installing
-------------------------------

vhostino can be installed from pypi::

    easy_install vhostino

or::

    pip install vhostino

should just work for most of the users

Using VHostino
---------------------------------

Simply name your watcher and socket as the domain they have to serve and set
``vhostino.vhost = True`` to make them serve through virtual hosts on the vhostino ``port``::

    [plugin:vhostino]
    use = vhostino.VHostino
    host = 0.0.0.0
    port = 8000

    [watcher:www.mywebsite.com]
    cmd = chaussette --fd $(circus.sockets.www.mywebsite.com) myapp.application
    use_sockets = True

    vhostino.vhost = True

    uid = www-data
    gid = www-data

    [socket:www.mywebsite.com]
    host = 127.0.0.1
    port = 8082


The ``myapp.application`` web application will be served as usual on ``127.0.0.1:8082``
but will be also available on port ``8000`` when the domain ``www.mywebsite.com`` is requested.

Default Virtual Host
---------------------------

By default VHostino will answer with a 404 error whenever a non configured host is requested,
to serve a default virtual host simply set the ``vhosting.default_vhost = True`` option inside
a watcher, whenever a virtual host is not available to serve the request it will be proxied to
that process.

Notes
---------------------------

To perform virtual hosts resolution vhostino uses the ``watcher`` name, so make sure that
your watchers are named like the domain they need to serve. In future versions aliases
will also be added.

To match ``socket`` and ``watcher`` vhostino uses their name, so make sure that your socket
share the same name, otherwise vhostino won't be able to detect the process port.

