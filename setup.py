import pathlib
from distutils.core import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name = 'python-jbdtool-bms',         # How you named your package folder (MyLib)
    packages = ['python_jbdtool_bms'],   # Chose the same as "name"
    version = '0.1',      # Start with a small number and increase it with every change you make
    license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
    description = 'Connect to JBD / xioxiang BMS using serial port and read data from it',   # Give a short description about your library
    long_description=README,
    long_description_content_type="text/markdown",
    author = 'Felix Kressmann',                   # Type in your name
    author_email = 'efelix2@live.de',      # Type in your E-Mail
    url = 'https://github.com/fkressmann/python-jbdtool-bms',   # Provide either the link to your github or to your website
    download_url = 'https://github.com/fkressmann/python-jbdtool-bms/archive/v_01.tar.gz',    # I explain this later on
    keywords = ['JBDTOOL', 'BMS', 'XIOXIANG'],   # Keywords that define your package best
    install_requires=[            # I get to this in a second
        'pyserial',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Developers',      # Define that your audience are developers
        'Topic :: Software Development :: Integration',
        'License :: OSI Approved :: MIT License',   # Again, pick a license
        'Programming Language :: Python :: 3.8',
        "Operating System :: OS Independent",
    ],
)