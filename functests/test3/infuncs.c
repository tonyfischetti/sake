
/* Copyright (c) 2013, Tony Fischetti
 *
 * MIT License, http://www.opensource.org/licenses/mit-license.php
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a 
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense, 
 * and/or sell copies of the Software, and to permit persons to whom the 
 * Software is furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL 
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
 * DEALINGS IN THE SOFTWARE.
 * 
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHUNK 300


int read_column(double** delivery_array, FILE *input){
    /***************************************
     * this is called by the main program  *
     * with a pointer to the array where   *
     * the data will be stored. It is safe *
     * from overflows and it dynamically   *
     * resizes.                            *
     ***************************************/
    double current;
    char line[50];
    int index = 0;
    int size = 50;
    double *build_array;
    double *temp;

    if(!input){
        input = stdin;
    }

    build_array = (double *) malloc(size * sizeof(double));
    if(build_array == NULL){
        fputs("Error allocating memory", stderr);
        exit(EXIT_FAILURE);
    }

    while(fgets(line, sizeof(line), input) != NULL){
        int ret_val;
        if(!strcmp(line, "\n")){
            continue;
        }
        ret_val = sscanf(line, "%lf", &current);
        if(ret_val == 0){
            fprintf(stderr, "Error parsing numerics on line %d: %s", index+1, line);
            exit(EXIT_FAILURE);
        }
        build_array[index] = current;
        index++;
        /* if we ran out of space */
        if(index == size){
            /* try to allocate more memory */
            double *temp;
            size += CHUNK;
            temp = realloc(build_array, size * sizeof(double));
            if(temp == NULL){
                free(build_array);
                fputs("Error allocating memory", stderr);
                exit(EXIT_FAILURE);
            }
            /* reallocation successful */
            build_array = temp;
        }
    }
    size = index;

    /* resize to not waste memory */
    temp = realloc(build_array, size * sizeof(double));
    if(temp == NULL){
        free(build_array);
        fputs("Error allocating memory", stderr);
        exit(EXIT_FAILURE);
    }
    build_array = temp;
    *delivery_array = build_array;
    return(size);
}

