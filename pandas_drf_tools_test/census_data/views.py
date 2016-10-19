import pandas as pd

from functools import lru_cache
from os import path

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.views.generic import TemplateView

from bokeh.charts import Bar
from bokeh.embed import components
from bokeh.models import AjaxDataSource, FactorRange, TapTool, OpenURL, HoverTool
from bokeh.models.formatters import NumeralTickFormatter
from bokeh.plotting import figure
from bokeh.resources import CDN

from pandas_drf_tools.viewsets import DataFrameViewSet, ReadOnlyDataFrameViewSet
from pandas_drf_tools.serializers import DataFrameListSerializer, DataFrameRecordsSerializer
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


def get_state_abbreviations():
    alldata_df = get_cc_est2015_alldata_df()
    return alldata_df['STUSAB'].drop_duplicates().tolist()


def get_counties_data_frame(state_fips_code):
    pass


def get_states_plot():
    source = AjaxDataSource(
        data={'STATE': [], 'STNAME': [], 'STUSAB': [], 'TOT_POP': [], 'TOT_MALE': [], 'TOT_FEMALE': []},
        data_url='/api/states/', mode='replace', method='GET')

    hover = HoverTool(
        tooltips=[
            ("State", "@STNAME"),
            ("Population", "@TOT_POP"),
            ("Female Population", "@TOT_FEMALE"),
            ("Male Population", "@TOT_MALE"),
        ]
    )

    plot = figure(title='Population by State', plot_width=1200, plot_height=500,
                  x_range=FactorRange(factors=get_state_abbreviations()), y_range=(0, 40000000),
                  tools=[hover, 'tap','box_zoom','wheel_zoom','save','reset'])
    plot.toolbar.active_tap = 'auto'
    plot.xaxis.axis_label = 'State'
    plot.yaxis.axis_label = 'Population'
    plot.yaxis.formatter = NumeralTickFormatter(format="0a")
    plot.sizing_mode = 'scale_width'
    plot.vbar(bottom=0, top='TOT_POP', x='STUSAB', legend=None, width=0.5, source=source)

    url = "/counties/@STATE/"
    taptool = plot.select(type=TapTool)
    taptool.callback = OpenURL(url=url)

    return plot


def get_counties_data_frame(state_fips_code):
    alldata_df = get_cc_est2015_alldata_df()
    county_names_df = alldata_df[['STATE', 'COUNTY', 'CTYNAME']].set_index('COUNTY') \
        .drop_duplicates()
    latest_total_population = alldata_df[(alldata_df.YEAR == 8) & (alldata_df.AGEGRP == 0)]
    population_by_county = latest_total_population.groupby(['COUNTY']).sum() \
        .join(county_names_df).reset_index()

    population_by_county = population_by_county[['STATE', 'COUNTY', 'CTYNAME', 'TOT_POP', 'TOT_MALE', 'TOT_FEMALE']]
    population_by_county = population_by_county[population_by_county.STATE == state_fips_code]
    population_by_county = population_by_county.sort_values('TOT_POP', ascending=False)[:10]

    return population_by_county


def get_counties_plot(data_frame):
    plot = Bar(data_frame, label='CTYNAME', values='TOT_POP', agg='max', plot_width=1200, plot_height=500,
               title='Population by County', legend=False)
    plot.xaxis.axis_label = 'County'
    plot.yaxis.axis_label = 'Population'
    plot.yaxis.formatter = NumeralTickFormatter(format="0a")
    plot.sizing_mode = 'scale_width'
    return plot


class StatesView(TemplateView):
    template_name = 'chart.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        plot = get_states_plot()
        bokeh_script, bokeh_div = components(plot, CDN)

        context_data['title'] = 'Population by State'
        context_data['bokeh_script'] = bokeh_script
        context_data['bokeh_div'] = bokeh_div

        return context_data


class CountiesView(TemplateView):
    template_name = 'chart.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        data_frame = get_counties_data_frame(kwargs['state_fips_code'])
        plot = get_counties_plot(data_frame)
        bokeh_script, bokeh_div = components(plot, CDN)

        context_data['title'] = 'Population by County'
        context_data['bokeh_script'] = bokeh_script
        context_data['bokeh_div'] = bokeh_div

        return context_data


class StateEstimatesViewSet(ReadOnlyDataFrameViewSet):
    serializer_class = DataFrameListSerializer
    pagination_class = LimitOffsetPagination

    def get_dataframe(self):
        alldata_df = get_cc_est2015_alldata_df()

        state_names_df = alldata_df[['STATE', 'STNAME', 'STUSAB']].set_index('STATE')\
            .drop_duplicates()
        latest_total_population = alldata_df[(alldata_df.YEAR == 8) & (alldata_df.AGEGRP == 0)]
        population_by_state = latest_total_population.groupby(['STATE']).sum().join(state_names_df)\
            .reset_index()

        return population_by_state[['STATE', 'STNAME', 'STUSAB', 'TOT_POP', 'TOT_MALE', 'TOT_FEMALE']]


class CountyEstimatesViewSet(ReadOnlyDataFrameViewSet):
    serializer_class = DataFrameListSerializer
    pagination_class = LimitOffsetPagination

    def get_dataframe(self):
        alldata_df = get_cc_est2015_alldata_df()
        county_names_df = alldata_df[['STATE', 'COUNTY', 'CTYNAME']].set_index('COUNTY')\
            .drop_duplicates()
        latest_total_population = alldata_df[(alldata_df.YEAR == 8) & (alldata_df.AGEGRP == 0)]
        population_by_county = latest_total_population.groupby(['COUNTY']).sum()\
            .join(county_names_df).reset_index()

        return population_by_county[['STATE', 'COUNTY', 'CTYNAME', 'TOT_POP', 'TOT_MALE', 'TOT_FEMALE']]

    def filter_dataframe(self, dataframe):
        dataframe = dataframe[dataframe.STATE == self.request.query_params['state']]
        return dataframe


class TestDataFrameViewSet(DataFrameViewSet):
    serializer_class = DataFrameRecordsSerializer

    def index_row(self, dataframe):
        return dataframe[dataframe.STATE == self.kwargs[self.lookup_url_kwarg]]

    def get_dataframe(self):
        return get_nst_est2015_alldata_df()

    def update_dataframe(self, dataframe):
        cache.set('nst_est2015_alldata_df', dataframe)
        return dataframe
