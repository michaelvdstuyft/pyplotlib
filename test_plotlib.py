from plotlib import PlotLib
import numpy as np

fig = PlotLib()

x = np.arange(23)
y = np.random.randint(8, 20, 23)
a = fig.get_subplot(1, 2, 0, 1)
a.plot_fill(x, y, legend='test')
b = fig.get_subplot(3, 1, 0, 0)
b.plot_fill(x, y, legend='test')
y = np.random.randint(8, 20, 23)
a.plot_fill(x, y, legend='test2')
