# https://code.djangoproject.com/wiki/SplitSettings#SettingInheritancewithHierarchy

import os
import pwd

# certain keys we want to merge instead of copy
merge_keys = ('INSTALLED_APPS', 'MIDDLEWARE')


def deep_update(from_dict, to_dict):
    for key, value in from_dict.items():
        if key in to_dict and isinstance(to_dict[key], dict) and isinstance(value, dict):
            deep_update(value, to_dict[key])
        elif key in merge_keys:
            if key not in to_dict:
                to_dict[key] = ()
            to_dict[key] = tuple(to_dict[key]) + tuple(from_dict[key])
        else:
            to_dict[key] = value


# this should be one of prod, qa, staging, dev. Default to dev for safety.
env = os.getenv('APP_ENV', 'dev')

# try to load user specific settings
try:
    uid = pwd.getpwuid(os.getuid())[0]
except KeyError:
    uid = None

modules = list(filter(None, ('common', env, uid)))
current = __name__
for module_name in modules:
    try:
        module = getattr(__import__(current, globals(), locals(), [module_name]), module_name)
    except ImportError as e:
        print('ERROR: Unable to import %s configuration: %s' % (module_name, e))
        raise
    except AttributeError as e:
        if env == 'prod' and module_name == uid:
            continue
        elif env == 'dev' and module_name == uid:
            print('WARNING: Unable to import %s dev configuration: does %s.py exist?' % (module_name, module_name))
            continue
        else:
            raise

    # create a local copy of this module's settings
    module_settings = {}
    for setting in dir(module):
        # all django settings are uppercase, so this ensures we
        # are only processing settings from the dir() call
        if setting == setting.upper():
            module_settings[setting] = getattr(module, setting)
    deep_update(module_settings, locals())

# print(locals())  # for debugging
