# coding: utf-8

"""模板解析


TODO:

1. 处理if for try 等语句.
2. 拼接执行代码.
3. 把代码动态嵌入到执行环境.

"""

import os


class TemplateException(Exception):
    pass



class Template(object):
    def __init__(self, name, body):
        self.name = name
        self.body = body


    def generate(self, **kwargs):
        pass



class TemplateLoader(object):
    """ 加载模板文件 """
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



class _Assemble(object):
    def __init__(self, items):
        self._items = items


    def gen(self):
        for item in self._items:
            pass



class Item(object):
    def __init__(self, text):
        self._text = text


    @property
    def text(self):
        return self._text


    def mix(self):
        raise NotImplementedError()



class _Text(Item):
    def mix(self):
        pass



class _Expression(Item):
    def mix(self):
        pass



class TemplateParse(object):
    def __init__(self, html):
        self._html = html
        self._len = len(html)
        self._curr = 0
        self._items = []


    def __call__(self):
        while True:
            loc = 0
            while True:
                loc = self.find("{", loc)
                if loc == -1:
                    self._items.append(_Text(self.cut()))
                    return

                if self[loc + 1] != "{":
                    loc += 1
                    continue

                if self[loc + 1] == "{" and self[loc + 2] == "{":
                    loc += 1
                    continue
                break

            if loc > -1:
                self._items.append(_Text(self.cut(loc)))
            exp_start = self.cut(2) # "{{"
            end = self.find("}}")
            content = self.cut(end).strip()
            self._items.append(_Expression(content))
            self.cut(2) # "}}"
            continue


    def cut(self, count=None):
        if count is None:
            count = self._len - self._curr

        pos = self._curr + count
        s = self._html[self._curr: pos]
        self._curr += count
        return s


    def find(self, delim, start=0):
        index = self._html.find(delim, start + self._curr)
        if index != -1:
            index -= self._curr
        return index


    def __getitem__(self, key):
        if isinstance(key, slice):
            start, step, stop = key.indices(self._len - self._curr)
            return self._html[start + self._curr: step: stop]
        else:
            return self._html[self._curr + key]



def test_template():
    html = """<!DOCTYPE html><html>
<head><title>Hello</title></head>
<body>
<h1>Name: {{{{ name }}}}</h1>
<h2>Company: {{ company }}}</h2>
<h3>Address: {{ address }}}}</h3>
<h4>Phone: {{ phone }}</h4>
</body>
</html>"""

    template = TemplateParse(html)
    template()
    for t  in template._items:
        print t.text,
    print "\n%s" % template._items



if __name__ == "__main__":
    test_template()
