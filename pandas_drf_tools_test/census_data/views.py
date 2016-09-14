from os import path

import pandas as pd

from rest_framework import response, views

from pandas_drf_tools.serializers import DataFrameDictSerializer


_data = path.join(path.abspath(path.dirname(__file__)), 'data')
_cc_est2015_alldata_df = pd.read_pickle(path.join(_data, 'CC-EST2015-ALLDATA.pkl'))


class DataFrameDictSerializerTestView(views.APIView):
    def get(self, request, *args, **kwargs):
        sample = _cc_est2015_alldata_df.sample(10)
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
