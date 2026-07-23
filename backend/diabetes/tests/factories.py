"""
Test Factories for Django Models.
Provides easy creation of model instances for unit testing.
"""

# import factory
# from diabetes.models import PatientProfile, DiabetesLog

# class PatientProfileFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = PatientProfile
#
#     user_id = factory.Sequence(lambda n: f"user_{n}")
#     target_min = 70
#     target_max = 140
#     diabetes_type = "TYPE_1"

# class DiabetesLogFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = DiabetesLog
#
#     profile = factory.SubFactory(PatientProfileFactory)
#     blood_sugar = 110
