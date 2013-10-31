# coding: utf-8

"""模板解析


TODO:

1. 处理if for try 等语句.
2. 区分代码与表达式.
3. 拼接执行代码.
4. 把代码动态嵌入到执行环境.

"""

import os


class TemplateException(Exception):
    pass



class Template(object):
    def __init__(self, name, body):
        self.name = name
        self.body = body



class TemplateLoader(object):
    def __init__(self, name, path="."):
        self.name = name
        self.path = path
        self.root = os.path.abspath(path)


    def read(self):
        try:
            path = os.path.join(os.path.sep, self.root, self.name)
            body = open(path, "r").read()
        except:
            raise TemplateException("No such %s file." % path)

        return body



class _TemplateReader(object):
    def __init__(self, name, body):
        assert name
        self.name = name
        self.body = body
        self.length = len(body)
        self.pos = 0
        self.line = 0


    def find(self, sep, start):
        index = self.body.index(sep, start + self.pos)
        self.pos = index
        return index


    def is_ending(self):
        return self.pos >= self.length


    def __getitem__(self, pos):
        if isinstance(pos, slice):
            return self.body[pos]
        elif pos > 0:
            return self.body[self.pos + pos]
        else:
            return self.body[pos]


    def _str__(self):
        return self.body[self.pos:]




class Norm(object):
    def write(self):
        raise NotImplementedError()



class _Text(Norm):
    def write(self):
        pass



class _Expression(Norm):
    def write(self):
        pass



class _TemplateParse(object):
    def __init__(self, reader):
        self.reader = reader


    def parse(self):
        body = []

        while True:
            curr = 0

            for i in xrange(self.reader.length):
                pos = self.reader.find("{", curr)
                if pos < 0:
                    body.append(self.reader[pos:])
                    return body

                if self.reader[pos + 1] == "{":
                    curr += 1
                    continue

                if self.reader[pos + 1] not in ("%", "{"):
                    curr += 1
                    continue

                break

            end = self.reader.find("}}")
            if end < 0: raise TemplateException("Miss }}.")
            express = self.reader[:end].strip()
            head, sep, tail = express.partition(" ")
            if tail.strip() == "}}":
                body.append(head)



def test_template():
    load = TemplateLoader("index.html", "/home/cc/work/test/web/templates")
    html = load.read()
    assert html
    print html


if __name__ == "__main__":
    test_template()
