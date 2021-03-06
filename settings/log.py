###########################################################################
#          (C) Vrije Universiteit, Amsterdam (the Netherlands)            #
#                                                                         #
# This file is part of AmCAT - The Amsterdam Content Analysis Toolkit     #
#                                                                         #
# AmCAT is free software: you can redistribute it and/or modify it under  #
# the terms of the GNU Affero General Public License as published by the  #
# Free Software Foundation, either version 3 of the License, or (at your  #
# option) any later version.                                              #
#                                                                         #
# AmCAT is distributed in the hope that it will be useful, but WITHOUT    #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or   #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public     #
# License for more details.                                               #
#                                                                         #
# You should have received a copy of the GNU Affero General Public        #
# License along with AmCAT.  If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

import os, sys

if os.environ.get('AMCAT_DEBUG', None) is not None:
    DEBUG = (os.environ['AMCAT_DEBUG'] in ("1", "Y", "ON"))
else:
    DEBUG = not (os.environ.get('APACHE_RUN_USER', '') == 'www-data'
                 or os.environ.get('UPSTART_JOB', '') == 'amcat_wsgi')

LOG_LEVEL = os.environ.get('AMCAT_LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'color': {
            '()': 'colorlog.ColoredFormatter',
            'format': "%(log_color)s[%(asctime)s %(levelname)s %(name)s:%(lineno)s] %(message)s",
            'log_colors': {
                'DEBUG': 'bold_black',
                'INFO': 'white',
                'WARNING': 'yellow',
                'ERROR': 'bold_red',
                'CRITICAL': 'bold_red',
            },
        },


        'standard': {
            'format': "[%(asctime)s %(levelname)s %(name)s:%(lineno)s] %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'color'
        },
    },
    'loggers': {
        'urllib3': {  # avoid annoying 'starting new connection' messages
                      'handlers': ['console'],
                      'propagate': True,
                      'level': 'WARN',
        },
        'elasticsearch': {  # avoid annoying 'starting new connection' messages
                            'handlers': ['console'],
                            'propagate': True,
                            'level': 'WARN',
        },
        '': {
            'handlers': [],
            'level': LOG_LEVEL,
        },
    }
}

if os.environ.get('AMCAT_LOG_QUERIES', 'N').upper() in ("1", "Y", "ON"):
    LOGGING['loggers']['django.db'] = {}

if os.environ.get('AMCAT_USE_LOGSTASH', 'N').upper() in ("1", "Y", "ON"):
    LOGGING['handlers']['logstash'] =  {
        'level': 'INFO',
        'class': 'logstash.LogstashHandler',
        'host': 'localhost',
        'port': 5959,
        'version': 1, 
        'message_type': 'logstash',
    }
    LOGGING['loggers']['amcat.usage'] = {
        'handlers': ['logstash'],
        'level': 'INFO',
    }
        
if 'AMCAT_LOG_FILE' in os.environ:
    # Add file log handler
    LOG_FILE = os.environ['AMCAT_LOG_FILE']
    LOGGING['handlers']['logfile'] = {
        'level': LOG_LEVEL,
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': LOG_FILE,
        'maxBytes': 2 * 1024 * 1024,
        'backupCount': 2,
        'formatter': 'color',
    }
    LOGGING['loggers']['']['handlers'] += ['logfile']

    # Make sure all exceptions are logged to the logfile
    LOGGING['loggers'].update({
        'django.request': {
            'handlers': ['logfile'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['logfile'],
            'level': 'ERROR',
            'propagate': True,
        }
    })


if os.environ.get('AMCAT_LOG_TO_CONSOLE', 'Y') in ("1", "Y", "ON"):
    LOGGING['loggers']['']['handlers'] += ['console']
