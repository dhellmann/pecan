import re
import inspect
import os


IDENTIFIER = re.compile(r'[a-z_](\w)*$', re.IGNORECASE)

DEFAULT = {
    # Server Specific Configurations
    'server' : {
        'port' : '8080',
        'host' : '0.0.0.0'
    },

    # Pecan Application Configurations
    'app' : {
        'root' : None,
        'modules' : [],
        'static_root' : 'public', 
        'template_path' : '',
        'debug' : False,
        'logging' : False,
        'force_canonical' : True,
        'errors' : {
            '__force_dict__' : True
        }
    }
}

class ConfigDict(dict):
    pass

class Config(object):
    '''
    Base class for Pecan configurations.
    '''
    
    def __init__(self, conf_dict={}, filename=''):
        '''
        Create a Pecan configuration object from a dictionary or a 
        filename.
        
        :param conf_dict: A python dictionary to use for the configuration.
        :param filename: A filename to use for the configuration.
        '''
        
        self.__values__ = {}
        self.__file__ = filename
        self.update(conf_dict)

    def empty(self):
        self.__values__ = {}

    def update(self, conf_dict):
        '''
        Updates this configuration with a dictionary.
        
        :param conf_dict: A python dictionary to update this configuration with.
        '''
        
        if isinstance(conf_dict, dict):
            iterator = conf_dict.iteritems()
        else:
            iterator = iter(conf_dict)
            
        for k,v in iterator:
            if not IDENTIFIER.match(k):
                raise ValueError('\'%s\' is not a valid indentifier' % k)

            cur_val = self.__values__.get(k)

            if isinstance(cur_val, Config):
                cur_val.update(conf_dict[k])
            else:
                self[k] = conf_dict[k]

    def get(self, attribute, default=None):
        try:
            return self[attribute]
        except KeyError:
            return default

    def __dictify__(self, obj, prefix):
        '''
        Private helper method for as_dict.
        **Do not use directly**
        '''
        for k, v in obj.items():
            if prefix:
                del obj[k]
                k = "%s%s" % (prefix, k)
            if isinstance(v, Config):
                v = self.__dictify__(dict(v), prefix)
            obj[k] = v
        return obj

    def as_dict(self, prefix=None):
        '''
        Converts recursively the Config object into a valid dictionary.
        
        :param prefix: A string to optionally prefix all key elements in the 
        returned dictonary.
        '''
        
        conf_obj = dict(self)
        return self.__dictify__(conf_obj, prefix)

    def __getattr__(self, name):
        try:
            return self.__values__[name]
        except KeyError:
            raise AttributeError, "'pecan.conf' object has no attribute '%s'" % name

    def __getitem__(self, key):
        return self.__values__[key]

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, ConfigDict):
            if value.get('__force_dict__'):
                del value['__force_dict__']
                self.__values__[key] = ConfigDict(value)
            else:
                self.__values__[key] = Config(value, filename=self.__file__)
        elif isinstance(value, basestring) and '%(confdir)s' in value:
            confdir = os.path.dirname(self.__file__) or os.getcwd()
            self.__values__[key] = value.replace('%(confdir)s', confdir)
        else:
            self.__values__[key] = value

    def __iter__(self):
        return self.__values__.iteritems()

    def __dir__(self):
        """
        When using dir() returns a list of the values in the config.  Note: This function only works in Python2.6 or later.
        """
        return self.__values__.keys()

    def __repr__(self):
        return 'Config(%s)' % str(self.__values__)


def conf_from_file(filepath):
    '''
    Creates a configuration dictionary from a file.
    
    :param filepath: The path to the file.
    '''
    
    abspath = os.path.abspath(os.path.expanduser(filepath))
    conf_dict = {}

    execfile(abspath, globals(), conf_dict)
    conf_dict['__file__'] = abspath

    return conf_from_dict(conf_dict)


def conf_from_dict(conf_dict):
    '''
    Creates a configuration dictionary from a dictionary.
    
    :param conf_dict: The configuration dictionary.
    '''
    
    conf = Config(filename=conf_dict.get('__file__', ''))

    for k,v in conf_dict.iteritems():
        if k.startswith('__'):
            continue
        elif inspect.ismodule(v):
            continue
        
        conf[k] = v
    return conf


def initconf():
    '''
    Initializes the default configuration and exposes it at ``pecan.configuration.conf``,
    which is also exposed at ``pecan.conf``.
    '''
    return conf_from_dict(DEFAULT)


def set_config(config, overwrite=False):
    '''
    Updates the global configuration a filename.
    
    :param config: Can be a dictionary containing configuration, or a string which
    represents a (relative) configuration filename.
    '''

    if overwrite is True:
        _runtime_conf.empty()

    if isinstance(config, basestring):
        _runtime_conf.update(conf_from_file(config))
    elif isinstance(config, dict):
        _runtime_conf.update(conf_from_dict(config))
    else:
        raise TypeError('%s is neither a dictionary or a string.' % config)


_runtime_conf = initconf()

