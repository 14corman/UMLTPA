import sqlite3

# Enter name of the sqlite database file
sqlite_file = 'adblock_mode.sqlite'

conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

"""
# create New table

table_name = 'new_table'   # name of the table to be created
id_field = 'new_id' # name of the ID column
field_type = 'REAL'  # column data type

c.execute('CREATE TABLE {tn} ({fn} {ft} PRIMARY KEY)'\
        .format(tn=table_name, fn=id_field, ft=field_type))
 
#  Create new column in existing table

table_name ='' # Enter Table Name
new_column ='new_column'
column_type = 'NULL' #(INTEGER, 'TEXT', NULL, REAL, BLOB)

c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
        .format(tn=table_name, cn=new_column, ct=column_type))
"""
for x in range (1,7):
    num = (x,)
    c.execute('SELECT * FROM http_requests WHERE E = 1 AND visit_id = ?', num)
    int_iframe, ext_iframe = 0,0
    for row in c.fetchall():
        if row[13] == 1: # row[10] is binary column for external
            ext_iframe += 1
        else:
            int_iframe += 1
    print ext_iframe, int_iframe

    c.execute('SELECT * FROM http_requests WHERE content_policy_type = 7 AND visit_id = ?', num)
    int_script, ext_script = 0, 0
    for row in c.fetchall():
        if row[13] == 1: # row[10] is binary column for external
            ext_script += 1
        else:
            int_script += 1
    print ext_script, int_script



# Committing changes and closing the connection to the database file
#conn.commit()
c.close()
conn.close()
