from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib import messages


def login(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'index'
            return redirect(next_url)
        else:
            form = AuthenticationForm(data=request.POST)
            form.is_valid()
            return render(request, 'login.html', {'form': form})

    return render(request, 'login.html')


def logout(request):
    auth_logout(request)
    messages.success(request, 'Você saiu com sucesso.')
    return redirect('login')


@login_required
def index(request):
    return render(request, 'index.html')