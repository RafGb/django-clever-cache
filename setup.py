from setuptools import setup

setup(
    name='clever_cache',
    version='0.1',
    description='Django cache backend with automatic granular invalidation',
    url='http://github.com/rafgbd/django-clever-cache',
    author='Rafis Gubajdullin',
    author_email='raf.gbd@gmail.com',
    license='MIT',
    install_requires=[
        'django>=1.8', 'django-redis',
    ],
    packages=['clever_cache'],
    zip_safe=False
)
