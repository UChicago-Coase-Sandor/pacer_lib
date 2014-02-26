import unittest
from pacer_scraper_2_parser import docket_parser

class test_docket_parser(unittest.TestCase):
    def setUp(self):
        par = docket_parser()

#def parser
def parse_all_tests():
    parser = docket_parser()
    parser.parse_dir(True)

def test_parser_extract_download_meta():
    parser = docket_parser()
    with open('./results/local_docket_archive/almdce_2+00-cv-00084.html') as f:
        meta = parser.extract_download_meta(f.read())
        return meta

def test_parser_extract_case_meta():
    parser = docket_parser()
    with open('./results/local_docket_archive/almdce_2+00-cv-00084.html') as f:
        meta = parser.extract_case_meta(f.read())
        return meta

def test_parser_extract_case_meta2():
    parser = docket_parser()
    with open('./results/local_docket_archive/casdce_3+00-cv-02484.html') as f:
        meta = parser.extract_case_meta(f.read())
        return meta        

def test_parser_extract_lawyer_meta():
    parser = docket_parser()
    with open('./results/local_docket_archive/almdce_2+00-cv-00084.html') as f:
        meta = parser.extract_lawyer_meta(f.read())
        return meta

def test_parser_extract_all_meta():
    parser = docket_parser()
    with open('./results/local_docket_archive/almdce_2+00-cv-00084.html') as f:
        meta = parser.extract_all_meta(f.read())
        return meta

def test_parser_extract_all_meta2():
    parser = docket_parser()
    with open('./results/local_docket_archive/azdce_2+98-cv-00020.html') as f:
        meta = parser.extract_all_meta(f.read(), True)
        return meta

def test_parser_prep_for_sql():
    parser = docket_parser()

#def test_docket_read():
#    
    
if __name__ == '__main__':
    parse_all_tests()

