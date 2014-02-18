More extensive documentation can be found at (http://pacer-lib.readthedocs.org)

Motivation and Overview
=======================
Morning.

[pacer_lib](https://pypi.python.org/pypi/pacer_lib/2.0) is a library that has
been designed to facilitate empirical legal research that uses data from the
[Public Access to Court Electronic Records (PACER)] (http://www.pacer.gov) 
database by providing easy-to-use objects for scraping, parsing and searching
PACER docket sheets and documents.

We developed *pacer_lib* in order to solve problems that arose naturally
during the course of our research and our goal is to make it easy to:

* **download a large number of specific documents from PACER**

    To locate and download multiple files on PACER requires a lot of manual
    labour, so one of the first things that we developed was a way to 
    programatically interface with the PACER Case Locator so that we could
    script all of our docket and document requests.

* **store downloaded dockets in a sensible and scalable way**
    
    PACER charges a fee for every page and document you access. If you have a
    project of any reasonable size and limited means, it becomes extremely 
    important to keep track of what files you have already downloaded (lest you
    inadvertently download the file twice). We create a well-documented folder
    structure and a equally well-documented unique identifier that can be 
    quickly disaggregated into a PACER search query or PACER case number.

* **extract information and create datasets from these dockets**
    
    We needed to create datasets for regression and textual analysis, so we 
    baked in the process of converting relatively unstructured data (.html 
    docket sheets) into more structured data (.csv for docket sheets and .json 
    objects for other meta information).
