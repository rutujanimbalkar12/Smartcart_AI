import os
import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemma-4-31b-it:free"

def get_openrouter_api_key():
    """Retrieve the OpenRouter API key from settings or environment."""
    key = getattr(settings, 'OPENROUTER_API_KEY', '') or os.getenv('OPENROUTER_API_KEY', '')
    return key.strip()

def get_openrouter_model():
    """Retrieve the OpenRouter model name (defaults to google/gemma-4-31b-it:free)."""
    return getattr(settings, 'OPENROUTER_MODEL', '') or os.getenv('OPENROUTER_MODEL', DEFAULT_MODEL)

def is_ai_configured():
    """Check if the OpenRouter API key is configured."""
    key = get_openrouter_api_key()
    return bool(key and not key.startswith('your_'))

def call_openrouter(messages, temperature=0.7, max_tokens=1024, timeout=20):
    """
    Call the OpenRouter chat completions API using the configured model.
    Returns (response_text, error_message).
    """
    api_key = get_openrouter_api_key()
    if not api_key:
        return None, "OPENROUTER_API_KEY is not configured. Set it in .env to enable live AI responses."

    model = get_openrouter_model()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://127.0.0.1:8000",
        "X-Title": "SmartCart AI",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                return content.strip(), None
            return None, "No completion choices returned by model."
        else:
            err_msg = f"OpenRouter API error {response.status_code}: {response.text[:200]}"
            logger.warning(err_msg)
            return None, err_msg
    except requests.exceptions.Timeout:
        return None, "OpenRouter request timed out. Using fallback response."
    except Exception as e:
        logger.exception("OpenRouter call failed")
        return None, f"Error communicating with OpenRouter: {str(e)}"


def get_recipe_from_gemma(prompt, servings=4, budget_limit=500.0, available_products=None):
    """
    Ask Gemma 4 on OpenRouter to plan a recipe, recommend ingredients,
    and estimate costs within the budget.
    """
    if not is_ai_configured():
        return None, "API key not configured"

    catalog_context = ""
    if available_products:
        catalog_context = f"Available grocery items in catalog: {', '.join(available_products[:40])}."

    system_prompt = (
        "You are the SmartCart AI Culinary and Budget Chef powered by Google Gemma 4. "
        "Help the user plan delicious meals strictly within their budget. "
        "Always respond in valid JSON format with this exact structure:\n"
        "{\n"
        '  "recipe_name": "Name of recipe",\n'
        '  "estimated_cost": 320,\n'
        '  "servings": 4,\n'
        '  "description": "Short appetizing description",\n'
        '  "ingredients": [\n'
        '    {"name": "Rice", "qty": "500g", "est_price": 50},\n'
        '    {"name": "Paneer", "qty": "200g", "est_price": 90}\n'
        "  ],\n"
        '  "cooking_time": "30 mins",\n'
        '  "instructions": ["Step 1...", "Step 2..."],\n'
        '  "budget_tip": "Tip to save money"\n'
        "}\n"
        "Do not include markdown code block backticks if possible, just the raw JSON."
    )

    user_prompt = (
        f"Meal / Prompt: {prompt}\n"
        f"Number of servings: {servings}\n"
        f"Target maximum budget: ₹{budget_limit}\n"
        f"{catalog_context}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw_text, err = call_openrouter(messages, temperature=0.6, max_tokens=1024)
    if not raw_text:
        return None, err

    # Parse JSON from response
    try:
        clean_text = raw_text
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0]
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0]
        clean_text = clean_text.strip()
        data = json.loads(clean_text)
        return data, None
    except Exception as e:
        logger.info(f"Could not parse json from Gemma recipe response: {e}")
        return {"raw_text": raw_text, "recipe_name": prompt.title()}, None


def run_gemma_shopping_agent(prompt, user_budget=2500.0, available_stores=None, sample_products=None):
    """
    Run Gemma 4 as an autonomous grocery shopping agent to select the best store,
    itemized cart, and calculate savings.
    """
    if not is_ai_configured():
        return None, "API key not configured"

    store_list = ", ".join(available_stores) if available_stores else "D-Mart, Reliance Smart, More Supermarket"
    prod_sample = ", ".join(sample_products[:30]) if sample_products else "Rice, Oil, Milk, Flour, Veggies, Spices"

    system_prompt = (
        "You are SmartCart AI Shopping Agent v5.0 powered by Google Gemma 4 (31B-IT). "
        "Given the user's budget and shopping requirements, plan an optimal shopping cart "
        "from the best available store to keep them strictly under budget while fulfilling requirements.\n"
        "Respond in valid JSON format:\n"
        "{\n"
        '  "store_name": "D-Mart",\n'
        '  "total_cost": 2150,\n'
        '  "remaining_budget": 350,\n'
        '  "items_count_summary": "10/10 items secured",\n'
        '  "estimated_savings": 220,\n'
        '  "strategy_summary": "Explanation of store choice and how budget was preserved",\n'
        '  "items": [\n'
        '    {"name": "Rice (5kg)", "price": 320, "discount": 30, "store": "D-Mart"},\n'
        '    {"name": "Cooking Oil (1L)", "price": 160, "discount": 20, "store": "D-Mart"}\n'
        "  ],\n"
        '  "savings_tips": ["Tip 1", "Tip 2"]\n'
        "}\n"
        "Do not include markdown code block backticks if possible, just the raw JSON."
    )

    user_prompt = (
        f"Goal: {prompt}\n"
        f"Budget: ₹{user_budget}\n"
        f"Available Stores: {store_list}\n"
        f"Sample Catalog: {prod_sample}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw_text, err = call_openrouter(messages, temperature=0.5, max_tokens=1200)
    if not raw_text:
        return None, err

    try:
        clean_text = raw_text
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0]
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0]
        clean_text = clean_text.strip()
        data = json.loads(clean_text)
        return data, None
    except Exception as e:
        logger.info(f"Could not parse json from Gemma agent response: {e}")
        return {"raw_text": raw_text, "strategy_summary": raw_text[:300]}, None


def get_gemma_budget_advice(budget, cart_total, items=None):
    """
    Get live AI recommendations from Gemma 4 on how to optimize an over-budget cart.
    """
    if not is_ai_configured():
        return None, "API key not configured"

    item_names = [i.get('name', 'Item') for i in (items or [])]
    system_prompt = (
        "You are the SmartCart AI Budget Optimization expert powered by Google Gemma 4. "
        "The customer is shopping and wants to save money. Give 3-4 concrete, realistic substitutions "
        "or removals with estimated savings in INR (₹) and a brief motivational closing message.\n"
        "Respond in valid JSON:\n"
        "{\n"
        '  "ai_message": "Advice summary",\n'
        '  "recommendations": [\n'
        '    {"action": "Replace Premium Brand Rice with Store Brand", "saving": 60},\n'
        '    {"action": "Reduce snack items", "saving": 45}\n'
        "  ]\n"
        "}"
    )

    user_prompt = (
        f"Target Budget: ₹{budget}\n"
        f"Current Cart Total: ₹{cart_total}\n"
        f"Items in cart: {', '.join(item_names) if item_names else 'Groceries, Snacks, Dairy, Staples'}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw_text, err = call_openrouter(messages, temperature=0.5, max_tokens=600)
    if not raw_text:
        return None, err

    try:
        clean_text = raw_text
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0]
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0]
        clean_text = clean_text.strip()
        return json.loads(clean_text), None
    except Exception:
        return None, "Failed to parse json"


def get_gemma_shopping_plan(prompt, total_budget=3000.0):
    """
    Ask Gemma 4 to generate a weekly grocery shopping plan with category-wise
    budget allocations for a family.
    """
    if not is_ai_configured():
        return None, "API key not configured"

    system_prompt = (
        "You are SmartCart AI Weekly Planner powered by Google Gemma 4. "
        "Given the user's budget and family details, create an optimal weekly grocery "
        "shopping plan with category-wise budget allocations.\n"
        "Respond in valid JSON format:\n"
        "{\n"
        '  "plan_title": "Weekly Grocery Plan",\n'
        '  "total_budget": 3000,\n'
        '  "categories": [\n'
        '    {"name": "Grains & Staples", "allocated": 700, "items": ["Rice 5kg", "Wheat Flour 5kg"]},\n'
        '    {"name": "Vegetables", "allocated": 500, "items": ["Potato 2kg", "Onion 2kg", "Tomato 1kg"]}\n'
        "  ],\n"
        '  "total_allocated": 2800,\n'
        '  "savings_tips": ["Buy seasonal vegetables", "Use store brands for staples"],\n'
        '  "ai_summary": "Brief smart summary of the plan"\n'
        "}\n"
        "Do not include markdown code block backticks, just raw JSON."
    )

    user_prompt = f"Plan request: {prompt}\nTotal Budget: ₹{total_budget}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw_text, err = call_openrouter(messages, temperature=0.6, max_tokens=1024)
    if not raw_text:
        return None, err

    try:
        clean_text = raw_text
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0]
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0]
        clean_text = clean_text.strip()
        return json.loads(clean_text), None
    except Exception as e:
        logger.info(f"Could not parse json from Gemma plan response: {e}")
        return {"raw_text": raw_text, "plan_title": "AI Shopping Plan"}, None


def get_gemma_spending_insights(spending_data=None):
    """
    Ask Gemma 4 to analyze spending patterns and generate personalized insights.
    """
    if not is_ai_configured():
        return None, "API key not configured"

    spending_context = ""
    if spending_data:
        spending_context = f"Spending data: {json.dumps(spending_data)}"

    system_prompt = (
        "You are SmartCart AI Spending Analyst powered by Google Gemma 4. "
        "Analyze the user's grocery spending patterns and provide 4-5 actionable insights. "
        "Each insight should have a type, icon emoji, category label, badge color, and helpful message.\n"
        "Respond in valid JSON format:\n"
        "{\n"
        '  "insights": [\n'
        '    {"type": "trend", "message": "Your spending increased 12%...", "icon": "📈", "category": "Spending Trend", "badge_color": "warning"},\n'
        '    {"type": "saving", "message": "Switch cooking oil brand to save ₹20...", "icon": "💡", "category": "Savings Tip", "badge_color": "success"}\n'
        "  ],\n"
        '  "ai_summary": "Brief overall spending health summary"\n'
        "}\n"
        "Badge colors must be one of: primary, success, warning, info, danger.\n"
        "Do not include markdown code block backticks, just raw JSON."
    )

    user_prompt = (
        "Analyze my recent grocery spending and give me personalized insights.\n"
        f"{spending_context}\n"
        "Focus on: spending trends, savings opportunities, price alerts, and shopping habits."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw_text, err = call_openrouter(messages, temperature=0.7, max_tokens=800)
    if not raw_text:
        return None, err

    try:
        clean_text = raw_text
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0]
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0]
        clean_text = clean_text.strip()
        return json.loads(clean_text), None
    except Exception:
        return None, "Failed to parse insights json"


def get_gemma_recommendations(purchase_history=None, catalog_sample=None):
    """
    Ask Gemma 4 to generate smart shopping recommendations based on purchase history.
    """
    if not is_ai_configured():
        return None, "API key not configured"

    history_context = ""
    if purchase_history:
        history_context = f"Recent purchases: {', '.join(purchase_history[:20])}"
    catalog_context = ""
    if catalog_sample:
        catalog_context = f"Available catalog items: {', '.join(catalog_sample[:30])}"

    system_prompt = (
        "You are SmartCart AI Smart Recommender powered by Google Gemma 4. "
        "Based on the user's purchase history and available catalog, generate 3-5 smart "
        "shopping recommendations including restock reminders, brand alternatives, and deal alerts.\n"
        "Respond in valid JSON format:\n"
        "{\n"
        '  "recommendations": [\n'
        '    {"type": "frequency", "title": "Restock Reminder", "message": "You usually buy Atta every 30 days...", "icon": "🔄", "badge_color": "primary"},\n'
        '    {"type": "brand_switch", "title": "Brand Alternative", "message": "Save ₹20 by switching to...", "icon": "💸", "badge_color": "success"}\n'
        "  ],\n"
        '  "ai_summary": "Brief recommendation summary"\n'
        "}\n"
        "Badge colors must be one of: primary, success, warning, info, danger.\n"
        "Do not include markdown code block backticks, just raw JSON."
    )

    user_prompt = (
        "Generate smart shopping recommendations for me.\n"
        f"{history_context}\n"
        f"{catalog_context}\n"
        "Include: restock reminders, cheaper brand alternatives, store deal alerts, and seasonal suggestions."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw_text, err = call_openrouter(messages, temperature=0.7, max_tokens=800)
    if not raw_text:
        return None, err

    try:
        clean_text = raw_text
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0]
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0]
        clean_text = clean_text.strip()
        return json.loads(clean_text), None
    except Exception:
        return None, "Failed to parse recommendations json"


def get_gemma_spending_analytics(categories=None, total_spending=0, monthly_budget=0):
    """
    Ask Gemma 4 to analyze spending analytics and provide a summary with tips.
    """
    if not is_ai_configured():
        return None, "API key not configured"

    cat_context = ""
    if categories:
        cat_context = f"Category breakdown: {json.dumps(categories)}"

    system_prompt = (
        "You are SmartCart AI Financial Analyst powered by Google Gemma 4. "
        "Analyze the user's monthly grocery spending analytics and give a helpful AI summary "
        "with 3-4 actionable tips to optimize spending.\n"
        "Respond in valid JSON format:\n"
        "{\n"
        '  "ai_summary": "Your spending analysis summary...",\n'
        '  "health_score": 72,\n'
        '  "tips": [\n'
        '    "Reduce snack spending by 15% to save ₹140/month",\n'
        '    "Buy vegetables from local vendors to save 20%"\n'
        "  ],\n"
        '  "predicted_monthly": 9200\n'
        "}\n"
        "Do not include markdown code block backticks, just raw JSON."
    )

    user_prompt = (
        f"Monthly Budget: ₹{monthly_budget}\n"
        f"Total Spending so far: ₹{total_spending}\n"
        f"{cat_context}\n"
        "Give me a spending health analysis with tips."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw_text, err = call_openrouter(messages, temperature=0.5, max_tokens=600)
    if not raw_text:
        return None, err

    try:
        clean_text = raw_text
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0]
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0]
        clean_text = clean_text.strip()
        return json.loads(clean_text), None
    except Exception:
        return None, "Failed to parse analytics json"
