from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Category, PastOrder
from stores.models import Store
from budget.models import Budget
from cart.models import ShoppingCart
from django.utils import timezone
import re

def product_list(request):
    selected_store_id = request.session.get('selected_store_id')
    selected_store = None
    products = Product.objects.all().select_related('category', 'store')
    
    if selected_store_id:
        try:
            selected_store = Store.objects.get(id=selected_store_id)
            products = products.filter(store=selected_store)
        except Store.DoesNotExist:
            pass

    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()

    if q:
        products = products.filter(name__icontains=q)
    if category_id:
        products = products.filter(category_id=category_id)

    if request.user.is_authenticated:
        budget_obj, _ = Budget.objects.get_or_create(customer=request.user, defaults={'amount': Decimal('2000.00')})
        cart_obj, _ = ShoppingCart.objects.get_or_create(customer=request.user)
        user_budget = budget_obj.amount
        cart_total = sum((item.subtotal() for item in cart_obj.items.all()), Decimal('0.00'))
    else:
        user_budget = Decimal('2000.00')
        cart_total = Decimal('0.00')

    remaining_budget = user_budget - cart_total

    context = {
        'products': products,
        'categories': Category.objects.all().order_by('name'),
        'selected_store': selected_store,
        'budget': {'amount': user_budget},
        'cart_total': cart_total,
        'remaining_budget': remaining_budget,
        'spent': cart_total,
        'remaining': remaining_budget,
    }
    return render(request, 'products/product_list.html', context)

@login_required
def view_cart(request):
    from cart.views import view_cart as cart_view
    return cart_view(request)


def price_comparison_view(request):
    query = request.GET.get('q', 'Rice 5kg')
    products = Product.objects.filter(name__icontains=query).select_related('store')
    
    comparison_data = []
    best_option = None
    min_price = float('inf')

    for product in products:
        is_available = product.stock_quantity > 0
        final_price = product.get_final_price()
        
        if is_available and final_price < min_price:
            min_price = final_price
            best_option = {
                'store_name': product.store.name if product.store else 'Unknown',
                'price': final_price
            }

        comparison_data.append({
            'store': product.store.name if product.store else 'Unknown',
            'price': final_price,
            'original_price': product.price,
            'available': is_available
        })

    context = {
        'query': query,
        'comparisons': comparison_data,
        'best_option': best_option if min_price != float('inf') else None
    }
    return render(request, 'products/price_comparison.html', context)

def cart_comparison_view(request):
    cart_item_queries = ['Rice', 'Oil', 'Sugar', 'Milk', 'Biscuits']
    stores = Store.objects.all()
    store_totals = []
    best_store = None
    min_total = float('inf')
    highest_total = 0

    for store in stores:
        store_products = Product.objects.filter(store=store)
        store_total = 0
        all_available = True

        for query in cart_item_queries:
            match = store_products.filter(name__icontains=query, stock_quantity__gt=0).first()
            if match:
                store_total += match.get_final_price()
            else:
                fallback = store_products.filter(name__icontains=query).first()
                if fallback:
                    store_total += fallback.get_final_price()
                else:
                    all_available = False

        if store_total > 0:
            store_totals.append({
                'store_name': store.name,
                'total': store_total,
                'available': all_available
            })
            
            if store_total < min_total:
                min_total = store_total
                best_store = store.name
            if store_total > highest_total:
                highest_total = store_total

    savings = highest_total - min_total if highest_total > min_total else 130

    context = {
        'cart_items': cart_item_queries,
        'store_totals': store_totals,
        'best_store': best_store,
        'min_total': min_total if min_total != float('inf') else 0,
        'savings': savings
    }
    return render(request, 'products/cart_comparison.html', context)

def ai_assistant_view(request):
    prompt = request.GET.get('prompt', '').strip()
    servings = int(request.GET.get('servings', 4))
    
    budget_limit = 500.00
    budget_match = re.search(r'(?:under\s*₹?|rs\.?)\s*(\d+)', prompt, re.IGNORECASE)
    if budget_match:
        budget_limit = float(budget_match.group(1))

    extracted_ingredients = []
    product_results = {}
    budget_recipes = []
    is_budget_query = 'under' in prompt.lower() or 'budget' in prompt.lower() or '₹' in prompt
    ai_recipe = None
    ai_active = False

    selected_store_id = request.session.get('selected_store_id')
    selected_store = None
    if selected_store_id:
        try:
            selected_store = Store.objects.get(id=selected_store_id)
        except Store.DoesNotExist:
            pass

    from .ai_service import is_ai_configured, get_openrouter_model, get_recipe_from_gemma
    model_name = get_openrouter_model()
    ai_configured = is_ai_configured()

    if prompt and ai_configured:
        catalog_sample = list(Product.objects.filter(stock_quantity__gt=0).values_list('name', flat=True)[:50])
        ai_data, _ = get_recipe_from_gemma(prompt, servings=servings, budget_limit=budget_limit, available_products=catalog_sample)
        if ai_data and isinstance(ai_data, dict) and ('ingredients' in ai_data or 'recipe_name' in ai_data):
            ai_recipe = ai_data
            ai_active = True
            for item in ai_data.get('ingredients', []):
                name = item.get('name') if isinstance(item, dict) else str(item)
                if name:
                    extracted_ingredients.append(name)

    if not ai_recipe:
        if is_budget_query:
            budget_recipes = [
                {
                    'name': 'Vegetable Pulao + Raita',
                    'estimated_cost': 320.00,
                    'ingredients': ['Rice', 'Mixed Vegetables', 'Curd', 'Spices', 'Ghee']
                },
                {
                    'name': 'Paneer Masala + Roti',
                    'estimated_cost': 470.00,
                    'ingredients': ['Paneer', 'Tomato', 'Onion', 'Wheat Flour', 'Butter', 'Spices']
                },
                {
                    'name': 'Vegetable Fried Rice',
                    'estimated_cost': 280.00,
                    'ingredients': ['Rice', 'Capsicum', 'Carrot', 'Soy Sauce', 'Oil', 'Spring Onion']
                }
            ]
            budget_recipes = [r for r in budget_recipes if r['estimated_cost'] <= budget_limit]
    elif prompt:
        lower_prompt = prompt.lower()
        if 'paneer butter masala' in lower_prompt:
            extracted_ingredients = ['Paneer', 'Butter', 'Tomato', 'Onion', 'Cream', 'Spices']
        elif 'pav bhaji' in lower_prompt:
            extracted_ingredients = ['Potato', 'Tomato', 'Onion', 'Capsicum', 'Pav', 'Butter', 'Pav Bhaji Masala', 'Coriander', 'Lemon']
        elif 'pizza' in lower_prompt:
            extracted_ingredients = ['Flour', 'Tomato', 'Onion', 'Capsicum', 'Pizza Sauce', 'Cheese', 'Oregano', 'Mozzarella']
        else:
            extracted_ingredients = [word.capitalize() for word in prompt.split() if len(word) > 3]

        for ingredient in extracted_ingredients:
            matches = Product.objects.filter(name__icontains=ingredient)
            if selected_store:
                matches = matches.filter(store=selected_store)
            product_results[ingredient] = matches.filter(stock_quantity__gt=0)

    if request.method == 'POST' and 'add_recipe_cart' in request.POST:
        return redirect('ai_assistant')

    context = {
        'prompt': prompt,
        'servings': servings,
        'budget_limit': budget_limit,
        'is_budget_query': is_budget_query,
        'budget_recipes': budget_recipes,
        'extracted_ingredients': extracted_ingredients,
        'product_results': product_results,
        'selected_store': selected_store,
    }
    return render(request, 'products/ai_assistant.html', context)

def budget_optimizer_view(request):
    from .ai_service import is_ai_configured, get_gemma_budget_advice

    budget = float(request.GET.get('budget', 1000.00))
    cart_total = float(request.GET.get('cart_total', 1150.00))
    ai_active = False

    # Default fallback data
    recommendations = [
        {'action': 'Replace Premium Oil with Standard Oil', 'saving': 40.00},
        {'action': 'Remove Biscuits from cart', 'saving': 30.00},
        {'action': 'Choose smaller Chocolate pack', 'saving': 50.00},
    ]
    ai_message = ""

    # Try live AI
    if is_ai_configured():
        ai_data, err = get_gemma_budget_advice(budget, cart_total)
        if ai_data and isinstance(ai_data, dict):
            ai_active = True
            if 'recommendations' in ai_data:
                recommendations = ai_data['recommendations']
            if 'ai_message' in ai_data:
                ai_message = ai_data['ai_message']

    total_savings = sum(float(r.get('saving', 0)) for r in recommendations)
    new_total = cart_total - total_savings
    deficit = new_total - budget

    if not ai_message:
        if deficit > 0:
            ai_message = f"You still need to save ₹{int(deficit)}. I recommend removing biscuits."
        else:
            ai_message = "Your cart is now fully within your target budget!"

    context = {
        'budget': budget,
        'cart_total': cart_total,
        'recommendations': recommendations,
        'total_savings': total_savings,
        'new_total': new_total,
        'ai_message': ai_message,
        'deficit': deficit,
        'ai_active': ai_active,
    }
    return render(request, 'products/budget_optimizer.html', context)

def plan_shopping_view(request):
    from .ai_service import is_ai_configured, get_gemma_shopping_plan

    prompt = request.GET.get('prompt', 'I have ₹3,000. Plan groceries for a family of 4 for one week.')
    ai_active = False
    ai_summary = ''
    savings_tips = []

    total_budget = 3000.00
    match = re.search(r'₹\s*([\d,]+)', prompt)
    if match:
        total_budget = float(match.group(1).replace(',', ''))

    # Default fallback categories
    categories = [
        {'name': 'Grains', 'allocated': 700.00},
        {'name': 'Vegetables', 'allocated': 500.00},
        {'name': 'Dairy', 'allocated': 400.00},
        {'name': 'Pulses', 'allocated': 500.00},
        {'name': 'Fruits', 'allocated': 400.00},
        {'name': 'Other', 'allocated': 300.00},
    ]

    # Try live AI for GET requests
    if request.method != 'POST' and is_ai_configured():
        ai_data, err = get_gemma_shopping_plan(prompt, total_budget)
        if ai_data and isinstance(ai_data, dict):
            ai_active = True
            if 'categories' in ai_data and isinstance(ai_data['categories'], list):
                ai_cats = []
                for c in ai_data['categories']:
                    ai_cats.append({
                        'name': c.get('name', 'Category'),
                        'allocated': float(c.get('allocated', 0)),
                        'items': c.get('items', []),
                    })
                if ai_cats:
                    categories = ai_cats
            ai_summary = ai_data.get('ai_summary', '')
            savings_tips = ai_data.get('savings_tips', [])

    if request.method == 'POST':
        updated_categories = []
        total_allocated = 0
        for cat in categories:
            name = cat['name']
            val = float(request.POST.get(f'cat_{name}', cat.get('allocated', 0)))
            updated_categories.append({'name': name, 'allocated': val})
            total_allocated += val
        categories = updated_categories
        total_allocated_sum = total_allocated
    else:
        total_allocated_sum = sum(c.get('allocated', 0) for c in categories)

    remaining = total_budget - total_allocated_sum

    context = {
        'prompt': prompt,
        'total_budget': total_budget,
        'categories': categories,
        'total_allocated_sum': total_allocated_sum,
        'remaining': remaining,
        'ai_active': ai_active,
        'ai_summary': ai_summary,
        'savings_tips': savings_tips,
    }
    return render(request, 'products/plan_shopping.html', context)

@login_required
def add_to_cart(request, product_id=None):
    from cart.views import add_to_cart as cart_add_to_cart
    if product_id is not None:
        return cart_add_to_cart(request, product_id)
    return redirect('view_cart')


@login_required
def shopping_history_view(request):
    # Handle "Buy Again" action
    order_id = request.GET.get('buy_again')
    if order_id:
        try:
            order = PastOrder.objects.get(id=order_id, customer=request.user)
            # Store items in session for instant checkout/cart recreation
            request.session['recreated_cart'] = order.items_summary
            return redirect('product_list')
        except PastOrder.DoesNotExist:
            pass

    # Fetch past orders ordered by date descending
    orders = PastOrder.objects.filter(customer=request.user).order_by('-date')

    context = {
        'orders': orders,
    }
    return render(request, 'products/shopping_history.html', context)

def bill_scanner_view(request):
    scanned_data = None
    success_message = None

    if request.method == 'POST' and request.FILES.get('bill_image'):
        bill_file = request.FILES['bill_image']
        
        # Simulated OCR extraction based on the uploaded bill example
        # In production, you would pass bill_file to pytesseract.image_to_string(Image.open(bill_file))
        extracted_items = "Rice (₹320), Oil (₹180), Milk (₹100), Biscuits (₹50)"
        total_amount = 650.00
        store_detected = "D-Mart"

        # Automatically save the purchase to the database
        order = PastOrder.objects.create(
            customer=request.user if request.user.is_authenticated else None,
            store_name=store_detected,
            total_amount=total_amount,
            date=timezone.now().date(),
            items_summary=extracted_items
        )

        scanned_data = {
            'store': store_detected,
            'items': [
                {'name': 'Rice', 'price': 320},
                {'name': 'Oil', 'price': 180},
                {'name': 'Milk', 'price': 100},
                {'name': 'Biscuits', 'price': 50},
            ],
            'total': total_amount
        }
        success_message = "Bill successfully scanned and saved to your purchase history!"

    context = {
        'scanned_data': scanned_data,
        'success_message': success_message,
    }
    return render(request, 'products/bill_scanner.html', context)

def spending_analytics_view(request):
    from .ai_service import is_ai_configured, get_gemma_spending_analytics

    total_spending = 8450.00
    monthly_budget = 10000.00
    remaining = monthly_budget - total_spending
    ai_active = False
    ai_summary = ''
    ai_tips = []
    health_score = 0

    categories = [
        {'name': 'Groceries', 'amount': 3500.00},
        {'name': 'Vegetables', 'amount': 1800.00},
        {'name': 'Dairy', 'amount': 1200.00},
        {'name': 'Personal Care', 'amount': 1000.00},
        {'name': 'Snacks', 'amount': 950.00},
    ]

    # Try live AI
    if is_ai_configured():
        ai_data, err = get_gemma_spending_analytics(
            categories=categories,
            total_spending=total_spending,
            monthly_budget=monthly_budget
        )
        if ai_data and isinstance(ai_data, dict):
            ai_active = True
            ai_summary = ai_data.get('ai_summary', '')
            ai_tips = ai_data.get('tips', [])
            health_score = ai_data.get('health_score', 0)

    context = {
        'total_spending': total_spending,
        'monthly_budget': monthly_budget,
        'remaining': remaining,
        'categories': categories,
        'ai_active': ai_active,
        'ai_summary': ai_summary,
        'ai_tips': ai_tips,
        'health_score': health_score,
    }
    return render(request, 'products/spending_analytics.html', context)

def spending_insights_view(request):
    from .ai_service import is_ai_configured, get_gemma_spending_insights

    ai_active = False
    ai_summary = ''

    # Default fallback insights
    insights = [
        {
            'type': 'trend',
            'message': 'Your grocery spending increased by 12% compared with last month.',
            'icon': '📈',
            'category': 'Spending Trend',
            'badge_color': 'warning'
        },
        {
            'type': 'highlight',
            'message': 'You spent the most on groceries this month (₹3,500 total).',
            'icon': '🛒',
            'category': 'Top Expense',
            'badge_color': 'primary'
        },
        {
            'type': 'saving',
            'message': 'You frequently purchase cooking oil. Store B (Reliance Smart) currently has a lower price (₹165 vs ₹180).',
            'icon': '💡',
            'category': 'Price Alert & Savings',
            'badge_color': 'success'
        },
        {
            'type': 'habit',
            'message': 'You tend to buy dairy items every Saturday morning. Consider batch-ordering on Friday to save on delivery fees.',
            'icon': '🥛',
            'category': 'Shopping Habit',
            'badge_color': 'info'
        }
    ]

    # Try live AI
    if is_ai_configured():
        spending_data = {
            'total_spending': 8450,
            'monthly_budget': 10000,
            'categories': [
                {'name': 'Groceries', 'amount': 3500},
                {'name': 'Vegetables', 'amount': 1800},
                {'name': 'Dairy', 'amount': 1200},
                {'name': 'Personal Care', 'amount': 1000},
                {'name': 'Snacks', 'amount': 950},
            ]
        }
        ai_data, err = get_gemma_spending_insights(spending_data)
        if ai_data and isinstance(ai_data, dict):
            ai_active = True
            if 'insights' in ai_data and isinstance(ai_data['insights'], list):
                insights = ai_data['insights']
            ai_summary = ai_data.get('ai_summary', '')

    context = {
        'insights': insights,
        'ai_active': ai_active,
        'ai_summary': ai_summary,
    }
    return render(request, 'products/spending_insights.html', context)

def advanced_ai_agent_view(request):
    from .ai_service import is_ai_configured, run_gemma_shopping_agent

    prompt = request.GET.get(
        'prompt', 
        'I have ₹2,500. I need groceries for 5 people. I also want ingredients for Paneer Butter Masala. Find the cheapest available store.'
    )
    ai_active = False
    strategy_summary = ''
    savings_tips = []

    # Extract budget from prompt
    budget = 2500.00
    budget_match = re.search(r'₹\s*([\d,]+)', prompt)
    if budget_match:
        budget = float(budget_match.group(1).replace(',', ''))

    # Default fallback data
    store_name = "D-Mart"
    total_cost = 2340.00
    remaining = budget - total_cost
    items_available = "9/10"
    estimated_savings = 180.00
    shopping_items = [
        {'name': 'Paneer (250g)', 'store': 'D-Mart', 'price': 110, 'discount': 15},
        {'name': 'Butter (500g)', 'store': 'D-Mart', 'price': 240, 'discount': 20},
        {'name': 'Tomatoes (1kg)', 'store': 'D-Mart', 'price': 40, 'discount': 5},
        {'name': 'Onions (2kg)', 'store': 'D-Mart', 'price': 60, 'discount': 10},
        {'name': 'Cashews & Cream', 'store': 'D-Mart', 'price': 150, 'discount': 10},
        {'name': 'Wheat Flour (5kg)', 'store': 'D-Mart', 'price': 220, 'discount': 30},
        {'name': 'Rice (5kg)', 'store': 'D-Mart', 'price': 350, 'discount': 40},
        {'name': 'Cooking Oil (1L)', 'store': 'D-Mart', 'price': 160, 'discount': 20},
        {'name': 'Mixed Spices & Masala', 'store': 'D-Mart', 'price': 120, 'discount': 15},
        {'name': 'Milk (1L)', 'store': 'D-Mart', 'price': 68, 'discount': 0},
    ]

    # Try live AI
    if is_ai_configured():
        available_stores = list(Store.objects.values_list('name', flat=True))
        sample_products = list(Product.objects.filter(stock_quantity__gt=0).values_list('name', flat=True)[:30])
        ai_data, err = run_gemma_shopping_agent(
            prompt, user_budget=budget,
            available_stores=available_stores or None,
            sample_products=sample_products or None
        )
        if ai_data and isinstance(ai_data, dict):
            ai_active = True
            store_name = ai_data.get('store_name', store_name)
            total_cost = float(ai_data.get('total_cost', total_cost))
            remaining = budget - total_cost
            items_available = ai_data.get('items_count_summary', items_available)
            estimated_savings = float(ai_data.get('estimated_savings', estimated_savings))
            strategy_summary = ai_data.get('strategy_summary', '')
            savings_tips = ai_data.get('savings_tips', [])
            if 'items' in ai_data and isinstance(ai_data['items'], list):
                ai_items = []
                for item in ai_data['items']:
                    ai_items.append({
                        'name': item.get('name', 'Item'),
                        'store': item.get('store', store_name),
                        'price': float(item.get('price', 0)),
                        'discount': float(item.get('discount', 0)),
                    })
                if ai_items:
                    shopping_items = ai_items

    context = {
        'prompt': prompt,
        'budget': budget,
        'store_name': store_name,
        'total_cost': total_cost,
        'remaining': remaining,
        'items_available': items_available,
        'estimated_savings': estimated_savings,
        'shopping_items': shopping_items,
        'ai_active': ai_active,
        'strategy_summary': strategy_summary,
        'savings_tips': savings_tips,
    }
    return render(request, 'products/advanced_agent.html', context)

def barcode_scanner_view(request):
    barcode = request.GET.get('barcode', '8901058853102') # Default sample barcode for Tata Salt 1kg
    
    product_found = None
    comparisons = []

    if barcode:
        # Simulated barcode database lookup
        if barcode in ['8901058853102', 'salt']:
            product_found = {'name': 'Tata Salt', 'quantity': '1kg'}
            comparisons = [
                {'store': 'D-Mart', 'price': 28.00, 'best': True},
                {'store': 'Reliance Smart', 'price': 30.00, 'best': False},
                {'store': 'More', 'price': 32.00, 'best': False},
            ]
        elif barcode in ['8901201011234', 'oil']:
            product_found = {'name': 'Fortune Sun Flower Oil', 'quantity': '1L'}
            comparisons = [
                {'store': 'Reliance Smart', 'price': 165.00, 'best': True},
                {'store': 'D-Mart', 'price': 170.00, 'best': False},
                {'store': 'More', 'price': 175.00, 'best': False},
            ]
        else:
            product_found = {'name': 'Generic Item (Scanned)', 'quantity': '1 unit'}
            comparisons = [
                {'store': 'D-Mart', 'price': 50.00, 'best': True},
                {'store': 'Reliance Smart', 'price': 55.00, 'best': False},
            ]

    context = {
        'barcode': barcode,
        'product_found': product_found,
        'comparisons': comparisons,
    }
    return render(request, 'products/barcode_scanner.html', context)

def smart_recommendations_view(request):
    from .ai_service import is_ai_configured, get_gemma_recommendations

    ai_active = False
    ai_summary = ''

    # Default fallback recommendations
    recommendations = [
        {
            'type': 'frequency',
            'title': 'Restock Reminder',
            'message': 'You usually buy Aashirvaad Atta (10kg) every 30 days. Your last purchase was 28 days ago.',
            'icon': '🔄',
            'badge_color': 'primary'
        },
        {
            'type': 'brand_switch',
            'title': 'Brand Alternatives',
            'message': 'Fortune Sun Flower Oil is ₹20 cheaper than your usual brand this week.',
            'icon': '💸',
            'badge_color': 'success'
        },
        {
            'type': 'store_offer',
            'title': 'Store Deal Alert',
            'message': 'D-Mart currently has a flat 15% offer on products in your active shopping list.',
            'icon': '🏷️',
            'badge_color': 'warning'
        }
    ]

    # Try live AI
    if is_ai_configured():
        catalog_sample = list(Product.objects.filter(stock_quantity__gt=0).values_list('name', flat=True)[:30])
        purchase_history = list(
            PastOrder.objects.values_list('items_summary', flat=True).order_by('-date')[:10]
        )
        ai_data, err = get_gemma_recommendations(
            purchase_history=purchase_history or None,
            catalog_sample=catalog_sample or None
        )
        if ai_data and isinstance(ai_data, dict):
            ai_active = True
            if 'recommendations' in ai_data and isinstance(ai_data['recommendations'], list):
                recommendations = ai_data['recommendations']
            ai_summary = ai_data.get('ai_summary', '')

    context = {
        'recommendations': recommendations,
        'ai_active': ai_active,
        'ai_summary': ai_summary,
    }
    return render(request, 'products/smart_recommendations.html', context)