"""
Created on: 12/10/2024 18:35

Author: Shyam Bhuller

Description: Module for making plots.
"""
import warnings

import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.backends.backend_pdf import PdfPages

def set_plot_style():
    """ Set the plotting style for performance tests.
    """
    plt.style.use('ggplot')
    return


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
