import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from healthapp.models import Medicament


class Command(BaseCommand):
    help = 'Import medicament data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default=r'C:\Users\Revotec\Desktop\clean\medicament_nettoye.csv',
            help='Path to the CSV file (default: C:\\Users\\Revotec\\Desktop\\clean\\medicament_nettoye.csv)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            default=True,
            help='Clear existing data before import (default: True)'
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        clear_existing = options['clear_existing']

        # Check if CSV file exists
        if not os.path.exists(csv_path):
            raise CommandError(f'CSV file not found: {csv_path}')

        self.stdout.write(f'Starting import from: {csv_path}')

        try:
            with transaction.atomic():
                # Clear existing data if requested
                if clear_existing:
                    existing_count = Medicament.objects.count()
                    Medicament.objects.all().delete()
                    self.stdout.write(
                        self.style.WARNING(f'Cleared {existing_count} existing medicament records')
                    )

                # Read and import CSV data
                imported_count = 0
                skipped_count = 0
                medicaments_to_create = []

                with open(csv_path, 'r', encoding='utf-8') as csvfile:
                    # Detect delimiter and read CSV
                    sample = csvfile.read(1024)
                    csvfile.seek(0)
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample).delimiter
                    
                    reader = csv.DictReader(csvfile, delimiter=delimiter)
                    
                    # Verify CSV headers match our model fields
                    expected_headers = ['CODE', 'DENOMINATION', 'FORME', 'DOSAGE', 'COND', 'NOM_DE_MARQUE']
                    if not all(header in reader.fieldnames for header in expected_headers):
                        raise CommandError(f'CSV headers do not match expected format. Expected: {expected_headers}, Found: {reader.fieldnames}')

                    self.stdout.write(f'CSV headers verified: {reader.fieldnames}')

                    for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
                        try:
                            # Clean and validate data
                            code = row['CODE'].strip() if row['CODE'] else ''
                            denomination = row['DENOMINATION'].strip() if row['DENOMINATION'] else ''
                            forme = row['FORME'].strip() if row['FORME'] else ''
                            dosage = row['DOSAGE'].strip() if row['DOSAGE'] else ''
                            cond = row['COND'].strip() if row['COND'] else ''
                            nom_de_marque = row['NOM_DE_MARQUE'].strip() if row['NOM_DE_MARQUE'] else ''

                            # Skip rows with missing critical data
                            if not code or not denomination or not nom_de_marque:
                                self.stdout.write(
                                    self.style.WARNING(f'Skipping row {row_num}: Missing critical data (code, denomination, or nom_de_marque)')
                                )
                                skipped_count += 1
                                continue

                            # Truncate fields to model max_length if necessary
                            code = code[:20]  # max_length=20
                            denomination = denomination[:255]  # max_length=255
                            forme = forme[:100]  # max_length=100
                            dosage = dosage[:50]  # max_length=50
                            cond = cond[:50]  # max_length=50
                            nom_de_marque = nom_de_marque[:255]  # max_length=255

                            # Create medicament object
                            medicament = Medicament(
                                code=code,
                                denomination=denomination,
                                forme=forme,
                                dosage=dosage,
                                cond=cond,
                                nom_de_marque=nom_de_marque
                            )
                            medicaments_to_create.append(medicament)
                            imported_count += 1

                            # Bulk create every 1000 records for efficiency
                            if len(medicaments_to_create) >= 1000:
                                Medicament.objects.bulk_create(medicaments_to_create)
                                self.stdout.write(f'Imported {imported_count} records so far...')
                                medicaments_to_create = []

                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f'Error processing row {row_num}: {str(e)}')
                            )
                            skipped_count += 1
                            continue

                    # Create remaining medicaments
                    if medicaments_to_create:
                        Medicament.objects.bulk_create(medicaments_to_create)

                # Final statistics
                total_records = Medicament.objects.count()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Import completed successfully!\n'
                        f'Records imported: {imported_count}\n'
                        f'Records skipped: {skipped_count}\n'
                        f'Total records in database: {total_records}'
                    )
                )

                # Test search functionality
                self.stdout.write('\nTesting search functionality:')
                
                # Test search for common medication names
                test_queries = ['PARACETAMOL', 'DOLIPRANE', 'ASPEGIC', 'CETIRIZINE']
                for query in test_queries:
                    results = Medicament.objects.filter(
                        nom_de_marque__icontains=query
                    ) | Medicament.objects.filter(
                        denomination__icontains=query
                    )
                    count = results.count()
                    if count > 0:
                        self.stdout.write(f'  Search "{query}": {count} results found')
                        # Show first few results
                        for med in results[:3]:
                            self.stdout.write(f'    - {med.nom_de_marque} ({med.denomination})')
                        if count > 3:
                            self.stdout.write(f'    ... and {count - 3} more')
                    else:
                        self.stdout.write(f'  Search "{query}": No results found')

        except Exception as e:
            raise CommandError(f'Import failed: {str(e)}')