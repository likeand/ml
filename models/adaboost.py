# -*- coding: utf-8 -*-
# @Date  : 2020/5/27
# @Author: Luokun
# @Email : olooook@outlook.com

import numpy as np


class AdaBoost:
    """
    Adaptive Boosting(自适应提升算法)
    """

    def __init__(self, n_estimators: int, eps=1e-5):
        """
        :param n_estimators: 弱分类器个数
        :param eps: 误差阈值
        """
        self.n_estimators, self.eps = n_estimators, eps
        self.estimators = []
        self.alpha = np.empty([n_estimators])  # 弱分类器权重
        self._X, self._Y, self._weights = None, None, None

    def fit(self, X: np.ndarray, Y: np.ndarray):
        self._X, self._Y, self._weights = X, Y, np.full([len(X)], 1 / len(X))
        estimators = [self._WeakEstimator(f) for f in range(X.shape[1])]  # 所有特征的弱分类器
        predictions = np.zeros([len(estimators), len(Y)])  # 弱分类器输出
        for i, estimator in enumerate(estimators):
            estimator.fit(X, Y)  # 逐特征训练弱分类器
            predictions[i] = estimator(X)  # 记录所有弱分类器输出
        for k in range(self.n_estimators):
            errors = np.array([
                np.sum(np.where(pred == Y, 0, self._weights)) for pred in predictions
            ])  # 计算每一个弱分类器的带权重误差
            idx = int(np.argmin(errors))  # 选择最小误差
            if errors[idx] < self.eps:  # 误差达到阈值，停止
                break
            self.estimators.append(estimators[idx])  # 添加弱分类器
            self._update_alpha(k, errors[idx])  # 更新弱分类器权重
            self._update_weights(k, predictions[idx])  # 更新样本权重
        self._X, self._Y, self._weights = None, None, None

    def predict(self, X: np.ndarray):
        pred = np.array([
            alpha * estimator(X) for alpha, estimator in zip(self.alpha, self.estimators)
        ])
        pred = np.sum(pred, axis=0)
        return np.where(pred > 0, 1, -1)

    def _update_alpha(self, k: int, e: float):  # 更新弱分类器权重
        self.alpha[k] = .5 * np.log((1 - e) / e)

    def _update_weights(self, k: int, pred: np.ndarray):  # 更新样本权重
        exp_res = np.exp(-self.alpha[k] * self._Y * pred)
        self._weights = self._weights * exp_res / (self._weights @ exp_res)

    class _WeakEstimator:  # 弱分类器, 一阶决策树
        def __init__(self, feature: int):
            self.feature = feature  # 划分特征
            self.split_value, self.sign = None, None  # 划分值、符号

        def fit(self, X: np.ndarray, Y: np.ndarray):
            pos_corr, neg_corr = np.sum(Y == 1), np.sum(Y == -1)
            Xf = X[:, self.feature]
            if pos_corr >= neg_corr:
                self.split_value, self.sign, max_corr = np.min(Xf) - .5, 1.0, pos_corr
            else:
                self.split_value, self.sign, max_corr = np.max(Xf) + .5, -1.0, neg_corr
            indices = np.argsort(Xf)
            for i in range(len(Xf) - 1):
                pos_corr -= Y[indices[i]]
                neg_corr += Y[indices[i]]
                if pos_corr > max_corr:
                    self.sign, max_corr = 1.0, pos_corr
                elif neg_corr > max_corr:
                    self.sign, max_corr = -1.0, neg_corr
                else:
                    continue
                self.split_value = (Xf[indices[i]] + Xf[indices[i + 1]]) / 2
                if max_corr == len(Xf):
                    break

        def __call__(self, X: np.ndarray):
            return np.where(X[:, self.feature] > self.split_value, self.sign, -self.sign)
