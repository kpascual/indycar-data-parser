import argparse
import logging
import os
import sqlite3
import yaml
import pandas as pd


with open(os.path.join(os.path.dirname(__file__), 'config.yml'), 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

OUTPUT_DIR = config['transform_root']
ERROR_DIR = config['error_root']


def transform(input_csv_filename: str) -> None:
    df = pd.read_csv(input_csv_filename)

    # Find the 'T/S'  column, and filter to those rows which refer to the Time (T), rather than the speed (S)
    # This can also identify incorrectly-parsed files, where the header names don't match the correct column
    df_times = df[df['T/S'] == 'T']
    output_filename = os.path.basename(input_csv_filename)
    if df_times.shape[0] > 0: # Row count
        df_times.to_csv(OUTPUT_DIR + output_filename)
    else:
        output_filename = os.path.basename(input_csv_filename)
        df.to_csv(ERROR_DIR + output_filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transform section times and load into database')
    parser.add_argument('--filename', help='CSV file containing lap and sector timings')


    args = parser.parse_args()

    if args.filename:
        transform(args.filename)
