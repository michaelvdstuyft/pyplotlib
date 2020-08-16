from plotlib import PlotLib
import numpy as np
# create random data
x = np.arange(23)
y = np.random.randint(8, 20, 23)
y2 = np.random.randint(8, 20, 23)


# load a figure
fig = PlotLib()
fig.plot_fill(x, y, legend='y')

fig2 = PlotLib()
# create two subplots
a = fig2.get_subplot(1, 2, 0, 1)
b = fig2.get_subplot(1, 2, 0, 0)

# plot data on subplots
a.plot_fill(x, y, legend='y')
b.plot_fill(x, y, legend='y')
a.plot_fill(x, y2, legend='y2')
