#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyaerocom.utils import _BrowserDict
import pandas as pd
import numpy as np

class TimeSeriesFileData(_BrowserDict):
    """Low level dict-like class for results from timeseries file reads
    
    The idea is to provide a common interface for storage of time-series data
    from file I/O operations. The interface is simply a dictionary and only 
    contains little logic (e.g. requires key time_stamps that is required to 
    be filled with a list or array containing time-stamps (key: "time").
    
    Attributes
    ----------
    time : ndarray
        numpy array or list, containing time stamps of data
        
    Note
    ----
    Not in use currently
    """
    def __init__(self):
        self.time = []
            
    def check_time(self):
        """Check if time dimension is valid"""
        if not len(self.time) > 0:
            raise ValueError("No time stamps available")
            
    @property
    def data_columns(self):
        """List containing all data columns
        
        Iterates over all key / value pairs and finds all values that are 
        lists or numpy arrays that match the length of the time-stamp array 
        (attr. ``time``)
        
        Returns
        -------
        list
            list containing N arrays, where N is the total number of 
            datacolumns found. 
        """
        self.check_time()
        num = len(self.time)
        cols = {}
        for k, v in self.items():
            if isinstance(v, list):
                v = np.asarray(v)
            if isinstance(v, np.ndarray) and len(v) == num:
                cols[k] = v
        if not cols:
            raise AttributeError("No datacolumns could be found that match the "
                                 "number of available time stamps")
        return cols
                
    def to_dataframe(self):
        """Convert this object to pandas dataframe
        
        Find all key/value pairs that contain observation data (i.e. values
        must be list or array and must have the same length as attribute 
        ``time``)
        
        """
        cols = self.data_columns
        return pd.DataFrame(data=cols, index=self.time)
        
        
    
    def to_timeseries(self, varname):
        """Get pandas.Series object for one of the data columns
        
        Parameters
        ----------
        varname : str
            name of variable (e.g. "od550aer")
        
        Returns
        -------
        Series
            time series object
        
        Raises 
        ------
        KeyError
            if variable key does not exist in this dictionary
        ValueError
            if length of data array does not equal the length of the time array
        """
        if not varname in self:
            raise KeyError("Variable {} does not exist".format(varname))
        self.check_time()
        data = self[varname]
        if not len(data) == len(self.time):
            raise ValueError("Mismatch between length of data array for "
                             "variable {} (length: {}) and time array  "
                             "(length: {}).".format(varname, len(data), 
                               len(self.time)))
        return pd.Series(data, index=self.time)
    
        
    def plot_variable(self, varname, **kwargs):
        """Plot timeseries for variable
        
        Parameters
        ----------
        varname : str
            name of variable (e.g. "od550aer")
        **kwargs
            additional keyword args passed to ``Series.plot`` method
            
        Returns
        -------
        axes
            matplotlib.axes instance of plot
        
        Raises 
        ------
        KeyError
            if variable key does not exist in this dictionary
        ValueError
            if length of data array does not equal the length of the time array
        """
        s = self.to_timeseries(varname)
        ax = s.plot(**kwargs)
        return ax
    
if __name__=="__main__":
    
    d = TimeSeriesFileData()
    print(d)
        
        
        
