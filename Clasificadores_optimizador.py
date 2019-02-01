# coding=utf-8
# __author__ = 'Mario Romera Fernández'

"""
Proyecto Captor 2015

Ejecutable de prueba de diferentes parametros para metodos de Machine Learning de clasificacion de vectores
en publicidad - no publicidad
"""

import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, ExtraTreesClassifier, \
    GradientBoostingClassifier
from sklearn.linear_model import RidgeClassifier
from sklearn.svm import LinearSVC, SVC
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import BernoulliNB
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestCentroid
from sklearn.metrics import classification_report
from sklearn.grid_search import GridSearchCV
from sklearn.cross_validation import StratifiedKFold, KFold, StratifiedShuffleSplit
import sys
from itertools import izip
from Utils import features
import glob

# OBTENCION DE DATOS ---- VECTORES Y TARGETS


# carpeta con los archivos npy y txt, con los mismos nombres cada par
vectorpath = 'D:\i+d\edasnet\prototipo_1\\vector_files\*.npy'
targetpath = 'D:\i+d\edasnet\prototipo_1\\vector_files\*.txt'  # ''

targets = []
vector = []
nombres_archivo = []
primero = True

for targetname, filename in izip(glob.glob(targetpath), glob.glob(vectorpath)):

    print 'Recuperando vector ', filename, targetname
    targetsaux = []
    nombres_archivo.append(os.path.split(filename)[1])
    vectoraux = np.load(filename)
    tamvector = len(vectoraux)
    targetfile = open(targetname, 'r')
    lineas = targetfile.readlines()
    for linea in lineas:
        for i in linea:
            if i.isdigit():
                targetsaux.append(int(i))
    targetsaux = np.array(targetsaux)
    tamtargets = len(targetsaux)

    if tamtargets != tamvector:
        print 'no coinciden datosanuncios y targets', tamtargets, tamvector
        if tamvector < tamtargets:
            targetsaux = targetsaux[:-(tamtargets - tamvector)]
        else:
            targetsaux = np.append(targetsaux, np.array([targetsaux[-1]] * (tamvector - tamtargets)))

    if primero:
        vector = np.array(vectoraux)
        targets = np.array(targetsaux)
    else:
        vector = np.row_stack([vector, np.array(vectoraux)])
        targets = np.append(targets, np.array(targetsaux), axis=0)
    primero = False

if len(vector) == 0 or len(targets) == 0:
    print 'error en la carga de archivos'
    print sys.exit()
elif not len(vector) == len(targets):
    print 'no coinciden el vector de parametros y targets'

pruebas = []

config_knn = [{'algorithm': ['auto'], 'n_neighbors': [3, 5, 7],
               'leaf_size': [20, 30, 40, 50]},
              {'algorithm': ['kd_tree'], 'n_neighbors': [3, 5, 7], 'weights': ['uniform', 'distance']}]
model_knn = KNeighborsClassifier()

# si se tiene data sets no balanceados, se puede hacer class_weight={1: 10} por ejemplo
config_linearsvc = [
    {'penalty': ['l1', 'l2'], 'C': [100, 1000, 10000], 'tol': [0.01, 0.001], 'class_weight': [{1: 5}, {1: 10}, 'auto']}]
model_linearsvc = LinearSVC(dual=False)  # np.logspace(-4,4,3) para C

config_svc = [{'kernel': ['sigmoid', 'rbf'], 'C': [100, 1000, 10000], 'tol': [0.01, 0.001],
               'class_weight': [{1: 5}, {1: 10}, 'auto']}]
model_svc = SVC()

config_logisticregression = [{'penalty': ['l1', 'l2'], 'C': [100, 1000, 10000, 100000], 'tol': [0.01, 0.001]}]
model_logisticregression = LogisticRegression()

config_tree = [{'criterion': ['gini'], 'max_features': ['auto', 'sqrt', None], 'min_samples_split': [1, 2, 3]},
               {'criterion': ['entropy'], 'max_features': ['auto', 'sqrt', None], 'min_samples_split': [1, 2, 3]}]
model_tree = DecisionTreeClassifier()

config_treereg = [{'max_features': ['auto', None], 'min_samples_split': [1, 2]}]
model_treereg = DecisionTreeRegressor()

config_naive = [{'alpha': [0.01, 0.07, 0.1, 0.2], 'fit_prior': [True, False]}]
model_naive = BernoulliNB()

config_nearest = [{'metric': ['cityblock', 'cosine', 'euclidean', 'l1', 'l2', 'manhattan']}]  # COMPLETO
model_nearest = NearestCentroid()

config_ridge = [{'alpha': [0.01, 0.1, 1.0], 'solver': ['auto', 'svd', 'cholesky', 'lsqr', 'sparse_cg'],
                 'tol': [0.01, 0.001, 0.0001]}]
model_ridge = RidgeClassifier()

# ENSEMBLE

config_forest = [{'criterion': ['entropy'], 'n_estimators': [100, 200, 300, 400], 'min_samples_split': [1, 2, 3]}]
model_forest = RandomForestClassifier(n_jobs=-1, max_features=None)

config_extraforest = [{'criterion': ['gini'], 'n_estimators': [100, 200, 300, 400],
                       'min_samples_split': [1, 2, 3, 4]},
                      {'criterion': ['entropy'], 'n_estimators': [100, 200, 300, 400], 'min_samples_split': [1, 2, 3]}]
model_extraforest = ExtraTreesClassifier(n_jobs=-1, max_features=None)

config_gradient = [
    {'learning_rate': [0.01, 0.1, 0.5, 1.0], 'n_estimators': [100, 200, 300, 400], 'min_samples_split': [1, 2, 3]}]
model_gradient = GradientBoostingClassifier(max_features=None)

config_ada = [{'n_estimators': [20, 30, 100, 200], 'learning_rate': [0.01, 0.1, 0.5, 1.0]}]
model_ada = AdaBoostClassifier(SVC(), algorithm='SAMME')

config_ada2 = [{'n_estimators': [20, 30, 100, 200], 'learning_rate': [0.01, 0.1, 0.5, 1.0]}]
model_ada2 = AdaBoostClassifier(DecisionTreeClassifier(), algorithm='SAMME')
config_ada3 = [{'n_estimators': [20, 30, 100, 200], 'learning_rate': [0.01, 0.1, 0.5, 1.0]}]
model_ada3 = AdaBoostClassifier(algorithm='SAMME.R')

pruebas.append((config_ada2, model_ada2))
pruebas.append((config_gradient, model_gradient))
pruebas.append((config_forest, model_forest))
# pruebas.append((config_ada,model_ada))
pruebas.append((config_extraforest, model_extraforest))
pruebas.append((config_ada3, model_ada3))
'''
#10 modelos a Optimizar

pruebas.append((config_svc,model_svc))
pruebas.append((config_logisticregression,model_logisticregression))
pruebas.append((config_ridge,model_ridge))

#pruebas.append((config_treereg,model_treereg))
#pruebas.append((config_nearest,model_nearest))
#pruebas.append((config_linearsvc,model_linearsvc))
#pruebas.append((config_knn,model_knn))
#pruebas.append((config_tree,model_tree))
#pruebas.append((config_naive,model_naive))
'''
nvector, ntargets = features.undersampling(vector, targets)

# Selector balanceado de indices de pruebas train -test

indices = StratifiedShuffleSplit(ntargets, 3, test_size=0.3)

for train_index, test_index in indices:
    X_train, X_test = vector[train_index], vector[test_index]
    y_train, y_test = targets[train_index], targets[test_index]

print len(ntargets)
print len(y_train)
print len(y_test)

best = 0
ranking = []
for config, model in pruebas:
    print("combinando parametros para resultado f1 de %s" % model)

    clf = GridSearchCV(model, config, scoring='recall', cv=indices, verbose=1)
    clf.fit(nvector, ntargets)
    if clf.best_score_ > best:
        mejor = clf.best_estimator_
        best = clf.best_score_
    print("Mejor configuracion:")
    print(clf.best_estimator_)
    print("Resultado del mejor:")
    print(clf.best_score_)
    '''
    for params, mean_score, scores in clf.grid_scores_:
        print("%0.3f (+/-%0.03f) for %r"
              % (mean_score, scores.std() / 2, params))

    ranking.append((clf,clf.best_estimator_))

    print 'Informe de clasificacion del modelo'

    modelo=clf.best_estimator_
    y_true, y_pred = y_test, modelo.predict(X_test)
    print(classification_report(y_true, y_pred))
    '''

print 'MEJOR CLASIFICADOR'
print mejor
print 'mejor resultado'
print best
