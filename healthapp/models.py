from django.db import models
from django.contrib.auth.models import User

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100, blank=True)
    prenom = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    specialite = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.specialite}"

class DoctorSchedule(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=10)  # e.g., 'Monday'
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.IntegerField()  # in minutes

    def __str__(self):
        return f"{self.doctor} - {self.day_of_week}"

class Appointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=100)
    user_email = models.EmailField()
    user_phone = models.CharField(max_length=20)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    appointment_type = models.CharField(max_length=50, default='Visite')
    status = models.CharField(max_length=20, default='booked')

    def __str__(self):
        return f"{self.user_name} with {self.doctor} on {self.appointment_date} at {self.appointment_time}"


class Medicament(models.Model):
    code = models.CharField(max_length=20)
    denomination = models.CharField(max_length=255)
    forme = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50)
    cond = models.CharField(max_length=50)
    nom_de_marque = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nom_de_marque} ({self.denomination})"

# Définition du modèle Prescription
class Prescription(models.Model):
    patient_nom = models.CharField(max_length=255)
    patient_age = models.IntegerField()
    patient_date = models.DateField()
    docteur_nom = models.CharField(max_length=255)
    docteur_specialite = models.CharField(max_length=100)
    docteur_adresse = models.TextField()
    medicaments = models.ManyToManyField(Medicament, through='PrescriptionMedicament')
    date_creation = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='prescriptions/')

    def __str__(self):
        return f"Prescription pour {self.patient_nom} du {self.date_creation}"

# Définition du modèle de liaison pour la relation ManyToMany entre Prescription et Medicament
class PrescriptionMedicament(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    quantite = models.IntegerField()
    forme = models.CharField(max_length=50)
    instructions = models.TextField(blank=True)
    frequence = models.CharField(max_length=100, blank=True, null=True)
    unite_frequence = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        unique_together = ('prescription', 'medicament')