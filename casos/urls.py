from django.urls import path
from . import views

urlpatterns = [
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/nuevo/', views.crear_cliente, name='crear_cliente'),
    path('clientes/<int:id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:id>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),
    path('casos/', views.lista_casos, name='lista_casos'),
    path('casos/<int:id>/', views.detalle_caso, name='detalle_caso'),
    path('casos/api/<int:id>/', views.api_caso, name='api_caso'),
]
