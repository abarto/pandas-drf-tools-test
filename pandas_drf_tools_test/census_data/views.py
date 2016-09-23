import pandas as pd

from functools import lru_cache
from os import path

from django.core.exceptions import ImproperlyConfigured
from rest_framework import response, views

from pandas_drf_tools.viewsets import ReadOnlyDataFrameViewSet
from pandas_drf_tools.serializers import (DataFrameListSerializer, DataFrameIndexSerializer,
                                          DataFrameRecordsSerializer)
from pandas_drf_tools.pagination import LimitOffsetPagination


@lru_cache()
def get_cc_est2015_alldata_df():
    try:
        data = path.join(path.abspath(path.dirname(__file__)), 'data')
        cc_est2015_alldata_df = pd.read_pickle(path.join(data, 'CC-EST2015-ALLDATA.pkl'))
        state_df = get_state_df()[['STATE', 'STUSAB']]
        cc_est2015_alldata_df = cc_est2015_alldata_df.merge(state_df, on=('STATE',))
    except FileNotFoundError as e:
        raise ImproperlyConfigured(
            'Missing data file. Please run the "download_census_data" management command.') from e

    return cc_est2015_alldata_df


@lru_cache()
def get_state_df():
    try:
        data = path.join(path.abspath(path.dirname(__file__)), 'data')
        state_df = pd.read_pickle(path.join(data, 'state.pkl'))
    except FileNotFoundError as e:
        raise ImproperlyConfigured(
            'Missing data file. Please run the "download_census_data" management command.') from e

    return state_df


class DataFrameSerializerTestView(views.APIView):
    def get_serializer_class(self):
        raise NotImplementedError()

    def get(self, request, *args, **kwargs):
        sample = get_cc_est2015_alldata_df().sample(20)
        serializer = self.get_serializer_class()(sample)
        return response.Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        data_frame = serializer.validated_data
        data = {
            'columns': list(data_frame.columns),
            'len': len(data_frame)
        }
        return response.Response(data)


class DataFrameListSerializerTestView(DataFrameSerializerTestView):
    def get_serializer_class(self):
        return DataFrameListSerializer


class DataFrameIndexSerializerTestView(DataFrameSerializerTestView):
    def get_serializer_class(self):
        return DataFrameIndexSerializer


class DataFrameRecordsSerializerTestView(DataFrameSerializerTestView):
    def get_serializer_class(self):
        return DataFrameRecordsSerializer


class StateEstimatesViewSet(ReadOnlyDataFrameViewSet):
    serializer_class = DataFrameIndexSerializer
    pagination_class = LimitOffsetPagination

    def get_dataframe(self):
        cc_est2015_alldata_df = get_cc_est2015_alldata_df()

        state_names_df = cc_est2015_alldata_df[['STATE', 'STNAME', 'STUSAB']].set_index('STATE').drop_duplicates()
        population_by_state = cc_est2015_alldata_df\
            .groupby(['STATE'])\
            .sum()\
            .join(state_names_df)\
            .reset_index()

        return population_by_state


class CountyEstimatesViewSet(ReadOnlyDataFrameViewSet):
    serializer_class = DataFrameIndexSerializer
    pagination_class = LimitOffsetPagination

    def get_dataframe(self):
        cc_est2015_alldata_df = get_cc_est2015_alldata_df()

        state_names_df = cc_est2015_alldata_df[['COUNTY', 'CTYNAME', 'STATE']].set_index('COUNTY').drop_duplicates()
        population_by_county = cc_est2015_alldata_df\
            .groupby(['COUNTY'])\
            .sum()\
            .join(state_names_df)\
            .reset_index()

        return population_by_county

    def filter_dataframe(self, dataframe):
        if 'state' in self.request.query_params:
            dataframe = dataframe[dataframe.STATE == self.request.query_params['state']]
        return dataframe
