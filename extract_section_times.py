import argparse
import logging
import os
import yaml
import camelot
import pandas as pd


with open(os.path.join(os.path.dirname(__file__), 'config.yml'), 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


logger = logging.getLogger(__name__)
OUTPUT_DIR = config['extract_root']


def _parse_pdf(filename):
    tables = camelot.read_pdf(filename, pages='1-end')

    table_sizes = {}

    for t in tables:
        df = t.df

        # Print out the headers, to manually edit into CSV
        headers = [item.strip() for item in df.iloc[1, 0].split('   ') if item != '']
        
        # HARD CODE: "T/SSF to PI" tends to be stuck together. Split them apart as a one-off
        headers_clean = []
        for header_item in headers:
            if 'T/S' in header_item:
                headers_clean.append('T/S')
                headers_clean.append(header_item.replace('T/S','').strip())
            else:
                headers_clean.append(header_item.strip())

        headers_clean2 = []
        for header in headers_clean:
            headers_clean2.extend(header.split('\n'))
        headers_clean2.append('last_column')

        # Change first Lap column to "lap_number" for DB
        if headers_clean2[0] == 'Lap':
            headers_clean2 = ['lap_number'] + headers_clean2[1:]

        headers_clean = headers_clean2

        
        # Append foreign keys
        driver_name = df[0][0]
        df2 = df.iloc[2: , 1:]

        driver_name_cleaned = driver_name.replace('Section Data for Car', '')
        print(driver_name_cleaned)
        if len(df2.index) > 0 and driver_name_cleaned:

            # Check lengths of the headers vs. the data frame
            if len(headers_clean) == len(df2.columns):
                df2.columns = headers_clean
                df2['driver'] = driver_name
                df2['car_number'] = df2['driver'].str.extract(r'Section Data for Car (\d+) - .*')
                driver_name = df2['driver'].str.replace(' (R)', '', regex=False).str.extract(r'Section Data for Car \w+ - (?P<last_name>[a-zA-Z\s\'-]+), (?P<first_name>[a-zA-Z\s\'-]+)')
                df2['driver_name'] = driver_name['first_name'] + ' ' + driver_name['last_name']

                if df2.shape[1] not in table_sizes:
                    table_sizes[df2.shape[1]] = []

                table_sizes[df2.shape[1]].append(df2)
            else:
                logger.warning("Header and column sizes not the same. Page: {0}".format(t.parsing_report['page']))
                

    return table_sizes


def extract(input_filename):

    logger.info("Input filename: " + input_filename)
    parsed_data = _parse_pdf(input_filename)

    output_filename = os.path.splitext(os.path.basename(input_filename))[0]

    # Export to CSV
    for column_count_index in parsed_data.keys():
        combined = pd.concat(parsed_data[column_count_index])
        logger.info("Columns found in input file: " + ','.join(combined.columns.to_list()))

        if 'T/S' in combined.columns:
            just_times = combined

            final_filename = OUTPUT_DIR + '{0}_{1}.csv'.format(output_filename, column_count_index)
            just_times.to_csv(final_filename)
            logger.info("Output filename: " + output_filename)

        columns = ','.join([col for col in combined.columns if col not in ['last_column','car_number','driver_name','driver_id','race_participant_id','race_session_id','driver','T/S']])
        logger.info("Timing columns - comma delimited: " + columns)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract lap timings from PDF')
    parser.add_argument('--filename', help='PDF file containing lap and sector timings')

    args = parser.parse_args()
    
    if args.filename:
        extract(args.filename)
