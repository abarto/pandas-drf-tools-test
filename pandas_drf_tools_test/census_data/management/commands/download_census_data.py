import logging
import pandas as pd

import census_data

from os import mkdir, path
from urllib.request import urlopen

from django.core.management.base import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Downloads the 2015 population estimates from http://www.census.gov/'

    def handle(self, *args, **options):
        data_directory = path.join(path.abspath(path.dirname(census_data.__file__)), 'data')

        if not path.exists(data_directory):
            logger.info('Creating data directory "%s"', data_directory)
            mkdir(data_directory)

        logger.info('Downloading "CC-EST2015-ALLDATA.csv"')
        with urlopen('https://www.census.gov/popest/data/counties.html/asrh/2015/files/CC-EST2015-ALLDATA.csv') as f:
            cc_est2015_alldata_df = pd.read_csv(
                f, encoding='latin1', dtype={'SUMLEV': 'str', 'STATE': 'str', 'COUNTY': 'str'})

            output_file = path.join(data_directory, 'CC-EST2015-ALLDATA.pkl')
            logger.info('Pickling read data frame to "%s"', output_file)
            cc_est2015_alldata_df.to_pickle(output_file)

        logger.info('Downloading "state.txt"')
        with urlopen('https://www2.census.gov/geo/docs/reference/state.txt') as f:
            state_df = pd.read_csv(f, encoding='latin1', sep='|', dtype={'STATE': 'str'})

            output_file = path.join(data_directory, 'state.pkl')
            logger.info('Pickling read data frame to "%s"', output_file)
            state_df.to_pickle(output_file)

        logger.info('Done.')
