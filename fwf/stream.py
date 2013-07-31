# coding: utf-8

"""Socket stream.

处理接入的socket流
TODO: 减少stream处理逻辑.

"""

import select

import rawio


class Stream(object):
    def __init__(self, sock, io=None, max_buffer_size=104857600, read_chunk_size=4096, response_txt=""):
        self.sock = sock
        self._listen_fds = {}
        self._requests = {} # 请求内容
        self._responses = {} # 响应的内容
        self._response_txt = response_txt
        self._read_buffer = ""
        self._write_buffer = ""
        self.io = io or rawio.RawIO.instance()
        self.max_buffer_size = max_buffer_size
        self.read_chunk_size = read_chunk_size
        self._read_callback = None

        self.io.add_handler(sock.fileno(), self._handle_events, select.EPOLLERR)


    def _handle_events(self, fd, event):
        if fd in self._listen_fds:
            conn, addr = self._listen_fds[fd].accept()
            conn.setblocking(0)
            self.add_handler(conn.fileno(), conn, select.EPOLLIN)
            self._handlers[conn.fileno()] = conn
            self._requests[conn.fileno()] = b""
            self._responses[conn.fileno()] = self._response_txt

        elif event & select.EPOLLIN:
            self._handle_read()

        elif event & select.EPOLLOUT:
            self._handle_write()

        elif event & select.EPOLLHUP:
            self._handlers[fd].close()
            self.remove_handler(fd)


    def _handle_write(self, data):
        # TODO 处理response写入和是否长连接, 关闭socket.
        num_bytes = self._handlers[fd].send(
            self._responses[fd])
        self._responses[fd] = self._responses[fd][num_bytes:]

        if not self._responses[fd]:
            self.io.remove_handler(fd)


    def _handle_read(self, fd):
        while True:
            # TODO 1. 接收数据大小限制
            # TODO 2. 处理HTTP请求生成response
            try:
                data = self._handlers[fd].recv(1024)
                self._read_buffer += data
                if not data: break
            except socket.error as ex:
                if ex.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                    break
                else:
                    logging.error("Read error.", exc_info=ex)

            self.io.modify_handler(fd, select.EPOLLOUT)


    def read(self, delimiter, callback):
        assert not self._read_callback, "Already reading."
        loc = self._read_buffer.find(delimiter)
        if loc != -1:
            callback(self._consume(loc + len(delimiter)))
            return


    def add_listen_fd(self, sock):
        if sock.fileno() not in self._listen_fds:
            self._listen_fds[sock.fileno()] = sock


    def _consume(self, loc):
        result = self._read_buffer[:loc]
        self._read_buffer = self._read_buffer[loc:]
        return result



if __name__ == "__main__":
    response = [b"HTTP/1.1 200 OK\r\n",
                b"Date: Mon, 1 Jan 2013 01:01:01 GMT\r\n",
                b"Content-Type: text/plain\r\n",
                b"Content-Length: 13\r\n\r\n",
                b"Hello, world!"]
    response = b"".join(response)

    def on_read(data):
        print "recv:", data


    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    s.connect(("localhost", 8888))
    stream = Stream(s, response_txt=response)
    stream.read("\r\n\r\n", on_read)
    rawio.RawIO.instance().loop()
