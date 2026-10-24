from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import ShoppingList, ListItem
from budget.models import Budget
from products.models import Product

@login_required
def list_management(request):
    shopping_lists = request.user.shopping_lists.all().order_by('-created_at')
    budget, _ = Budget.objects.get_or_create(customer=request.user)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            ShoppingList.objects.create(customer=request.user, name=name)
            return redirect('list_management')

    context = {
        'shopping_lists': shopping_lists,
        'budget': budget,
    }
    return render(request, 'lists/list_management.html', context)

@login_required
def list_detail(request, list_id):
    shopping_list = get_object_or_404(ShoppingList, id=list_id, customer=request.user)
    budget, _ = Budget.objects.get_or_create(customer=request.user)
    
    items = shopping_list.items.all()
    estimated_total = sum((item.subtotal() for item in items), Decimal('0.00'))
    remaining_budget = budget.amount - estimated_total

    if request.method == 'POST':
        # Add item logic
        product_id = request.POST.get('product_id')
        custom_name = request.POST.get('custom_item_name')
        quantity = int(request.POST.get('quantity', 1))
        price = Decimal(request.POST.get('estimated_price', '0.00'))
        
        product = None
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            price = product.price # Auto-fill from catalog if selected

        ListItem.objects.create(
            shopping_list=shopping_list,
            product=product,
            custom_item_name=custom_name if not product else product.name,
            quantity=quantity,
            estimated_price=price
        )
        return redirect('list_detail', list_id=shopping_list.id)

    products = Product.objects.filter(stock_quantity__gt=0)
    context = {
        'shopping_list': shopping_list,
        'items': items,
        'estimated_total': estimated_total,
        'budget': budget,
        'remaining_budget': remaining_budget,
        'products': products,
    }
    return render(request, 'lists/list_detail.html', context)

@login_required
def delete_list_item(request, item_id):
    item = get_object_or_404(ListItem, id=item_id, shopping_list__customer=request.user)
    list_id = item.shopping_list.id
    item.delete()
    return redirect('list_detail', list_id=list_id)