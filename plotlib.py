import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from multiprocessing import Process, Queue


class PlotterThread:
    def __init__(self, input_queue, sns_input_queue, object_input_queue, result_queue):
        self.input_queue = input_queue
        self.result_queue = result_queue
        self.sns_input_queue = sns_input_queue
        self.object_input_queue = object_input_queue
        self.main()

    def main(self):
        objects = dict()
        plt.ion()
        while True:
            try:
                plt.pause(.02)
            except:
                pass

            if not self.input_queue.empty():
                function, args, kwargs, save_to_dict, save_name = self.input_queue.get()
                result = getattr(plt, function)(*args, **kwargs)
                if save_to_dict:
                    objects[save_name] = result
                self.result_queue.put(result)
            if not self.sns_input_queue.empty():
                function, args, kwargs = self.sns_input_queue.get()
                self.result_queue.put(getattr(sns, function)(*args, **kwargs))
            if not self.object_input_queue.empty():
                object, function, args, kwargs, save_to_dict, save_name = self.object_input_queue.get()
                if type(object) == type('string'):
                    object = objects[object]
                result = getattr(object, function)(*args, **kwargs)
                if save_to_dict:
                    objects[save_name] = result
                self.result_queue.put(result)


class PlotLib:
    def __init__(self, color_style="whitegrid", color_palette="muted", fig=None, ax=None, input_queue=None, sns_input_queue=None, object_input_queue=None, output_queue=None, start_thread=True):
        """
            :param str: color_style:
            :param str:color_palette: can be ["pastel', 'deep', 'muted', 'bright', 'colorblind', 'dark', 'Blues', 'BuGn_r', 'GnBu_d', 'cubehelix', ] for reference: https://seaborn.pydata.org/tutorial/color_palettes.html
        """
        self.color_style = color_style
        self.color_palette = color_palette
        self.plot_nr = 1
        if input_queue is None:
            self.input_queue = Queue()
        else:
            self.input_queue = input_queue
        if sns_input_queue is None:
            self.sns_input_queue = Queue()
        else:
            self.sns_input_queue = sns_input_queue
        if object_input_queue is None:
            self.object_input_queue = Queue()
        else:
            self.object_input_queue = object_input_queue
        if output_queue is None:
            self.output_queue = Queue()
        else:
            self.output_queue = output_queue
        if start_thread:
            p = Process(target=PlotterThread, args=(self.input_queue, self.sns_input_queue, self.object_input_queue, self.output_queue))
            p.start()
            self.process = p
        else:
            self.process = None
        self.call_sns_function("set_style", self.color_style)
        if fig is None or ax is None:
            self.fig = "figure"
            self.call_function("figure", save_to_dict=True, save_name=self.fig)
        else:
            self.fig = fig

        self.ax = ax

    def get_ax(self):
        if self.ax is None:
            index = 0
            while f'ax{index}' in PlotLib.existing_names:
                index += 1
            self.ax = f'ax{index}'
            PlotLib.existing_names.add(self.ax)
            gs = gridspec.GridSpec(1, 1)
            self.call_object_function(self.fig, 'add_subplot', gs[0, 0], save_to_dict=True, save_name=self.ax)
        return self.ax

    def call_function(self, function_name, *args, save_to_dict=False, save_name="", **kwargs):
        self.input_queue.put((function_name, args, kwargs, save_to_dict, save_name))
        while self.output_queue.empty():
            pass
        return self.output_queue.get()

    def call_sns_function(self, function_name, *args, **kwargs):
        self.sns_input_queue.put((function_name, args, kwargs))
        while self.output_queue.empty():
            pass
        return self.output_queue.get()

    def call_object_function(self, object, function_name, *args, save_to_dict=False, save_name="", **kwargs):
        if object is None:
            raise Exception("object cannot be None")
        self.object_input_queue.put((object, function_name, args, kwargs, save_to_dict, save_name))
        while self.output_queue.empty():
            pass
        return self.output_queue.get()

    def change_color_style(self, color_style="whitegrid"):
        self.color_style = color_style
        self.call_sns_function("set_style", self.color_style)

    def get_subplot(self, rows, columns, row, col):
        gs = gridspec.GridSpec(rows, columns)
        index = 0
        while f'ax{index}' in PlotLib.existing_names:
            index += 1
        ax = f'ax{index}'
        PlotLib.existing_names.add(ax)
        self.call_object_function(self.fig, 'add_subplot', gs[row, col], save_to_dict=True, save_name=ax)

        return PlotLib(color_style=self.color_style, color_palette=self.color_palette, fig=self.fig, ax=ax, input_queue=self.input_queue, sns_input_queue=self.sns_input_queue, object_input_queue=self.object_input_queue, output_queue=self.output_queue, start_thread=False)

    def draw(self, object, function, *args, data=None, legend=None, color=None, live_update=True, line_width=3, **kwargs):
        if not legend is None and not "label" in kwargs.keys():
            kwargs["label"] = legend
        if not "lw" in kwargs.keys():
            kwargs["lw"] = line_width

        self.call_object_function(object, function, *args, data=data, color=color, **kwargs)
        if "label" in kwargs.keys():
            self.call_object_function(self.get_ax(), "legend")
        self.plot_nr += 1

    def plot(self, *args, scalex=True, scaley=True, data=None, legend=None, color=None, live_update=True, line_width=3, alpha=1, **kwargs):
        if color is None:
            color = [*sns.color_palette(self.color_palette, self.plot_nr)[self.plot_nr-1], alpha]
        self.draw(self.get_ax(), "plot", *args, scalex=scalex, scaley=scaley, data=data, legend=legend, color=color, live_update=live_update, line_width=line_width, alpha=alpha, **kwargs)

    def plot_fill(self, *args, scalex=True, scaley=True, data=None, legend=None, color=None, live_update=True, line_width=3, alpha=1, fill_alpha=.3, **kwargs):
        if color is None:
            color = [*sns.color_palette(self.color_palette, self.plot_nr)[self.plot_nr - 1], alpha]
            fill_color = list(color)
            fill_color[-1] = fill_alpha

        self.plot(*args, scalex=scalex, scaley=scaley, data=data, legend=legend, color=color, live_update=live_update, line_width=line_width, **kwargs)
        self.call_object_function(self.get_ax(), "fill_between", *args, color=fill_color)

    def histogram(self, *args, data=None, legend=None, color=None, live_update=True, line_width=3, alpha=.3, edge_color=None, **kwargs):
        if color is None:
            color = [*sns.color_palette(self.color_palette, self.plot_nr)[self.plot_nr-1], alpha]
        if edge_color is None:
            edge_color = color[:3]
        self.draw(self.get_ax(), "hist", *args, data=data, legend=legend, color=color, live_update=live_update, line_width=line_width, edgecolor=edge_color, **kwargs)

    def test(self):
        import numpy as np

        x = np.arange(23)
        for i in range(1):
            y = np.random.randint(8, 20, 23)
            self.plot_fill(x, y, legend='test')

PlotLib.existing_names = set()