import codecs
import cStringIO
import csv
import datetime
import json
import os
import requests
import re
import time
from bs4 import BeautifulSoup, Comment
#import lxml
#Implement logging in the search_agent --> initiate a timestamped logfile (init), initiate an error variable (init) create a function that writes to the file when there is an error, make any query or request store errors and make errors write to that file
#Implement mySQL stuff
class search_agent():
    """
    Returns a ``search_agent()`` object, that serves as an interface for 
    the PACER case locator. It will query and download both dockets 
    and documents. It is a modified requests.sessions object.

    **Keyword Arguments**

    * ``username``: a valid PACER username
    * ``password``: a valid PACER password that goes with ``username``
    * ``output_path``: allows you to specify the relative path where you would
      like to save your downloads. The actual docket sheets will be saved to a
      subfolder within output_path, '/local_docket_archive/'. If the folders do
      not exist, they will be created.
    * ``auto_login``: specify if you would like to login when the object is
      instantiated (you may want to use ``search_agent()`` to create PACER query
      strings).
    * ``wait_time``: how long to wait between requests to the PACER website.

    """
    def __init__(self, username, password, output_path ='./results', auto_login=True, wait_time=1):
        #ATTRIBUTES: username, password, br (browser),
        self.username = username
        self.password = password
        self.wait_time = 1
        #Login to PACER unless told otherwise.
        self.br = ''
        if auto_login:
            self.refresh_login()

        #Check for save folders, and if missing, create them.
        # Check that the folders "/results/" and "local_docket_archive"
        # and "local_document_archive" exists
        if not os.path.exists(output_path):
            os.makedirs(os.path.abspath(output_path) + "/local_docket_archive")
            os.makedirs(os.path.abspath(output_path) 
                        + "/local_document_archive")
        elif not os.path.exists(output_path+"/local_docket_archive/"):
            os.makedirs(os.path.abspath(output_path) + "/local_docket_archive/")
            if not os.path.exists(output_path+"/local_document_archive/"):
                os.makedirs(os.path.abspath(output_path) 
                            + "/local_document_archive/")

        self.output_path = os.path.abspath(output_path)

    def refresh_login(self):
        """
        Logs in to the PACER system using the login and password provided at
        the initialization of ``search_agent()``. This will create a Requests
        session that will allow you to query the PACER system. If 
        *auto_login* =False, ``refresh_login()`` must be called before you can
        query the case_locator. This function will raise an error if you 
        supply an invalid login or password.

        Returns nothing.
        """
        #SETTINGS (determined from the form from PACER's '/login.pl')
        payload = {'loginid':self.username, 'passwd':self.password}
        login_url = 'https://pacer.login.uscourts.gov/cgi-bin/check-pacer-passwd.pl'
        self.br = requests.Session()
        response = self.br.post(login_url, data=payload)
        if "Login Error" in response.text:
            raise ValueError("Invalid PACER username or password.")

    def query_case_locator(self, payload):
        """
        Returns a string literal of the HTML of the search results page. This 
        function passes queries to the PACER Case Locator 
        (https://pcl.uscourts.gov/dquery) and this is the simplest interface
        (you can send any key:value pairs as a POST request). 

        We do not recommend using this unless you want more advanced
        functionality. 

        **Keyword Arguments**

        * ``payload``: key-value pairs that will be converted into a POST 
          request.

        """
        #Locator
        locator_url = 'https://pcl.uscourts.gov/dquery'
        # 1. INITIALIZATION CHECKS
        # Check if search_agent has started a PACER session
        if not self.br:
            self.refresh_login()
        # Check the POST data
        if type(payload) is not dict:
            raise TypeError("'payload' must be a dictionary.")
        if 'case_no' not in payload:
            print "Warning: You are not searching for a case number."
        response = self.br.post(locator_url, data=payload)
        time.sleep(self.wait_time)
        return response.text

    def search_case_locator(self, case_no, other_options={'court_type':'all',
    'default_form':'b'}):
        """
        Passes a query to the PACER Case Locator and returns a list of search 
        results (as well as error message, if applicable). Returns two objects, 
        a list (*results*) and a string that indicates if there was an error.

        **Keyword Arguments**

        * ``case_no``: a string that represents a PACER query.
        * ``other_options``: allows you to determine the payload sent to 
          ``query_case_locator()``. This is validated in ``search_case_locator()``
          so that you only pass known valid POST requests. The default options
          are those known to be necessary to get search results.

        **Output Documentation**
        Each search result is a dictionary with these keys: 

        * ``searched_case_no``
        * ``result_no``
        * ``case_name``
        * ``listed_case_no``
        * ``court_id``
        * ``nos``
        * ``date_filed``
        * ``date_closed``
        * ``query_link``

        The second object returned is a string that verbosely indicates errors
        that occured. If the search result was found, the string is empty.        
        """
        # 1. CHECK FOR VALID ARGUMENTS AND PREPARE PAYLOAD
        payload = other_options
        # Are these really the only form options?
        form_options = ["all_region","case_no","court_type","date_discharge_end","date_discharge_start","date_dismiss_end","date_dismiss_start","date_filed_end","date_filed_start","date_term_end","date_term_start","default_form","mdl_id","party","ssn","ssn4","stitle"]
        # Make sure that all of the options are valid.
        for key in payload.keys():
            if key not in form_options:
                raise KeyError("'" + key + "' is not a form option.")
        #Add the case_no into the payload
        payload['case_no'] = str(case_no)
        # Ensure that we can query.
        if 'court_type' not in payload:
            payload['court_type'] = 'all'
        if 'default_form' not in payload:
            payload['default_form'] ='b'
        # Check if case_no is in the correct format
        #???? THERE ARE MULTIPLE FORMATS FOR THIS
        # 2. QUERY PACER CASE LOCATOR
        source = self.query_case_locator(payload)
        # Simple error checking of the results.
        if "Invalid case number" in source:
            return [], "ERROR: Invalid Case Number"
        elif "No records found" in source:
            return [], "No Search Results"
        # Pass to BeautifulSoup HTML Parser
        source_code = BeautifulSoup(source)
        # Identify the results table and create a list of search results
        results_table = source_code.find('table', {'align':'center'})
        if results_table:
            search_results = results_table.findAll('tr')
        else:
            return [], "ERROR: No Results Table"
        results = []
        for result in search_results:
            # Skip the row with column headers.
            if not result.find('td', {'class':'court_id'}):
                continue
            # Pull out the cell information.
            case_info = {}
            case_info['searched_case_no'] = case_no
            case_info['result_no'] = result.find('td', {'class':'line_no'}).string
            case_info['case_name'] = result.find('td', {'class':'cs_title'}).string
            case_info['listed_case_no'] = result.find('td', {'class':'case'}).a.string
            case_info['court_id']  = result.find('td', {'class':'court_id'}).string
            case_info['nos'] = result.find('td', {'class':'nos'}).string
            case_info['link'] = result.find('td', {'class':'case'}).a.get('href')
            # Handle the Dates
            dates= result.find_all('td', {'class':'cs_date'})
            if not dates[0].string:
                case_info['date_filed'] = "None"
            else:
                case_info['date_filed'] = dates[0].string
            if not dates[1].string:
                case_info['date_closed'] = "None"
            else:
                case_info['date_closed'] = dates[1].string
            results.append(case_info)
        return results, ""

    def request_docket_sheet(self, docket_link, other_options={}):
        """
        Returns the HTML of the docket sheet specified by *docket_link*.

        You can also pass additional POST requests through *other_options*.
        """
        # Pull up the docket report generator page
        response = self.br.get(docket_link)
        # Identify the Query Token
        temp_search = re.search('DktRpt.pl\?(.*)"',response.text)
        if temp_search:
            query_value = temp_search.group(1)
        else:
            raise ValueError('Unable to parse the docket report generator page')

        # Identify the Case Value
        temp_search = re.search('DktRpt.pl\?(\d*)', docket_link)
        if temp_search:
            case_value = temp_search.group(1)
        else:
            raise ValueError('Bad Link')
        #Set Default Values if no other_options
        payload = other_options
        if not payload:
            payload = {'date_range_type':'Filed',
                        'list_of_member_cases':'on',
                        'list_of_parties_and_counsel':'on',
                        'terminated_parties':'on',
                        'pdf_header':'1',
                        'output_format':'html',
                        'sort1':'oldest date first'}
        # Set case dependent options
        payload['all_case_ids'] = case_value
        payload['CaseNum_' + case_value] = 'on'
        # Request the docket report
        response = self.br.post(docket_link.replace(case_value, query_value), 
                                data=payload)
        # Sometimes, PACER gives you a "many docket entries" page
        if "</form>" in response.text.lower():
            raise SystemError("Many Docket Entries; Charles needs to code in this exception")
            __ = """"temp_search = re.search('DktRpt.pl\?(.*)"',response.text)
            query_value_many = temp_search.group(1)
            if not query_value_many:

            payload_many = {'date_from':''}
            response = self.br.post(docket_link.replace(case_value, 
                                    query_value_many), data=payload_many)"""
        return response.text

    def request_document(self, case_filename, document_link, other_options={}):
        """
        Using a case_filename and a link to the document, this function
        constructs the necesssary POST data and finds the correct document URL
        to download the specified PDF document.

        Returns binary data.

        You can also pass additional POST requests through *other_options*.

        (For version 2.1) Currently only implemented for district courts, but
        should eventually be implemented for bankruptcy and appellate courts. 
        """
        __original_link = document_link

        # 0. Check that the case_filenumber is in the correct format.
        case_filename_search = re.search('([a-zA-Z]{5,6})_(\d)\+(\d\d)-'
                                         '([a-zA-Z]{2})-(\d{1,5})', 
                                         case_filename.lower())
        if case_filename_search:
            court_id = case_filename_search.group(1)
            court_short_id = court_id.replace('ce', '').replace('ke','')
        else:
            raise ValueError('Bad case_filename')

        # 1. Identify case_id, de_seq_num and if it is a single-file document.
        de_seq_num = ''
        case_id = ''
        single_file = True
        # Method 1: Try finding both of the variables in the link.
        case_id_search = re.search('caseid=(\d*)', document_link)
        if case_id_search:
            case_id = case_id_search.group(1)
            de_seq_search = re.search('de_seq_num=(\d*)', document_link)
            if de_seq_search:
                de_seq_num = de_seq_search.group(1)

        # Method 2: Find it in the HTML of the link.
        else:
            r = self.br.get(document_link)
            temp_soup = BeautifulSoup(r.text)
            post_data = temp_soup.find('form')
            # If there is a form, look at the 'onsumbit' attribute.
            if post_data:
                if post_data['onsubmit']:
                    search = re.search("goDLS\('/doc1/\d*','(?P<case_id>\d*)'"
                                        +",'(?P<de_seq_num>\d*)'",
                                        post_data['onsubmit'])
                if search:
                    case_id = search.group('case_id')
                    de_seq_num = search.group('de_seq_num')
            else:
                #If there isn't a form, then this is a multi-file document.
                single_file = False

                #Look for a "View All" Button
                post_data = temp_soup.find('input', {'value':'View All'})
                if post_data:
                    if post_data['onclick']:
                        url = post_data['onclick']
                        url = url.replace('\'', '')
                        url = url.replace('parent.location=', '')

                        document_link = ("https://ecf."+ court_short_id + 
                                         ".uscourts.gov" + url)
                        case_id_search = re.search('caseid=(\d*)', 
                                                   document_link)
                        de_seq_search = re.search('arr_de_seq_nums=(\d*)',
                                    document_link)
                        if case_id_search and de_seq_search:
                            case_id = case_id_search.group(1)
                            de_seq_num = de_seq_search.group(1)
        
        # Check if we identified the case_id or not.
        if not case_id or not de_seq_num:
            if document_link == __original_link:
                raise ValueError('Could not identify case_id or de_seq_num ' +
                                 'from \n\'' + document_link + '\'' )
            else:
                raise ValueError('Multi-part document. Could not identify ' +
                                  'case_id or de_seq_num from \n\'' + 
                                  document_link + '\' or \n\'' + __original_link
                                  +' \'')                                
        
        # 2. Encode the POST Request
        #Default values
        payload = {'caseid' : case_id,
                   'got_receipt' : '1',
                   'pdf_header' : '2',
                   'pdf_toggle_possible' : '1'}

        if single_file:
            payload['de_seq_num'] = de_seq_num,
        else:
            payload['arr_de_seq_nums'] = de_seq_num

        payload.update(other_options)

        # 3. Find the final download link from the'charge' page.
        # (there used to be a retry if cannot open, but removed, for now)
        response = self.br.get(document_link)
        
        # Parse the 'charge' page to find the 'viewdoc' url that will request
        # the actual document.

        temp_soup = BeautifulSoup(response.text)
        viewdoc_url = temp_soup.find('form', {'action':True})
        
        # If there is no form on this page, then we have found another
        # intermediate multi-file document page. Follow the links.  
        if not viewdoc_url:
            multipage_viewdoc_url = temp_soup.find('a', {'onclick':True})
            temp_response = self.br.post(multipage_viewdoc_url.get('href'))
            temp_soup = BeautifuLSoup.response(temp_response.text)
            
            #We should now be at the "Accept Charges Page"
            viewdoc_url = temp_soup.find('form', {'action':True})

        # Pull out the final document URL.
        document_url = viewdoc_url.get('action')

        # 4. Post to the URL from step 3 with the post_data from part 2.
        document = self.br.post(document_url, data=payload)

        # The PDF might be embedded in an iframe.
        iframes = re.search("/cgi-bin/show_temp\.pl\?file=.*=application/pdf",
                            document.text)
        if iframes:
            iframe_src = ("https://ecf." + court_short_id + ".uscourts.gov" + 
                          iframes.group(0))
            document= self.br.post(iframe_src, data=payload)

        # Return the content of the document
        return document.content
    
    def download_case_docket(self, case_no, court_id, other_options={'court_type':'all','default_form':'b'}, overwrite=False):
        """
        Returns a list that indicates the case_no, court_id and any error.
        ``download_case_docket`` also writes the .html docket sheet to
        *self.output_path* (in a subfolder '/local_docket_archive/'. If you set 
        *overwrite*=True, it will overwrite previous dockets. Otherwise, 
        ``download_case_docket`` will check to see if the docket has already 
        been downloaded **before** incurring any additional search or download 
        charges.

        You can also pass additional POST requests through *other_options*.
        """
        # ':' is not an acceptable character for Windows filenames, so we replace it with '+'. In older versions, we replaced it with '_'.
        docket_filepath = (self.output_path + "/local_docket_archive/"+ court_id
                           + '_' + case_no.replace(':', '+').strip() +'.html')
        # 0. Check if this docket has already been downloaded
        if overwrite is False:
            if os.path.exists(docket_filepath) or \
            os.path.exists(docket_filepath.replace('+','_')):
                return [case_no, court_id, "Docket already downloaded"]

        # 1. Search PACER Case locator using case_no
        results, error = self.search_case_locator(case_no, other_options)
        # 2. IDENTIFY THE CORRECT RESULT
        if not results:
            return [case_no, court_id, error]
        else:
            correct_result = {}
            for result in results:
                # Iterate through the results and identify the case from the right court
                if court_id == result['court_id']:
                    correct_result = result
                    break
            else:
                return [case_no, court_id, 'No cases correspond to this case number in that court']
        # 3. DOWNLOAD THE DOCKET SHEET
        # Convert the link to a direct link to the docket report
        docket_link = correct_result['link'].replace('iqquerymenu', 'DktRpt')
        if not docket_link:
            return [case_no, court_id, "No links to this case."]
        # Add the header (JSON-object)
        detailed_info = ("<!--detailed_info:\n{" +
                     "'searched_case_no':'" + correct_result['searched_case_no'] + "',"+
                     "'result_no':'" + correct_result['result_no'] + "'," +
                     "'case_name':'" + correct_result['case_name'] + "'," +
                     "'listed_case_no':'" + correct_result['listed_case_no'] + "'," +
                     "'court_id':'" + correct_result['court_id'] + "'," +
                     "'nos':'" + correct_result['nos'] + "'," +
                     "'link':'"+ correct_result['link'] + "'," +
                     "'date_filed':'"+ correct_result['date_filed'] + "'," +
                     "'date_closed':'"+ correct_result['date_closed'] + "'," +
                     "'downloaded':'" + datetime.datetime.now().strftime('%Y-%m-%d,%H:%M:%S') +
                     "'}" + "-->\n")
        # Save the docket sheet.
        output = BeautifulSoup(detailed_info + self.request_docket_sheet(docket_link))
        with codecs.open(docket_filepath, 'w', encoding='utf-8') as f:
            f.write(output.prettify())
        # Manually double check
        if case_no not in output.prettify():
            return [case_no, court_id,
                    "WARNING: Docket Downloaded, but manually double check downloaded docket"]
        return [case_no, court_id, "Docket Downloaded"]

    def download_document(self, case_filename, doc_no, doc_link, no_type='U', overwrite=False):
        """
        Returns a list that indicates the case_name, doc_no and any error.
        ``download_case_document`` also writes the .pdf document to
        *self.output_path* (to the sub-folder '/local_document_archive/'. 
        If you set *overwrite*=True, it will overwrite previously downloaded
        documents. Otherwise, ``download_case_document`` will check to see
        if the docket has already been downloaded **before** incurring any 
        additional search or download charges.
        
        (To be implemented) docket_parser() assigns two types of numbers:
        the listed docket number (i.e., the number listed on the page) and
        the unique identifier (i.e., the position of the docket entry on 
        the page). We should default to using the unique identifier, but
        all of the legacy files will be using the listed identifier and we
        will need to reassociate / convert those documents to their unique
        identifier.

        no_type = 'U' --> unique identifier
        no_type = 'L' --> listed identifier

        We have begun implementing this, but this is not completely finished.

        Using the listed identifier should be considered legacy and not advised.

        This will be dangerous in terms of redundant download protection.

        Document this properly once we finish.

        (Not implemented) You can also pass additional POST requests through 
        *other_options*.
        """
        # 0. Check for valid inputs 
        # Check that the case_filenumber is in the correct format.
        case_filename_search = re.search('([a-zA-Z]{5,6})_(\d)\+(\d\d)-'
                                         '([a-zA-Z]{2})-(\d{1,5})', 
                                         case_filename.lower())
        if case_filename_search:
            court_id = case_filename_search.group(1)
            court_short_id = court_id.replace('ce', '').replace('ke','')
        else:
            raise ValueError('Bad case_filename')

        # check that no_type is valid
        if no_type.upper() != 'U' and no_type.upper() != 'L' :
            raise ValueError('Bad no_type. Must be \'U\' or \'L\'')
        else:
            no_type = no_type.upper()

        # ':' is not an acceptable character for Windows filenames, so we 
        # replace it with '+'. In older versions, we replaced it with '_'.
        # We also prefix the document number with a 'U' if we are using 
        # the unique identifier.
        if no_type == 'L':
            doc_filepath = (self.output_path + "/local_document_archive/"+ 
                            case_filename + "_document_"  + str(doc_no) 
                            +'.pdf')
        elif no_type == 'U':
            doc_filepath = (self.output_path + "/local_document_archive/"+ 
                            case_filename + "_document_U" + str(doc_no) 
                            +'.pdf')

        # 0. Check if this docket has already been downloaded
        if overwrite is False:
            if os.path.exists(doc_filepath) or \
            os.path.exists(doc_filepath.replace('+','_')):
                return [case_filename, doc_no, 
                        "Document already downloaded"]

        # 1. Format the download link.
        if "http" in doc_link:
            document_link = doc_link
        else:
            document_link = ("https://ecf." + court_short_id + ".uscourts.gov"
                         + doc_link)

        # 2 Pass the download link to request_document()
        output = self.request_document(case_filename, document_link)

        # 3. Save the output.
        if output:
            with open(doc_filepath, 'w') as f:
                f.write(output)
            return [case_filename, doc_no, "Document downloaded"]
        else:
            return [case_filename, doc_no, "ERROR: Nothing Downloaded"]

def disaggregate_docket_number(combined_docket_number):
    """
    Returns a string that indicates the year of the case and the PACER-valid
    case_id.

    Disaggregates the year from the case number when we have combined docket numbers.
    Combined year and case numbers are often stored as integers, but this
    leads to the truncation of leading zeroes. We restore these leading
    zeroes and then return the two-digit year of the case and the case_id.
    The minimum number of digits for this function is five (which assumes
    that the case was from 2000). If there are further truncations (e.g.,
    '00-00084' stored as '0000084' and truncated to '84'), pre-process your
    case-numbers.
    """
    #Force the docket number to a string.
    combined_docket_number = str(combined_docket_number)
    if len(combined_docket_number) == 6:
        combined_docket_number = '0' + combined_docket_number
    elif len(combined_docket_number) == 5:
        combined_docket_number = '00' + combined_docket_number
    if len(combined_docket_number) != 7:
        raise ValueError ('The docket_number must have either 5, 6 or 7 '
        + 'digits.')
    year = combined_docket_number[0:2]
    case_id = combined_docket_number[2:7]
    return year, case_id

def gen_case_query(district, office, year, docket_number, type_code, district_first=True):
    """
    Creates a PACER query from the district, office, year, case_id and case_type 
    and returns a tuple of (case_id, court_id, region).
    
    PACER case-numbers can be generated by consolidating the district,
    office, year, case id and case type information in a specific way.
    This function formats the district name and type_code correctly and then
    combines the case identifying information into a single PACER query.

    Many other data sources list the district of the court before the state,
    e.g., EDNY rather than NYED. If this is not the case, turn off the
    district_first option.

    **Keyword Arguments**

    * ``year`` should be either 2 digits (e.g., 00) or 4 digits (e.g., 1978).
    * ``case_id`` should be exactly 5digits
    * ``type code`` must be one of the following: civil, civ, criminal, crim,
      bankruptcy, bank, cv, cr, bk
    
    Returns a tuple (case_number, court_id)
    
    (For Version 2.1)
    Note: Appellate Courts have not been implemented yet.
    
    Some of this functionality may not be necessary and should be revisited.
    
    Specifically, year can be 2 or 4 digits and case number does not have to
    be exactly 5 digits (up to 5 digits). Office must be exactly 1 digit.
    
    We could also consider including the specific sate in the output.
    We should also create a list of all valid courtids and check against it.
    """
    type_code_dict = {'civil':'cv', 'civ': 'cv',
                      'criminal': 'cr', 'crim': 'cr',
                      'bankruptcy': 'bk', 'bank': 'bk'}
    state_to_code = {"alaska": "ak", "alabama": "al", "arkansas": "ar",
                    "arizona": "az", "california": "ca", "colorado": "co",
                    "connecticut": "ct", "delaware": "de",
                    "district of columbia": "dc", "florida": "fl",
                    "georgia": "ga", "hawaii": "hi", "iowa": "ia",
                    "idaho": "id", "illinois": "il",
                    "indiana": "in", "kansas": "ks", "kentucky": "ky",
                    "louisiana": "la","maine": "me", "maryland": "md",
                    "massachusetts": "ma", "michigan": "mi", "minnesota": "mn",
                    "mississippi": "ms",  "missouri": "mo", "montana": "mt",
                    "nebraska": "ne", "nevada": "nv", "new hampshire": "nh",
                    "new jersey": "nj", "new mexico": "nm", "new york": "ny",
                    "north carolina": "nc", "north dakota": "nd",
                    "northern mariana islands": "nmi", "ohio": "oh",
                    "oklahoma": "ok", "oregon": "or", "pennsylvania": "pa",
                    "puerto rico": "pr", "rhode island": "ri",
                    "south carolina": "sc", "south dakota": "sd",
                    "tennessee": "tn", "texas": "tx", "utah": "ut",
                    "vermont": "vt", "virgin islands": "vi", "virginia": "va",
                    "washington": "wa", "west virginia": "wv",
                    "wisconsin": "wi", "wyoming": "wy"}
    district_dict = {'northern district': 'nd',
                     'southern district': 'sd',
                     'eastern district': 'ed',
                     'western district': 'wd',
                     'middle district': 'md',
                     'central district': 'cd',
                     'northern bankruptcy': 'nb',
                     'southern bankruptcy': 'sb',
                     'eastern bankruptcy': 'eb',
                     'western bankruptcy': 'wb',
                     'middle bankruptcy': 'mb',
                     'central bankruptcy': 'cb'}
    states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
    district_court_ids = ("almdce",  "alndce", "alsdce", "akdce", "azdce",
                          "aredce", "arwdce", "cacdce", "caedce", "candce",
                          "casdce", "codce", "ctdce", "dedce", "dcdce",
                          "flmdce", "flndce", "flsdce", "gamdce", "gandce",
                          "gasdce", "gudce", "hidce", "iddce", "ilcdce",
                          "ilndce", "ilsdce", "inndce", "insdce", "iandce",
                          "iasdce", "ksdce", "kyedce", "kywdce", "laedce",
                          "lamdce", "lawdce", "medce", "mddce", "madce",
                          "miedce", "miwdce", "mndce", "msndce", "mssdce",
                          "moedce", "mowdce", "mtdce", "nedce", "nvdce",
                          "nhdce", "njdce", "nmdce", "nyedce", "nyndce",
                          "nysdce", "nywdce", "ncedce", "ncmdce", "ncwdce",
                          "nddce", "nmidce", "ohndce", "ohsdce", "okedce",
                          "okndce", "okwdce", "ordce", "paedce", "pamdce",
                          "pawdce", "prdce", "ridce", "scdce", "sddce",
                          "tnedce", "tnmdce", "tnwdce", "txedce", "txndce",
                          "txsdce", "txwdce", "utdce", "vtdce", "vidce",
                          "vaedce", "vawdce", "wawdce", "wvndce", "wvsdce",
                          "wiedce", "wiwdce", "wydce")
    bankruptcy_court_ids = ("almbke", "alnbke", "alsbke", "akbke", "azbke",
                            "arebke", "arwbke", "cacbke", "caebke", "canbke",
                            "casbke", "cobke", "ctbke", "debke", "dcbke",
                            "flmbke", "flnbke", "flsbke", "gambke", "ganbke",
                            "gasbke", "gubke", "hibke", "idbke", "ilcbke",
                            "ilnbke", "ilsbke", "innbke", "insbke", "ianbke",
                            "iasbke", "ksbke", "kyebke", "kywbke", "laebke",
                            "lambke", "lawbke", "mebke", "mdbke","mabke",
                            "miebke", "miwbke", "mnbke", "msnbke", "mssbke",
                            "moebke", "mowbke", "mtbke", "nebke", "nvbke",
                            "nhbke", "njbke", "nmbke", "nyebke", "nynbke",
                            "nysbke", "nywbke", "ncebke", "ncmbke", "ncwbke",
                            "ndbke", "nmibke", "ohnbke", "ohsbke", "okebke",
                            "oknbke", "okwbke", "orbke", "paebke", "pambke",
                            "pawbke", "prbke", "ribke", "scbke", "sdbke",
                            "tnebke", "tnmbke", "tnwbke", "txebke", "txnbke",
                            "txsbke", "txwbke", "utbke", "vtbke", "vibke",
                            "vaebke", "vawbke", "waebke", "wawbke", "wvnbke",
                            "wvsbke", "wiebke", "wiwbke", "wybke")
    # 0. PRE-PROCESS: Force all inputs to string type.
    district = str(district)
    office = str(office)
    year = str(year)
    docket_number = str(docket_number)
    type_code = str(type_code)
    # 1. PROCESS THE TYPE-CODE
    # Convert the type code.
    if type_code.lower() in type_code_dict.keys():
        type_code=type_code_dict[type_code]
    # Check if the user has inputed a valid type_code.
    # ('ap' has not been implemented')
    if type_code not in ('cr', 'cv', 'bk'):
        raise ValueError ('Invalid type-code.')
    #Using the type-code, we determine the correct suffix.
    if type_code in ('cr', 'cv'):
        suffix = 'ce'
    elif type_code in 'bk':
        suffix = 'ke'
    #elif type_code in 'ap':
        #Appellate Cases not yet implemented.
    # 2. PROCESS THE DISTRICT NAME
    district=district.lower().replace(' ','')
    court_id=''
    # For fully written out district names, we attempt to
    # convert this into a useable PACER abbreviation.
    if len(district) > 4:
        # Find the state.
        for key in state_to_code:
            if key.replace(' ', '') in district:
                court_id = state_to_code[key]
                break
        if not court_id:
            raise ValueError ("Invalid 'district' input;"
                               + " could not determine the state in \""
                               + district +"\"")
        #Find the district within the state.
        for key in district_dict:
            if key.replace(' ', '') in district:
                court_id = court_id + district_dict[key]+suffix
                break
        #If the district is not fully written out, one last try.
        if len(court_id) == 2:
            if 'district' in district and 'columbia' not in district:
                court_id = court_id+'d'+suffix
            elif 'bankruptcy' in district:
                court_id = court_id+'b'+suffix
        if len(court_id) < 5 or len(court_id) > 6:
            raise ValueError ("Invalid 'district' input;"
                               + " could not determine the district in \""
                               + district +"\"")
    #Process abbreviations.
    if district_first:
        # The program converts the district input into a court_id.
        if district.startswith('dc') and len(district) == 4:
            # Single-district districts courts.
            court_id = district[2:4]+'dce'
        elif len(district) == 4:
            # Reverse the order of 4-character district codes
            court_id = district[2:4]+district[0:2]+suffix
        elif len(district) == 3:
            # Reverse the order of 3-character codes
            court_id = district[1:3]+district[0:1]+suffix
    else:
        # The program converts the district input into a court_id.
        if district.endswith('dc') and len(district)==4:
            # Single-district districts courts.
            court_id = district[0:2] + 'dce'
        elif len(district) == 4 or len(district) == 3:
            # Append the suffix to 3 or 4 letter districts.
            court_id = district + suffix
    #Raise an error if we have not recognized the court.
    if not court_id:
        raise ValueError("Invalid 'district' input;"
                         + " could not recognize \""
                         + district + "\"")
    # 3. PROCESS YEAR
    if len(year) == 4:
        year = year[2:4]
    if len(year) != 2:
        raise ValueError("Invalid 'year' input;" + "could not recognize \""
                         + year + "\"")
    # 4. SANITY CHECKS
    if len(office) > 1:
        raise ValueError("'office' cannot be more than 1 character")
    if len(type_code) > 2:
        raise ValueError("Final 'type-code' cannot be more than 2 characters")
    if len(docket_number) > 5:
        raise ValueError("'docket_number' cannot be more than 5 characters")
    if type_code == "cv" or type_code == "cr":
        if court_id not in district_court_ids:
            raise ValueError("'" + court_id + "' is an invalid district "
                             + "court_id.")
    elif type_code == "br":
        if court_id not in bankruptcy_court_ids:
            raise ValueError("'" + court_id + "' is an invalid bankruptcy " +
                             "court_id.")
    if court_id[0:2].upper() not in states:
        raise ValueError("'" + court_id + "' is not from a valid state/region")
    # 5. COMBINE INFORMATION
    # Return both the court_id and the case_number as a tuple.
    case_no = office + ":" + year + "-" + type_code + "-" + docket_number
    if type_code != 'ap':
        region = court_id[0:2].upper()
    return (case_no, court_id, region)
