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
from django.conf.urls import url, include
from django.core.urlresolvers import reverse_lazy
from django.contrib import admin
from django.views.generic.base import RedirectView, TemplateView

from rest_framework.routers import DefaultRouter


from census_data.views import (DataFrameListSerializerTestView, DataFrameIndexSerializerTestView,
                               DataFrameRecordsSerializerTestView, StateEstimatesViewSet,
                               CountyEstimatesViewSet, CountiesView)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'states', StateEstimatesViewSet, base_name='state')
router.register(r'counties', CountyEstimatesViewSet, base_name='county')

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', RedirectView.as_view(url=reverse_lazy('states')), name='home'),
    url(r'^states/$', TemplateView.as_view(template_name='states.html'), name='states'),
    url(r'^counties/(?P<state_fips_code>\d{2})/$', CountiesView.as_view(), name='counties'),
    url(r'^list_serializer_test/$', DataFrameListSerializerTestView.as_view(),
        name='list-serializer-test'),
    url(r'^index_serializer_test/$', DataFrameIndexSerializerTestView.as_view(),
        name='index-serializer-test'),
    url(r'^records_serializer_test/$', DataFrameRecordsSerializerTestView.as_view(),
        name='records-serializer-test'),
    url(r'^api/', include(router.urls)),
]
