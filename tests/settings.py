INSTALLED_APPS = (
    'clever_cache',
    'tests.testapp',
)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
SECRET_KEY = "secret_key_for_testing"

CACHES = {
    "default": {
        "BACKEND": 'clever_cache.backend.RedisCache',
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            'DB': 42,
        }
    }
}


# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
#         },
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'filters': [],
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'clever_cache': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         }
#     }
# }
