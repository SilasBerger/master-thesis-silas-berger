import numpy as np

from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier

trainX = np.array([2, 3, 1.8, 1, 1.6, 45, 1.79, 10, 1.56, 47, 1.66, 51, 2.01, 0.1, 1.63, 53]).reshape((8, 2))
trainY = np.array([0, 0, 1, 0, 1, 1, 0, 1])

knn_train_x = np.array([1, 2, 3, 10, 11]).reshape(5, 1)
knn_train_y = np.array([0, 0, 0, 1, 1])

clf = MultinomialNB()
clf.fit(trainX, trainY)
result = clf.predict_proba(np.array([1.9, 2]).reshape(1, -1))
winning_class = result.argmax()
confidence = result[0][winning_class]
print(result)

knn = KNeighborsClassifier(3)
knn.fit(knn_train_x, knn_train_y)
res_knn = knn.predict_proba(np.array([4, 9, 12]).reshape(-1, 1))
print(res_knn)