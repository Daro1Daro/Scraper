from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout

from .forms import UrlsForm
from . import scraper as sc
from .models import Product


@login_required
def get_urls(request):
    if request.method == 'POST':
        form = UrlsForm(request.POST)
        if form.is_valid():
            product_list = []
            data = form.cleaned_data.get('urls')
            urls = data.splitlines()
            results, invalids = sc.scrape(urls)
            for result in results:
                product = Product()
                product.index = result['Indeks']
                product.name = result['Nazwa']
                product.producer = result['Producent']
                product.price = result['Cena']
                product.gender = result['Płeć']
                product.url = result['Adres zdjecia']
                if result.get('Opis dodatkowy') is not None:
                    product.description = result['Opis dodatkowy']
                if result.get('Cena przed promocja') is not None:
                    product.price_old = result['Cena przed promocja']


                product_list.append(product)
                product.save()

            xml = serializers.serialize("xml", product_list)
            response = HttpResponse(xml, content_type='application/xml')
            response['Content-Disposition'] = 'attachement; filename=wynik.xml'

            return response
    else:
        form = UrlsForm()

    return render(request, 'scraper.html', {'form': form})


def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('scraper'))
            else:
                return HttpResponse('Your account is disabled')
        else:
            print('Invalid login details: {0}, {1}'.format(username, password))
            return HttpResponse('Invalid login detail supplied.')
    else:
        return render(request, 'login.html', {})


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))