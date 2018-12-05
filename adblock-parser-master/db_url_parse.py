import sqlite3
from abparser import abparser
from Crypto.Cipher import AES # pip install pycryptodome
                             #python -m Crypto.SelfTest (to test install)

# Enter name of the sqlite database file
sqlite_file = 'output_data_detected_ads.sqlite'

conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

match = abparser.lookup()

c.execute('SELECT * FROM http_requests')

id_ = 0
for row in c.fetchall():
    id_ += 1
    url = row[3]
    c.execute('UPDATE http_requests SET current_list = ? WHERE id = ?', (match.match_url(url), id_))
     
conn.commit()
c.close()
conn.close()
