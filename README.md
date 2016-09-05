Fwf

Micro [Tornado](https://github.com/tornadoweb/tornado).

[说明文档](https://win0x86.github.io/blog/python/fwf/2015/03/31/python-web-framework-fwf-01-intro.html)

创建时间: 2013-07-25

简介:
该框架参考tornado web server，tornado 名称带有web server，说明它具有web server 功能。从tcp连接到http有完整的实现，
这个框架使用了分层去简化复杂度，上层不用知道下一层的具体实现，分层思想在操作系统中，和网络中都有具体的体现
在操作系统中我们使用的编程语言调用API，系统调用，系统调用又使用了硬件的驱动程序的接口
在网络中，http基于tcp，tcp基于ip，ip基于以态网
此框架主要用于学习Web开发中所有的开发细节，便于我们在以后解决问题中精确的定位问题所在。

文件相关描述:
rawio.py: tcp连接处理
stream.py: 流数据读取
server.py: http相关
web.py: http协议具体实现
template.py: 模板处理
util.py: 一些实用方法
