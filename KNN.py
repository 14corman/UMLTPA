# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 19:06:23 2018

@author: Cory Kromer-Edwards
"""

from sklearn.neighbors import KNeighborsClassifier
import sqlite3

#file parameters
dataset_name = "two"
checkpoint_dir = "checkpoint"
database_path = "output_data_detected_ads.sqlite"


def loadData():
    with sqlite3.connect(database_path, check_same_thread=False) as database:
        cur = database.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS prediction_table (\
            id INTEGER PRIMARY KEY AUTOINCREMENT,\
            url TEXT,\
            visit_id INTEGER,\
            trained TEXT,\
            knn_pred INTEGER,\
            nn_pred INTEGER);")
        cur.execute("SELECT A_one, A_two, B_one, B_two, C_one, C_two, D_one, D_two, F_script, F_resource, " + dataset_name + "_month_list FROM http_requests \
                    WHERE A_one IS NOT NULL AND A_two IS NOT NULL AND B_one IS NOT NULL AND B_two IS NOT NULL AND C_one IS NOT NULL AND\
                    C_two IS NOT NULL AND D_one IS NOT NULL AND D_two IS NOT NULL AND\
                    F_script IS NOT NULL AND F_resource IS NOT NULL")
        
        rows = cur.fetchall()
     
        x = []
        y = []
        for row in rows:
            data_row = []
            data_row.append(row[0])
            data_row.append(row[1])
            data_row.append(row[2])
            data_row.append(row[3])
            data_row.append(row[4])
            data_row.append(row[5])
            data_row.append(row[6])
            data_row.append(row[7])
            data_row.append(row[8])
            data_row.append(row[9])
            
            x.append(data_row)
            y.append(row[10])
            
        
        database.commit()    
        return x, y
  
x, y = loadData()


neigh = KNeighborsClassifier(n_neighbors=5, algorithm='kd_tree', weights='distance')
neigh.fit(x, y) 

with sqlite3.connect(database_path, check_same_thread=False) as database:
    cur = database.cursor()
    cur.execute("SELECT A_one, A_two, B_one, B_two, C_one, C_two, D_one, D_two, F_script, F_resource, current_list,\
                url, visit_id FROM http_requests \
                WHERE A_one IS NOT NULL AND A_two IS NOT NULL AND B_one IS NOT NULL AND B_two IS NOT NULL AND C_one IS NOT NULL AND\
                C_two IS NOT NULL AND D_one IS NOT NULL AND D_two IS NOT NULL AND\
                F_script IS NOT NULL AND F_resource IS NOT NULL AND current_list IS NOT NULL")
    
    rows = cur.fetchall()
    
    right = 0
    total = 0
     
    for row in rows:
        data_row = []
        data_row.append(row[0])
        data_row.append(row[1])
        data_row.append(row[2])
        data_row.append(row[3])
        data_row.append(row[4])
        data_row.append(row[5])
        data_row.append(row[6])
        data_row.append(row[7])
        data_row.append(row[8])
        data_row.append(row[9])
        
        total += 1
        
        result = neigh.predict([data_row])
        
        print("Pred = ", result)
        print("Correct = ", row[10])
        print()
        
        if result == row[10]:
          right += 1
        
#        x.append(data_row)
#        y.append(row[10])
#        print("DATA: ", [data_row])
#        print("URL %s has pred %d" % (row[11], neigh.predict([data_row])))
    print("Accuracy = ", (right / total))