import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib
import seaborn as sns
from multiprocessing import Process, Queue
from mpldatacursor import datacursor


def onpick(event):
    thisline = event.artist
    if type(thisline) == matplotlib.text.Text:
        pass  # delete the artist
    else:
        print(thisline._axes.text(0, 0, "test", bbox={'facecolor': 'white', 'alpha': 0.5, 'pad': 10}, picker=50))
        xdata = thisline.get_xdata()
        ydata = thisline.get_ydata()
        ind = event.ind
        points = tuple(zip(xdata[ind], ydata[ind]))
        print('onpick points:', points)


def onclick(event):
    print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
          ('double' if event.dblclick else 'single', event.button,
           event.x, event.y, event.xdata, event.ydata))


class PlotterThread:
    def __init__(self, input_queue, sns_input_queue, object_input_queue, result_queue):
        self.input_queue = input_queue
        self.result_queue = result_queue
        self.sns_input_queue = sns_input_queue
        self.object_input_queue = object_input_queue
        self.main()

    def main(self):
        objects = dict()
        object_id = 0
        plt.ion()
        pause_interval = .2
        while True:
            try:
                plt.pause(pause_interval)
                pause_interval = min(.2 + pause_interval, 1)
                for i in range(10):
                    if not self.sns_input_queue.empty():
                        pause_interval = .2
                        function, args, kwargs, return_result = self.sns_input_queue.get()
                        result = getattr(sns, function)(*args, **kwargs)
                        if return_result:
                            self.result_queue.put(result)
                    if not self.input_queue.empty():
                        pause_interval = .2
                        function, args, kwargs, save_to_dict, return_result = self.input_queue.get()
                        result = getattr(plt, function)(*args, **kwargs)
                        if save_to_dict:
                            name = f'o{object_id}'
                            objects[name] = result
                            object_id += 1
                            self.result_queue.put((result, name))
                        elif return_result:
                                self.result_queue.put(result)
                    if not self.object_input_queue.empty():
                        pause_interval = .2
                        object, function, args, kwargs, save_to_dict, return_result = self.object_input_queue.get()
                        if type(object) == type('string'):
                            object = objects[object]
                        if type(function) == type("string"):
                            f = getattr(object, function)
                        else:
                            f = getattr(object, function[0])
                            for function_item in function[1:]:
                                f = getattr(f, function_item)

                        result = f(*args, **kwargs)
                        if save_to_dict:
                            name = f'o{object_id}'
                            objects[name] = result
                            object_id += 1
                            self.result_queue.put((result, name))
                        elif return_result:
                            self.result_queue.put(result)
                        # datacursor()

            except Exception as e:
                print(e)


class PlotLibCommunication:
    input_queue = Queue()
    sns_input_queue = Queue()
    object_input_queue = Queue()
    output_queue = Queue()
    start_thread = True

    def __init__(self, color_style="whitegrid", color_palette="muted", fig=None, ax=None, onpick=onpick):
        """
            :param str: color_style:
            :param str:color_palette: can be ["pastel', 'deep', 'muted', 'bright', 'colorblind', 'dark', 'Blues', 'BuGn_r', 'GnBu_d', 'cubehelix', ] for reference: https://seaborn.pydata.org/tutorial/color_palettes.html
        """

        self.color_style = color_style
        self.color_palette = color_palette
        self.plot_nr = 1

        if PlotLib.start_thread:
            p = Process(target=PlotterThread, args=(PlotLib.input_queue, PlotLib.sns_input_queue, PlotLib.object_input_queue, PlotLib.output_queue))
            p.start()
            PlotLib.process = p
            PlotLib.start_thread = False

        self.call_sns_function("set_style", self.color_style, return_result=False)
        if fig is None or ax is None:
            _, self.fig = self.call_function("figure", save_to_dict=True)
            self.call_object_function(self.fig, ["canvas", "mpl_connect"], 'pick_event', onpick)
        else:
            self.fig = fig

        self.ax = ax

    def get_ax(self):
        if self.ax is None:
            gs = gridspec.GridSpec(1, 1)
            _, self.ax = self.call_object_function(self.fig, 'add_subplot', gs[0, 0], save_to_dict=True)
        return self.ax

    def call_function(self, function_name, *args, save_to_dict=False, return_result=True, **kwargs):
        self.input_queue.put((function_name, args, kwargs, save_to_dict, return_result))
        if return_result or save_to_dict:
            while self.output_queue.empty():
                pass
            return self.output_queue.get()

    def call_sns_function(self, function_name, *args, return_result=True, **kwargs):
        self.sns_input_queue.put((function_name, args, kwargs, return_result))
        if return_result:
            while self.output_queue.empty():
                pass
            return self.output_queue.get()

    def call_object_function(self, object, function_name, *args, save_to_dict=False, return_result=True, **kwargs):
        if object is None:
            raise Exception("object cannot be None")
        self.object_input_queue.put((object, function_name, args, kwargs, save_to_dict, return_result))
        if return_result or save_to_dict:
            while self.output_queue.empty():
                pass
            return self.output_queue.get()


class PlotLib(PlotLibCommunication):
    def change_color_style(self, color_style="whitegrid"):
        self.color_style = color_style
        self.call_sns_function("set_style", self.color_style)

    def get_subplot(self, rows, columns, row, col):
        gs = gridspec.GridSpec(rows, columns)
        _, ax = self.call_object_function(self.fig, 'add_subplot', gs[row, col], save_to_dict=True)

        return PlotLib(color_style=self.color_style, color_palette=self.color_palette, fig=self.fig, ax=ax)

    def draw(self, object, function, *args, data=None, legend=None, color=None, live_update=True, line_width=3, **kwargs):
        if not legend is None and not "label" in kwargs.keys():
            kwargs["label"] = legend
        if not "lw" in kwargs.keys():
            kwargs["lw"] = line_width

        self.call_object_function(object, function, *args, data=data, color=color, return_result=False, **kwargs)
        if "label" in kwargs.keys():
            self.call_object_function(self.get_ax(), "legend", return_result=False)
        self.call_object_function(self.get_ax(), "legend", return_result=False)

    def plot(self, *args, scalex=True, scaley=True, data=None, legend=None, color=None, live_update=True, picker=5, line_width=3, alpha=1, **kwargs):
        if color is None:
            color = [*sns.color_palette(self.color_palette, self.plot_nr)[self.plot_nr-1], alpha]
            self.plot_nr += 1
        try:
            self.draw(self.get_ax(), "plot", *args, scalex=scalex, scaley=scaley, data=data, legend=legend, color=color, live_update=live_update, line_width=line_width, alpha=alpha, picker=picker, **kwargs)
        except:
            self.draw(self.get_ax(), "plot", *args, scalex=scalex, scaley=scaley, data=data, legend=legend, color=color, live_update=live_update, line_width=line_width, alpha=alpha, pickradius=picker, **kwargs)

    def plot_fill(self, *args, scalex=True, scaley=True, data=None, legend=None, color=None, live_update=True, line_width=3, alpha=1, fill_alpha=.3, **kwargs):
        if color is None:
            color = [*sns.color_palette(self.color_palette, self.plot_nr)[self.plot_nr - 1], alpha]
            self.plot_nr += 1
            fill_color = list(color)
            fill_color[-1] = fill_alpha

        self.plot(*args, scalex=scalex, scaley=scaley, data=data, legend=legend, color=color, live_update=live_update, line_width=line_width, **kwargs)
        self.call_object_function(self.get_ax(), "fill_between", *args, color=fill_color, return_result=False)

    def histogram(self, *args, data=None, legend=None, color=None, live_update=True, line_width=3, alpha=.3, edge_color=None, **kwargs):
        if color is None:
            color = [*sns.color_palette(self.color_palette, self.plot_nr)[self.plot_nr-1], alpha]
            self.plot_nr += 1
        if edge_color is None:
            edge_color = color[:3]
        self.draw(self.get_ax(), "hist", *args, data=data, legend=legend, color=color, live_update=live_update, line_width=line_width, edgecolor=edge_color, **kwargs)

