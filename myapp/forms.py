from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm

ROLE_CHOICES = (
    ('student', 'Student'),
    ('teacher', 'Teacher'),
)


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input'}),
        help_text='We\'ll never share your email with anyone else.'
    )
    full_name = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-input'}),
        help_text='How you want your name to appear to others.'
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial='student',
        widget=forms.Select(attrs={'class': 'form-input'}),
        help_text='Choose your role in the system.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-input'})
        self.fields['password1'].widget.attrs.update({'class': 'form-input'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input'})
        
        # Custom error messages
        self.fields['username'].error_messages.update({
            'unique': 'This username is already taken. Please choose another one.',
            'invalid': 'Username can only contain letters, numbers, and @/./+/-/_ characters.'
        })
        self.fields['password2'].error_messages.update({
            'password_mismatch': 'The two password fields didn\'t match. Please try again.'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use. Please use a different email.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # assign group
            role = self.cleaned_data.get('role')
            if role:
                grp, _ = Group.objects.get_or_create(name=role.capitalize())
                user.groups.add(grp)
            # save profile full_name if provided
            full_name = self.cleaned_data.get('full_name')
            if full_name:
                try:
                    user.profile.full_name = full_name
                    user.profile.save()
                except Exception:
                    pass
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class ProfileExtendedForm(forms.ModelForm):
    class Meta:
        from .models import Profile
        model = Profile
        fields = ('full_name', 'phone', 'bio')
