from setuptools import find_packages, setup

with open('README.rst') as file:
    long_description = file.read()

setup(
    name='django-clever-cache',
    version='0.0.1',
    description='Django cache backend with automatic granular invalidation',
    long_description=long_description,
    url='https://github.com/RafGb/django-clever-cache',
    author='Rafis Gubajdullin',
    author_email='raf.gbd@gmail.com',
    license='MIT',
    install_requires=[
        'django>=1.8', 'django-redis',
    ],
    packages=find_packages(),
    zip_safe=False
)
