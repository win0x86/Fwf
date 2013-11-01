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



class _TemplateReader(object):
    """ 处理模板读取的内容 """
    def __init__(self, name, body):
        assert name
        self.name = name
        self.body = body
        self.length = len(body)
        self.pos = 0
        self.line = 0


    def find(self, sep, start=0):
        index = self.body.index(sep, start + self.pos)
        self.pos = index
        return index


    def is_ending(self):
        return self.pos >= self.length


    def __getitem__(self, pos):
        if isinstance(pos, slice):
            return self.body[pos]
        elif pos > 0:
            return self.body[self.pos + pos:]
        else:
            return self.body[pos:]


    def _str__(self):
        return self.body[self.pos:]



class Norm(object):
    def __init__(self, body):
        self.body = body


    def write(self):
        raise NotImplementedError()



class _Text(Norm):
    """ 文本 """
    def write(self, stream):
        pass



class _Expression(Norm):
    """ Python 表达式"""
    def write(self, stream):
        pass



class _Code(Norm):
    """Python var"""
    def write(self, stream):
        stream.write("%s" % self.body)



class Assembly(object):
    """生成python code"""
    def __init__(self):
        self.stream = cStringIO.StringIO()


    def run(self, things):
        self.stream.write("def __assembly_template():")
        
        for t in things:
            t.write(self.stream)



class _TemplateParse(object):
    """转换 text -> python code"""
    def __init__(self, reader):
        self.reader = reader


    def parse(self):
        body = []
        while True:
            curly = 0
            while True:
                index = self.reader.find("{{")
                if index < 0:
                    body.append(_Text(self.reader[:]))
                    return body

                if self.reader[index + 1] == "{":
                    curly += 1
                    continue

                if self.reader[index + 1] not in ("%", "{"):
                    curly += 1
                    continue
                break

            # 处理 变量, 方法
            part = self.reader[curly +  2:].strip()
            head, spacing, tail = part.partition(" ").strip()



def test_template_loader():
    load = TemplateLoader("index.html", "/home/cc/work/test/web/templates")
    html = load.read()
    assert html
    print html



def test_template_reader():
    pass



def test_template_parse():
    # reader = _TemplateReader("index.html", TemplateLoader("index.html", "/home/cc/work/test/web/templates").read())
    html = """
<html DOCTYPE>
<head><title></title></head>
<body>
<h1> {{ name }}</h1>
</body>
</html>
"""
    reader = _TemplateReader("index.html", html)
    parse = _TemplateParse(reader)
    print parse.parse()



if __name__ == "__main__":
    # test_template_loader()
    test_template_parse()
