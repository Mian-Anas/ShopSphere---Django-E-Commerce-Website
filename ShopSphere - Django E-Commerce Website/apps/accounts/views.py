"""
Accounts Views — Login, Register, Logout, Profile, Password, Addresses.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .forms import (
    CustomLoginForm, RegistrationForm, ProfileUpdateForm,
    AddressForm, CustomPasswordChangeForm
)
from .models import Profile, Address


def login_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    form = CustomLoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Welcome back, {user.first_name or user.username}!')
        next_url = request.GET.get('next', 'store:home')
        return redirect(next_url)
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Welcome to ShopSphere! Your account has been created.')
        return redirect('store:home')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('store:home')
    return render(request, 'accounts/logout_confirm.html')


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileUpdateForm(
        request.POST or None,
        request.FILES or None,
        instance=profile
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')
    context = {
        'form': form,
        'profile': profile,
        'orders': request.user.orders.order_by('-created_at')[:5],
        'addresses': request.user.addresses.all(),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def change_password_view(request):
    form = CustomPasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed successfully.')
        return redirect('accounts:profile')
    return render(request, 'accounts/password_change.html', {'form': form})


@login_required
def address_list_view(request):
    addresses = request.user.addresses.all()
    return render(request, 'accounts/addresses.html', {'addresses': addresses})


@login_required
def address_add_view(request):
    form = AddressForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        address.save()
        messages.success(request, 'Address added successfully.')
        next_url = request.GET.get('next', 'accounts:addresses')
        return redirect(next_url)
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add Address'})


@login_required
def address_edit_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    form = AddressForm(request.POST or None, instance=address)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Address updated successfully.')
        return redirect('accounts:addresses')
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Edit Address', 'address': address})


@login_required
@require_http_methods(['POST'])
def address_delete_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.success(request, 'Address removed.')
    return redirect('accounts:addresses')


@login_required
def order_history_view(request):
    orders = request.user.orders.prefetch_related('items').order_by('-created_at')
    return render(request, 'accounts/orders.html', {'orders': orders})


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/email/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')
    extra_context = {'title': 'Reset Password'}


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
