#....An Open source Library for Minmax transformation
""" Created on 8/12/2019
  @author:Jayas p Jacob
  """
import numpy as np
from scipy import sparse

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted, check_array, warn_if_not_float


class MinMax(BaseEstimator, TransformerMixin):
   

    def __init__(self, feature_range=(0, 1), copy=True):
        self.feature_range = feature_range
        self.copy = copy

    def fit(self, X, y=None):
       
        X = check_array(X, copy=self.copy, ensure_2d=True,
                        accept_sparse="csc", dtype=np.float32,
                        ensure_min_samples=2)

        if warn_if_not_float(X, estimator=self):
           
            X = X.astype(np.float)

        feature_range = self.feature_range
        if feature_range[0] >= feature_range[1]:
            raise ValueError("Minimum of desired feature range must be smaller"
                             " than maximum. Got %s." % str(feature_range))
        if sparse.issparse(X):
            data_min = []
            data_max = []
            data_range = []
            for i in range(X.shape[1]):
                if X.indptr[i] == X.indptr[i+1]:
                    data_min.append(0)
                    data_max.append(0)
                    data_range.append(0)
                else:
                    data_min.append(X.data[X.indptr[i]:X.indptr[i + 1]].min())
                    data_max.append(X.data[X.indptr[i]:X.indptr[i + 1]].max())
            data_min = np.array(data_min, dtype=np.float32)
            data_max = np.array(data_max, dtype=np.float32)
            data_range = data_max - data_min

        else:
            data_min = np.min(X, axis=0)
            data_range = np.max(X, axis=0) - data_min

        # Do not scale constant features
        if isinstance(data_range, np.ndarray):
            # For a sparse matrix, constant features will be set to one!
            if sparse.issparse(X):
                for i in range(len(data_min)):
                    if data_range[i] == 0.0:
                        data_min[i] = data_min[i] - 1
            data_range[data_range == 0.0] = 1.0
        elif data_range == 0.:
            data_range = 1.

        self.scale_ = (feature_range[1] - feature_range[0]) / data_range
        self.min_ = feature_range[0] - data_min * self.scale_
        self.data_range = data_range
        self.data_min = data_min
        return self

    def transform(self, X):
      
        check_is_fitted(self, 'scale_')

        X = check_array(X, accept_sparse="csc", copy=self.copy)

        if sparse.issparse(X):
            for i in range(X.shape[1]):
                X.data[X.indptr[i]:X.indptr[i + 1]] *= self.scale_[i]
                X.data[X.indptr[i]:X.indptr[i + 1]] += self.min_[i]
        else:
            X *= self.scale_
            X += self.min_
        return X

    def inverse_transform(self, X):
      
        check_is_fitted(self, 'scale_')

        X = check_array(X, copy=self.copy, accept_sparse="csc", ensure_2d=False)
        X -= self.min_
        X /= self.scale_
        return X
