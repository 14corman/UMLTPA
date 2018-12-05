# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 19:06:23 2018

@author: Cory Kromer-Edwards
"""

X = [[0], [1], [2], [3], [4], [5], [6], [7]]
y = [0, 0, 1, 1, 0, 0, 1, 1]
from sklearn.neighbors import KNeighborsClassifier
neigh = KNeighborsClassifier(n_neighbors=5, algorithm='kd_tree', weights='distance')
neigh.fit(X, y) 
print(neigh.predict([[3]]))
print(neigh.predict_proba([[3]]))