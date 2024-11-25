"""
Created on: 12/10/2024 18:35

Author: Shyam Bhuller

Description: Module for making plots.
"""
from abc import ABC, abstractmethod
from matplotlib.cm import get_cmap
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from matplotlib.backends.backend_pdf import PdfPages

def isinteger(x : np.ndarray) -> np.ndarray:
    return np.equal(np.mod(x, 1), 0)


def set_plot_style():
    """ Set the plotting style for performance tests.
    """
    plt.style.use('ggplot')
    plt.rcParams.update({"axes.prop_cycle" : plt.cycler("color", get_cmap("tab20").colors)})
    return


def figure_dimensions(x : int, orientation : str = "horizontal") -> tuple[int]:
    """ Compute dimensions for a multiplot which makes the grid as "square" as possible.

    Args:
        x (int): number of plots in multiplot
        orientation (str, optional): which axis of the grid is longer. Defaults to "horizontal".

    Returns:
        tuple[int]: length of each grid axes
    """
    nearest_square = int(np.ceil(x**0.5)) # get the nearest square number, always round up to ensure there is enough space in the grid to contain all the plots

    if x < 4: # the special case where the the smallest axis is 1
        dim = (1, x)
    elif (nearest_square - 1) * nearest_square >= x: # check if we can fit the plots in a smaller grid than a square to reduce whitespace
        dim = ((nearest_square - 1), nearest_square)
    else:
        dim = (nearest_square, nearest_square)
    
    if orientation == "vertical": # reverse orientation if needed
        dim = dim[::-1]
    return dim


def hline(v, label : str = None, color = "k", linestyle = "-", autofmt : str = None):
    if autofmt:
        formatter, units = autoscale(v, autofmt, "2f")
        if label:
            label += f" ({formatter(v)} {units})"
    plt.axhline(v, label = label, color = color, linestyle = linestyle)
    return


def autoscale(data : float, units : str, style : str = "2g") -> tuple[FuncFormatter, str]:
    """ Create a formatter to automatically scale units based on provided sample data.

    Args:
        data (float): Sample data.
        units (str): Unit of measure.

    Returns:
        tuple[FuncFormatter, str]: Formatter function for matplotlib and the modified unit of measure.
    """
    scales = ["", "k","M","G","T"]
    scale = int(np.floor(np.log10(data)))//3
    new_units = scales[scale] + units
    if units[0] in scales:
        new_units = scales[scales.index(units[0])] + units[1:]

    def formatter(x, pos):
        if style is None:
            return f"{x/(10**(3*scale))}"
        else:
            return f"{x/(10**(3*scale)):.{style}}"
    return FuncFormatter(formatter), new_units


class PlotBook:
    """ Object to manage saving plots to a pdf file.
    """
    def __init__(self, name : str, open : bool = True) -> None:
        self.name = name
        if ".pdf" not in self.name: self.name += ".pdf" 
        if open: self.open()
        self.is_open = True

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        self.is_open = False

    def save(self):
        if hasattr(self, "pdf"):
            try:
                self.pdf.savefig(bbox_inches='tight')
                plt.close()
            except AttributeError:
                pass

    def open(self):
        if not hasattr(self, "pdf"):
            self.pdf = PdfPages(self.name)
            print(f"pdf {self.name} has been opened")
        else:
            warnings.warn("pdf has already been opened")
        return

    def close(self):
        if hasattr(self, "pdf"):
            self.pdf.close()
            delattr(self, "pdf")
            print(f"pdf {self.name} has been closed")
        else:
            warnings.warn("pdf has not been opened.")
        return

    @classmethod
    @property
    def null(cls):
        return cls(name = "", open = False)


def plot(x, y, label : str, xlabel : str, ylabel : str, newFigure : bool = True, book : PlotBook = None, autofmt : str = None):
    """ Create a line plot.

    Args:
        x : x data.
        y : y data.
        label (str): Label for line.
        xlabel (str): x label.
        ylabel (str): y label.
        newFigure (bool, optional): Option to create a new figure. Defaults to True.
        book (PlotBook, optional): PlotBook to save the plot to. Defaults to None.
        autofmt (str, optional): automatically scale y axis if a unit of measure is given. Defaults to None.
    """
    if newFigure: plt.figure()
    plt.plot(x, y, label = label)

    if autofmt:
        formatter, units = autoscale(max(plt.gca().get_ylim()), autofmt, None)
        plt.gca().yaxis.set_major_formatter(formatter)
        ylabel += f" ({units})"

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if label is not None: plt.legend()
    plt.tight_layout()

    if book is not None:
        book.save()
        plt.clf()
    return


def bar(x, y, xlabel : str, ylabel : str, title : str = None, rotation : int = 0, bar_label : bool = False, horizontal : bool = False, newFigure : bool = True, book : PlotBook = None):
    if newFigure: plt.figure()

    if horizontal:
        rect = plt.barh(x, y)
    else:
        rect = plt.bar(x, y)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)

    bl = []
    if not all(isinteger(rect.datavalues)):
        for i in rect.datavalues:
            if i > 10:
                bl.append(f"{i:,.1f}")
            else:
                bl.append(f"{i:,.3f}")

    if bar_label: plt.bar_label(rect, label_type = "edge", labels = bl)
    plt.xticks(rotation = rotation)
    plt.tight_layout()

    if book is not None:
        book.save()
        plt.clf()
    return


def relative_time(df : pd.DataFrame) -> pd.Series:
    """ Convert absolute time from the performance metric into relative time.

    Args:
        df (pd.DataFrame): Performance metric.

    Returns:
        pd.Series: Relative time.
    """
    time = df.index.astype(int)
    return time - time[0]


class PlotEngine(ABC):
    def __init__(self, metrics : list[str], data : dict[pd.DataFrame]) -> None:
        self.metrics = metrics
        self.data = data
        pass

    @abstractmethod
    def plot_metric(self, metric : str):
        pass


    def plot_display(self):
        """ Plot metrics in a grid layout for displaying in notebooks.
        """
        valid_metrics = [m for m in self.metrics if not self.data[m].empty]
        dims = figure_dimensions(len(valid_metrics), "vertical")

        fig_size = (8 * dims[1], 6 * dims[0])

        plt.figure(figsize = fig_size)
        for i, m in enumerate(valid_metrics):
            plt.subplot(*dims, i + 1)
            self.plot_metric(m)
        return


    def plot_book(self, name : str):
        """ Plot matrics to pdf file.

        Args:
            name (str): file name.
        """
        with PlotBook(name) as book:
            for i in self.metrics:
                plt.figure(figsize=(8*1.2, 6*1.2))
                self.plot_metric(i)
                book.save()
                plt.clf()
        return