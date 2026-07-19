"""
Accounts Forms — Registration, Profile update, Address, Login.
"""
import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import Profile, Address

# ─── Country and City Data ───────────────────────────────────────────────────
COUNTRY_DATA = {
    'United States': {
        'New York': 'New York',
        'Los Angeles': 'California',
        'Chicago': 'Illinois',
        'Houston': 'Texas',
        'Phoenix': 'Arizona',
        'Philadelphia': 'Pennsylvania',
        'San Antonio': 'Texas',
        'San Diego': 'California',
        'Dallas': 'Texas',
        'San Jose': 'California'
    },
    'Pakistan': {
        'Karachi': 'Sindh',
        'Lahore': 'Punjab',
        'Faisalabad': 'Punjab',
        'Rawalpindi': 'Punjab',
        'Gujranwala': 'Punjab',
        'Peshawar': 'Khyber Pakhtunkhwa',
        'Multan': 'Punjab',
        'Islamabad': 'Islamabad Capital Territory',
        'Hyderabad': 'Sindh',
        'Quetta': 'Balochistan'
    },
    'United Kingdom': {
        'London': 'England',
        'Birmingham': 'England',
        'Glasgow': 'Scotland',
        'Liverpool': 'England',
        'Bristol': 'England',
        'Manchester': 'England',
        'Sheffield': 'England',
        'Leeds': 'England',
        'Edinburgh': 'Scotland',
        'Leicester': 'England'
    },
    'Canada': {
        'Toronto': 'Ontario',
        'Montreal': 'Quebec',
        'Vancouver': 'British Columbia',
        'Calgary': 'Alberta',
        'Edmonton': 'Alberta',
        'Ottawa': 'Ontario',
        'Winnipeg': 'Manitoba',
        'Quebec City': 'Quebec',
        'Hamilton': 'Ontario',
        'Kitchener': 'Ontario'
    },
    'United Arab Emirates': {
        'Dubai': 'Dubai',
        'Abu Dhabi': 'Abu Dhabi',
        'Sharjah': 'Sharjah',
        'Al Ain': 'Abu Dhabi',
        'Ajman': 'Ajman',
        'Ras Al Khaimah': 'Ras Al Khaimah',
        'Fujairah': 'Fujairah',
        'Umm Al Quwain': 'Umm Al Quwain'
    }
}

# ─── Reusable Validators ─────────────────────────────────────────────────────
def validate_alphabetic(value):
    if not re.match(r'^[a-zA-Z\s\-]+$', value):
        raise ValidationError('Only alphabetic characters, spaces, and hyphens are allowed.')

def validate_numeric(value):
    if not re.match(r'^[0-9]+$', value):
        raise ValidationError('Only numeric digits are allowed.')

# ─── Forms ───────────────────────────────────────────────────────────────────

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Username or Email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Password',
        })
    )


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50,
        validators=[validate_alphabetic],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'data-type': 'alphabet',
            'pattern': '[A-Za-z\\s\\-]+',
            'title': 'Only alphabets, spaces, and hyphens are allowed.'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        validators=[validate_alphabetic],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'data-type': 'alphabet',
            'pattern': '[A-Za-z\\s\\-]+',
            'title': 'Only alphabets, spaces, and hyphens are allowed.'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password (min 8 chars)'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email.lower()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        validators=[validate_alphabetic],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'data-type': 'alphabet',
            'pattern': '[A-Za-z\\s\\-]+',
            'title': 'Only alphabets, spaces, and hyphens are allowed.'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        validators=[validate_alphabetic],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'data-type': 'alphabet',
            'pattern': '[A-Za-z\\s\\-]+',
            'title': 'Only alphabets, spaces, and hyphens are allowed.'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        validators=[validate_numeric],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'data-type': 'number',
            'pattern': '[0-9]+',
            'title': 'Only numeric digits are allowed.'
        })
    )

    class Meta:
        model = Profile
        fields = ('phone_number', 'bio', 'avatar')
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile.save()
        return profile


class AddressForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=150,
        validators=[validate_alphabetic],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name',
            'data-type': 'alphabet',
            'pattern': '[A-Za-z\\s\\-]+',
            'title': 'Only alphabets, spaces, and hyphens are allowed.'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[validate_numeric],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number',
            'data-type': 'number',
            'pattern': '[0-9]+',
            'title': 'Only numeric digits are allowed.'
        })
    )
    postal_code = forms.CharField(
        max_length=20,
        validators=[validate_numeric],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal Code',
            'data-type': 'number',
            'pattern': '[0-9]+',
            'title': 'Only numeric digits are allowed.'
        })
    )
    country = forms.ChoiceField(
        choices=[('', 'Select Country')] + [(c, c) for c in COUNTRY_DATA.keys()],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_country'})
    )
    city = forms.ChoiceField(
        choices=[('', 'Select City')],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_city'})
    )
    state = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_state',
            'readonly': 'readonly',
            'placeholder': 'State/Province (Auto-filled)'
        })
    )

    class Meta:
        model = Address
        fields = (
            'full_name', 'address_type', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country', 'phone', 'is_default'
        )
        widgets = {
            'address_type': forms.Select(attrs={'class': 'form-select'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate dynamic city choices based on instance or post data so validation passes
        country_value = None
        if self.is_bound:
            country_value = self.data.get('country')
        elif self.instance and self.instance.pk:
            country_value = self.instance.country

        if country_value in COUNTRY_DATA:
            self.fields['city'].choices = [('', 'Select City')] + [(c, c) for c in COUNTRY_DATA[country_value].keys()]
        else:
            self.fields['city'].choices = [('', 'Select City')]

    def clean(self):
        cleaned_data = super().clean()
        country = cleaned_data.get('country')
        city = cleaned_data.get('city')
        
        # Validate that selected city matches the country to prevent raw HTTP manipulation
        if country in COUNTRY_DATA:
            cities = COUNTRY_DATA[country]
            if city not in cities:
                self.add_error('city', 'Selected city is not valid for the chosen country.')
            else:
                cleaned_data['state'] = cities[city]
        else:
            self.add_error('country', 'Please select a valid country.')
            
        return cleaned_data


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
