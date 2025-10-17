from __future__ import annotations

from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from allauth.account.forms import SignupForm as AllauthSignupForm

from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "role")


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ("email", "first_name", "last_name", "role", "is_active", "is_staff")


class SignupForm(AllauthSignupForm):
    role = forms.ChoiceField(choices=User.Role.choices, initial=User.Role.BUYER)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    def save(self, request):
        user = super().save(request)
        user.role = self.cleaned_data["role"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.save()
        return user
