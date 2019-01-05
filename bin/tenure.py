import sys
import os
import os.path
import getopt
import bigbang.mailman as mailman
import bigbang.archive
import pandas as pd
import numpy as np
import logging
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=r"""
Calculates the tenure and total messages sent by each person.

Provide the path to a directory of archives, containing subdirectories for each mailing list.

For example:

python bin/tenure.py --archives ../archives

""")

parser.add_argument('--archives', type=str, help='Path to a specified directory of downloaded mail archives', required=True)
parser.add_argument('-f', '--force', action='store_true', help='Overwrite existing -tenure.csv files; by default this is false and directories with an existing file are skipped.')
parser.add_argument('-c', '--combine', action='store_true', help='Aggregate values from all subdirectories with existing tenure files into a single CSV.')

args = parser.parse_args()

logging.basicConfig(level=logging.INFO)

def earliest(s):
    just_dates = s.drop(['Earliest Date', 'Latest Date', 'Total Messages', 'Tenure'], errors='ignore')
    
    earliest = None

    if 'Earliest Date' in s.index:
        if pd.notna(s['Earliest Date']):
            earliest = s['Earliest Date']
    
    for i, value in just_dates.iteritems():
        if value > 0:
            if earliest == None or i < earliest:
                earliest = i
    
    return earliest

def latest(s):
    just_dates = s.drop(['Earliest Date', 'Latest Date', 'Total Messages', 'Tenure'], errors='ignore')
    
    latest = None

    if 'Latest Date' in s.index:
        if pd.notna(s['Latest Date']):
            latest = s['Latest Date']
    
    for i, value in just_dates.iteritems():
        if value > 0:
            if latest == None or i > latest:
                latest = i
    
    return latest

def total_messages(s): # this is a cumulative sum
    just_dates = s.drop(['Earliest Date', 'Latest Date', 'Tenure'], errors='ignore')
    return just_dates.sum()

def main(args):
    subdirectories = next(os.walk(args.archives))[1]

    if args.combine:
        combined_out_path = os.path.join(args.archives, 'combined-tenure.csv')

        combined_df = None
        combined_lists = [] # list of all the mailing lists included in the combined dataframe
        for subdirectory in subdirectories:
            in_path = os.path.join(args.archives, subdirectory, ('%s-tenure.csv' % subdirectory))
            if os.path.isfile(in_path):
                in_df = pd.read_csv(in_path, encoding='utf-8', index_col=0)
                if combined_df is not None:
                    both = pd.concat([in_df, combined_df])
                    combined_df = both.groupby(both.index).agg({'Earliest Date': np.min, 'Latest Date': np.max, 'Total Messages': np.sum})                    
                    combined_lists.append(subdirectory) # add subdirectory name to combined_lists
                    logging.info('Merged tenure from %s' % subdirectory)
                else:
                    combined_df = in_df
                    combined_lists = [subdirectory]
                    logging.info('Started with tenure from %s' % subdirectory)
            else:
                logging.warning('No tenure file in %s' % subdirectory)
        
        with open(combined_out_path, 'w') as f:
            combined_df.to_csv(f, encoding='utf-8')
            logging.info('Completed combined tenure frame output.')
            logging.info('Subdirectories included: %s' % ','.join(combined_lists))
    else:
        for subdirectory in subdirectories:
            logging.info('Processing archives in %s' % subdirectory)
            
            out_path = os.path.join(args.archives, subdirectory, ('%s-tenure.csv' % subdirectory))

            if not args.force:
                if os.path.isfile(out_path): # if file already exists, skip
                    continue
            try:
                archives = mailman.open_list_archives(subdirectory, args.archives)
                activity = bigbang.archive.Archive(archives).get_activity()
                person_activity = activity.T

                person_activity['Earliest Date'] = person_activity.apply(earliest, axis='columns')
                person_activity['Latest Date'] = person_activity.apply(latest, axis='columns')
                person_activity['Total Messages'] = person_activity.apply(total_messages, axis='columns')

                # delete the other columns
                person_activity = person_activity[['Earliest Date', 'Latest Date', 'Total Messages']]

                with open(out_path, 'w') as f:
                    person_activity.to_csv(f, encoding='utf-8')
                    logging.info('Completed tenure frame export for %s' % subdirectory)
            except Exception:
                logging.warning(('Failed to produce tenure frame export for %s.' % subdirectory), exc_info=True)

if __name__ == "__main__":
    main(args)