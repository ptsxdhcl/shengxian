from django.shortcuts import render
# from goods.models import Goods
# Create your views here.
def index(request):
    '''首页'''
    return render(request, 'index.html')