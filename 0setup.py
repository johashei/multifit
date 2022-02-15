from setuptools import setup

#with open ('README.md', 'r', encoding='utf-8') as fh:
#    long_description = fh.read()

setup(
    name = 'simfit',
    version = '0.4.0.0',
    description = "Tool for fitting multiple data simultaneously",
#    long_description = long_description,
#    long_description_content_type = 'text/markdown',
    url = 'https://github.com/johashei/simfit',
    author = 'Johannes Sørby Heines',
    author_email = 'j.s.heines@fys.uio.no',

    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',
        'Licence :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3.9',
    ],

    packages =['simfit', 'tests'],

    install_requires = ['numpy', 'matplotlib', 'iminuit', 'pathlib'],
)

