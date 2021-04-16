import numpy as np
import matplotlib.pyplot as plt

from scipy.optimize import curve_fit



def gaussian(x, mean, amplitude, standard_deviation):
    return amplitude * np.exp(- (x - mean) ** 2 / (2 * standard_deviation ** 2))


x = np.random.normal(10, 5, size=10000)

bin_heights, bin_borders, _ = plt.hist(x, bins='auto', label='histogram')
bin_centers = bin_borders[:-1] + np.diff(bin_borders) / 2
popt, _ = curve_fit(gaussian, bin_centers, bin_heights, p0=[1., 0., 1.])

x_interval_for_fit = np.linspace(bin_borders[0], bin_borders[-1], 100000)
plt.plot(x_interval_for_fit, gaussian(x_interval_for_fit, *popt), label='fit')
plt.legend()

plt.show()