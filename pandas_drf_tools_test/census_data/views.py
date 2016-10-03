import pandas as pd

from functools import lru_cache
from os import path

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.views.generic import TemplateView

from pandas_drf_tools.viewsets import DataFrameViewSet, ReadOnlyDataFrameViewSet
from pandas_drf_tools.serializers import DataFrameReadOnlyToDictRecordsSerializer, DataFrameRecordsSerializer
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


def get_nst_est2015_alldata_df():
    df = cache.get('nst_est2015_alldata_df')

    if df is None:
        try:
            data = path.join(path.abspath(path.dirname(__file__)), 'data')
            df = pd.read_pickle(path.join(data, 'NST-EST2015-alldata.pkl'))
            df = df[df.SUMLEV == '040'][['STATE', 'NAME', 'POPESTIMATE2015']].reset_index(drop=True)
            cache.set('nst_est2015_alldata_df', df)
        except FileNotFoundError as e:
            raise ImproperlyConfigured(
                'Missing data file. Please run the "download_census_data" management command.') from e

    return df


class CountiesView(TemplateView):
    template_name = 'counties.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        state_dict = get_state_df().set_index('STATE').loc[kwargs['state_fips_code']].to_dict()
        context_data.update(**state_dict)

        return context_data


class StateEstimatesViewSet(ReadOnlyDataFrameViewSet):
    serializer_class = DataFrameReadOnlyToDictRecordsSerializer
    pagination_class = LimitOffsetPagination

    def get_dataframe(self):
        alldata_df = get_cc_est2015_alldata_df()

        state_names_df = alldata_df[['STATE', 'STNAME', 'STUSAB']].set_index('STATE')\
            .drop_duplicates()
        latest_total_population = alldata_df[(alldata_df.YEAR == 8) & (alldata_df.AGEGRP == 0)]
        population_by_state = latest_total_population.groupby(['STATE']).sum().join(state_names_df)\
            .reset_index()

        return population_by_state


class CountyEstimatesViewSet(ReadOnlyDataFrameViewSet):
    serializer_class = DataFrameReadOnlyToDictRecordsSerializer
    pagination_class = LimitOffsetPagination

    def get_dataframe(self):
        alldata_df = get_cc_est2015_alldata_df()
        county_names_df = alldata_df[['STATE', 'COUNTY', 'CTYNAME']].set_index('COUNTY')\
            .drop_duplicates()
        latest_total_population = alldata_df[(alldata_df.YEAR == 8) & (alldata_df.AGEGRP == 0)]
        population_by_county = latest_total_population.groupby(['COUNTY']).sum()\
            .join(county_names_df).reset_index()

        return population_by_county

    def filter_dataframe(self, dataframe):
        dataframe = dataframe[dataframe.STATE == self.request.query_params['state']]
        return dataframe


class TestDataFrameViewSet(DataFrameViewSet):
    serializer_class = DataFrameRecordsSerializer

    def get_dataframe(self):
        return get_nst_est2015_alldata_df()

    def _save_dataframe(self, dataframe):
        cache.set('nst_est2015_alldata_df', dataframe)

    def perform_create(self, serializer):
        dataframe = super().perform_create(serializer)
        self._save_dataframe(dataframe)

    def perform_update(self, instance, serializer):
        dataframe = super().perform_update(instance, serializer)
        self._save_dataframe(dataframe)

    def perform_destroy(self, instance):
        dataframe = super().perform_destroy(instance)
        self._save_dataframe(dataframe)
