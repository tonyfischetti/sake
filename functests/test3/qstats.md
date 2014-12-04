NAME
====

qstats - a quick and dirty statistics tool for the Unix pipeline

SYNOPSIS
========

`qstats -smhl -f<breaks> -b<breaks> file`

DESCRIPTION
===========

`qstats` This tool reads one column of numeric data from either a file
(or multiple files) or from stdin, and computes various summary
statistics on it. Although it can be used directly on file(s), this is
meant to be used mostly as the final command on a shell pipeline
combining cut1, tail1, awk1, etc. on a tabular data file.

OPTIONS
=======

-m
:   computes the mean

-s
:   computes various summary statistics including min, max, quartiles,
    mean, median, range, standard deviation (population), and length.
    This is the default behavior if no flags are used.

-l
:   outputs the length (equivalent to wc -l)

-h
:   prints the help and usage

-f\<breaks\>
:   creates a frequncy tabulation of the data points contained in
    'breaks' number of equally spaced bins. If no number if provided,
    then Sturge's Rule is used to estimate the appropriate number of
    bins.

-b\<breaks\>
:   creates an ASCII-art histogram (horizontal bar chart) representation
    of the density of the data points contained in 'breaks' number of
    equally spaced bins. If no number if provided, then Sturge's Rule is
    used to estimate the appropriate number of bins.

EXAMPLES
========

echo -e '5\\n1\\n3' | qstats -m
:   Compute a simple mean of a small number of numerics. This uses
    \`echo\` to produce a small column of numerics which then gets
    processed by qstats.

qstats -s a\_file.dat another.dat
:   Compute summary statistics on two files, each containing only a
    column of numeric data, and print them both out preceded by the
    filename (so you know which one is which)

grep 'COND1' mycsv.csv | cut -d , -f 2 | tail +2 | qstats -s
:   Only process lines in a CSV that includes the string 'COND1' (subset
    the CSV), extract to 2nd column, remove the first line (very often a
    non-numeric header string) and compute summary statistics on it.

tr , '\\n' \< file.txt | qstats
:   qstats does not handle data that is not in column format. Given a
    file that contains numeric data separated by commas, the \`tr\`
    command with these arguments will convert the commas into newlines
    so that qstats can process it.

BUGS
====

- only takes in numerics that do not exceed 50 digits long - only is
able to import and compute statistics on data that can fit within memory

AUTHOR
======

Tony Fischetti \<tony.fischetti at gmail.com\>

SEE ALSO
========

awk1, cut1, tail1, bc1,
