from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('login', views.login, name='login'),
    path('welcome1', views.home_welcome, name='welcome1'),
    #path('form_post', views.get_form, name='form_post'),
    path('show_data', views.show_data, name='show_data'),
    path('show_trend', views.show_trend, name='show_trend'),
    path('gen_wordcloud_pic', views.gen_wordcloud_pic, name='gen_wordcloud_pic'),
    path('form_trend_data', views.form_trend_data, name='form_trend_data'),
    path('default_trend_data', views.default_trend_data, name='default_trend_data'),
    path('get_topic_data', views.get_topic_data, name='get_topic_data'),
    #path('get_full_topic_data', views.get_full_topic_data, name='get_full_topic_data'),
    path('mark_process', views.mark_process, name='mark_process'),
    path('del_error', views.del_error, name='del_error')
]