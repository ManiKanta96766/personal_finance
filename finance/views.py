from django.shortcuts import render, redirect, get_object_or_404
from .models import Transaction, Budget
from .forms import TransactionForm, BudgetForm, SignUpForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout  # Import the logout function
from django.db.models import Sum
from django.contrib import messages

from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings
from django.utils.safestring import mark_safe
import json

# Signup View
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

# Logout View
def user_logout(request):
    logout(request)  # Log the user out
    return redirect('login')  # Redirect to login page after logging out

# Dashboard View
@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)
    income = transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    savings = income - expenses

    budgets = Budget.objects.filter(user=request.user)
    total_budget = sum(budget.amount for budget in budgets)

    return render(request, 'finance/dashboard.html', {
        'income': income,
        'expenses': expenses,
        'savings': savings,
        'transactions': transactions,
        'total_budget': total_budget,
    })

# Add Transaction View
@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, "Transaction added successfully!")
            return redirect('dashboard')
    else:
        form = TransactionForm()
    return render(request, 'finance/add_transaction.html', {'form': form})

# Edit Transaction View
@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    form = TransactionForm(request.POST or None, instance=transaction)
    if form.is_valid():
        form.save()
        messages.success(request, "Transaction updated successfully!")
        return redirect('dashboard')
    return render(request, 'finance/edit_transaction.html', {'form': form})

# Delete Transaction View
@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, "Transaction deleted successfully!")
        return redirect('dashboard')
    return render(request, 'finance/delete_transaction.html', {'transaction': transaction})

# Manage Budget View
@login_required
def manage_budget(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        amount = request.POST.get('limit')  # Budget limit input by the user
        
        # Assuming you're also sending month and year in the form
        month = request.POST.get('month')  # Month to be included in the budget
        year = request.POST.get('year')    # Year to be included in the budget
        
        user = request.user  # Current logged-in user
        
        # Check if a budget for the same category, month, and year exists for the user, then update it, else create a new one
        budget, created = Budget.objects.update_or_create(
            user=user,
            category=category,
            month=month,
            year=year,
            defaults={'amount': amount}
        )
        
        # Check if the budget limit is exceeded
        if budget.amount > amount:
            send_budget_overrun_email(user, budget)
        
        messages.success(request, "Budget updated successfully!")
        return redirect('manage_budget')  # Redirect to the same page to see the updated budget
    
    budgets = Budget.objects.filter(user=request.user)  # Only show budgets for the logged-in user
    return render(request, 'finance/manage_budget.html', {'budgets': budgets})

def send_budget_overrun_email(user, budget):
    subject = f"Budget Overrun Alert for {budget.category} in {budget.month}/{budget.year}"
    message = f"""
    Dear {user.username},
    
    You have exceeded your budget for {budget.category} in {budget.month}/{budget.year}.
    
    Your set budget was ₹{budget.amount}, but your spending has exceeded the limit. Please review your spending.
    
    Best regards,
    Personal Finance Tracker Team
    """
    recipient_email = user.email  # Send the email to the logged-in user's email address
    
    # Send email (using settings for email configuration)
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,  # Sender's email (from settings)
        [recipient_email],  # Recipient's email (user's email)
        fail_silently=False,
    )

# Report View
@login_required
def report(request):
    today = datetime.now()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    transactions = Transaction.objects.filter(
        user=request.user,
        date__month=month,
        date__year=year
    )

    income = transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = income - expenses

    category_data = transactions.filter(transaction_type='expense').values('category').annotate(total=Sum('amount')).order_by('-total')

    # Budget tracking per category
    budgets = Budget.objects.filter(user=request.user, month=month, year=year)
    budget_dict = {b.category: b.amount for b in budgets}

    # Combine budget info with category totals
    category_summary = []
    for item in category_data:
        category = item['category']
        spent = float(item['total'])
        budget = float(budget_dict.get(category, 0))
        percentage = (spent / budget * 100) if budget > 0 else 0
        category_summary.append({
            'category': category,
            'spent': spent,
            'budget': budget,
            'percentage': round(percentage, 1)
        })

    labels = [item['category'] for item in category_data]
    totals = [float(item['total']) for item in category_data]
    labels_json = mark_safe(json.dumps(labels))
    totals_json = mark_safe(json.dumps(totals))

    return render(request, 'finance/report.html', {
        'income': income,
        'expenses': expenses,
        'balance': balance,
        'transactions': transactions,
        'category_data': category_data,
        'category_summary': category_summary,
        'labels_json': labels_json,
        'totals_json': totals_json,
        'month': month,
        'year': year,
    })
