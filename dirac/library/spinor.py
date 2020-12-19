from abc import ABCMeta, abstractmethod

import numpy as np

from dirac.library.grid import *


class SpinorComponent(BaseGrid, metaclass=ABCMeta):

    def __init__(self, data, shape, periodic=False):
        M, N = shape
        self.data = data

        BaseGrid.__init__(self, N, M, periodic)

    @classmethod
    def init_on_full_grid(cls, data, periodic=False):
        shape = data.shape
        idx = cls.stag_to_reg(np.arange(int(data.size / 2)), shape[1])
        data = data.flatten()[idx]

        return cls(data, shape, periodic)

    def complex_interpolate(self, idx):
        n = self[self.get_neighbours(idx)]
        real = np.sum(np.real(n), axis=0) / 4
        imag = np.sum(np.imag(n), axis=0) / 4

        return real + 1j * imag

    def to_full_grid(self):
        full_data = np.zeros(self.M * self.N, dtype=np.complex_)
        exist_idx = self.stag_to_reg(np.arange(self.num), self.N)
        not_exist_idx = np.setdiff1d(np.arange(self.N * self.M), exist_idx)

        full_data[exist_idx] = self.data
        full_data[not_exist_idx] = self.complex_interpolate(not_exist_idx)

        return full_data.reshape(self.M, self.N)

    def __add__(self, other):
        data = self.data.copy()

        not_nan = np.invert(np.isnan(other))
        data[not_nan] = self.data[not_nan] + other[not_nan]

        new = type(self)(data, (self.M, self.N), self.periodic)
        return new

    def __sub__(self, other):
        return self + (-1) * other

    def __mul__(self, other):
        if isinstance(other, type(self)):
            data = self.data * other.data
        else:
            data = self.data * other

        new = type(self)(data, (self.M, self.N), self.periodic)
        return new

    def __rmul__(self, other):
        if isinstance(other, type(self)):
            data = self.data * other.data
        else:
            data = self.data * other

        new = type(self)(data, (self.M, self.N), self.periodic)
        return new


class UComponent(UGrid, SpinorComponent):
    pass


class VComponent(VGrid, SpinorComponent):
    pass


class Spinor:

    def __init__(self, u, v, periodic=False):
        self.u = UComponent.init_on_full_grid(u, periodic)
        self.v = VComponent.init_on_full_grid(v, periodic)
        self.shape = u.shape

    def __abs__(self):
        u, v = self.u.to_full_grid(), self.v.to_full_grid()
        norm = np.real(np.sqrt(u * np.conjugate(u) + v * np.conjugate(v)))
        return norm

    @staticmethod
    def get_meshgrid(shape, delta):
        range = BaseGrid.get_range(shape, delta)
        x = np.linspace(-range[0], range[0], shape[1], endpoint=True)
        y = np.linspace(-range[1], range[1], shape[0], endpoint=True)

        return np.meshgrid(x, y)

    def get_neighbours(self):
        n_u = self.u.get_all_neighbours()
        n_v = self.v.get_all_neighbours()

        return n_u, n_v