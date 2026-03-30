import uuid
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import DoctorRegistrationForm, DoctorProfileForm
from .models import Doctor, Medicament
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.files import File
from django.conf import settings # Pour accéder aux paramètres comme le chemin wkhtmltopdf
from django.db.models import Q # Pour la recherche
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from bs4 import BeautifulSoup
import json
import os
import tempfile
from io import BytesIO

# Importations pour le PDF minimal (Reportlab)
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas

# Importation du modèle de l'application
from .models import Medicament, Prescription, PrescriptionMedicament, Doctor, Appointment, DoctorSchedule
from .forms import AppointmentForm

# Importer pdfkit si vous l'utilisez pour la conversion HTML -> PDF
import pdfkit

def home(request):
    if request.user.is_authenticated:
        try:
            doctor = request.user.doctor
            return render(request, 'chatbot.html')
        except Doctor.DoesNotExist:
            return redirect('register')
    return render(request, 'login.html')

def register(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'doctor'):
            return redirect('search_medicament')
        # Complete profile for authenticated user
        if request.method == 'POST':
            form = DoctorProfileForm(request.POST)
            if form.is_valid():
                doctor = form.save(commit=False)
                doctor.user = request.user
                doctor.save()
                return redirect('search_medicament')
            else:
                messages.error(request, 'Please correct the errors.')
        else:
            form = DoctorProfileForm()
        return render(request, 'register.html', {'form': form, 'completing': True})
    else:
        # Full registration for new users
        if request.method == 'POST':
            form = DoctorRegistrationForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(request, 'Registration successful!')
                return redirect('search_medicament')
            else:
                messages.error(request, 'Registration failed. Please correct the errors.')
        else:
            form = DoctorRegistrationForm()
        return render(request, 'register.html', {'form': form, 'completing': False})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('search_medicament')
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('search_medicament')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def complete_profile(request):
    if request.user.is_authenticated:
        # If already authenticated, complete profile
        if request.method == 'POST':
            address = request.POST.get('address')
            phone_number = request.POST.get('phone_number')
            specialite = request.POST.get('specialite')
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            if address and phone_number and specialite and nom and prenom:
                Doctor.objects.create(
                    user=request.user,
                    nom=nom,
                    prenom=prenom,
                    address=address,
                    phone_number=phone_number,
                    specialite=specialite
                )
                return redirect('search_medicament')
            else:
                messages.error(request, 'All fields are required.')
        return render(request, 'complete_profile.html')
    else:
        # New user registration
        if request.method == 'POST':
            email = request.POST.get('email')
            password = request.POST.get('password')
            address = request.POST.get('address')
            phone_number = request.POST.get('phone_number')
            specialite = request.POST.get('specialite')
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            if email and password and address and phone_number and specialite and nom and prenom:
                if User.objects.filter(username=email).exists():
                    messages.error(request, 'Email already exists.')
                elif User.objects.filter(email=email).exists():
                    messages.error(request, 'Email already exists.')
                elif len(password) < 8:
                    messages.error(request, 'Password must be at least 8 characters.')
                else:
                    user = User.objects.create_user(username=email, email=email, password=password)
                    Doctor.objects.create(
                        user=user,
                        nom=nom,
                        prenom=prenom,
                        address=address,
                        phone_number=phone_number,
                        specialite=specialite
                    )
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.success(request, 'Account created successfully!')
                    return redirect('search_medicament')
            else:
                messages.error(request, 'All fields are required.')
        return render(request, 'complete_profile.html')



def recherche_view(request):
    query = request.GET.get('q')
    medicaments = []
    if query:
        # Recherche par dénomination ou nom de marque
        medicaments = Medicament.objects.filter(
            nom_de_marque__icontains=query
        ) | Medicament.objects.filter(
            denomination__icontains=query
        )

    # Get doctor data
    doctor = None
    if request.user.is_authenticated:
        try:
            doctor = request.user.doctor
        except Doctor.DoesNotExist:
            doctor = None

    # Check if it's an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Return JSON for AJAX requests
        medicaments_list = list(medicaments.values('code', 'nom_de_marque', 'denomination', 'dosage'))
        return JsonResponse({'medicaments': medicaments_list})
    else:
        # Render HTML for regular requests
        return render(request, 'chatbot.html', {'medicaments': medicaments, 'query': query, 'doctor': doctor})


def add_medicament(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        nom_de_marque = data.get('nom_de_marque')
        denomination = data.get('denomination')
        dosage = data.get('dosage')
        forme = data.get('forme')
        cond = data.get('cond', '')

        if not all([nom_de_marque, denomination, dosage, forme]):
            return JsonResponse({'success': False, 'error': 'Tous les champs requis doivent être remplis.'})

        # Generate unique code
        code = str(uuid.uuid4())[:10].upper()

        try:
            medicament = Medicament.objects.create(
                code=code,
                denomination=denomination,
                forme=forme,
                dosage=dosage,
                cond=cond,
                nom_de_marque=nom_de_marque
            )
            return JsonResponse({
                'success': True,
                'medicament': {
                    'code': medicament.code,
                    'nom_de_marque': medicament.nom_de_marque,
                    'denomination': medicament.denomination,
                    'dosage': medicament.dosage,
                    'forme': medicament.forme
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


def list_prescriptions(request):
    query = request.GET.get('q')
    prescriptions = Prescription.objects.all().order_by('-date_creation')
    print(f"DEBUG: Total prescriptions in DB: {prescriptions.count()}")
    for p in prescriptions:
        print(f"DEBUG: Prescription ID {p.id}: {p.patient_nom} by {p.docteur_nom}")
        if p.pdf_file:
            print(f"DEBUG: PDF file name: {p.pdf_file.name}")
            print(f"DEBUG: PDF file path: {p.pdf_file.path}")
            print(f"DEBUG: PDF file url: {p.pdf_file.url}")
            print(f"DEBUG: PDF file exists: {os.path.exists(p.pdf_file.path)} at {p.pdf_file.path}")
        else:
            print(f"DEBUG: No PDF file for prescription {p.id}")
    if query:
        prescriptions = prescriptions.filter(patient_nom__icontains=query) | prescriptions.filter(docteur_nom__icontains=query)
        print(f"DEBUG: Prescriptions after query '{query}': {prescriptions.count()}")
    return render(request, 'list_prescriptions.html', {'prescriptions': prescriptions, 'query': query})


def save_and_print_prescription(request):
    if request.method == 'POST':
        try:
            print("DEBUG: Starting save_and_print_prescription")
            print(f"DEBUG: request.POST keys: {list(request.POST.keys())}")
            patient_nom = request.POST.get('patient_nom')
            print(f"DEBUG: patient_nom={patient_nom}")
            patient_age_str = request.POST.get('patient_age')
            print(f"DEBUG: patient_age_str={patient_age_str}")
            patient_age = int(patient_age_str) if patient_age_str else 0
            patient_date = timezone.now().date()  # Use current date if not provided
            docteur_nom = request.POST.get('docteur_nom')
            docteur_specialite = request.POST.get('docteur_specialite')
            docteur_adresse = request.POST.get('docteur_adresse')
            medicaments_json = request.POST.get('medicaments', '[]')
            print(f"DEBUG: medicaments_json={medicaments_json}")
            medicaments_data = json.loads(medicaments_json)
            print(f"DEBUG: Extracted data: patient_nom={patient_nom}, medicaments={len(medicaments_data)}")

            prescription = Prescription.objects.create(
                patient_nom=patient_nom,
                patient_age=patient_age,
                patient_date=patient_date,
                docteur_nom=docteur_nom,
                docteur_specialite=docteur_specialite,
                docteur_adresse=docteur_adresse,
            )

            for item in medicaments_data:
                medicament = Medicament.objects.filter(code=item['id']).first()
                if not medicament:
                    raise ValueError(f"Medicament with code {item['id']} not found")
                try:
                    PrescriptionMedicament.objects.create(
                        prescription=prescription,
                        medicament=medicament,
                        quantite=item['quantite'],
                        forme=item['forme'],
                        instructions=item.get('instructions', ''),
                        frequence=item.get('frequence', ''),
                        unite_frequence=item.get('unite_frequence', ''),
                    )
                except IntegrityError:
                    # Skip if duplicate
                    pass

            # Créer le PDF à partir du HTML
            html_content = request.POST.get('html_content')
            print(f"DEBUG: html_content length: {len(html_content) if html_content else 0}")
            if html_content:
                print(f"DEBUG: html_content preview: {html_content[:200]}")
            else:
                print("DEBUG: html_content is EMPTY!")
            
            # Nettoyer le HTML pour supprimer définitivement les boutons d'impression et d'action
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Supprimer le formulaire d'impression et le bouton "Imprimer la Prescription"
            print_form = soup.find('form', {'id': 'printForm'})
            if print_form:
                print_form.decompose()
            
            # Supprimer la colonne "Action" du tableau
            action_headers = soup.find_all(['th', 'td'], class_='print-hide')
            for element in action_headers:
                element.decompose()
            
            # Supprimer les boutons "Supprimer" des lignes de médicaments
            delete_buttons = soup.find_all('button', class_='delete-medicine-btn')
            for button in delete_buttons:
                button.decompose()

            # Remove all class attributes to avoid Tailwind issues in PDF
            for tag in soup.find_all():
                if 'class' in tag.attrs:
                    del tag.attrs['class']

            # Convertir le HTML nettoyé en chaîne
            cleaned_html = str(soup)
            print(f"DEBUG: cleaned_html length: {len(cleaned_html)}")
            print(f"DEBUG: cleaned_html preview: {cleaned_html[:200]}")

            # Wrap in full HTML with basic CSS for better PDF rendering
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Prescription</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .layout-content-container {{ width: 100%; }}
                    .flex {{ display: block; }}
                    .flex-col {{ display: block; }}
                    .gap-3 {{ margin-bottom: 12px; }}
                    .w-full {{ width: 100%; }}
                    .p-4 {{ padding: 16px; }}
                    .text-[#0e161b] {{ color: #0e161b; }}
                    .tracking-light {{ letter-spacing: 0.5px; }}
                    .text-[32px] {{ font-size: 32px; }}
                    .font-bold {{ font-weight: bold; }}
                    .leading-tight {{ line-height: 1.25; }}
                    .text-base {{ font-size: 16px; }}
                    .text-sm {{ font-size: 14px; }}
                    .text-gray-600 {{ color: #666; }}
                    .mt-2 {{ margin-top: 8px; }}
                    .border-b {{ border-bottom: 1px solid #ccc; padding-bottom: 8px; }}
                    .p-2 {{ padding: 8px; }}
                    .bg-white {{ background-color: white; }}
                    .rounded-lg {{ border-radius: 8px; }}
                    .shadow {{ box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                </style>
            </head>
            <body>
                {cleaned_html}
            </body>
            </html>
            """
            print(f"DEBUG: full_html preview: {full_html[:500]}")

            options = {
                'page-size': 'A5',
                'orientation': 'Portrait',
                'encoding': 'UTF-8',
                'print-media-type': None,
                'title': 'Prescription',
            }
            
            pdf_bytes = pdfkit.from_string(full_html, False, options=options)
            print(f"DEBUG: PDF bytes length: {len(pdf_bytes)}")
            buffer = BytesIO(pdf_bytes)
            
            # Sauvegarder le PDF dans un fichier temporaire
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(buffer.getvalue())
                temp_file_path = temp_file.name

            # Joindre le fichier PDF au modèle
            from django.core.files import File
            with open(temp_file_path, 'rb') as f:
                print(f"DEBUG: About to save PDF file for prescription {prescription.id}")
                prescription.pdf_file.save(f'prescription_{prescription.id}.pdf', File(f), save=True)
                print(f"DEBUG: PDF saved. File name: {prescription.pdf_file.name}")
                print(f"DEBUG: PDF path: {prescription.pdf_file.path}")
                print(f"DEBUG: PDF url: {prescription.pdf_file.url}")

            # Supprimer le fichier temporaire
            os.remove(temp_file_path)

            return JsonResponse({'success': True, 'prescription_id': prescription.id, 'pdf_url': prescription.pdf_file.url})

        except Exception as e:
            print(f"ERROR: PDF generation failed: {str(e)}")
            return JsonResponse({'error': f'PDF generation failed: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def delete_prescription(request, pk):
    if request.method == 'POST':
        try:
            prescription = Prescription.objects.get(pk=pk)
            # Delete associated PDF file if it exists
            if prescription.pdf_file:
                if os.path.exists(prescription.pdf_file.path):
                    os.remove(prescription.pdf_file.path)
            prescription.delete()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('list_prescriptions')
        except Prescription.DoesNotExist:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Prescription not found'}, status=404)
            return redirect('list_prescriptions')
    return redirect('list_prescriptions')

def appointment_view(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            # Check if the slot is available
            doctor = form.cleaned_data['doctor']
            date = form.cleaned_data['appointment_date']
            time = form.cleaned_data['appointment_time']
            if Appointment.objects.filter(doctor=doctor, appointment_date=date, appointment_time=time).exists():
                messages.error(request, 'This time slot is already booked.')
            else:
                form.save()
                messages.success(request, 'Appointment booked successfully!')
                return redirect('appointment')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AppointmentForm()
    return render(request, 'appointment.html', {'form': form})

def doctor_appointments_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        doctor = request.user.doctor
        if request.method == 'POST':
            user_name = request.POST.get('user_name')
            user_email = request.POST.get('user_email')
            user_phone = request.POST.get('user_phone')
            appointment_date = request.POST.get('appointment_date')
            appointment_time = request.POST.get('appointment_time')
            appointment_type = request.POST.get('appointment_type', 'Visite')
            status = request.POST.get('status', 'booked')
            if user_name and user_email and user_phone and appointment_date and appointment_time:
                Appointment.objects.create(
                    doctor=doctor,
                    user_name=user_name,
                    user_email=user_email,
                    user_phone=user_phone,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    appointment_type=appointment_type,
                    status=status
                )
                messages.success(request, 'Appointment added successfully!')
                return redirect('doctor_appointments')
            else:
                messages.error(request, 'All fields are required.')
        appointments = Appointment.objects.filter(doctor=doctor).order_by('appointment_date', 'appointment_time')
        appointments_list = list(appointments.values('user_name', 'user_email', 'user_phone', 'appointment_date', 'appointment_time', 'status', 'appointment_type'))
        for app in appointments_list:
            app['appointment_date'] = str(app['appointment_date'])
            app['appointment_time'] = str(app['appointment_time'])
        appointments_json = json.dumps(appointments_list)
        return render(request, 'doctor_appointments.html', {'appointments': appointments, 'appointments_json': appointments_json, 'doctor_id': doctor.id})
    except Doctor.DoesNotExist:
        return redirect('home')

@csrf_exempt
def get_available_slots(request):
    if request.method == 'GET':
        doctor_id = request.GET.get('doctor_id')
        date_str = request.GET.get('date')
        if not doctor_id or not date_str:
            return JsonResponse({'error': 'Doctor ID and date are required'}, status=400)
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            day_of_week = date.strftime('%A')
            schedules = DoctorSchedule.objects.filter(doctor=doctor, day_of_week=day_of_week)
            slots = []
            for schedule in schedules:
                start = schedule.start_time
                end = schedule.end_time
                duration = schedule.slot_duration
                current = start
                while current < end:
                    slots.append(current.strftime('%H:%M'))
                    current = (timezone.datetime.combine(date, current) + timezone.timedelta(minutes=duration)).time()
            # Remove booked slots
            booked = Appointment.objects.filter(doctor=doctor, appointment_date=date).values_list('appointment_time', flat=True)
            booked_times = [t.strftime('%H:%M') for t in booked]
            available_slots = [slot for slot in slots if slot not in booked_times]
            # If no available slots, provide default demo slots
            if not available_slots:
                available_slots = ['09:00', '10:00', '11:00', '13:00', '14:00', '15:00']
            return JsonResponse({'slots': available_slots})
        except Doctor.DoesNotExist:
            return JsonResponse({'error': 'Doctor not found'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)
