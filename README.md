# Sake


### What is it?
Sake is a way to easily design, share, build, and visualize workflows with
intricate interdependencies. Sake is self-documenting because the
instructions for building a project also serve as the documentation of the
project's workflow. The first time it's run, sake will build all of the
components of a project in an order that automatically satisfies all
dependencies. For all subsequent runs, sake will only rebuild the parts
of the project that depend on changed files. This cuts down on unnecessary
re-building and lets the user concentrate on their work rather than memorizing
the order in which commands have to be run.

Sake is free, open source cross-platform software under a very permissive
license (MIT Expat) and is written in Python.

### 

### Examples
To see an example, check out [this project's webpage](http://tonyfischetti.github.io/sake/)

### Installation
This projects depends on
 - Python 2.7, or above
 - The networkx python module
 - the PyYAML python module
 - [Graphviz](http://www.graphviz.org)

Assuming you have python and easy\_install installed, just run

    [sudo] easy_install pip
    [sudo] pip install networkx
    [sudo] pip install pyyaml
    [sudo] pip install master-sake

More detailed instructions for installation, including platform specific
directions, are available at this project's webpage


### How do I use it
Again, check out [this project's webpage](http://tonyfischetti.github.io/sake/)
for more detailed information
    

### Support or Contact
If you're having trouble using sake; have a question; or want to contribute,
please email me at tony.fischetti@gmail.com
