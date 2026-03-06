from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from .models import Agent, SeanceProspection, Equipe
from .authentication import AgentJWTAuthentication
from .serializers import (
    AgentRegistrationSerializer,
    AgentLoginSerializer,
    AgentProfileSerializer,
    ChangePasswordSerializer,
    SeanceProspectionSerializer,
    EquipeSerializer,
    EquipeCreateSerializer,
    AjouterMembreSerializer,
    ReconduireEquipeSerializer,
    ActivationAgentSerializer,
    AgentListSerializer
)


class AgentRegistrationView(APIView):
    """
    Vue pour l'inscription d'un nouvel agent
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = AgentRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            agent = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Inscription réussie. Votre compte sera activé par un administrateur.',
                'agent': {
                    'id': agent.id,
                    'matricule': agent.matricule,
                    'nom_complet': agent.nom_complet,
                    'email': agent.email,
                    'statut': agent.statut
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Erreur lors de l\'inscription',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AgentLoginView(APIView):
    """
    Vue pour la connexion d'un agent
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = AgentLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            agent = serializer.validated_data['agent']
            
            # Générer les tokens JWT
            refresh = RefreshToken()
            refresh['agent_id'] = agent.id
            refresh['email'] = agent.email
            refresh['matricule'] = agent.matricule
            
            return Response({
                'success': True,
                'message': 'Connexion réussie',
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                },
                'agent': {
                    'id': agent.id,
                    'matricule': agent.matricule,
                    'nom_complet': agent.nom_complet,
                    'email': agent.email,
                    'telephone': agent.telephone,
                    'type_agent': agent.type_agent,
                    'statut': agent.statut,
                    'last_login': agent.last_login
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': serializer.errors.get('non_field_errors', ['Erreur de connexion'])[0],
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AgentProfileView(APIView):
    """
    Vue pour récupérer et mettre à jour le profil de l'agent
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_agent_from_token(self, request):
        """Récupérer l'agent à partir du token JWT"""
        try:
            # Si l'utilisateur est déjà authentifié via notre système personnalisé
            if hasattr(request.user, 'agent'):
                return request.user.agent

            # Sinon, essayer de récupérer l'agent_id du token
            token = request.auth
            if hasattr(token, 'payload'):
                agent_id = token.payload.get('agent_id')
                if agent_id:
                    return Agent.objects.get(id=agent_id, is_active=True)
            return None
        except (Agent.DoesNotExist, AttributeError):
            return None
    
    def get(self, request):
        """Récupérer le profil de l'agent connecté"""
        agent = self.get_agent_from_token(request)
        
        if not agent:
            return Response({
                'success': False,
                'message': 'Agent non trouvé ou token invalide'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = AgentProfileSerializer(agent)
        return Response({
            'success': True,
            'agent': serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        """Mettre à jour le profil de l'agent"""
        agent = self.get_agent_from_token(request)
        
        if not agent:
            return Response({
                'success': False,
                'message': 'Agent non trouvé ou token invalide'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = AgentProfileSerializer(agent, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profil mis à jour avec succès',
                'agent': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Erreur lors de la mise à jour',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Vue pour changer le mot de passe de l'agent
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_agent_from_token(self, request):
        """Récupérer l'agent à partir du token JWT"""
        try:
            # Si l'utilisateur est déjà authentifié via notre système personnalisé
            if hasattr(request.user, 'agent'):
                return request.user.agent

            # Sinon, essayer de récupérer l'agent_id du token
            token = request.auth
            if hasattr(token, 'payload'):
                agent_id = token.payload.get('agent_id')
                if agent_id:
                    return Agent.objects.get(id=agent_id, is_active=True)
            return None
        except (Agent.DoesNotExist, AttributeError):
            return None
    
    def post(self, request):
        agent = self.get_agent_from_token(request)
        
        if not agent:
            return Response({
                'success': False,
                'message': 'Agent non trouvé ou token invalide'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Ajouter l'agent au contexte pour la validation
        request.user = agent
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Changer le mot de passe
            agent.set_password(serializer.validated_data['new_password'])
            agent.save()
            
            return Response({
                'success': True,
                'message': 'Mot de passe changé avec succès'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Erreur lors du changement de mot de passe',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def validate_token(request):
    """
    Vue pour valider un token JWT et récupérer les informations de l'agent
    """
    try:
        # Récupérer le token depuis l'en-tête Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({
                'success': False,
                'valid': False,
                'message': 'Token manquant'
            }, status=status.HTTP_401_UNAUTHORIZED)

        token_string = auth_header.split(' ')[1]

        # Utiliser notre authentification personnalisée
        auth = AgentJWTAuthentication()
        try:
            validated_token = auth.get_validated_token(token_string)
            user = auth.get_user(validated_token)

            if user and hasattr(user, 'agent'):
                agent = user.agent
                return Response({
                    'success': True,
                    'valid': True,
                    'agent': {
                        'id': agent.id,
                        'matricule': agent.matricule,
                        'nom_complet': agent.nom_complet,
                        'email': agent.email,
                        'statut': agent.statut
                    }
                }, status=status.HTTP_200_OK)
        except Exception:
            pass

        return Response({
            'success': False,
            'valid': False,
            'message': 'Token invalide'
        }, status=status.HTTP_401_UNAUTHORIZED)

    except Exception:
        return Response({
            'success': False,
            'valid': False,
            'message': 'Erreur de validation du token'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_agent(request):
    """
    Vue pour déconnecter un agent (blacklister le token)
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'success': True,
            'message': 'Déconnexion réussie'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': True,  # Même en cas d'erreur, on considère la déconnexion comme réussie
            'message': 'Déconnexion effectuée'
        }, status=status.HTTP_200_OK)


# ===== VUES POUR LES SÉANCES DE PROSPECTION =====

class SeanceProspectionListView(APIView):
    """
    Vue pour lister et créer les séances de prospection
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Lister toutes les séances"""
        seances = SeanceProspection.objects.all()
        serializer = SeanceProspectionSerializer(seances, many=True)
        return Response({
            'success': True,
            'seances': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """Créer automatiquement la séance du jour"""
        try:
            # Récupérer l'utilisateur créateur si possible
            created_by = None
            if hasattr(request.user, 'agent'):
                # Si c'est un agent, on ne peut pas l'assigner directement
                # car created_by attend un BaseUser
                pass

            # Récupérer la campagne depuis les données de la requête
            campagne_id = request.data.get('campagne_id')
            if not campagne_id:
                return Response({
                    'success': False,
                    'message': 'ID de campagne requis'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                from .models import Campagne
                campagne = Campagne.objects.get(id=campagne_id)
            except Campagne.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Campagne non trouvée'
                }, status=status.HTTP_404_NOT_FOUND)

            seance, created = SeanceProspection.creer_seance_aujourd_hui(
                campagne=campagne,
                created_by=created_by
            )

            if created:
                return Response({
                    'success': True,
                    'message': 'Séance du jour créée avec succès',
                    'seance': SeanceProspectionSerializer(seance).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': True,
                    'message': 'La séance du jour existe déjà',
                    'seance': SeanceProspectionSerializer(seance).data
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de la création: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class SeanceProspectionDetailView(APIView):
    """
    Vue pour récupérer, modifier ou supprimer une séance
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return SeanceProspection.objects.get(pk=pk)
        except SeanceProspection.DoesNotExist:
            return None

    def get(self, request, pk):
        """Récupérer une séance"""
        seance = self.get_object(pk)
        if not seance:
            return Response({
                'success': False,
                'message': 'Séance non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = SeanceProspectionSerializer(seance)
        return Response({
            'success': True,
            'seance': serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Modifier une séance"""
        seance = self.get_object(pk)
        if not seance:
            return Response({
                'success': False,
                'message': 'Séance non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)

        if not seance.peut_etre_modifiee:
            return Response({
                'success': False,
                'message': 'Cette séance ne peut plus être modifiée'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = SeanceProspectionSerializer(seance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Séance modifiée avec succès',
                'seance': serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Erreur lors de la modification',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Supprimer une séance"""
        seance = self.get_object(pk)
        if not seance:
            return Response({
                'success': False,
                'message': 'Séance non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)

        if not seance.peut_etre_modifiee:
            return Response({
                'success': False,
                'message': 'Cette séance ne peut plus être supprimée'
            }, status=status.HTTP_400_BAD_REQUEST)

        seance.delete()
        return Response({
            'success': True,
            'message': 'Séance supprimée avec succès'
        }, status=status.HTTP_200_OK)


# ===== VUES POUR LES ÉQUIPES DE PROSPECTION =====

class EquipeProspectionListView(APIView):
    """
    Vue pour lister et créer les équipes de prospection
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Lister toutes les équipes"""
        seance_id = request.query_params.get('seance_id')
        print(seance_id)
        if seance_id:
            equipes = Equipe.objects.filter(seance_id=seance_id)
        else:
            equipes = Equipe.objects.all()
        print(equipes)
        serializer = EquipeSerializer(equipes, many=True)
        return Response({
            'success': True,
            'equipes': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """Créer une nouvelle équipe"""
        serializer = EquipeCreateSerializer(data=request.data)
        if serializer.is_valid():
            equipe = serializer.save()
            return Response({
                'success': True,
                'message': 'Équipe créée avec succès',
                'equipe': EquipeSerializer(equipe).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'message': 'Erreur lors de la création',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EquipeProspectionDetailView(APIView):
    """
    Vue pour récupérer, modifier ou supprimer une équipe
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return Equipe.objects.get(pk=pk)
        except Equipe.DoesNotExist:
            return None

    def get(self, request, pk):
        """Récupérer une équipe"""
        equipe = self.get_object(pk)
        if not equipe:
            return Response({
                'success': False,
                'message': 'Équipe non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = EquipeSerializer(equipe)
        return Response({
            'success': True,
            'equipe': serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Modifier une équipe"""
        equipe = self.get_object(pk)
        if not equipe:
            return Response({
                'success': False,
                'message': 'Équipe non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)

        if not equipe.seance.peut_etre_modifiee:
            return Response({
                'success': False,
                'message': 'Cette équipe ne peut plus être modifiée'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = EquipeSerializer(equipe, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Équipe modifiée avec succès',
                'equipe': serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Erreur lors de la modification',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def ajouter_membre_equipe(request, equipe_id):
    """
    Ajouter un membre à une équipe
    """
    try:
        equipe = Equipe.objects.get(pk=equipe_id)
    except Equipe.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Équipe non trouvée'
        }, status=status.HTTP_404_NOT_FOUND)

    if equipe.seance and not equipe.seance.peut_etre_modifiee:
        return Response({
            'success': False,
            'message': 'Cette équipe ne peut plus être modifiée'
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = AjouterMembreSerializer(data=request.data)
    if serializer.is_valid():
        agent_id = serializer.validated_data['agent_id']

        try:
            agent = Agent.objects.get(id=agent_id)
            peut_ajouter, message = equipe.peut_ajouter_agent(agent)

            if not peut_ajouter:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)

            # Ajouter l'agent à l'équipe
            equipe.agents.add(agent)

            return Response({
                'success': True,
                'message': 'Membre ajouté avec succès',
                'agent': {
                    'id': agent.id,
                    'nom_complet': agent.nom_complet,
                    'matricule': agent.matricule,
                    'telephone': agent.telephone
                }
            }, status=status.HTTP_201_CREATED)

        except Agent.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Agent non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'success': False,
        'message': 'Données invalides',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def supprimer_membre_equipe(request, equipe_id, agent_id):
    """
    Supprimer un membre d'une équipe
    """
    try:
        equipe = Equipe.objects.get(pk=equipe_id)
        agent = Agent.objects.get(pk=agent_id)
    except Equipe.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Équipe non trouvée'
        }, status=status.HTTP_404_NOT_FOUND)
    except Agent.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Agent non trouvé'
        }, status=status.HTTP_404_NOT_FOUND)

    if equipe.seance and not equipe.seance.peut_etre_modifiee:
        return Response({
            'success': False,
            'message': 'Cette équipe ne peut plus être modifiée'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Vérifier que l'agent fait partie de l'équipe
    if agent not in equipe.agents.all():
        return Response({
            'success': False,
            'message': 'Cet agent ne fait pas partie de l\'équipe'
        }, status=status.HTTP_400_BAD_REQUEST)

    equipe.agents.remove(agent)
    return Response({
        'success': True,
        'message': 'Membre supprimé avec succès'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reconduire_equipe(request):
    """
    Reconduire une équipe précédente pour une nouvelle séance
    """
    serializer = ReconduireEquipeSerializer(data=request.data)
    if serializer.is_valid():
        equipe_precedente_id = serializer.validated_data['equipe_precedente_id']
        nouvelle_seance_id = serializer.validated_data['nouvelle_seance_id']
        nouveau_nom = serializer.validated_data.get('nouveau_nom')

        try:
            equipe_precedente = Equipe.objects.get(id=equipe_precedente_id)
            nouvelle_seance = SeanceProspection.objects.get(id=nouvelle_seance_id)

            # Créer la nouvelle équipe
            nouvelle_equipe = Equipe.objects.create(
                seance=nouvelle_seance,
                nom=nouveau_nom or f"{equipe_precedente.nom} (Reconduite)",
                chef_equipe=equipe_precedente.chef_equipe,
                zone_assignee=equipe_precedente.zone_assignee,
                objectif_equipe=equipe_precedente.objectif_equipe or equipe_precedente.objectif_prospects or 0
            )

            # Copier les agents actifs
            agents_actifs = equipe_precedente.agents.filter(is_active=True)
            nouvelle_equipe.agents.set(agents_actifs)
            membres_copies = agents_actifs.count()

            return Response({
                'success': True,
                'message': f'Équipe reconduite avec succès. {membres_copies} membres copiés.',
                'equipe': EquipeSerializer(nouvelle_equipe).data
            }, status=status.HTTP_201_CREATED)

        except Equipe.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Équipe précédente non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)
        except SeanceProspection.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Nouvelle séance non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'success': False,
        'message': 'Données invalides',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def agents_actifs(request):
    """
    Lister tous les agents actifs
    """
    agents = Agent.objects.filter(is_active=True)
    agents_data = []

    for agent in agents:
        agents_data.append({
            'id': agent.id,
            'matricule': agent.matricule,
            'nom_complet': agent.nom_complet,
            'email': agent.email,
            'telephone': agent.telephone,
            'type_agent': agent.type_agent
        })

    return Response({
        'success': True,
        'agents': agents_data
    }, status=status.HTTP_200_OK)


# ===== VUES POUR LA GESTION DES AGENTS (RESPONSABLES) =====

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def liste_agents_gestion(request):
    """
    Lister tous les agents pour la gestion (responsables de scolarité)
    """
    # TODO: Ajouter une vérification de permissions pour les responsables
    statut_filter = request.query_params.get('statut')

    agents = Agent.objects.all()
    if statut_filter:
        agents = agents.filter(statut=statut_filter)

    agents = agents.order_by('nom', 'prenom')
    serializer = AgentListSerializer(agents, many=True)

    return Response({
        'success': True,
        'agents': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def activer_agent(request):
    """
    Activer ou désactiver un agent
    """
    # TODO: Ajouter une vérification de permissions pour les responsables
    serializer = ActivationAgentSerializer(data=request.data)

    if serializer.is_valid():
        agent_id = serializer.validated_data['agent_id']
        activer = serializer.validated_data['activer']
        motif = serializer.validated_data.get('motif', '')

        try:
            agent = Agent.objects.get(id=agent_id)

            # Mettre à jour le statut
            if activer:
                agent.is_active = True
                agent.statut = 'actif'
                message = f'Agent {agent.nom_complet} activé avec succès'
            else:
                agent.is_active = False
                agent.statut = 'inactif'
                message = f'Agent {agent.nom_complet} désactivé avec succès'

            agent.save()

            # TODO: Envoyer une notification à l'agent par email

            return Response({
                'success': True,
                'message': message,
                'agent': AgentListSerializer(agent).data
            }, status=status.HTTP_200_OK)

        except Agent.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Agent non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'success': False,
        'message': 'Données invalides',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def statistiques_agents(request):
    """
    Statistiques sur les agents
    """
    # TODO: Ajouter une vérification de permissions pour les responsables

    total_agents = Agent.objects.count()
    agents_actifs = Agent.objects.filter(is_active=True).count()
    agents_pending = Agent.objects.filter(statut='pending').count()
    agents_inactifs = Agent.objects.filter(statut='inactif').count()
    agents_suspendus = Agent.objects.filter(statut='suspendu').count()

    # Agents par type
    agents_internes = Agent.objects.filter(type_agent='interne').count()
    agents_externes = Agent.objects.filter(type_agent='externe').count()

    return Response({
        'success': True,
        'statistiques': {
            'total_agents': total_agents,
            'agents_actifs': agents_actifs,
            'agents_pending': agents_pending,
            'agents_inactifs': agents_inactifs,
            'agents_suspendus': agents_suspendus,
            'agents_internes': agents_internes,
            'agents_externes': agents_externes,
            'taux_activation': round((agents_actifs / total_agents * 100) if total_agents > 0 else 0, 2)
        }
    }, status=status.HTTP_200_OK)
