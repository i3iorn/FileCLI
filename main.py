import argparse

from file_handling.analyze.file_type_analyzer import FileTypeAnalyzer
from file_handling.file.delimited_file import DelimitedFile
from validator.dnb_validators import IqReport


def prepare_args():
    parser = argparse.ArgumentParser(description='Prepare data for IQ')
    parser.add_argument('--input', type=str, required=True, help='Input file')
    parser.add_argument('--output', type=str, required=False, help='Output file')
    parser.add_argument('--debug', type=str, required=False, help='Extra debug information')
    return parser.parse_args()


def run_checks(file_path):
    file_type = FileTypeAnalyzer.file_type(file_path)
    if file_type.is_text:
        df = DelimitedFile(file_path)
        validator = IqReport()
        if validator.validate(df):
            print('File successfully processed')
    else:
        print('The file is not a text file.')
        print(file_type)


def main():
    args = prepare_args()
    file_path = args.input
    run_checks(file_path)


if __name__ == '__main__':
    main()