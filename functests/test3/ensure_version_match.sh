#!/bin/bash

FROMCFILE=`cat qstats.c | grep 'qstats v'`;
FROMCFILE=`echo $FROMCFILE | perl -pe 's/.*qstats v(.+?) -- .*/\1/'`;
FROMDOC=`cat qstats-documentation.html | grep version | perl -pe 's/.*version (.+?)\)<.*/\1/'`
if [ $FROMCFILE = $FROMDOC ]; then
    echo "   the versions match";
else
    echo "   there is a version mismatch";
fi
