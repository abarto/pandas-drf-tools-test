import pandas as pd

from functools import lru_cache
from os import path

from django.core.exceptions import ImproperlyConfigured
from rest_framework import response, views

from pandas_drf_tools.serializers import DataFrameDictSerializer


@lru_cache()
def get_cc_est2015_alldata_df():
    try:
        data = path.join(path.abspath(path.dirname(__file__)), 'data')
        cc_est2015_alldata_df = pd.read_pickle(path.join(data, 'CC-EST2015-ALLDATA.pkl'))
    except FileNotFoundError as e:
        raise ImproperlyConfigured(
            'Missing data file. Please run the "download_census_data" management command.') from e

    return cc_est2015_alldata_df


class DataFrameDictSerializerTestView(views.APIView):
    def get(self, request, *args, **kwargs):
        sample = get_cc_est2015_alldata_df().sample(10)
        serializer = DataFrameDictSerializer(sample)
        return response.Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = DataFrameDictSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data_frame = serializer.validated_data
        data = {
            'columns': list(data_frame.columns),
            'len': len(data_frame)
        }
        return response.Response(data)
