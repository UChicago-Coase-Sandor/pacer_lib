import codecs
import cStringIO
import csv
import datetime
import json
import os
import requests
import re
import time
import html5lib
from bs4 import BeautifulSoup, Comment

#Implement mySQL stuff
# Handle stuff
#ALlow for multiple docket_paths?
#Should also return meta-data from the download header

class docket_parser():
    """
    Returns a docket_parser object that provides functions which allow you to
    quickly load .html PACER docket sheets from the specified docket_path 
    parse metadata (about both the download of the docket as well as the 
    characteristics of the case), and convert into a machine-readable format
    (CSV)
    
    This object is built on top of BeautifulSoup 4.
    
    **Keyword Arguments:**

    * ``docket_path``: which specifies a relative path to the storage of dockets
      (i.e., input data); dockets shoudl be in .html format
    
    * ``output_path``: which specifies a relative path to the folder where output
      should be written. If this folder does not exist, it will be created. If the
      two subfolders (``/case_meta/`` and ``/download_meta``) do not exist within
      the output_path, then they will also be created.

    """
    def __init__(self, docket_path='./results/local_docket_archive',
                 output_path='./results'):
        self.docket_path = docket_path

        self.bugged_path = os.path.abspath(output_path + '/bugged_dockets/') 
        self.output_path = os.path.abspath(output_path + '/parsed_dockets/')
        self.output_meta_path = os.path.abspath(output_path + '/parsed_dockets_meta/')

        #Check that the output path exists and create it if it doesn't
        if not os.path.exists(output_path):
            os.makedirs(self.output_path)
            os.makedirs(self.output_meta_path)
            os.makedirs(self.bugged_path)
        elif (not os.path.exists(self.output_path) or 
              not os.path.exists(self.output_meta_path) or
              not os.path.exists(self.bugged_path)):
            if not os.path.exists(self.output_path):
                os.makedirs(self.output_path)
            if not os.path.exists(self.output_meta_path):
                os.makedirs(self.output_meta_path)
                os.makedirs(self.output_meta_path + '/case_meta/')
                os.makedirs(self.output_meta_path + '/download_meta/')
            if not os.path.exists(self.bugged_path):
                os.makedirs(self.bugged_path)
                
    def parse_data(self, data):
        """
        Returns a list of all of the docket entries in ``data``, which should be
        a string literal. BeautifulSoup is useed to parse a .html docket file 
        (pass as a string literal through ``data``) into a list
        of docket entries. Each docket entry is also a list.

        This uses html.parser and, in the case of failure, switches to html5lib. 
        
        If it cannot find the table or entries, it will return a string as an
        error message.

        **Keyword Arguments**

        * ``data``: should be a string, read from a .html file.
        
        **Output Documentation**

        0. date_filed
        1. document_number
        2. docket_description
        3. link_exist (this is a dummy to indicate the existence of a link)
        4. document_link (docket_number does not uniquely identify the docket
           entry so we also create a separate unique identifier)
        5. unique_id (document_number is not a unique identifier so we create
           one based on the placement in the .html docket sheet)
        
        """  
        parsed_docket_table = []
    
        # Open the .html docket file and parse using BeautifulSoup 
        # into a list of entries

        # While most files can be processed with html.parser, some files
        # cannot. In those cases, we switch to the more lenient html5lib.

        # A. Make Soup.
        source = BeautifulSoup(data)
        for s in source('script'): s.extract()      #Remove Script Elements
        
        # B. Identify the table.
        docket_table = source.find('table', {'rules':'all'})
        if not docket_table: # Rerun in case we can't find the table
            source = BeautifulSoup(data, "html5lib")
            for s in source('script'): s.extract()
            docket_table = source.find('table', {'rules':'all'})
            if not docket_table: # If still can't find the table, return error.
                return "Error, could not find docket_table."

        # C. Find the entries.
        docket_entries = docket_table.find_all('tr')
        if not docket_entries: #Rerun in case we found the table, but no rows
            source = BeautifulSoup(data, "html5lib")
            for s in source('script'): s.extract()
            docket_table = source.find('table', {'rules':'all'})
            docket_entries = docket_table.find_all('tr')
            if not docket_entries: # If still can't find entries, return error.
                return "Error, could not find docket_entries."

        # D. Parse each entry into a list of characteristics and append to the 
        # parsed_docket_table
        skip_first_line = 0
        for entry in docket_entries:
            if skip_first_line == 0:
                skip_first_line = 1
                continue

            # Turn the docket entry into a list     
            row_cells = entry.find_all('td')
            row_contents = [c.get_text(' ', strip=True) for c in row_cells]
            row_contents = [c.replace('\t','').replace('\r\n','') for c 
                            in row_contents]

            # Truncate extremely long cells:
            for n, content in enumerate(row_contents):
                if len(content) > 20000:
                    row_contents[n] = content[0:20001] + "(TRUNCATED)"

            # Replace missing information
            if row_contents[0] == '':row_contents[0]='NA'
            if row_contents[1] == '':row_contents[1]='NA'
            
            # Search for the link to a document
            link = row_cells[1].find('a')
            if link:
                link_exist = '1'
                link = link.get('href')
            else:
                link_exist = '0'
                link = ''
                
            row_contents.extend([link_exist, link])
            parsed_docket_table.append(row_contents)

        for number, line in enumerate(parsed_docket_table):
            parsed_docket_table[number].append(str(number))

        return parsed_docket_table

    def extract_download_meta(self, data):
        """
        Returns a dictionary that contains all of the downloadmeta that was
        stored by ``pacer_lib.scraper()`` at the time of download (i.e., the
        *detailed_info* json object that is commented out at the top of new
        downloads from PACER). This is meant to help improve reproducibility.

        *detailed_info* is an add-on in later versions of pacer_lib that
        records case-level data from the search screen (date_closed, link, 
        nature of suit, case-name, etc.) as well as the date and time of
        download.
        
        In earlier versions of pacer_lib (i.e., released as 
        pacer_scraper_library), this was stored as a list and did not include
        the date and time of download. ``extract_download_meta()`` can also
        handle these *detailed_info* objects.
        
        If there is no *detailed_info*, the function returns a dictionary with
        the key 'Error_download_meta'.
        
        **Keyword Arguments**

        * ``data``: should be a string, read from a .html file.
        
        **Output Documentation**
        Unless otherwise noted, all of these are collected from the PACER
        Case Locator results page. This is documented as 
        ``key``: description of value.        
        
        These terms are found in documents downloaded by any version of pacer_lib:

        * ``searched_case_no``: the case number that was passed to pacer_lib.scraper(),
          this is recorded to ensure reproducibility and comes from pacer_lib. 
          This is not found on the PACER Case Locator results page.

        * ``court_id``: the abbreviation for the court the case was located in
        * ``case_name``: the name of the case, as recorded by PACER
        * ``nos``: a code for "Nature of Suit"
        * ``date_filed``: the date the case was filed, as recorded by PACER
        * ``date_closed``: the date the case was closed, as recorded by PACER
        * ``link``: a link to the docket
        
        These are only in documents downloaded with newer versions of 
        pacer_lib:

        * ``downloaded``: string that describes the time the docket was 
          downloaded by pacer_lib. This is not found on the PACER Case Locator 
          results page. (Format: yyyy-mm-dd,hh:mm:ss)
        * ``listed_case_no``: string that describes the preferred PACER case no
          for this case (as opposed to the query we submitted)
        * ``result_no``: which result was the case on the PACER Case Locator
          results page.

        """
        source = BeautifulSoup(data)
        r = source.find(text=lambda text:isinstance(text, Comment))
        if r:
            # New detailed_info
            if "detailed_info:" in r and '{' in r:
                r = r.replace('detailed_info:\n','').replace("\"\"", "\"")
                r = r.replace(" \"", " \\\"").replace("\" ","\\\" ") # fix internal quotation marks
                detailed_info = eval(r)

            # Legacy detailed_info
            elif "detailed_info:" in r and '(' in r:
                r = r.replace('detailed_info:', '')
                r = r.replace('(','[').replace(')',']').replace("\"\"", "\"").strip()
                r = r.replace(" \"", " \\\"").replace("\" ","\\\" ") # fix internal quotation marks
                temp = eval(r)
                detailed_info = {'searched_case_no':temp[0],
                                 'court_id':temp[1],
                                 'case_name':temp[2],
                                 'nos':temp[3],
                                 'date_filed':temp[4],
                                 'date_closed':temp[5],
                                 'link':temp[6]}
            else:
                return {'Error_download_meta' : '\'detailed_info:\' not found'}
        else:
            return {'Error_download_meta' : 'no comments in source code'}

        return detailed_info

    def extract_lawyer_meta(self, data):
        """
        Returns a dictionary of information about the plaintiff, defendant and
        their lawyers extracted from an .html docket (passed as a string literal
        through ``data``).
        
        At the moment, ``extract_lawyer_meta()`` only handles the most common
        listing (i.e., if there is one listing for plaintiff and one listing
        for defendant). If there is more than one set of plaintiffs or
        defendants (e.g., in a class action suit), the function will return a 
        dictionary with a single key *Error_lawyer_meta*. This function will not
        handle movants and will probably not handle class-action cases. 
        
        In dockets downloaded from older versions of pacer_lib 
        (e.g., pacer_scraper_library), lawyer information was not requested so
        the dockets will not contain any lawyer_meta to be extracted.
        
        **Output Documentation**
        This is documented as ``key``: description of value.
        
        * ``plaintiffs``: list of the names of plaintiffs
        * ``defendants``: list of the names of defendants
        * ``plaintiffs_attorneys``: list of the name of attorneys representing
          the plaintiffs
        * ``defendants_attorneys``: list of the name of attorneys representing 
          the defendants
        * ``plaintiffs_attorneys_details``: string that contains the cleaned
          output of all plaintiff lawyer data (e.g., firm, address, email, etc.)
          that can be further cleaned in the future.
        * ``defendants_attorneys_details``: string that contains the cleaned
          output of all defendant lawyer data (e.g., firm, address, email, etc.)
          that can be further cleaned in the future.

        """
        source = BeautifulSoup(data)
        table_id = {'border':'0',
                    'cellspacing':'5',
                    'width':'100%'}
        tables = source.find_all('table', table_id)

        lawyer_table = ''
        # Identify the base table that holds lawyer meta
        base = ''
        for table in tables:
            filter_text = table.get_text().lower()
            # Skip the top meta info
            if ("jury demand" in filter_text
                or "date filed" in filter_text
                or "docket text" in filter_text):
                continue

            if ("plaintiff" in filter_text 
                and "defendant" in filter_text
                and "represented" in filter_text):
                base = table

        if not base:
            return {'Error_lawyer_meta' : 'Could not identify table'}

        rows = base.find_all('tr')

        #Keep track of the parsing
        plaintiff_row = ''
        defendant_row = ''
        parse_state = 0

        for row in rows:
            # Change the state as we pass different rows
            if "Plaintiff" in row.get_text():
                parse_state = 1
                continue
            if "Defendant" in row.get_text():
                parse_state = 2
                continue
            if "Fictitious Defendant" in row.get_text():
                parse_state = 3

            # Skip empty rows
            if not row.get_text().strip():
                continue

            # Assign the next non-empty row to plaintiff and defendant
            # The order should not matter
            if parse_state == 1 and not plaintiff_row:
                plaintiff_row = row

            if parse_state == 2 and not defendant_row:
                defendant_row = row

        # Return an error if we don't find any applicable rows.
        if parse_state == 0:
            return {'Error_lawyer_meta' : 'Could not identify any rows.'}

        plaintiff_cells = plaintiff_row.find_all('td', {'width':'40%'})
        defendant_cells = defendant_row.find_all('td', {'width':'40%'})
        
        if len(defendant_cells) != 2 or len(plaintiff_cells) != 2:
            return {'Error_lawyer_meta' : 'Too many cells or not enough cells. Check source.'}

        # Clean the plaintiffs names.
        plaintiffs = plaintiff_cells[0].find_all('b')
        for n, name in enumerate(plaintiffs):
            new_name = name.get_text().strip()
            new_name = new_name.replace('\t', ' ')
            while '  ' in new_name:
                new_name = new_name.replace('  ', ' ')
            plaintiffs[n] = new_name

        plaintiffs_attorneys = plaintiff_cells[1].find_all('b')
        for n, name in enumerate(plaintiffs_attorneys):
            new_name = name.get_text().strip()
            new_name = new_name.replace('\t', ' ')
            while '  ' in new_name:
                new_name = new_name.replace('  ', ' ')
            plaintiffs_attorneys[n] = new_name

        plaintiffs_attorneys_details = plaintiff_cells[1].get_text().strip()
        plaintiffs_attorneys_details = plaintiffs_attorneys_details.replace('\r', '')
        while '  ' in plaintiffs_attorneys_details:
            plaintiffs_attorneys_details = plaintiffs_attorneys_details.replace('  ', ' ')

        while '\n ' in plaintiffs_attorneys_details:
            plaintiffs_attorneys_details =  plaintiffs_attorneys_details.replace('\n ', '\n')

        while '\n\n' in plaintiffs_attorneys_details:
            plaintiffs_attorneys_details = plaintiffs_attorneys_details.replace('\n\n', '\n')

        # Clean the defendants names
        defendants = defendant_cells[0].find_all('b')
        for n, name in enumerate(defendants):
            new_name = name.get_text().strip()
            new_name = new_name.replace('\t', ' ')
            while '  ' in new_name:
                new_name = new_name.replace('  ', ' ')
            defendants[n] = new_name

        defendants_attorneys = defendant_cells[1].find_all('b')
        for n, name in enumerate(defendants_attorneys):
            new_name = name.get_text().strip()
            new_name = new_name.replace('\t', ' ')
            while '  ' in new_name:
                new_name = new_name.replace('  ', ' ')
            defendants_attorneys[n] = new_name

        defendants_attorneys_details = defendant_cells[1].get_text().strip()
        defendants_attorneys_details = defendants_attorneys_details.replace('\r', '')
        while '  ' in defendants_attorneys_details:
            defendants_attorneys_details = defendants_attorneys_details.replace('  ', ' ')

        while '\n ' in defendants_attorneys_details:
            defendants_attorneys_details =  defendants_attorneys_details.replace('\n ', '\n')

        while '\n\n' in defendants_attorneys_details:
            defendants_attorneys_details = defendants_attorneys_details.replace('\n\n', '\n')
        
        lawyer_meta_dict = {'plaintiffs':plaintiffs,
                            'plaintiffs_attorneys':plaintiffs_attorneys,
                            'plaintiffs_attorneys_details':plaintiffs_attorneys_details,
                            'defendants':defendants,
                            'defendants_attorneys':defendants_attorneys,
                            'defendants_attorneys_details':defendants_attorneys_details}

        return lawyer_meta_dict

    def extract_case_meta(self, data):
        """
        Returns a dictionary of case information (e.g., case_name, demand,
        nature of suit, jurisdiction, assigned judge, etc.) extracted from
        an .html docket (passed as a string literal through ``data``). This
        information should be available in all dockets downloaded from PACER.

        This information may overlap with information from 
        ``extract_download_meta()``, but it is technically extracted from a 
        different source (the docket sheet, rather than the results page of the
        PACER Case Locator).
        
        In consolidated cases, there is information about the
        lead case, and a link. We extract any links in the case_meta section of
        the document and store it in the dictionary with the key *meta_links*.

        There are some encoding issues with characters such as \xc3 that we have
        tried to address, but may need to be improved in the future.
        
        If ``extract_case_meta()`` cannot find the case_meta section of the
        docket, it will return a dictionary with a single key, 
        *Error_case_meta*.
        
        **Output Documentation**
        Please note that ``extract_case_meta`` does common cleaning and then
        treats each (text):(text) line as a key:value pair, so this 
        documentation only documents the most common keys that we have observed.

        These keys are, generally, self-explanatory and are only listed for
        convenience.
        
        * ``Case name``
        * ``Assigned to``
        * ``Referred to``
        * ``Demand``
        * ``Case in other court``
        * ``Cause``
        * ``Date Filed``
        * ``Date Terminated``
        * ``Jury Demand``
        * ``Nature of Suit``
        * ``Jurisdiction``
        
        Special keys:

        * ``Member case``: the existence of this key indicates that this is 
          probably the lead case of a consolidated case.
        * ``Lead case``: the existence of this key indicates that this is
          probably a member case of a consolidated case.
        * ``meta_links``: this will only exists if there are links in the
          case_meta section of the PACER docket.
        
        """

        source = BeautifulSoup(data)
        case_meta = ''
        case_meta_dict = {}
        meta_links = []

        # Find the correct cells (split into two columns)
        left_column = source.find_all('td', {'valign':'top', 'width':'60%'})
        for cell in left_column:
            if "Assigned to" in cell.prettify():
                case_meta += cell.text.strip()
                #Extract left column links
                links = cell.find_all('a')
                for link in links:
                    meta_links.append((link.text, link['href']))
                    
        right_column = source.find_all('td', {'valign':'top', 'width':'40%'})
        for cell in right_column:
            if "Date Filed:" in cell.prettify():
                case_meta += cell.text.strip()

        if case_meta == '':
            return {'Error_case_meta' : 'case_meta string not found in columns'}

        #1. CLEAN the case_meta string
        #strip leading whitespace
        case_meta = case_meta.strip()

        #remove carriage returns
        case_meta = case_meta.replace('\r', '')

        #remove double spaces
        while '  ' in case_meta:
            case_meta = case_meta.replace('  ', ' ')

        #remove leading spaces
        while '\n ' in case_meta:
            case_meta = case_meta.replace('\n ', '\n')

        #remove double line breaks
        while '\n\n' in case_meta:
            case_meta = case_meta.replace('\n\n', '\n')

        #remove problem strings
        case_meta = case_meta.replace(':\n', ': ')


        #2. PARSE the case_meta string into a case_meta list
        # and finally into a case_meta dictionary
        case_meta = case_meta.split('\n')
        for n, item in enumerate(case_meta):
            if u'\xa0' in item:
                case_meta[n] = item.replace(u'\xa0', u' ')
            if u'\xc3' in item:
                case_meta[n] = item.replace(u'\c3', '')

            case_meta[n] = case_meta[n].split(':')
            for n2, subitem in enumerate(case_meta[n]):
                case_meta[n][n2] = subitem.strip()

            if len(case_meta[n]) == 1:
                case_meta_dict['Case name'] = case_meta[n][0]
            elif len(case_meta[n]) > 2:
                case_meta_dict[case_meta[n][0]] = ':'.join(case_meta[n][1:len(case_meta[n])])
            else:
                case_meta_dict[case_meta[n][0]] = case_meta[n][1]
        
        #3. Add all links in
        if meta_links:
            case_meta_dict['meta_links'] = meta_links
        return case_meta_dict

    def extract_all_meta(self, data, debug=False):
        """
        Returns two dictionaries, one that has download_meta and one that 
        contains meta extracted from the docket. ``extract_all_meta()`` runs 
        ``extract_case_meta()``, ``extract_lawyer_meta()`` and 
        ``extract_download_meta()`` on ``data`` (a string literal of an .html
        document). It returns two dictionaries (one containing download_meta
        and one containing both case_meta and lawyer_meta) because download_meta
        and case_meta have overlapping information. 
        
        If debug is not turned on, extract_all_meta will ignore any
        error output from the sub functions (e.g., if the functions cannot find
        the relevant sections).
        
        **Output Documentation**
        See the output documentation of  ``extract_case_meta()``, 
        ``extract_lawyer_meta()`` and ``extract_download_meta()``.
        """
        #Check for errors.
        download_meta = self.extract_download_meta(data)
        if "Error_download_meta" in download_meta and not debug:
            download_meta = {}

        case_meta = self.extract_case_meta(data)
        if "Error_case_meta" in case_meta and not debug:
            case_meta = {}

        lawyer_meta = self.extract_lawyer_meta(data)
        if "Error_lawyer_meta" in lawyer_meta and not debug:
            lawyer_meta = {}

        # Check for duplicate keys
        l_c_keys = [key for key in lawyer_meta if key in case_meta]
        if l_c_keys:
           return download_meta, {'Error':'Key Conflicts'}
        else:
            docket_meta = dict(case_meta.items() + lawyer_meta.items())

        return  download_meta, docket_meta

    def parse_dir(self, overwrite=True):
        """
        Run ``parse_data()`` and ``extract_all_meta()`` on each file in the 
        docket_path folder and writes the output to the output_path. 
        
        **Output Documentation**
        This function returns nothing.
        
        **File documentation**
        The docket entries of each docket are stored as a .csv in a folder
        'processed_dockets'. The filename of the csv indicates the source docket
        and the columns represent (in order):
        
        0. date_filed
        1. document_number
        2. docket_description
        3. link_exist (this is a dummy to indicate the existence of a link)
        4. document_link (docket_number does not uniquely identify the docket
           entry so we also create a separate unique identifier)
        5. unique_id (document_number is not a unique identifier so we create
           one based on the placement in the .html docket sheet)
        
        The download meta and case and lawyer meta information of each docket 
        is stored as a JSON-object in the sub-folders 
        'processed_dockets_meta/download_meta/' and
        'processed_dockets_meta/case_meta/' within the output path. The files
        indicate the source docket and are prefixed by **download_meta_** and
        **case_meta_**, respectively.
        """
        csv_headers = ['date_filed', 'document_number', 'docket_description', 
                       'link_exist', 'document_link', 'unique_id']

        # Check for all of the files that have been downloaded
        for dir, list, files in os.walk(self.docket_path):
            for file in files:
                output_filename = (self.output_path + '/' +  
                                   file.replace('html', 'csv'))
                case_meta_filename = (self.output_meta_path + '/case_meta/case_meta_' +
                                      file.replace('html', 'json'))
                download_meta_filename = (self.output_meta_path + 
                                          '/download_meta/download_meta_' + 
                                          file.replace('html', 'json'))

                #If the file exists and we have been told not to overwrite, skip.
                if overwrite or not os.path.exists(output_filename):
                    with open(self.docket_path + '/' + file, 'r') as input:
                        source = input.read()
                        download_meta, case_meta = self.extract_all_meta(source)
                        content = self.parse_data(source)

                        # Error handling; copy the docket out and continue.
                        if (content == "Error, could not find docket_table." or
                            content == "Error, could not find docket_entries."):
                            print file, content
                            with open(self.bugged_path + '/' + file, 'w') as bugged:
                                bugged.write(source)
                            continue

                        #Add the number of download entries
                        case_meta['docket_entries'] = len(content)

                        with codecs.open(output_filename, 'w') as output:
                            writer = UnicodeWriter(output, dialect='excel')
                            writer.writerow(csv_headers)
                            writer.writerows(content)

                        with codecs.open(download_meta_filename, 'w') as output:
                            json.dump(download_meta, output)

                        with codecs.open(case_meta_filename, 'w') as output:
                            json.dump(case_meta, output)                                    

class docket_processor():
    """
    Returns a ``docket_processor()`` object that allows for keyword and boolean
    searching of docket entries from dockets specified in *processed_path*. 
    ``docket_processor`` relies on the use of `docket_parser`` to
    parse .html PACER dockets into structured .csv, although it is theoretically
    possible (but quite tedious) to independently bring dockets into compliance
    for use with ``docket_processor``.
    
    This will give you a set of documents (and their associated links) for
    download (and which can be passed to pacer_lib.scraper()).
    
    The object then outputs a docket-level or consolidated .csv that describes
    all documents that meet the search criteria (stored in *hit_list*).
    
    **Keyword Arguments**

    * ``processed_path`` points to the folder containing .csv docket files
    * ``output_path`` points to the folder where you would like output to be
      stored. Note that the output will actually be stored in a subfolder of the
      *output_path* called */docket_hits/*. If the folders do not exist, they will
      be created.

    """
    def __init__(self, processed_path='./results/parsed_dockets',
                 output_path='./results/'):
        self.processed_path = processed_path
        
        #Check that the output path exists
        if not os.path.exists(output_path + '/docket_hits'):
            os.makedirs(os.path.abspath(output_path) + "/docket_hits")

        self.output_path = os.path.abspath(output_path + '/docket_hits')

        #Initialize dictionary of Docket:Match Listing
        self.hit_list = {}
    
    def search_text(self, text, require_term=[], exclude_term=[], 
                    case_sensitive=False):
        """
        Returns a boolean indicating if all criteria are satisified in
        *text*. The criteria are determined in this way:
        
        * all strings in the list *require_term* are found in *text*
        * and, no strings in the list *exclude_term* are found in 
          *text*

        If you pass a string instead of a list to either *require_term* or 
        *exclude_term*, ``search_text()`` will convert it to a list.

        This search is, by default case-insensitive, but you can turn on
        case-sensitive search through *case_sensitive*.
        """
        # If there are neither required terms or exluded terms, you have
        # used this function incorrectly. You suck. Raises an error.
        if not require_term and not exclude_term:
            raise ValueError('You must search for at least one required or' +
                             'excluded term.')

        # If search terms are single strings, convert them to lists. 
        if isinstance(require_term, str):
            require_term = [require_term]
        if isinstance(exclude_term, str):
            exclude_term = [exclude_term]

        # Convert to case-insensitive
        if not case_sensitive:
            text = text.lower()
            for n, term in enumerate(require_term):
                require_term[n] = term.lower()
            for n, term in enumerate(exclude_term):
                exclude_term[n] = term.lower()

        #SEARCH THE TEXT
        term_match = True
        # Check that all required terms are in the text
        for term in require_term:
            if term not in text:
                term_match = False

        # Check that no excluded terms are in the text
        for term in exclude_term:
            if term in text:
                term_match = False

        return term_match

    def search_docket(self, docket, require_term=[], exclude_term=[], 
                      case_sensitive=False, within=0):
        """
        Returns a lists of docket entries that match the search criteria.
        Docket entries are lists that should have the same structure as 
        described in docket_parser, i.e. in order:

        0. date_filed
        1. document_number
        2. docket_description
        3. link_exist (this is a dummy to indicate the existence of a link)
        4. document_link (docket_number does not uniquely identify the docket
           entry so we also create a separate unique identifier)
        5. unique_id (document_number is not a unique identifier so we create
           one based on the placement in the .html docket sheet)

        The docket is specified by the argument *docket* and searched for 
        in the *self.processed_path* folder.

        The search criteria is specified by *require_term*, *exclude_term*, 
        *case_sensitive* and *within*, such that:

        * if *within* !=0, all searches are constrained to the first x
          characters of the text, where x = *within*
        * all strings in the list *require_term* are found in *text* 
          (or the first x charactersm, if *within* is used)
        * and, no strings in the list *exclude_term* are found in 
          *text* (or the first x charactersm, if *within* is used)
        * if *case_sensitive* =True, then the search is case sensitive

        """

        # Returns a list of entries (list of lists) that matches the search_term
        matched_list = []
        header_passed = False

        with open(self.processed_path + '/' + docket, 'r') as search_csv:
            docket_reader = csv.reader(search_csv, dialect='excel')
            for num, row in enumerate(docket_reader):
                # skip column headers
                if not header_passed: 
                    if row == ['date_filed', 'document_number', 'docket_description', 
                               'link_exist', 'document_link', 'unique_id']:
                        header_passed = True
                        continue

                if within == 0:
                    if self.search_text(row[2], require_term, exclude_term, 
                                        case_sensitive):
                        matched_list.append(row)
                else:
                    in_char = within - 1
                    if self.search_text(row[2][:in_char], require_term, 
                                        exclude_term, case_sensitive):
                        matched_list.append(row)
        return matched_list
                
    def search_dir(self, require_term=[], exclude_term=[], case_sensitive=False, 
                   within=0):
        """
        Runs ``search_docket()`` on each docket in *self.processed_path* and
        adds hits to *self.hit_list* as a key value pair 
        *case_number* : *[docket entries]*, where *case_number* is taken from the
        filename and *[docket_entries]* is a list of docket entries (which are 
        also lists) that meet the search criteria.

        The search criteria is specified by *require_term*, *exclude_term*, 
        *case_sensitive* and *within*, such that:

        * if *within* !=0, all searches are constrained to the first x
          characters of the text, where x = *within*
        * all strings in the list *require_term* are found in *text* 
          (or the first x charactersm, if *within* is used)
        * and, no strings in the list *exclude_term* are found in 
          *text* (or the first x charactersm, if *within* is used)
        * if *case_sensitive* =True, then the search is case sensitive

        Returns nothing.
        """
        #Searches through the directory for all dockets with matching documents
        for root, dir, files in os.walk(self.processed_path):
            for file in files: 
                filename = file.replace('.csv', '')
                #Adds docket with matches to hit_list dictionary
                if filename not in self.hit_list:
                    matched_list = self.search_docket(file, require_term, 
                        exclude_term, case_sensitive, within)
                    if matched_list:
                        self.hit_list[filename] = matched_list
                else:
                    for match in self.search_docket(file, require_term, 
                                                    exclude_term, 
                                                    case_sensitive, within):
                        if match not in self.hit_list[filename]:
                            self.hit_list[filename].append(match)
        
        
    def write_all_matches(self, suffix, overwrite_flag = False):
        """
        Writes all of the matches found in the *self.hit_list* dictionary to 
        a single .csv file (**all_match__[suffix].csv**) in the *self.output_path*. 
        The columns of the .csv are (in order):

        0. case_number (as defined by the source .csv)
        1. date_filed
        2. document_number
        3. docket_description
        4. link_exist (this is a dummy to indicate the existence of a link)
        5. document_link (docket_number does not uniquely identify the docket
           entry so we also create a separate unique identifier)
        6. unique_id (document_number is not a unique identifier so we create
           one based on the placement in the .html docket sheet)

        There is a flag for overwriting.

        You cannot use ``/ \  % * : | " < > . _`` in the suffix.

        Returns nothing.
        """
        csv_headers = ['date_filed', 'document_number', 'docket_description', 
                       'link_exist', 'document_link', 'unique_id']

        suffix = suffix.replace('_', '').replace('/','').replace('\\','')
        suffix = suffix.replace('?','').replace('?','').replace('%','')
        suffix = suffix.replace('*','').replace(':','').replace('|','')
        suffix = suffix.replace('\"','').replace('<','').replace('>','')
        suffix = suffix.replace('.','').replace(' ','')

        if not overwrite_flag:
            if os.path.exists(self.output_path + '/all_match__' +
                              suffix + '.csv'):
                raise IOError('A .csv with the suffix "'+ suffix + 
                              '" already exists. ' +
                              'Choose new suffix or specify '+
                              'overwrite_flag.')

        with open(self.output_path + '/all_match__' + suffix + '.csv', 'w') as f:
            writer = csv.writer(f, dialect= 'excel')
            writer.writerow(csv_headers)

            for key in self.hit_list.keys():
                for row in self.hit_list[key]:
                    temp = row
                    temp.insert(0, key)
                    writer.writerow(temp)

    def write_individual_matches(self, suffix, overwrite_flag = False):
        """
        Writes all of the matches in the *self.hit_list* dictionary to one .csv
        file per docket sheet (determined by the source .csv) in a folder named
        after the suffix. To distinguish
        from the source .csv, they are prefixed by a ^. They are also suffixed 
        to allow for multiple searches of the same source .csv. 

        Suffix is required and if the same suffix is specified, it will 
        overwrite previous searches if the overwrite flag is turned on.
        (It will delete all of the old files in the suffix folder.) 

        You cannot use ``/ \  % * : | " < > . _`` in the suffix.

        Returns nothing.
        """

        csv_headers = ['case_number', 'date_filed', 'document_number', 
                       'docket_description', 'link_exist', 'document_link', 
                       'unique_id']

        suffix = suffix.replace('_', '').replace('/','').replace('\\','')
        suffix = suffix.replace('?','').replace('?','').replace('%','')
        suffix = suffix.replace('*','').replace(':','').replace('|','')
        suffix = suffix.replace('\"','').replace('<','').replace('>','')
        suffix = suffix.replace('.','').replace(' ','')

        # Check if the directory exists. If not, create it. If it does,
        # check if we need to overwrite it. If we do need to overwrite,
        # delete everything in the folder.
        result_path = self.output_path + '/' + suffix
        if not os.path.exists(result_path):
            os.makedirs(result_path)
        else:
            if overwrite_flag:
                for f in os.listdir(result_path):
                    os.remove(result_path + '/' + f)
            else:
                raise IOError('.csv files with the suffix "'+ suffix + 
                              '" already exist. ' +
                              'Choose new suffix or specify '+
                              'overwrite_flag.')
        
        # If everything is working, write the good stuff.
        for key in self.hit_list.keys():
            with open(result_path + '/' + '^' + key + '_' + suffix +'.csv'
                      , 'w') as f:
                 writer = csv.writer(f, dialect='excel')
                 writer.writerow(csv_headers)
                 writer.writerows(self.hit_list[key])         
             
        
    
class document_sorter():
    """
    Not implemented yet. Sorry.
    """
    def __init__(self, docket_path='./results/local_docket_archive',
                 document_path='./results/local_document_archive',
                 output_path='./results',
                 searchable_criteria = 'court'):
        self.docket_path = docket_path
        self.document_path = document_path    

        self.searchable_criteria = searchable_criteria

        self.file_index = {}
        self.flags = []
        #Set the output folder for the text conversions        
        x = """self.output_path = (os.path.abspath(output_path) +'/text_document_archive/')
        if not os.path.exists(output_path):
            os.makedirs(os.path.abspath(output_path) + "/local_docket_archive")
            os.makedirs(os.path.abspath(output_path) + "/local_document_archive")
        elif not os.path.exists(output_path+"/local_docket_archive/"):
            os.makedirs(os.path.abspath(output_path) + "/local_docket_archive/")
            if not os.path.exists(output_path+"/local_document_archive/"):
                os.makedirs(os.path.abspath(output_path) + "/local_document_archive/")
        """

    def convert_PDF_to_text(self, filename):
        """
        Convert a file to text and save it in the text_output_path
        """
        pass

    def convert_all(self, overwrite=False):
        """
        For files in the document path, use convert_PDF_to_text if it
        has not been converted before. Determine if a file is searchable
        or not.
        """

    def set_flag(self):
        """
        Add a criteria to the flagging process.
        """
        pass

    def flag_searchable(self):
        """
        Flag according to self.flags()
        Move files to a folder (make this an option)
        """
        pass

    def count(self):
        """
        Count the file_index
        """
        pass

    def export_file_index(self):
        """
        Save the file_index to a file
        """
        pass

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
# class postprocessor():
#    print datetime.datetime.now().strftime(%Y-%m-%d-%H-%M-%S)
