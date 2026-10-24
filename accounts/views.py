from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db.models import Avg, Count, Sum
from django.shortcuts import render, redirect
from django.utils import timezone

from budget.models import Budget
from products.models import Category, PastOrder
from .forms import CustomerRegistrationForm
from .forms import CustomerProfileForm, UserProfileForm
from .models import CustomerProfile
from django.db import IntegrityError
from stores.models import Store

def register_customer(request):
    if request.user.is_authenticated:
        return redirect('product_list')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, f'Welcome, {user.first_name or user.username}! Your account has been created.')
                return redirect('product_list')
            except IntegrityError:
                form.add_error(None, 'An account with this username or email already exists. Please choose another username or sign in.')
            except Exception as e:
                form.add_error(None, f'Unable to register: {str(e)}')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def customer_dashboard(request):
    return render(request, 'accounts/customer_dashboard.html')


@login_required
def customer_profile(request):
    profile, _ = CustomerProfile.objects.get_or_create(customer=request.user)
    budget, _ = Budget.objects.get_or_create(customer=request.user)
    profile_form = UserProfileForm(instance=request.user)
    settings_form = CustomerProfileForm(instance=profile)
    budget_error = ''

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'profile':
            profile_form = UserProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Your profile details were updated.')
                return redirect('customer_profile')
        elif action == 'preferences':
            settings_form = CustomerProfileForm(request.POST, instance=profile)
            if settings_form.is_valid():
                profile = settings_form.save()
                if 'preferred_categories' in request.POST:
                    profile.preferred_categories = request.POST.getlist('preferred_categories')
                    profile.save(update_fields=['preferred_categories', 'updated_at'])
                messages.success(request, 'Your preferences were saved.')
                return redirect('customer_profile')
        elif action == 'budget':
            try:
                amount = Decimal(request.POST.get('amount', '').strip())
                if amount < 0:
                    raise InvalidOperation
                budget.amount = amount
                budget.save(update_fields=['amount', 'updated_at'])
                messages.success(request, 'Your monthly budget was updated.')
                return redirect('customer_profile')
            except (InvalidOperation, ValueError):
                budget_error = 'Enter a valid budget amount of zero or more.'

    current_month = timezone.localdate().replace(day=1)
    orders = PastOrder.objects.filter(
        customer=request.user,
        date__year=current_month.year,
        date__month=current_month.month,
    )
    spending = orders.aggregate(total=Sum('total_amount'), count=Count('id'), average=Avg('total_amount'))
    current_spending = spending['total'] or Decimal('0.00')
    remaining = budget.amount - current_spending
    usage = min(100, max(0, int((current_spending / budget.amount) * 100))) if budget.amount else 0

    context = {
        'profile': profile,
        'budget': budget,
        'profile_form': profile_form,
        'settings_form': settings_form,
        'budget_error': budget_error,
        'categories': Category.objects.order_by('name'),
        'stores': Store.objects.order_by('name'),
        'recent_orders': PastOrder.objects.filter(customer=request.user).order_by('-date')[:5],
        'current_spending': current_spending,
        'remaining_budget': remaining,
        'budget_usage': usage,
        'purchase_count': spending['count'] or 0,
        'average_purchase': spending['average'] or Decimal('0.00'),
    }
    return render(request, 'accounts/profile.html', context)