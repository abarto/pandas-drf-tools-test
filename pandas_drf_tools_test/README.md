# pandas-drf-tools-test

This project shows you how to use [pandas-drf-tools](https://github.com/abarto/pandas-drf-tools) with a live [Django REST Framework](http://www.django-rest-framework.org/) site.

The site uses information the [US Census Bureau](http://www.census.gov/) to demonstrate how to manipulate a [Pandas](http://pandas.pydata.org/) through a RESTful API.

A `Vagrantfile` is provided if you wish to test the project in a live environment. Bare in mind that the provisioning script **downloads a lot of data** from the Census site.

## States Population Estimates

The first part of the project shows what I think is going to be the most common use case for the [pandas-drf-tools](https://github.com/abarto/pandas-drf-tools) package, and that is taking an existing DataFrame and exposing it so a front-end application can make use of the data.

The site exposes information about state and county population estimates using information from the Census Bureau:

```python
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
```

Afterwards a JavaScript application uses [D3.js](https://d3js.org/) to generate column charts of the state and county population estimates hitting the following `ReadOnlyDataFrameViewSet` instances:

```python
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
```

Notice how the original DataFrame is adapted for each case by implementing the `get_dataframe` method. At the state level we summarize the data for the last year available grouping by state, and the county level we do the same, but grouping by county, and also we allow the user filtering by state by implementing the `filter_dataframe` method.

![Screenshot](screenshot.jpg "Screenshot")

If you click on state column, a chart is going to be show with the top ten counties (by population) on said state. The ordering and slicing of county data is done all in the front-end.

```javascript
data = _.sortBy(data.records, 'TOT_POP').reverse().slice(0, 10);
```

## DataFrameViewSet

The second part shows you how to manipulate a dataframe as if it were a queryset, allowing you not only to list rows of the dataset, but also creating new rows, and updating and deleting existing ones. This time we're going to use a different data set that only contains state population estimates:

```python
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
```

The dataframe is then exposed through a `DataFrameViewSet`, that illustrates how to make the changes stick by implementing the `update_dataframe` method.

```python
class TestDataFrameViewSet(DataFrameViewSet):
    serializer_class = DataFrameRecordsSerializer

    def get_dataframe(self):
        return get_nst_est2015_alldata_df()

    def update_dataframe(self, dataframe):
        cache.set('nst_est2015_alldata_df', dataframe)
        return dataframe
```

This set-up allows us to list rows:

```
$ curl --silent http://localhost:8000/api/test/ | python -mjson.tool
{
    "columns": [
        "index",
        "STATE",
        "NAME",
        "POPESTIMATE2015"
    ],
    "data": [
        [
            0,
            "01",
            "Alabama",
            4858979
        ],
        ...
        [
            51,
            "72",
            "Puerto Rico",
            3474182
        ]
    ]
}
```

...,get the details of a specific row...

```
$ curl --silent http://localhost:8000/api/test/51/ | python -mjson.tool
{
    "columns": [
        "index",
        "STATE",
        "NAME",
        "POPESTIMATE2015"
    ],
    "data": [
        [
            51,
            "72",
            "Puerto Rico",
            3474182
        ]
    ]
}
```

...add new rows...

```
$ curl --silent -X POST -H "Content-Type: application/json" --data '{"columns":["index","STATE","NAME","POPESTIMATE2015"],"data":[[52,"YY","Mars",1]]}' http://localhost:8000/api/test/
{"columns":["index","STATE","NAME","POPESTIMATE2015"],"data":[[52,"YY","Mars",1]]}
```

...update existing rows...

```
$ curl --silent -X PUT -H "Content-Type: application/json" --data '{"columns":["index","STATE","NAME","POPESTIMATE2015"],"data":[[52,"YY","Mars",0]]}' http://localhost:8000/api/test/52/
```

...and delete rows...

```
$ curl --silent -X DELETE http://localhost:8000/api/test/52/
```

It provides pretty much the same functionality as regular DRM `ModelViewSet`s.

## Feedback

Comments, tickets and pull requests are welcomed. Hit
me up on Twitter at [@m4rgin4l](<https://twitter.com/m4rgin4l>) if you
have specific questions.
