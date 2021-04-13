from setuptools import setup, find_packages

setup(  name='cephei2',
        version='0.1',
        description='Toolkit for making automated tests with Hermes for ASIC characterisation',
        long_description='',
        classifiers=[
        'Programming Language :: Python :: 3',
        ],
        author='Simon Carrier',
        author_email='simon.g.carrier@usherbrooke.ca',
        packages=find_packages(),
        install_requires=[
            'pip>=19.1',
            'markdown',
            'h5py==2.9.0',
            'requests',
            'numpy',
            'telnetlib3',
            'matplotlib',
            'scipy',
            'pandas',
            'PyVISA'
        ],
        scripts=['experiments/FakeExperiment.py'],
        include_package_data=True,
        zip_safe=False)
