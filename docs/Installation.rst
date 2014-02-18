************
Installation
************
-------------
First Install
-------------
*pacer_lib* is published on `PyPi <https://pypi.python.org/pypi/pacer_lib>`_, 
the standard Python module repository, While you can download the tarball from
the website, we suggest that you use setuptools to install *pacer_lib*. 

Specifically, if you have either ``easy_install`` or ``pip`` installed, just 
type:

``pip install pacer_lib``

or

``easy_install pacer_lib``

------------------------------------
Compatibility and Required Libraries
------------------------------------
In case you are running into trouble using *pacer_lib* or are looking to 
develop or modify *pacer_lib*, we have provided some notes on the system on
which we developed *pacer_lib*.

We developed *pacer_lib* on Cygwin x86 in Windows 7 for Python 2.7.6. 

We make extensive use of `Requests v2.3.0 
<http://requests.readthedocs.org/en/latest/>`_ and `BeautifulSoup 4 
<http://www.crummy.com/software/BeautifulSoup/bs4/doc/>`_. We also use
`datetime <http://docs.python.org/2/library/datetime.html>`_ and, in older
versions of *pacer_lib*, we use `lxml <http://lxml.de>`_.
 