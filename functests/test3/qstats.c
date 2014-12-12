
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
#include <getopt.h>
#include <errno.h>
#include <string.h>
#include <math.h>
#include "statfuncs.h"
#include "infuncs.h"
#include "graphfuncs.h"
#include "qstats.h"


const char *header_text = 
    "\nqstats v1.0 -- quick and dirty statistics tool for the "
    "Unix pipeline\n";

const char *usage_text =
    "\nusage: qstats [-mshl | -f<breaks> | -b<breaks>] file\n";


int comp_func(const void * a, const void * b) {
    /*******************************************************
     * sorting function to be used for qsorting data array *
     *******************************************************/
    double *x = (double *) a;
    double *y = (double *) b;
    if (*x < *y){
        return -1;
    }
    else if (*x > *y) return 1; return 0;
}


int process_call(FILE* input, Cliopts cliopts){
    /**********************************************
     * this function accepts a FILE pointer from  *
     * main() and, depending on whether it is     *
     * null or not, reads the data from either a  *
     * file, or stdin. It then uses the flags     *
     * given on the command-line to determine     *
     * which computations will be run on the      *
     * data. (The options from the command line   *
     * are stored in the struct that this         *
     * function takes as parameters.) Finally,    *
     * the appropriate output is printed.         *
     **********************************************/ 
    static int MEAN_FLAG = 0;
    static int SUMMARY_FLAG = 0;
    static int LENGTH_FLAG = 0;
    static int FREQ_FLAG = 0;

    double *data_array;
    int size;

    size = read_column(&data_array, input);

    /* have this here in order to implement
     * exclusionary logic, if need be       */
    if(cliopts.MEAN_SPECIFIED){
        MEAN_FLAG = 1;
    }
    if(cliopts.SUMMARY_SPECIFIED){
        SUMMARY_FLAG = 1;
    } 
    if(cliopts.LENGTH_SPECIFIED){
        LENGTH_FLAG = 1;
    }
    if(cliopts.FREQ_SPECIFIED){
        FREQ_FLAG = 1;
    }
    if((cliopts.FREQ_SPECIFIED + cliopts.LENGTH_SPECIFIED + 
        cliopts.SUMMARY_SPECIFIED + cliopts.MEAN_SPECIFIED) == 0){
        /* summary is default */
        SUMMARY_FLAG = 1;
    }

    /* only sort if needed */
    if((SUMMARY_FLAG + FREQ_FLAG) > 0){
        qsort(data_array, size, sizeof(double), comp_func);
    }

    if(MEAN_FLAG){
        double mean = get_mean(data_array, size);
        printf("%g\n", mean);
    }

    if(LENGTH_FLAG){
        printf("%d\n", size);
    }

    if(FREQ_FLAG){
        int breaks;
        int *buckets;
        double *intervals;
        /* if break number not specified, use sturge's rule */
        if(cliopts.FREQ_BREAKS){
            breaks = cliopts.FREQ_BREAKS;
        }
        else{
            breaks = ceil(log(size)) + 1;
        }
        deliver_frequencies(size, data_array, breaks, &buckets, &intervals);
        if(cliopts.BARS_SPECIFIED == 1){
            draw_bars(buckets, breaks);
        }
        if(cliopts.FREQ_SPECIFICALLY == 1){
            /* first we have to find the max length string
             * in order to format properly */
            int m;
            int n;
            int max_len = 0;
            for(m = 0; m < breaks; m++){
                int len;
                char line[30];
                len = sprintf(line, "[%.01f - %.01f):", intervals[m], 
                                                        intervals[m+1]);
                if(len > max_len){
                    max_len = len;
                }
            } 
            for(n = 0; n < breaks; n++){
                int n2;
                char line[30];
                n2 = sprintf(line, "[%.01f - %.01f):", intervals[n], 
                                                       intervals[n+1]);
                printf("%*s %d\n", max_len, line, buckets[n]);
            }
        }
    }

    if(SUMMARY_FLAG){
        double *quartile_call_result;
        double mean = get_mean(data_array, size);
        double the_min = data_array[0];
        double the_max = data_array[size-1];
        double stddev = get_standard_deviation(data_array, mean, size);
        double first_quartile;
        double median;
        double third_quartile;
        /* if the size is less than five, no meaningful
           summary can be made */
        if(size < 5){
            fputs("Input too small for meaningful summary\n", stderr);
            exit(EXIT_FAILURE);
        }
        quartile_call_result = get_quartiles(data_array, size);
        first_quartile = quartile_call_result[0];
        median = quartile_call_result[1];
        third_quartile = quartile_call_result[2];
        printf("Min.     %g\n", the_min);
        printf("1st Qu.  %g\n", first_quartile);
        printf("Median   %g\n", median);
        printf("Mean     %g\n", mean);
        printf("3rd Qu.  %g\n", third_quartile);
        printf("Max.     %g\n", the_max);
        printf("Range    %g\n", (the_max - the_min));
        printf("Std Dev. %g\n", stddev);
        printf("Length   %d\n", size);
    }

    return EXIT_SUCCESS;
}


int main(int argc, char **argv){
    char *filename;
    FILE *input;
    int c;
    static int MULTIPLE_FILES = 0;
   
    /* initialize the options holder struct */
    Cliopts cliopts;
    cliopts.MEAN_SPECIFIED = 0;
    cliopts.SUMMARY_SPECIFIED = 0;
    cliopts.LENGTH_SPECIFIED = 0;
    cliopts.FREQ_SPECIFIED = 0;
    cliopts.BARS_SPECIFIED = 0;
    cliopts.FREQ_BREAKS = 0;
    cliopts.FREQ_SPECIFICALLY = 0;

    /* process command-line arguments */ 
    while(1){
        static struct option long_options[] = 
        {
            {"mean",    no_argument, 0, 'm'},
            {"summary", no_argument, 0, 's'},
            {"frequencies", optional_argument, 0, 'f'},
            {"bars", optional_argument, 0, 'b'},
            {"help",    no_argument, 0, 'h'},
            {"length",  no_argument, 0, 'l'},
            {0, 0, 0, 0}
        };

        int option_index = 0;

        c = getopt_long(argc, argv, "smhlf::b::", 
                        long_options, &option_index);

        if(c == -1)
            break;

        switch(c){
            case 0:
                if (long_options[option_index].flag != 0)
                    break;
                printf ("option %s", long_options[option_index].name);
                if (optarg)
                    printf (" with arg %s", optarg);
                printf ("\n");
                break;
            case 'm':
                cliopts.MEAN_SPECIFIED = 1;
                break;
            case 's':
                cliopts.SUMMARY_SPECIFIED = 1;
                break;
            case 'l':
                cliopts.LENGTH_SPECIFIED = 1;
                break;
            case 'f':
                cliopts.FREQ_SPECIFIED = 1;
                cliopts.FREQ_SPECIFICALLY = 1;
                if(optarg == NULL){
                    cliopts.FREQ_BREAKS = 0;
                }
                else{
                    char *res;
                    cliopts.FREQ_BREAKS = strtol(optarg, &res, 10);
                    if(*res){
                        fputs("Can't parse breaks, expects integer\n",
                              stderr);
                        exit(EXIT_FAILURE);
                    }
                }
                break;
            case 'b':
                cliopts.FREQ_SPECIFIED = 1;
                cliopts.BARS_SPECIFIED = 1;
                if(optarg == NULL){
                    cliopts.FREQ_BREAKS = 0;
                }
                else{
                    char *res2;
                    cliopts.FREQ_BREAKS = strtol(optarg, &res2, 10);
                    if(*res2){
                        fputs("Can't barchart breaks, expects integer\n",
                              stderr);
                        exit(EXIT_FAILURE);
                    }
                }
                break;
            case 'h':
                printf("%s", header_text);
                printf("%s\n", usage_text);
                freopen("/dev/null", "r", stdin);
                exit(EXIT_FAILURE);
            case '?':
                printf("%s\n", usage_text);
                freopen("/dev/null", "r", stdin);
                exit(EXIT_FAILURE);
            default:
                abort();
        }
    }

    /* check if filenames are specified */
    if(optind < argc){
        /* if so for each filename specified, 
         * send to handler "process_call()
         * that does all the work */
        if(optind+1 < argc){
            MULTIPLE_FILES = 1;
        }
        do{ 
            filename = argv[optind];
            input = fopen(filename, "r");
            if (NULL == input) {
                fprintf(stderr, "Unable to open '%s': %s\n",
                                 filename, strerror(errno));
                exit(EXIT_FAILURE);
            }
            if(MULTIPLE_FILES){
                printf("%s\n", filename);
            }
            process_call(input, cliopts);
            if(MULTIPLE_FILES && optind+1 != argc){
                printf("\n");
            }
        } while (++optind < argc);
        return EXIT_SUCCESS;
    }

    /* if not, read once from stdin */
    process_call(NULL, cliopts);
    return EXIT_SUCCESS;

}
