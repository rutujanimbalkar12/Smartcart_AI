from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Budget
from cart.models import ShoppingCart

@login_required
def budget_view(request):
    budget, _ = Budget.objects.get_or_create(customer=request.user, defaults={'amount': Decimal('2000.00')})
    
    if request.method == 'POST':
        amount_raw = request.POST.get('amount', '').strip()
        if amount_raw:
            try:
                new_amount = Decimal(amount_raw)
                if new_amount < 0:
                    messages.error(request, 'Budget cannot be negative.')
                else:
                    budget.amount = new_amount
                    budget.save()
                    messages.success(request, f'Monthly budget successfully updated to ₹{budget.amount:.2f}')
                    return redirect('budget_view')
            except (InvalidOperation, ValueError):
                messages.error(request, 'Please enter a valid numeric budget amount.')

    # Compute live cart spending
    cart, _ = ShoppingCart.objects.get_or_create(customer=request.user)
    items = cart.items.select_related('product').all()
    cart_total = sum((item.subtotal() for item in items), Decimal('0.00'))
    remaining = budget.amount - cart_total
    
    usage_pct = 0
    if budget.amount > 0:
        usage_pct = min(100, max(0, int((cart_total / budget.amount) * 100)))

    context = {
        'budget': budget,
        'cart_total': cart_total,
        'remaining': remaining,
        'usage_pct': usage_pct,
        'cart_item_count': items.count(),
    }
    return render(request, 'budget/budget.html', context)

@login_required
def update_budget(request):
    if request.method == 'POST':
        budget, _ = Budget.objects.get_or_create(customer=request.user, defaults={'amount': Decimal('2000.00')})
        amount_raw = request.POST.get('amount', '').strip()
        if amount_raw:
            try:
                new_amount = Decimal(amount_raw)
                if new_amount >= 0:
                    budget.amount = new_amount
                    budget.save()
                    messages.success(request, f'Budget updated to ₹{budget.amount:.2f}')
            except (InvalidOperation, ValueError):
                pass
    return redirect('budget_view')