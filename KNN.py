# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 19:06:23 2018

@author: Cory Kromer-Edwards
"""

from sklearn.neighbors import KNeighborsClassifier
import sqlite3

#file parameters
dataset_name = "six"
checkpoint_dir = "checkpoint"
database_path = "output_data.sqlite"


def loadData():
    with sqlite3.connect(database_path, check_same_thread=False) as database:
        cur = database.cursor()
#        cur.execute("DELETE FROM prediction_table")
#        cur.execute("CREATE TABLE IF NOT EXISTS prediction_table (\
#            id INTEGER PRIMARY KEY AUTOINCREMENT,\
#            url TEXT,\
#            visit_id INTEGER,\
#            trained TEXT,\
#            knn_pred INTEGER,\
#            nn_pred INTEGER);")
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
    t_positive = 0
    t_negative = 0
    f_positive = 0
    f_negative = 0
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
        
        result = int(neigh.predict([data_row])[0])
        
#        print("Pred = ", result)
#        print("Correct = ", row[10])
#        print()
        
        if result == row[10]:
          right += 1
          if result == 1:
            t_positive += 1
          else:
            t_negative += 1
            
        if result != row[10]:
          if result == 1:
            f_positive += 1
          else:
            f_negative += 1
          
#        cur.execute("INSERT INTO prediction_table (url, visit_id, trained, knn_pred) VALUES (?, ?, ?, ?)", (row[11], row[12], dataset_name, result))
        
#        x.append(data_row)
#        y.append(row[10])
#        print("DATA: ", [data_row])
#        print("URL %s has pred %d" % (row[11], neigh.predict([data_row])))
    print("Accuracy = ", (right / total))
    print("False positive = ", f_positive)
    print("False negative = ", f_negative)
    print("True negative = ", t_negative)
    print("True positive = ", t_positive)
    
    
    precision = t_positive / (t_positive + f_positive)
    recall = t_positive / (t_positive + f_negative)
    f_1 = 2 * ((precision * recall) / (precision + recall))
    
    print("Precision = ", precision)
    print("Recall = ", recall)
    print("F1 score = ", f_1)
#    database.commit()