from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import Agent, SeanceProspection, Equipe




class AgentSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Agent
    """
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = Agent
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'telephone', 'email',
            'type_agent', 'statut', 'date_embauche', 'adresse',
            'password', 'last_login', 'is_active', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'last_login': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            'matricule': {'read_only': True},
        }
    
    def create(self, validated_data):
        """Créer un nouvel agent avec mot de passe hashé"""
        password = validated_data.pop('password')
        agent = Agent(**validated_data)
        agent.set_password(password)
        agent.save()
        return agent
    
    def update(self, instance, validated_data):
        """Mettre à jour un agent"""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class AgentRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription d'un nouvel agent
    """
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = Agent
        fields = [
            'nom', 'prenom', 'telephone', 'email', 'type_agent',
            'date_embauche', 'adresse', 'password', 'password_confirm'
        ]
    
    def validate(self, data):
        """Validation des données d'inscription"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        
        # Vérifier si l'email existe déjà
        if Agent.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Un agent avec cet email existe déjà.")
        
        return data
    
    def create(self, validated_data):
        """Créer un nouvel agent en attente d'activation"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        agent = Agent(**validated_data)
        agent.statut = 'pending'  # Compte en attente d'activation
        agent.is_active = False
        agent.set_password(password)
        agent.save()
        
        return agent


class AgentLoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion d'un agent
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        """Validation des données de connexion"""
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Email et mot de passe requis.")
        
        try:
            agent = Agent.objects.get(email=email)
        except Agent.DoesNotExist:
            raise serializers.ValidationError("Identifiants invalides.")
        
        if not agent.check_password(password):
            raise serializers.ValidationError("Identifiants invalides.")
        
        if not agent.is_active:
            if agent.statut == 'pending':
                raise serializers.ValidationError(
                    "Votre compte n'est pas encore activé. Veuillez contacter un administrateur."
                )
            elif agent.statut == 'suspendu':
                raise serializers.ValidationError("Votre compte a été suspendu.")
            else:
                raise serializers.ValidationError("Votre compte est inactif.")
        
        # Mettre à jour la dernière connexion
        agent.last_login = timezone.now()
        agent.save(update_fields=['last_login'])
        
        data['agent'] = agent
        return data


class AgentProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil de l'agent (lecture seule principalement)
    """
    nom_complet = serializers.ReadOnlyField()
    
    class Meta:
        model = Agent
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'nom_complet', 'telephone', 
            'email', 'type_agent', 'statut', 'date_embauche', 'adresse',
            'last_login', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'matricule', 'statut', 'is_active', 'last_login', 
            'created_at', 'updated_at'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer pour changer le mot de passe d'un agent
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, data):
        """Validation du changement de mot de passe"""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
        
        return data
    
    def validate_old_password(self, value):
        """Vérifier l'ancien mot de passe"""
        agent = self.context['request'].user
        if not agent.check_password(value):
            raise serializers.ValidationError("Ancien mot de passe incorrect.")
        return value


class SeanceProspectionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les séances de prospection
    """
    nom = serializers.ReadOnlyField()
    nombre_equipes = serializers.ReadOnlyField()
    nombre_agents_total = serializers.ReadOnlyField()
    est_active = serializers.ReadOnlyField()
    peut_etre_modifiee = serializers.ReadOnlyField()
    campagne_nom = serializers.CharField(source='campagne.nom', read_only=True)

    class Meta:
        model = SeanceProspection
        fields = [
            'id', 'nom', 'date_seance', 'statut', 'campagne', 'campagne_nom',
            'created_by', 'created_at', 'updated_at', 'nombre_equipes',
            'nombre_agents_total', 'est_active', 'peut_etre_modifiee'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'nom']


class EquipeSerializer(serializers.ModelSerializer):
    """
    Serializer pour les équipes (adapté pour séances et campagnes)
    """
    chef_equipe_nom = serializers.CharField(source='chef_equipe.nom_complet', read_only=True)
    seance_nom = serializers.CharField(source='seance.nom', read_only=True)
    campagne_nom = serializers.CharField(source='campagne.nom', read_only=True)
    campagne_id = serializers.IntegerField(source='campagne.id', read_only=True)
    nombre_agents = serializers.ReadOnlyField()
    agents_actifs_count = serializers.SerializerMethodField()
    agents = serializers.SerializerMethodField()

    class Meta:
        model = Equipe
        fields = [
            'id', 'nom', 'seance', 'seance_nom', 'campagne_id', 'campagne_nom',
            'chef_equipe', 'chef_equipe_nom', 'zone_assignee', 'objectif_equipe',
            'created_at', 'updated_at', 'nombre_agents', 'agents_actifs_count', 'agents'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_agents_actifs_count(self, obj):
        """Retourne le nombre d'agents actifs dans l'équipe"""
        return obj.agents_actifs.count()

    def get_agents(self, obj):
        """Retourne la liste des agents de l'équipe"""
        agents_data = []
        for agent in obj.agents.all():
            agents_data.append({
                'id': agent.id,
                'matricule': agent.matricule,
                'nom_complet': agent.nom_complet,
                'email': agent.email,
                'telephone': agent.telephone,
                'type_agent': agent.type_agent,
                'statut': agent.statut,
                'is_active': agent.is_active,
                'est_chef': agent.id == obj.chef_equipe.id if obj.chef_equipe else False
            })
        return agents_data

    def validate(self, data):
        """Validation des données d'équipe"""
        chef_equipe = data.get('chef_equipe')
        if chef_equipe and not chef_equipe.is_active:
            raise serializers.ValidationError("Le chef d'équipe doit être un agent actif.")

        # Vérifier qu'une séance est définie
        seance = data.get('seance')
        if not seance:
            raise serializers.ValidationError("Une équipe doit être liée à une séance.")

        return data


class EquipeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer une équipe avec ses membres
    """
    agents_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="Liste des IDs des agents à ajouter à l'équipe"
    )

    class Meta:
        model = Equipe
        fields = [
            'nom', 'seance', 'campagne', 'chef_equipe', 'zone_assignee',
            'objectif_equipe', 'agents_ids'
        ]

    def validate_agents_ids(self, value):
        """Valider que tous les agents existent et sont actifs"""
        if value:
            agents = Agent.objects.filter(id__in=value)
            if agents.count() != len(value):
                raise serializers.ValidationError("Certains agents n'existent pas.")

            agents_inactifs = agents.filter(is_active=False)
            if agents_inactifs.exists():
                noms = [agent.nom_complet for agent in agents_inactifs]
                raise serializers.ValidationError(
                    f"Les agents suivants ne sont pas actifs: {', '.join(noms)}"
                )
        return value

    def create(self, validated_data):
        """Créer l'équipe et ajouter les membres"""
        agents_ids = validated_data.pop('agents_ids', [])
        equipe = Equipe.objects.create(**validated_data)

        # Ajouter les agents via la relation ManyToMany
        if agents_ids:
            agents = Agent.objects.filter(id__in=agents_ids, is_active=True)
            equipe.agents.set(agents)

        return equipe


class AjouterMembreSerializer(serializers.Serializer):
    """
    Serializer pour ajouter un membre à une équipe
    """
    agent_id = serializers.IntegerField()

    def validate_agent_id(self, value):
        """Valider que l'agent existe et est actif"""
        try:
            agent = Agent.objects.get(id=value)
            if not agent.is_active:
                raise serializers.ValidationError("L'agent n'est pas actif.")
            return value
        except Agent.DoesNotExist:
            raise serializers.ValidationError("Agent non trouvé.")


class ReconduireEquipeSerializer(serializers.Serializer):
    """
    Serializer pour reconduire une équipe précédente
    """
    equipe_precedente_id = serializers.IntegerField()
    nouvelle_seance_id = serializers.IntegerField()
    nouveau_nom = serializers.CharField(max_length=100, required=False)

    def validate_equipe_precedente_id(self, value):
        """Valider que l'équipe précédente existe"""
        try:
            Equipe.objects.get(id=value)
            return value
        except Equipe.DoesNotExist:
            raise serializers.ValidationError("Équipe précédente non trouvée.")

    def validate_nouvelle_seance_id(self, value):
        """Valider que la nouvelle séance existe et peut être modifiée"""
        try:
            seance = SeanceProspection.objects.get(id=value)
            if not seance.peut_etre_modifiee:
                raise serializers.ValidationError("La séance ne peut plus être modifiée.")
            return value
        except SeanceProspection.DoesNotExist:
            raise serializers.ValidationError("Séance non trouvée.")


class ActivationAgentSerializer(serializers.Serializer):
    """
    Serializer pour activer/désactiver un agent
    """
    agent_id = serializers.IntegerField()
    activer = serializers.BooleanField(default=True)
    motif = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_agent_id(self, value):
        """Valider que l'agent existe"""
        try:
            Agent.objects.get(id=value)
            return value
        except Agent.DoesNotExist:
            raise serializers.ValidationError("Agent non trouvé.")


class AgentListSerializer(serializers.ModelSerializer):
    """
    Serializer pour lister les agents (pour les responsables)
    """
    nom_complet = serializers.ReadOnlyField()

    class Meta:
        model = Agent
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'nom_complet', 'email',
            'telephone', 'type_agent', 'statut', 'is_active', 'date_embauche',
            'last_login', 'created_at'
        ]
        read_only_fields = ['matricule', 'created_at']
