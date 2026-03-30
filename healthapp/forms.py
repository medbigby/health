from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Doctor, Appointment

class DoctorRegistrationForm(UserCreationForm):
    nom = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}))
    prenom = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}))
    address = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}))
    phone_number = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}))
    specialite = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}))

    class Meta:
        model = User
        fields = ('username', 'nom', 'prenom', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'password1': forms.PasswordInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'password2': forms.PasswordInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            doctor = Doctor.objects.create(
                user=user,
                nom=self.cleaned_data['nom'],
                prenom=self.cleaned_data['prenom'],
                address=self.cleaned_data['address'],
                phone_number=self.cleaned_data['phone_number'],
                specialite=self.cleaned_data['specialite']
            )
        return user

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['nom', 'prenom', 'address', 'phone_number', 'specialite']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'prenom': forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'address': forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'phone_number': forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'specialite': forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
        }

class AppointmentForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(queryset=Doctor.objects.all(), empty_label="Sélectionnez un Médecin", widget=forms.Select(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}))
    appointment_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}))
    appointment_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}))
    appointment_type = forms.ChoiceField(choices=[('Visite', 'Visite'), ('MAPA', 'MAPA')], widget=forms.RadioSelect(attrs={'class': 'mr-4'}))

    class Meta:
        model = Appointment
        fields = ['doctor', 'user_name', 'user_email', 'user_phone', 'appointment_date', 'appointment_time', 'appointment_type']
        widgets = {
            'user_name': forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'user_email': forms.EmailInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'user_phone': forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
        }