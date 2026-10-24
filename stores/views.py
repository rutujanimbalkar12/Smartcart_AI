from django.shortcuts import render, redirect
from .models import Store
from products.models import Product

def store_selection(request):
    if request.method == 'POST':
        store_id = request.POST.get('store_id')
        if store_id:
            request.session['selected_store_id'] = store_id
        return redirect('product_list')
    
    stores = Store.objects.all()
    context = {'stores': stores}
    return render(request, 'stores/store_selection.html', context)

def store_dashboard(request):
    return render(request, 'stores/store_dashboard.html')

def store_locator_view(request):
    query = request.GET.get('q', '')
    stores = Store.objects.all().order_by('distance_km')
    
    if query:
        stores = stores.filter(name__icontains=query)
        
    store_data = []
    for store in stores:
        products = Product.objects.filter(store=store)
        store_data.append({
            'store': store,
            'products': products,
        })
        
    context = {
        'store_data': store_data,
        'query': query,
    }
    return render(request, 'stores/store_locator.html', context)