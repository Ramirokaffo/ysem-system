from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from .models import Agent, Campagne, Equipe, Prospect
from academic.models import AcademicYear
from schools.models import School


class ProspectionModelsTest(TestCase):
    """Tests pour les modèles de prospection"""
    
    def setUp(self):
        """Configuration des données de test"""
        # Créer une année académique
        self.academic_year = AcademicYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 8, 31),
            is_active=True
        )
        
        # Créer une école
        self.school = School.objects.create(
            name="Lycée Test",
            address="123 Rue Test",
            phone_number="123456789"
        )
        
        # Créer des agents
        self.agent1 = Agent.objects.create(
            matricule="AGT001",
            nom="Dupont",
            prenom="Jean",
            telephone="123456789",
            type_agent="interne",
            date_embauche=date(2024, 1, 1)
        )
        
        self.agent2 = Agent.objects.create(
            matricule="AGT002",
            nom="Martin",
            prenom="Marie",
            telephone="987654321",
            type_agent="externe",
            date_embauche=date(2024, 2, 1)
        )
        
        # Créer une campagne
        self.campagne = Campagne.objects.create(
            nom="Campagne Test 2024",
            annee_academique=self.academic_year,
            date_debut=date(2024, 6, 1),
            date_fin=date(2024, 8, 31),
            objectif_global=1000
        )
        
        # Créer une équipe
        self.equipe = Equipe.objects.create(
            nom="Équipe Alpha",
            campagne=self.campagne,
            chef_equipe=self.agent1,
            etablissement_cible=self.school,
            objectif_prospects=50
        )
        self.equipe.agents.add(self.agent1, self.agent2)
    
    def test_agent_creation(self):
        """Test de création d'un agent"""
        self.assertEqual(self.agent1.nom_complet, "Dupont Jean")
        self.assertEqual(self.agent1.statut, "actif")
        self.assertTrue(str(self.agent1).startswith("AGT001"))
    
    def test_campagne_properties(self):
        """Test des propriétés de la campagne"""
        self.assertEqual(self.campagne.duree_jours, 92)  # 1er juin au 31 août
        self.assertFalse(self.campagne.is_active)  # Dates passées
    
    def test_equipe_properties(self):
        """Test des propriétés de l'équipe"""
        self.assertEqual(self.equipe.nombre_agents, 2)
        self.assertEqual(self.equipe.prospects_collectes, 0)
        self.assertEqual(self.equipe.taux_realisation, 0)
    
    def test_prospect_creation(self):
        """Test de création d'un prospect"""
        prospect = Prospect.objects.create(
            nom="Doe",
            prenom="John",
            telephone="555123456",
            equipe=self.equipe,
            agent_collecteur=self.agent1
        )
        
        self.assertEqual(prospect.nom_complet, "Doe John")
        self.assertEqual(self.equipe.prospects_collectes, 1)
        self.assertEqual(self.equipe.taux_realisation, 2.0)  # 1/50 * 100
