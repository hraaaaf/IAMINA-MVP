"""
Management command to set up demo data for local development.

Usage:
    python manage.py setup_demo          # Creates everything
    python manage.py setup_demo --reset  # Wipes and recreates
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import BasePatientProfile
from diabetes.models import AISummary, DiabetesProfile, LogEntry

MEALS = {
    'fasting': {
        'hour_range': (6, 8),
        'bs_range': (85, 155),
        'insulin': (4, 6),
        'desc': '',
    },
    'breakfast': {
        'hour_range': (8, 10),
        'bs_range': (120, 180),
        'insulin': (6, 10),
        'desc': [
            'Pain, fromage, café',
            'Oeufs, pain complet, thé',
            'Crêpes, miel, lait',
            'Yaourt, fruits, céréales',
            'Msemen, beurre, thé',
        ],
    },
    'lunch': {
        'hour_range': (12, 14),
        'bs_range': (130, 195),
        'insulin': (8, 12),
        'desc': [
            'Couscous, légumes',
            'Tajine poulet, pain',
            'Riz, poisson, salade',
            'Pâtes, sauce tomate',
            'Salade composée, pain complet',
            'Lentilles, riz, légumes',
        ],
    },
    'snack': {
        'hour_range': (15, 17),
        'bs_range': (100, 145),
        'insulin': None,
        'desc': [
            'Fruits, amandes',
            'Yaourt',
            'Biscuits, thé',
            'Pomme',
            'Dattes, lait',
        ],
    },
    'dinner': {
        'hour_range': (19, 21),
        'bs_range': (110, 185),
        'insulin': (6, 10),
        'desc': [
            'Soupe de lentilles, pain',
            'Harira, dattes',
            'Légumes grillés, fromage',
            'Salade, poulet',
            'Soupe, pain',
        ],
    },
}


class Command(BaseCommand):
    help = 'Crée les données de démo (admin, patient1/Amina, 3 semaines d\'entrées)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprimer les données existantes avant de recréer',
        )

    def handle(self, *args, **options):
        reset = options['reset']

        # --- Admin ---
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@test.com', 'is_staff': True, 'is_superuser': True},
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Admin créé : admin / admin123'))
        else:
            self.stdout.write('Admin existe déjà')

        # --- Patient1 (Amina) ---
        patient, created = User.objects.get_or_create(
            username='patient1',
            defaults={'first_name': 'Amina', 'last_name': 'B.'},
        )
        if created:
            patient.set_password('test1234')
            patient.save()
            self.stdout.write(self.style.SUCCESS('Patient créé : patient1 / test1234'))
        else:
            self.stdout.write('Patient1 existe déjà')

        if reset:
            BasePatientProfile.objects.filter(patient=patient).delete()
            LogEntry.objects.filter(patient=patient).delete()
            AISummary.objects.filter(patient=patient).delete()
            self.stdout.write(self.style.WARNING('Données de patient1 supprimées'))

        # --- Profile (two-step: BasePatientProfile first, then DiabetesProfile) ---
        base, base_created = BasePatientProfile.objects.get_or_create(
            patient=patient,
            defaults={
                'gender': 'female',
                'date_of_birth': '1985-03-15',
                'weight': Decimal('68.0'),
                'height': 165,
            },
        )
        profile, created = DiabetesProfile.objects.get_or_create(
            base_profile=base,
            defaults={
                'diabetes_type': 'type2',
                'treatment_type': 'oral_meds',
                'target_range_low': 70,
                'target_range_high': 180,
                'unit_preference': 'mg_dl',
            },
        )
        if created or base_created:
            self.stdout.write(self.style.SUCCESS('Profil créé pour patient1'))
        else:
            self.stdout.write('Profil existe déjà')

        # --- Log entries (3 weeks) ---
        existing = LogEntry.objects.filter(patient=patient).count()
        if existing > 0 and not reset:
            self.stdout.write(f'{existing} entrées existent déjà (utilisez --reset pour recréer)')
            return

        now = timezone.now()
        random.seed(42)
        entries_created = 0

        for days_ago in range(20, -1, -1):
            day = now - timedelta(days=days_ago)

            # 10% chance of skipping a day
            if random.random() < 0.1:
                continue

            day_meals = ['fasting']
            if random.random() < 0.7:
                day_meals.append('breakfast')
            day_meals.append('lunch')
            if random.random() < 0.35:
                day_meals.append('snack')
            if random.random() < 0.75:
                day_meals.append('dinner')

            # Trend: week 1 higher, week 3 better
            week = days_ago // 7
            trend_offset = {2: 15, 1: 5, 0: -10}.get(week, 0)

            exercised = 'yes' if random.random() < (0.3 + (0.15 * (2 - week))) else 'no'
            sleep = 'good' if random.random() < (0.5 + (0.1 * (2 - week))) else 'bad'
            stressed = 'yes' if random.random() < (0.5 - (0.1 * (2 - week))) else 'no'
            fatigue = 'tired' if random.random() < (0.4 - (0.1 * (2 - week))) else 'ok'
            sick = 'yes' if random.random() < 0.08 else 'no'

            for meal_type in day_meals:
                m = MEALS[meal_type]
                hour = random.randint(*m['hour_range'])
                minute = random.randint(0, 59)

                bs_low, bs_high = m['bs_range']
                bs = random.randint(bs_low + trend_offset, bs_high + trend_offset)
                bs = max(55, min(350, bs))

                if m['insulin']:
                    insulin = random.choice(
                        range(m['insulin'][0] * 2, m['insulin'][1] * 2 + 1)
                    ) / 2
                else:
                    insulin = None

                desc = random.choice(m['desc']) if isinstance(m['desc'], list) else m['desc']

                entry_time = day.replace(hour=hour, minute=minute, second=0, microsecond=0)

                LogEntry.objects.create(
                    patient=patient,
                    blood_sugar=Decimal(str(bs)),
                    meal_type=meal_type,
                    exercised=exercised,
                    sleep_quality=sleep,
                    stressed=stressed,
                    fatigue_level=fatigue,
                    is_sick=sick,
                    insulin_units=Decimal(str(insulin)) if insulin else None,
                    meal_description=desc,
                    logged_at=entry_time,
                )
                entries_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'{entries_created} entrées créées sur ~21 jours'
        ))
        self.stdout.write(self.style.SUCCESS(
            '\nPrêt ! Lancez : python manage.py runserver 8000'
        ))
        self.stdout.write('  -> Admin  : admin / admin123')
        self.stdout.write('  -> Patient : patient1 / test1234')
