********
Tutorial
********

We can't document every single use-case, but in this section, we will show code
examples for some common (in our mind, at least) tasks to give you an idea of 
how to use *pacer_lib*. In addition, we'll make note of lower-level functions 
that you can also access in case you need more customized functionality.

======================
1. Downloading Dockets
======================
------------
Code example
------------
    
Downloading one document::

    from pacer_lib.scraper import search_agent()

    court_id = 'almdce'
    case_number = '2:00-cv-00084'
    
    # Login
    s = search_agent("[Username]", "[Password]")

    # Download
    s.download_case_docket(case_number,court_id)

Downloading Multiple Documents::

    from pacer_lib.scraper import search_agent()

    # Login the search_agent into PACER
    s = search_agent("[Username]", "[Password]")

    cases = [('almdce', '2:00-cv-00084'),
             ('azdce', '2:98-cv-00020'),
             ('cacdce', '2:95-cv-03731')]

    # Download the case dockets to ./results/local_docket_archive/
    for court_id, case_num in cases:
        s.download_case_docket(case_num, court_id)
        
        
As you can see, before you begin you will need:

* a valid PACER username and password
* court ids and case numbers in a PACER case-number format for cases that
  you want to download
  
---------------------------
PACER username and password
---------------------------
You'll need to get that `here <http://www.pacer.gov/register.html>`_.

For most purposes, you will register for a "PACER - Case Search Only 
Registration"

--------
Court Id
--------
This is an identifier for the court that you are searching. Usually, this is not
particularly difficult to figure out. 

For example, the court id **almdce** is made up of three parts:

* **al** -- the state abbreviation for "Alabama"
* **md** -- the abbreviation for "Middle District"
* **ce** -- not sure what this stands for, but it's what PACER wants

For the equivalent bankruptcy court, **md** (Middle District) is changed to
**mb** (Middle District Bankruptcy). If the state only has a single district,
then the abbreviation is just **d**.

For example, the Massachusetts district court's court id is **madce**.

Appellate courts and the Supreme Court have not been implemented yet in 
*pacer_lib* yet.

To see a listing of all of the courts on PACER, you can go `to this page 
<http://www.pacer.gov/cgi-bin/links.pl>`_.
 
------------------
PACER Case-Numbers
------------------
If you login to the `PACER Case Locator <https://pcl.uscourts.gov/search>`_,
they will tell you that any of these formats can be used:

* yy-nnnnn
* yy-tp-nnnnn
* yy tp nnnnn
* yytpnnnnn
* o:yy-nnnnn
* o:yy-tp-nnnnn
* o:yy tp nnnnn
* o:yytpnnnnn

where:

* *yy* is the case-year (2 or 4 digits)
* *nnnnn* is the case-number (up to 5 digits)
* *tp* is the case type (e.g., 'cv', 'cr', 'bk', etc.)
* *o* is the office where the case was filed (1 digit)

*pacer_lib* works best with the clearest and mostly heavily delimited version:

* **o:yy-tp-nnnnn**

We use 2-digit years and we appended leading zeros to the *nnnnn* section
if the case-number is less than 5 digits long.

-------------------
Downloaded Filename
-------------------

Files downloaded by ``scraper.search_agent.download_case_docket()`` are saved
in the format: (court_id)_(case_num).html with colons replaced by plus signs, 
e.g., ('almdce', '2:00-cv-00084') is saved as 'almdce_2+00-cv-00084.html'.

--------------
Advanced Usage
--------------
For more information, look at the documentation at the object and
function reference for ``pacer_lib.scraper``. Here are some
suggestions about how to do more complicated docket downloading:

* If you want to make your own searches you can use 
  ``search_agent.search_case_locator()`` to create your own searches with
  other parameters.

* Once you have created your own searches and determined which dockets you
  want to download, you can use ``search_agent.request_docket_sheet()`` to
  download the docket.

* If you need to craft your own POST request, you can code it yourself 
  using `Requests <http://docs.python-requests.org/en/latest/>`_ or use
  ``search_agent.query_case_locator()``.

If you would like to create your own POST request and pass them to 

=============================
2. Parsing Downloaded Dockets
=============================
------------
Code example
------------
We are normally interested in parsing an entire directory of dockets at once
(an this has minimal costs as all of the dockets are already local)::

    from pacer_lib.reader import docket_parser

    # initialize a default docket_parser() object
    # the default values look for dockets in './results/local_docket_archive/'
    # and outputs to './results/processed_dockets/'
    p = docket_parser()

    # extract all docket information and case meta from dockets in the input
    # directory and save the data to the output directory
    p.parse_dir()

It is generally a bit unusual to just parse one file and you can always
just parse the entire directory and find the parsed afterwards, but 
to prove that we can::

    from pacer_lib.reader import docket_parser

    # initialize a default docket_parser() object
    # the default values look for dockets in 
    # './results/local_docket_archive/'
    # and outputs to './results/processed_dockets/'

    p = docket_parser()

    # open a file, parse the file

    file = './results/local_docket_archive/almdce_2+00-cv-00084.html'
    with open(file, 'r') as f:
        print p.parse_data(f.read())
        print p.extract_all_meta(f.read())

-------------------
Default Directories
-------------------
``reader.docket_parser.parse_dir()`` will output to the default output
directory. Unless otherwise specified, the  output directory will be
'./results/'. Within this output directory, there will be two sub
directories created:

* ``/parsed_dockets/``

    contains .csv documents that correspond to specific dockets

* ``/parsed_dockets_meta/`` which contains two additional directories:
    * ``/case_meta/`` 
    
        *case_meta* refers to the header information about the docket
        entries, e.g., assigned judge, case name, jurisdiction, etc.
        It also includes information about the lawyers who are associated
        with the case.

    * ``/download_meta/`` 

        *download_meta* refers to the information about the case that
        can be found on the PACER Case Locator results page. It also
        records when the docket was downloaded (only in newer versions).
        
-----
Notes
-----

* In older versions of *pacer_lib* (<= v2.32), we used ``/processed_dockets/``
  and ``/processed_dockets_meta/`` as the default folders for ``docket_parser``.

===========================
3. Searching Parsed Dockets
===========================
------------
Code example
------------
**Example 1:**
After parsing all of the dockets using docket_parser, search for
documents that are described with the word "judge" and "dismiss"
but that does not include the word "foreign"::

    from pacer_lib.reader import docket_processor
    
    r = docket_processor()
    r.search_dir(require_term=['judge', 'dismiss'], 
                 exclude_term=['foreign'])
    r.write_all_matches('firstsearch')
    
In this code example, all document entries that match this criteria
will be written into a single file called 'all_match_firstsearch.csv'.


**Example 2:**
Alternatively, search for the word "motion" in the first 10 characters
of a document description and then write a result file for each case
docket::

    from pacer_lib.reader import docket_processor
    
    r = docket_processor()
    r.search_dir(require_term=['motion'],
                 within='10')
    r.write_individual_matches('motion10')

In this code example, all document entries from a single case will be
written into a corresponding case file in a folder called 
'/docket_hits/' in the output path. 

For example, if the case *(almdce, 2:00-cv-00084)* has 3 documents that
have the word "motion" in the first 10 characters of their document
description, then those 3 document entries will be written a new file
called '^almdce_2+00-cv-00084_motion10.csv'.

--------------
Advanced Usage
--------------

The function ``reader.docket_processor.search_dir()`` commits its search
results to the ``reader.docket_processor.hit_list`` variable inclusively.
This means that you can run ``reader.docket_processor.search_dir()``
several times if you want to simulate an **OR** boolean search::

    from pacer_lib.reader import docket_processor
    
    r = docket_processor()
    r.search_dir(require_term=['motion'],
                 within='10')
    r.search_dir(require_term=['opinion'],
                 within='10')
    r.write_individual_matches('motion10')

**AND** searches and **NOT** searches, obviously, are built into the
``require_term`` and ``exclude_term`` arguments.

========================
4. Downloading Documents
========================

------------
Code example
------------
After parsing a docket, you can downloading a single document
very simply::
    
    from pacer_lib.scraper import search_agent()

    # Document information, can be taken from parsed csv
    case_filename = 'almdce_2+00-cv-00084'
    doc_no = '31'
    doc_link = 'https://ecf.almd.uscourts.gov/doc1/017149132'


    # Login
    s = search_agent("[Username]", "[Password]")

    # Download
    s.download_document(case_filename, doc_no, doc_link)

--------------
Advanced Usage
--------------
The actual document request and its raw response data (binary) can
also be exposed using the ``scraper.search_agent.request_document()``
function.

=====================
5. Sorting Documents
=====================
------------
Code example
------------
This code hasn't been implemented yet.
