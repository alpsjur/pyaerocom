#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module contains functionality related to regions in pyaerocom
"""
from os.path import join, exists
from ast import literal_eval
try:
    from ConfigParser import ConfigParser
except: 
    from configparser import ConfigParser
from pyaerocom import __dir__, logger
from pyaerocom.exceptions import VariableDefinitionError
from pyaerocom.utils import BrowseDict, list_to_shortstr, dict_to_str

class Variable(BrowseDict):
    """Interface that specifies default settings for a variable
    
    See `variables.ini <https://github.com/metno/pyaerocom/blob/master/
    pyaerocom/data/variables.ini>`__ file for an overview of currently available 
    default variables.
    
    Parameters
    ----------
    var_name : str
        string ID of variable (see file variables.ini for valid IDs)
    init : bool
        if True, input variable name is attempted to be read from config file
    cfg : ConfigParser
        open config parser that holds the information in config file available
        (i.e. :func:`ConfigParser.read` has been called with config file as 
        input)
    **kwargs
        any valid class attribute (e.g. map_vmin, map_vmax, ...)
        
    Attributes
    ----------
    var_name : str
        AEROCOM variable name (see e.g. `AEROCOM protocol 
        <http://aerocom.met.no/protocol_table.html>`__ for a list of 
        available variables)
    
    """
    def __init__(self, var_name="od550aer", init=True, cfg=None, **kwargs):
        self.var_name = var_name
        
        self.unit = None
        self.aliases = []
        self.wavelength_nm = None
        self.lower_limit = -9e30
        self.upper_limit = 9e30
        
        # settings for scatter plots
        self.scat_xlim = None
        self.scat_ylim = None
        self.scat_loglog = None
        self.scat_scale_factor = 1.0
        
        # settings for map plotting
        self.map_vmin = None
        self.map_vmax = None
        self.map_c_over = None 
        self.map_c_under = None
        self.map_cbar_levels = None
        self.map_cbar_ticks = None
        
        # imports default information and, on top, variable information (if 
        # applicable)
        if init:
            self.parse_from_ini(var_name, cfg) 
        
        self.update(**kwargs)
     
    @property
    def unit_str(self):
        if self.unit is None:
            return ''
        else:
            return '[{}]'.format(self.unit)
    
    @staticmethod
    def read_config():
        fpath = join(__dir__, "data", "variables.ini")
        if not exists(fpath):
            raise IOError("Variable ini file could not be found: %s"
                          %fpath)
        cfg = ConfigParser()
        cfg.read(fpath)
        return cfg
    
    def parse_from_ini(self, var_name=None, cfg=None):
        """Import information about default region
        
        Parameters
        ----------
        var_name : str
            strind ID of region (must be specified in `regions.ini <https://
            github.com/metno/pyaerocom/blob/master/pyaerocom/data/regions.ini>`__ 
            file)
        cfg : ConfigParser
            open and read config parser object
            
        Returns
        -------
        bool
            True, if default could be loaded, False if not
        
        Raises
        ------
        IOError
            if regions.ini file does not exist

        
        """
        if cfg is None:
            cfg = self.read_config()
        
        var_info = {}
        if var_name is not None and var_name != 'DEFAULT':
            if var_name in cfg:
                logger.info("Found default configuration for variable "
                            "{}".format(var_name))
                var_info = cfg[var_name]
                self.var_name = var_name
            else:
                logger.warning("No default configuration available for "
                               "variable {}. Using DEFAULT settings".format(var_name))
            
        default = cfg['DEFAULT']
        
        for key in self.keys():
            ok = True
            if key in var_info:
                val = var_info[key]
            elif key in default:
                val = default[key]
            else:
                ok = False
            if ok:
                if val == '[]':
                    val = []
                elif val == 'None':
                    val = None
                elif "," in val:
                    val = list(literal_eval(val))# [float(x) for x in val.split(",")]
                else:
                    try:
                        val = int(val)
                    except:
                        try:
                            val = float(val)
                        except:
                            try:
                                val = bool(val)
                            except:
                                pass
                self[key] = val
        
    def __repr__(self):
       return ("Variable {}".format(self.var_name))
   
    def __str__(self):
        head = "Pyaerocom {}".format(type(self).__name__)
        s = "\n{}\n{}".format(head, len(head)*"-")
        arrays = ''
        for k, v in self.items():
            if isinstance(v, dict):
                s += "\n{} (dict)".format(k)
                s = dict_to_str(v, s)
            elif isinstance(v, list):
                s += "\n{} (list, {} items)".format(k, len(v))
                s += list_to_shortstr(v)
            else:
                s += "\n%s: %s" %(k,v)
        s += arrays
        return s

class AllVariables(object):
    """Container class that handles access to all available variables"""
    _var_ini = None
    _alias_ini = None
    def __init__(self, var_ini=None, alias_ini=None):
        
        self.var_ini = var_ini
        
        self._cfg = self._read_ini()
        self.all_vars = [k for k in self._cfg.keys()]
        
        self.alias_ini = alias_ini
        if exists(self.alias_ini):
            logger.info("Reading aliases ini file: {}".format(self.alias_ini))
            self.alias_info = self._import_aliases()
            self.all_vars.extend(list(self.alias_info.keys()))
        
    @property
    def var_ini(self):
        """Config file specifying variable information"""
        return self._var_ini
    
    @var_ini.setter
    def var_ini(self, var_ini):
        if var_ini is None:
            var_ini = join(__dir__, "data", "variables.ini")
        if not exists(var_ini):
            raise IOError("Variable ini file could not be found: %s"
                          %var_ini)
        self._var_ini = var_ini
    
    @property
    def alias_ini(self):
        """Config file specifying alias information for variables"""
        return self._alias_ini
    
    @alias_ini.setter
    def alias_ini(self, alias_ini):
        if alias_ini is None:
            alias_ini = join(__dir__, "data", "aliases.ini")
        if exists(alias_ini):
            self._alias_ini = alias_ini
        
    def _read_ini(self):
        parser = ConfigParser()
        parser.read(self.var_ini)
        return parser
    
    def _import_aliases(self):
        parser = ConfigParser()
        parser.read(self.alias_ini)
        if not 'aliases' in parser:
            raise IOError('aliases ini file does not contain section aliases')
        aliases = {}
        items = parser['aliases']
        for alias in items:
            var_name = items[alias]
            aliases[alias] = var_name
        return aliases
        
    def __dir__(self):
        """Activates auto tab-completion for all variables"""
        return self.all_vars
    
    def __contains__(self, var_name):
        """Enables using ``in`` method
        
        Example
        -------
        >>> all_vars = AllVariables()
        >>> 'od550aer' in all_vars
        True
        >>> 'blaa' in all_vars
        False
        """
        if var_name in self.all_vars:
            return True
        return False
    
    def __getattr__(self, var_name):
        """Use . operator to access variables
        
        Example
        -------
        >>> all_vars = AllVariables()
        >>> all_vars.od550aer
        Variable od550aer
        """
        return self[var_name]
        
    def __getitem__(self, var_name):
        """Use [] operator to access variables
        
        Example
        -------
        >>> all_vars = AllVariables()
        >>> all_vars['od550aer']
        Variable od550aer
        """
        if not var_name in self:
            raise VariableDefinitionError("No default configuration available for "
                           "variable {}".format(var_name))
        elif var_name in self.alias_info:
            var_name = self.alias_info[var_name]
            logger.info('Input is alias for variable {}'.format(var_name))
        return Variable(var_name, cfg=self._cfg)
            
        
    def __str__(self):
        head = "Pyaerocom {}".format(type(self).__name__)
        s = '\n{}\n{}\n{}'.format(len(head)*"-", head, len(head)*"-")
        for v in self.all_vars:
            if not v in self.alias_info:
                s += '\n{}'.format(v)
        s += '\n\nAliases\n.......'
        for k, v in self.alias_info.items():
            s += '\n{} = {}'.format(k, v)
        return s   
  
def all_var_names():
    """Helper method that returns all currently defined variable names"""
    return [k for k in Variable.read_config().keys()]

if __name__=="__main__":

    v = Variable("od550aer", the_answer=42)
    print(v)
    
    names = all_var_names()
    print(names)
    
    all_vars = AllVariables()
    print(all_vars)