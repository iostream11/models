"""
This module provide the attack method for deepfool. Deepfool is a simple and
accurate adversarial attack.
"""
from __future__ import division

import logging

import numpy as np

from .base import Attack


class DeepFoolAttack(Attack):
    """
    DeepFool: a simple and accurate method to fool deep neural networks",
    Seyed-Mohsen Moosavi-Dezfooli, Alhussein Fawzi, Pascal Frossard,
    https://arxiv.org/abs/1511.04599
    """

    def _apply(self, adversary, iterations=100, overshoot=0.02):
        """
          Apply the deep fool attack.

          Args:
              adversary(Adversary): The Adversary object.
              iterations(int): The iterations.
              overshoot(float): We add (1+overshoot)*pert every iteration.
          Return:
              adversary: The Adversary object.
          """
        assert adversary is not None

        pre_label = adversary.original_label
        min_, max_ = self.model.bounds()
        f = self.model.predict([(adversary.original, 0)])
        if adversary.is_targeted_attack:
            labels = [adversary.target_label]
        else:
            max_class_count = 10
            if len(f) > max_class_count:
                labels = np.argsort(f)[-(max_class_count + 1):-1]
            else:
                labels = np.arange(len(f))

        gradient = self.model.gradient([(adversary.original, pre_label)])
        x = adversary.original.reshape(gradient.shape)
        for iteration in xrange(iterations):
            w = np.inf
            w_norm = np.inf
            pert = np.inf
            for k in labels:
                if k == pre_label:
                    continue
                gradient_k = self.model.gradient([(x, k)])
                w_k = gradient_k - gradient
                f_k = f[k] - f[pre_label]
                w_k_norm = np.linalg.norm(w_k) + 1e-8
                pert_k = (np.abs(f_k) + 1e-8) / w_k_norm
                if pert_k < pert:
                    pert = pert_k
                    w = w_k
                    w_norm = w_k_norm

            r_i = -w * pert / w_norm  # The gradient is -gradient in the paper.
            x = x + (1 + overshoot) * r_i
            x = np.clip(x, min_, max_)

            f = self.model.predict([(x, 0)])
            gradient = self.model.gradient([(x, pre_label)])
            adv_label = np.argmax(f)
            logging.info('iteration = {}, f = {}, pre_label = {}'
                         ', adv_label={}'.format(iteration, f[pre_label],
                                                 pre_label, adv_label))
            if adversary.try_accept_the_example(x, adv_label):
                return adversary

        return adversary
