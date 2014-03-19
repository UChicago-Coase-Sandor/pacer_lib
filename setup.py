from distutils.core import setup
setup(name='pacer_lib',
	  version='2.33',
	  author='C Zhang, K Jiang',
	  author_email='admin@uchicagolawandecon.org',
	  maintainer='Coase-Sandor Institute for Law and Economics, C Zhang, K Jiang',
	  url='http://coase-sandor.uchicago.edu',
	  description='A download interface for the Public Access to Court Electronic Records system',
	  long_description='A library that has been designed to facilitate \
      empirical legal research that uses data from the Public Access to Court \
      Electronic Records (PACER) (http://www.pacer.gov) database by providing \
      easy-to-use objects for scraping, parsing and searching PACER docket \
      sheets and documents. This is an updated version of pacer-scraper-library\
       and has been updated to be object-oriented.',
	  classifiers=['Development Status :: 4 - Beta', 
				  'Intended Audience :: Legal Industry', 
				  'Intended Audience :: Science/Research', 
				  'License :: Free To Use But Restricted', 
				  'Natural Language :: English',
				  'Programming Language :: Python :: 2.6',
				  'Topic :: Utilities'],
	  license = 'Python Software Foundation License',
	  packages=['pacer_lib'],
	  requires = ['bs4', 'lxml', 'html5lib' 'requests', 'datetime'],
	  )