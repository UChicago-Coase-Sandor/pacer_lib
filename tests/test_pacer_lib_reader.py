import sys, os
sys.path.insert(0, os.path.dirname("../pacer_lib/"))

import unittest
from reader import docket_parser, docket_processor

class test_docket_parser(unittest.TestCase):
    def setUp(self):
        self.p = docket_parser()
        self.path = './results/local_docket_archive/'
    def test_parse_data(self):
        # Test the good case
        with open(self.path + 'azdce_2_01-cv-01767.html', 'r') as f:
            results = self.p.parse_data(f.read())

            # Check that it got all the docket entries
            self.assertTrue(len(results) == 28)

            # Check that it got the correct number of elements in the row
            self.assertTrue(len(results[0]) == 6)


        # Test a case that we know we've had trouble with before.
        with open(self.path + "cacdce_2_07-cv-03950.html", 'r') as f:
            results = self.p.parse_data(f.read())

            # Check that it got all the docket entries
            self.assertTrue(len(results) == 31)

            # Check that it got the correct number of elements in the row
            self.assertTrue(len(results[0]) == 6)

        # Test a known bad case.
        with open(self.path + "~bad.html", 'r') as f:
            results = self.p.parse_data(f.read())

            # Check that it got all the docket entries
            self.assertTrue("Error" in results)


    def test_extract_download_meta(self):
        # Test legacy download meta
        with open(self.path + 'azdce_2_01-cv-01767.html', 'r') as f:
            results = self.p.extract_download_meta(f.read())
            self.assertTrue(len(results) == 7 )
            self.assertTrue(results['case_name'] == "Irwin, et al v. Zila Inc, et al")

        # Test known troubled meta
        with open(self.path + 'candce_5_06-cv-06486.html', 'r') as f:
            results = self.p.extract_download_meta(f.read())
            self.assertTrue(results['case_name'] =="In re Network Appliance Derivative Litigation")

        # Test new download meta
        with open(self.path + "almdce_2+00-cv-00084.html", 'r') as f:
            results = self.p.extract_download_meta(f.read())
            self.assertTrue(len(results) == 10)
            self.assertTrue (results['case_name'] == "Gilmore v. Mony Life Insurance, et al")
            self.assertTrue ('listed_case_no' in results)

        # Test known bad case
        with open(self.path + "~bad.html", 'r') as f:
            results = self.p.extract_download_meta(f.read())
            self.assertTrue('Error_download_meta' in results)            

    def test_extract_case_meta(self):
        pass

    def test_extract_lawyer_meta(self):
        pass

    def test_extract_all_meta(self):
        pass

    def test_parse_dir(self):
        pass


class test_docket_processor(unittest.TestCase):
    def setUp(self):
        self.p = docket_processor()

    def test_search_text(self):
        pass

    def test_search_docket(self):
        pass

    def test_search_dir(self):
        pass

    def test_write_all_matches(self):
        self.assertTrue(0==1)
        pass

    def test_write_individual_matchest(self):
        pass


x="""
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
"""    

if __name__ == '__main__':
    unittest.main()

