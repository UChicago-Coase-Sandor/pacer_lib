import unittest
import time
from reader import docket_processor

t = docket_processor()
'''
t.search_dir([], ['Kowal'])
t.write_individual_matches("test%")

try:
    t.write_individual_matches("test%")
except:
    print "Error Good"

time.sleep(10)

t = docket_processor()
t.search_dir(['Kowal'],[])
t.write_individual_matches("test", True)

#t.write_all_matches("test", True)
'''

#Test search_text for taking strings
str_test = t.search_text(["this is a string"], "string")
print type(str_test.text)


'''
#Test search_text for matching required
t_req = t.search_text("this is true for required", ["true"])
print t_req
if t_req:
    print "ok"
else:
    print "Error: No match was found"

f_req = t.search_text("this is false for required",["true"])
print f_req 
if not f_req:
    print "ok"
else:
    print "Error: Match was found"



##TESTING AREA##
  
t = docket_processor()



t.search_dir(['koWAl'], ['declaration'])

t.write_all_matches()

t.search_docket(['Kowal','DECLARATION'],[], 'azdce_2+98-cv-00134.csv')

#
t.search_dir('Kowal')



t.search_docket('Kowal', 'azdce_2+98-cv-00134.csv')

test_list=['Kowal', 'plas']

t.search_docket(test_list, 'azdce_2+98-cv-00134.csv')
'''