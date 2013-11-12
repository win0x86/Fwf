# coding: utf-8

"""模板解析


[code]

name = "index.html"
template = Template(name, TemplateLoader("name").read()).generate(name="jack", op="add")

[/code]


"""

import os
import cStringIO


class TemplateException(Exception):
    pass



class Template(object):
    def __init__(self, name, body, compress_whitespace=None):
        self.name = name
        self.body = body
        if compress_whitespace is None:
            self.compress_whitespace = name.endswith(".html") or \
                name.endswith(".js")
        self.writer = cStringIO.StringIO()
        _parse = TemplateParse(_TemplateReader(self.body))
        _Assemble(_parse()).gen(self.writer)

    def generate(self, **kwargs):
        namespace = {}
        namespace.update(kwargs)
        self.code = self.writer.getvalue()
        try:
            self.compiled = compile(self.code, self.name, "exec")
            exec self.compiled in namespace
            return namespace["_fwf_mix_code"]()
        except:
            print "Template error: %s" % self.code
            raise



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


    def gen(self, writer):
        code = _CodeContact(writer)
        code.write("def _fwf_mix_code():")

        with code.indent():
            code.write("s = []")
            for item in self._items:
                item.mix(code)
            code.write("return u''.join(s)")

        return code



class _CodeContact():
    def __init__(self, writer):
        self._indent = 0
        self.writer = writer


    def indent(self):
        return self


    def __enter__(self):
        self._indent += 1
        return self


    def __exit__(self, *args):
        self._indent -= 1


    @property
    def indent_size(self):
        return self._indent


    def write(self, code, indent=None):
        if indent is None:
            indent = self._indent
        self.writer.write("    " * indent)
        self.writer.write(code)
        self.writer.write("\n")



class Item(object):
    def __init__(self, text):
        self._text = text


    @property
    def text(self):
        return self._text


    def mix(self, writer):
        raise NotImplementedError()



class _Text(Item):
    def mix(self, writer):
        if self.text and self.text != "\n":
            writer.write(u"s.append(%s)" % repr(self.text))



class _Expression(Item):
    def mix(self, writer):
        writer.write(u"s.append(%s)" % self.text)



class _Code(Item):
    def __init__(self, text, items):
        self._text = text
        self._items = items
        self.indent = 0

        
    def mix(self, writer):
        writer.write("%s:" % self.text)
        with writer.indent():
            for item in self._items:
                item.mix(writer)


class _CodeElse(Item):
    def __init__(self, text, indent=0):
        self._text = text
        self.indent = indent

        
    def mix(self, writer):
        writer.write("%s :" % self.text, writer.indent_size + self.indent)



class TemplateParse(object):
    def __init__(self, reader):
        self._reader = reader
        self._items = []


    def __call__(self):
        while True:
            loc = 0
            while True:
                loc = self._reader.find("{", loc)
                if loc == -1:
                    self._items.append(_Text(self._reader.cut()))
                    return self._items

                if self._reader[loc + 1] not in ("{", "%"):
                    loc += 1
                    continue

                if self._reader[loc + 1] == "{" and self._reader[loc + 2] == "{":
                    loc += 1
                    continue
                break

            if loc > -1:
                self._items.append(_Text(self._reader.cut(loc)))
            exp_start = self._reader.cut(2) # "{{"

            if exp_start == "{{":
                end = self._reader.find("}}")
                content = self._reader.cut(end).strip()
                self._items.append(_Expression(content))
                self._reader.cut(2) # "}}"
                continue

            end = self._reader.find("%}")
            if end == -1:
                raise TemplateException("Miss %} block.")
            content = self._reader.cut(end).strip()
            op, space, suffix = content.partition(" ")
            suffix = suffix.strip()
            self._reader.cut(2)
            if op in ("else", "elif", "except", "finally"):
                self._items.append(_CodeElse(content, -1))
                continue
            
            if op == "end":
                return self._items

            if op in ("if", "for", "try", "while"):
                _items = TemplateParse(self._reader)()
                self._items.append(_Code(content, _items))
                continue
            else:
                raise TemplateException("unknown operator: %r" % op)



class _TemplateReader(object):
    def __init__(self, html, curr=0, items=None):
        self._html = html
        self._len = len(html)
        self._curr = curr


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
    html = """<!DOCTYPE html><html>
<head><title>Hello</title></head>
<body>
<h1>Name: {% if name == "jack" %}</h1>
{% if op == "add" %}
<div>ADDDDDDDDDDDDDDDDDdddd {{ name }}</div>
{% if op == "edit" %}
<span>EDITTTTTTTTTTTTTTTT {{ op }}</span>{% end %}
{% elif i == 100 %}
<h3>else</h3>
{% end %}
{% end %}
{{ os.uname()[0] }}
</body>
</html>
"""
    
    print "html:"
    print "=" * 30
    print html
    print "=" * 30
    print
    print "code:"
    print "=" * 30
    template = Template("index.html", html).generate(name="jack", op="add", os=os)
    print template
    print "=" * 30



if __name__ == "__main__":
    test_template()
