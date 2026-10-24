from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from products.models import Product
from .models import ShoppingCart, CartItem
from budget.models import Budget

@login_required
def view_cart(request):
    cart, _ = ShoppingCart.objects.get_or_create(customer=request.user)
    budget, _ = Budget.objects.get_or_create(customer=request.user)
    
    items = cart.items.select_related('product').all()
    cart_total = sum((item.subtotal() for item in items), Decimal('0.00'))
    remaining_budget = budget.amount - cart_total
    
    budget_percentage = (float(cart_total) / float(budget.amount) * 100) if budget.amount > 0 else 0
    
    # Version 1.3 Alert & Smart Suggestions Logic
    alert_message = None
    alert_class = "success"
    suggestions = []

    if budget.amount > 0:
        if cart_total > budget.amount:
            deficit = cart_total - budget.amount
            alert_message = f"You need to save ₹{deficit}."
            alert_class = "danger"
            
            # Sort items by subtotal descending to suggest cutting expensive items first
            sorted_items = sorted(items, key=lambda x: x.subtotal(), reverse=True)
            for item in sorted_items:
                savings_amt = item.subtotal()
                item_name = item.product.name if item.product else 'custom item'
                suggestions.append({
                    'action': f"Remove {item_name}",
                    'savings': savings_amt
                })
        elif cart_total == budget.amount:
            alert_message = "🔴 You have reached your budget."
            alert_class = "danger"
        elif budget_percentage >= 80:
            alert_message = f"⚠️ You have used {int(budget_percentage)}% of your budget."
            alert_class = "warning"
        else:
            alert_message = "Within Budget"

    context = {
        'items': items,
        'cart_total': cart_total,
        'budget': budget,
        'remaining_budget': remaining_budget,
        'budget_percentage': budget_percentage,
        'alert_message': alert_message,
        'alert_class': alert_class,
        'suggestions': suggestions,
    }
    return render(request, 'cart/cart_detail.html', context)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, stock_quantity__gt=0)
    cart, _ = ShoppingCart.objects.get_or_create(customer=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        if cart_item.quantity < product.stock_quantity:
            cart_item.quantity += 1
            cart_item.save()
    else:
        if product.stock_quantity > 0:
            cart_item.quantity = 1
            cart_item.save()
            
    return redirect('view_cart')

@login_required
def update_cart_item(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)
    
    if action == 'increase':
        if cart_item.quantity < cart_item.product.stock_quantity:
            cart_item.quantity += 1
            cart_item.save()
    elif action == 'decrease':
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            cart_item.delete()
        else:
            cart_item.save()
    elif action == 'remove':
        cart_item.delete()
        
    return redirect('view_cart')