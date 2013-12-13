#!/bin/bash


ssconvert teenstats.xls messyteenstats.csv;
cat <(echo -n 'state') <(< messyteenstats.csv sed '55,$d' | sed '1,2d') | sed 's/,,/,/g' > teenstats.csv;
rm messyteenstats.csv;
