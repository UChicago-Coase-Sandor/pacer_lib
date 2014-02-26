*********
Changelog
*********
Version 2.31 (2014-02-26)

    Fixed three bugs in ``reader.docket_processor().parse_data()``,
    ``reader.docket_processor().extract_download_meta()`` and 
    ``reader.docket_processor().extract_case_meta()``

Version 2.3 (2014-02-18)

    Made a bunch of mistakes, fixed them (mostly of the packaging variety) but
    burned through Versions 2.1 and 2.2.
    
    Changed the name of submodule pacer_lib.parser to pacer_lib.reader
    because of potential confusion.
    
    Implemented overwrite protection and suffixing for 
    ``docket_processor.write_all_matches()``

    Implemented overwrite protection for 
    ``docket_processor.write_individual_matches()``

    Cleaned up the documentation.
    
Version 2.0 (2014-02-17)
    
    Added ``parser`` sub-module, which includes the objects ``docket_parser()``
    and ``docket_processor()``, which brings scraping and docket parsing 
    functionality to 
    
    ``document_sorter()`` outlined in ``parser`` sub-module but not yet 
    implemented.
    
    Improved documentation, including the use of docstrings, Sphinx and hosting
    documentation on ReadTheDocs.org.
    
    Kevin Jiang added as maintainer.
    
Version 1.0 (2014-01-08)

    Added ``scraper`` sub-module, which includes the object ``search_agent()``  
    that interfaces with the PACER Case Locator and allows the downloading of
    both dockets and documents.
    
    Added the functions ``disaggregate_docket_number()`` and ``gen_case_query``,
    which handle specific query-creation issues in our PACER requests.
    
*pacer_scraper_library* Version 1.0a (2013-03-01)
    Original library; function based. For legacy users, you can access the 
    undocumented and unsupported pacer_scraper_library `here 
    <https://pypi.python.org/pypi/pacer-scraper-library>`_.