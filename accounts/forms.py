from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError


class RegisterForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'first_name',
            'placeholder': 'First name (e.g. John)',
            'class': 'w-full pl-9 pr-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
            'autocomplete': 'given-name',
        }),
        error_messages={
            'required': 'Please enter your first name.',
        }
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'last_name',
            'placeholder': 'Last name (e.g. Cena',
            'class': 'w-full pl-9 pr-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
            'autocomplete': 'family-name',
        }),
        error_messages={
            'required': 'Please enter your last name.',
        }
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'username',
            'placeholder': 'Choose a unique username',
            'class': 'w-full pl-9 pr-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
            'autocomplete': 'username',
        }),
        error_messages={
            'required': 'Please choose a username.',
        }
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'id': 'email',
            'placeholder': 'name@example.com',
            'class': 'w-full pl-9 pr-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
            'autocomplete': 'email',
        }),
        error_messages={
            'required': 'Please enter a valid email address.',
            'invalid': 'Please enter a valid email address.',
        }
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'id': 'password',
            'placeholder': 'Create password (min 8 characters)',
            'class': 'w-full pl-9 pr-10 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
            'autocomplete': 'new-password',
        }),
        error_messages={
            'required': 'Please enter a password.',
        }
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'id': 'confirm_password',
            'placeholder': 'Confirm your password',
            'class': 'w-full pl-9 pr-10 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
            'autocomplete': 'new-password',
        }),
        error_messages={
            'required': 'Please confirm your password.',
        }
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError("Please choose a username.")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise ValidationError("Please enter a valid email address.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
            else:
                # Validate password with Django's password validation framework
                temp_user = User(
                    username=cleaned_data.get('username', ''),
                    first_name=cleaned_data.get('first_name', ''),
                    last_name=cleaned_data.get('last_name', ''),
                    email=cleaned_data.get('email', '')
                )
                try:
                    password_validation.validate_password(password, temp_user)
                except ValidationError as error:
                    self.add_error('password', error)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name'].strip()
        user.last_name = self.cleaned_data['last_name'].strip()
        user.username = self.cleaned_data['username'].strip()
        user.email = self.cleaned_data['email'].strip().lower()
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'username',
            'placeholder': 'Enter your username or email',
            'class': 'w-full pl-9 pr-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
            'autocomplete': 'username',
        }),
        error_messages={
            'required': 'Please enter your username or email address.',
        }
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'id': 'password',
            'placeholder': '••••••••',
            'class': 'w-full pl-9 pr-10 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
            'autocomplete': 'current-password',
        }),
        error_messages={
            'required': 'Please enter your password.',
        }
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'id': 'remember-me',
            'class': 'w-4 h-4 text-primary rounded border-slate-300 focus:ring-primary/20 cursor-pointer',
        })
    )
