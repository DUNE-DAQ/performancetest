"""
Created on: 12/10/2024 18:35

Author: Shyam Bhuller

Description: Module for making plots.
"""
from abc import ABC, abstractmethod
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.backends.backend_pdf import PdfPages

def set_plot_style():
    """ Set the plotting style for performance tests.
    """
    plt.style.use('ggplot')
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


def plot(x, y, label : str, xlabel : str, ylabel : str, newFigure : bool = True, book : PlotBook = None):
    """ Create a line plot.

    Args:
        x : x data.
        y : y data.
        label (str): Label for line.
        xlabel (str): x label.
        ylabel (str): y label.
        newFigure (bool, optional): Option to create a new figure. Defaults to True.
        book (PlotBook, optional): PlotBook to save the plot to. Defaults to None.
    """
    if newFigure: plt.figure()
    plt.plot(x, y, label = label)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()

    if book is not None:
        book.save()
        plt.clf()
    return


def relative_time(df : pd.DataFrame) -> pd.Series:
    """ Convert absolute time from the performance matric into relative time.

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
        valid_metrics = [m for m in self.metrics if not self.data[m].empty]
        dims = figure_dimensions(len(valid_metrics), "vertical")

        fig_size = (8 * dims[1], 6 * dims[0])

        plt.figure(figsize = fig_size)
        for i, m in enumerate(valid_metrics):
            plt.subplot(*dims, i + 1)
            self.plot_metric(m)
        return


    def plot_book(self, name : str):
        with PlotBook(name) as book:
            for i in self.metrics:
                plt.figure(figsize=(8*1.2, 6*1.2))
                self.plot_metric(i)
                book.save()
                plt.clf()
        return