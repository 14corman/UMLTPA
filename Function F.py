import sqlite3

# Enter name of the sqlite database file
sqlite_file = 'output_data.sqlite'

conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

# Empty lists which will hold the values for the functions, later to be inputed in the correct column.
    # Start considering entries from 1-500, not from 0.

prop_ext_iframe=[None] 
prop_ext_script=[None]
prop_ext_url_resources= [None]

# This first for loop collects the required metrics for each website.

for x in range (1,501):
    num = (x,)

    # This part of the function calculates proportion of external iframes for each website ID and
        # and stores it in a list 'prop_ext_iframe'.
    
    c.execute('SELECT * FROM http_requests WHERE E = 1 AND visit_id = ?', num)
    ext_iframe, total_iframe = 0,0
    for row in c.fetchall():
        total_iframe += 1
        if row[13] == 1: # row[10] is binary column for external
            ext_iframe += 1 
    if total_iframe !=0 :
        prop_ext_iframe.append(ext_iframe/float(total_iframe))
    else:
        prop_ext_iframe.append(0.0)

    # This part of the function calculates proportion of external scripts for each website ID and
        # and stores it in a list 'prop_ext_script'.
        
    c.execute('SELECT * FROM http_requests WHERE content_policy_type = 2 AND visit_id = ?', num)
    ext_script, total_script = 0, 0
    for row in c.fetchall():
        total_script += 1
        if row[13] == 1: # row[10] is binary column for external
            ext_script += 1
    if total_script !=0 :
        prop_ext_script.append(ext_script/float(total_script))
    else:
        prop_ext_script.append(0.0)

    # This part of the function calculates proportion of URL's which are external resources for each website ID and
        # and stores it in a list 'prop_ext_resources'.

    c.execute('SELECT * FROM http_requests WHERE visit_id = ?', num)
    ext_url_resources, total_url_resources = 0, 0
    for row in c.fetchall():
        total_url_resources += 1
        if row[13] == 1 : # row[10] is binary column for external
            ext_url_resources += 1
    if total_url_resources != 0:
        prop_ext_url_resources.append(ext_url_resources/float(total_url_resources))  
    else:
        prop_ext_url_resources.append(0.0)        

#print prop_ext_iframe        
#print prop_ext_script
#print prop_ext_url_resources

# This second for loop inputs the calculated data into the feature F columns.

for x in range (1,501):  
    c.execute ('UPDATE http_requests SET F_iframe = (?) WHERE visit_id = (?)', (prop_ext_iframe[x], x))
    c.execute ('UPDATE http_requests SET F_script = (?) WHERE visit_id = (?)', (prop_ext_script[x], x))
    c.execute ('UPDATE http_requests SET F_resource = (?) WHERE visit_id = (?)', (prop_ext_url_resources[x], x))

# Committing changes and closing the connection to the database file
conn.commit()
c.close()
conn.close()


