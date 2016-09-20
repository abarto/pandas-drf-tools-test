"""pandas_drf_tools_test URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from census_data.views import (DataFrameListSerializerTestView, DataFrameIndexSerializerTestView,
                               DataFrameRecordsSerializerTestView)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^list_serializer_test/$', DataFrameListSerializerTestView.as_view(),
        name='list-serializer-test'),
    url(r'^index_serializer_test/$', DataFrameIndexSerializerTestView.as_view(),
        name='index-serializer-test'),
    url(r'^records_serializer_test/$', DataFrameRecordsSerializerTestView.as_view(),
        name='records-serializer-test')
]
