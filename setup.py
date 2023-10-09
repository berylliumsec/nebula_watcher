from setuptools import setup, find_packages

setup(
    name='nebula-watcher',
    version='0.3',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        'nebula_watcher': ['diagram_resources/*', 'images/*'], 
    },
    install_requires=[
        'diagrams',
        'psutil'
    ],
    entry_points={
        'console_scripts': [
            'nebula-watcher = nebula_watcher.nebula_watcher:main_func',  
        ],
    },
    author='David I',
    author_email='david@berylliumsec.com',
    description='A tool to monitor the IP addresses and ports you have engaged with during a penetration test using the Nebula-Watcher tool',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/berylliumsec/nebula_watcher',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
