from decimal import Decimal
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import CustomerProfile, User

class CustomerRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True, label="Full Name")
    phone = forms.CharField(max_length=20, required=True, label="Phone Number")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True, label="Delivery Address")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'full_name', 'phone', 'address']

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise forms.ValidationError("Username is required.")
        # Check case-insensitive existence
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with this username already exists. Please choose a different username.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise forms.ValidationError("Email address is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists. Please sign in or use a different email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CUSTOMER
        name_parts = self.cleaned_data['full_name'].strip().split(maxsplit=1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        user.phone = self.cleaned_data['phone'].strip()
        user.address = self.cleaned_data['address'].strip()
        user.email = self.cleaned_data['email'].strip()
        
        if commit:
            with transaction.atomic():
                user.save()
                CustomerProfile.objects.get_or_create(customer=user)
                from cart.models import ShoppingCart
                from budget.models import Budget
                
                ShoppingCart.objects.get_or_create(customer=user)
                Budget.objects.get_or_create(customer=user, defaults={'amount': Decimal('2000.00')})
        return user



class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = [
            'city', 'state', 'pincode', 'preferred_area', 'preferred_store',
            'budget_alert_threshold', 'budget_alerts', 'shopping_reminders',
            'offers_notifications', 'price_change_notifications', 'ai_recommendations',
        ]

    def clean_budget_alert_threshold(self):
        threshold = self.cleaned_data['budget_alert_threshold']
        if threshold not in (70, 80, 90, 100):
            raise forms.ValidationError('Choose a threshold of 70%, 80%, 90%, or 100%.')
        return threshold