import gevent
gevent.monkey.patch_all()

from socket import error as SocketError
from circus import logger

from itertools import chain as ichain
from functools import partial

from gevent.server import StreamServer
from rfc822 import Message

class ProxyStream(object):
    BUFFER_SIZE = 4096

    def __init__(self, raw_requestline, message, proxy_socket, proxy_to):
        self.message = message
        self.proxy_socket = proxy_socket
        self.requestline = raw_requestline
        self.endpoint = gevent.socket.create_connection(('127.0.0.1', proxy_to))

    def _write_headers(self):
        headers = ''.join(ichain([self.requestline], self.message.headers))
        self.endpoint.sendall(headers)
        self.endpoint.sendall('\r\n')

    def start(self):
        try:
            self._write_headers()
            self.run_proxy()
        finally:
            self.endpoint.close()

    def run_proxy(self):
        exit_event = gevent.event.Event()

        endpoint_greenlet = gevent.Greenlet(self._proxy_io, self.endpoint, self.proxy_socket, exit_event)
        client_greenlet = gevent.Greenlet(self._proxy_io, self.proxy_socket, self.endpoint, exit_event)

        client_greenlet.start()
        endpoint_greenlet.start()

        #Whenever one of the endpoints is closed end both.
        exit_event.wait()
        gevent.killall((endpoint_greenlet,
                        client_greenlet))

    def _proxy_io(self, source, dest, on_exit):
        while True:
            data = source.recv(self.BUFFER_SIZE)
            if not data:
                break
            dest.sendall(data)

        on_exit.set()

class RequestRouter(object):
    MAX_REQUEST_LINE = 8192

    REQUEST_TOO_LONG_RESPONSE = "HTTP/1.0 414 Request URI Too Long\r\nConnection: close\r\nContent-length: 0\r\n\r\n"
    BAD_REQUEST_RESPONSE = "HTTP/1.0 400 Bad Request\r\nConnection: close\r\nContent-length: 0\r\n\r\n"
    NOT_FOUND_RESPONSE = "HTTP/1.1 404 Not Found\r\n\r\n"

    def __init__(self, config, socket):
        self.config = config
        self.socket = socket
        self.rfile = socket.makefile('rb', -1)
        self.message = None

    def close(self):
        self.rfile.close()
        self.socket.close()
        if self.message is not None:
            self.message.fp.close()

    def handle(self):
        try:
            raw_requestline = self.rfile.readline(self.MAX_REQUEST_LINE)
        except SocketError:
            # "Connection reset by peer" or other socket errors aren't interesting here
            return False

        if not raw_requestline:
            return False

        if len(raw_requestline) >= self.MAX_REQUEST_LINE:
            self.socket.sendall(self.REQUEST_TOO_LONG_RESPONSE)
            return False

        if not self._request_check(raw_requestline):
            self.socket.sendall(self.BAD_REQUEST_RESPONSE)
            return False

        self.message = Message(self.rfile, 0)

        host = self.message.get('Host', '')
        if ':' in host:
            host, port = host.split(':', 1)
        host = host.strip()

        proxy_to = self.config.get_vhost(host)
        if not proxy_to:
            self.socket.sendall(self.NOT_FOUND_RESPONSE)
            self.message.fp.close()
            return False

        ProxyStream(raw_requestline, self.message, self.socket, proxy_to).start()

    def _request_check(self, reqline):
        try:
            command, path, version = reqline.split()
            if version.strip() not in ('HTTP/1.0', 'HTTP/1.1'):
                return False
            return True
        except:
            return False

class VirtualHostsConfig(object):
    def __init__(self):
        self.default_vhost_port = None
        self.vhosts = {}

    def add_vhost(self, host, port):
        self.vhosts[host] = port

    def set_default(self, port):
        self.default_vhost_port = port

    def get_vhost(self, host):
        return self.vhosts.get(host, self.default_vhost_port)

class ProxyServer(StreamServer):
    def __init__(self, listener, backlog=None, spawn='default'):
        super(ProxyServer, self).__init__(listener, backlog=backlog, spawn=spawn)
        self.config = VirtualHostsConfig()

    def handle(self, socket, address):
        try:
            router = RequestRouter(self.config, socket)
            router.handle()
        finally:
            router.close()

