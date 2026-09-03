from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def login_view(request):
    """
    Login view - handles user authentication with Django sessions
    
    GET: Shows the login form
    POST: Processes the login form
    """
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('ops:dashboard')
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user against the database
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login successful - create session
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to dashboard (or next page if specified)
            next_url = request.GET.get('next', 'ops:dashboard')
            return redirect(next_url)
        else:
            # Login failed
            messages.error(request, 'Invalid username or password.')
    
    # Handle GET request (show login form)
    return render(request, 'ops/login.html')


def logout_view(request):
    """
    Logout view - ends user session and redirects to login
    
    This view logs out the user, clears the session, and redirects to login page
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('ops:login')


@login_required
def dashboard_view(request):
    """
    Dashboard view - shows overview of the system
    
    This view is protected by @login_required decorator
    Only authenticated users can access this page
    """
    # Get user information
    user = request.user
    
    # For now, we'll use mock data
    # Later, we'll fetch real data from the database
    context = {
        'user': user,
        'stats': {
            'active_jobs': 12,
            'subcontractors': 28,
            'invoices': 45,
            'revenue': 124500,
        }
    }
    
    return render(request, 'ops/dashboard.html', context)
