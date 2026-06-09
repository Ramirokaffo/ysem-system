from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from .access_modules import ALL_MODULE_CODES, MODULE_CHOICES, MODULE_CONFIG, ROLE_MODULES_MAP



class AccessModule(models.Model):
    """Module applicatif auquel un utilisateur peut avoir accès."""

    code = models.CharField(max_length=50, primary_key=True, choices=MODULE_CHOICES)
    name = models.CharField(max_length=100, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    icon_class = models.CharField(max_length=100, blank=True, verbose_name="Icône")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Module d'accès"
        verbose_name_plural = "Modules d'accès"
        ordering = ['name']

    def __str__(self):
        return self.name


class BaseUserManager(UserManager):
    """Manager avec compatibilité temporaire pour l'ancien mot-clé role."""

    def _create_user(self, username, email, password, **extra_fields):
        legacy_role = extra_fields.pop('role', None)
        user = super()._create_user(username, email, password, **extra_fields)
        module_codes = ROLE_MODULES_MAP.get(legacy_role or '', [])
        if module_codes:
            modules = AccessModule.objects.filter(code__in=module_codes, is_active=True)
            user.accessible_modules.add(*modules)
            if not user.last_accessed_module:
                user.last_accessed_module = module_codes[0]
                user.save(update_fields=['last_accessed_module'])
        return user


class BaseUser(AbstractUser):
    """
    Extension du modèle User de Django pour ajouter des champs personnalisés
    Inclut les propriétés du personnel (Staff) pour simplifier l'architecture
    """
    # Champs personnels de base
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True, verbose_name="Photo de profil")

    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Masculin'), ('F', 'Féminin')],
        blank=True,
        null=True
    )
    accessible_modules = models.ManyToManyField(
        AccessModule,
        blank=True,
        related_name='users',
        verbose_name="Modules accessibles",
    )
    last_accessed_module = models.CharField(
        max_length=50,
        choices=MODULE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Dernier module accédé",
    )
    two_factor_enabled = models.BooleanField(
        default=False,
        verbose_name="Double authentification activée",
        help_text="Si activée, un code de vérification est envoyé par email à chaque connexion.",
    )
    two_factor_user_can_manage = models.BooleanField(
        default=True,
        verbose_name="L'utilisateur peut gérer sa double authentification",
        help_text=(
            "Si décoché, l'utilisateur ne peut pas activer ou désactiver lui-même "
            "la double authentification depuis son profil."
        ),
    )

    class Meta:
        db_table = 'accounts_baseuser'
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    objects = BaseUserManager()

    def get_accessible_module_codes(self):
        """Retourne les codes modules autorisés pour l'utilisateur."""
        if self.is_superuser:
            return list(ALL_MODULE_CODES)

        if self.pk:
            codes = list(
                self.accessible_modules.filter(is_active=True).values_list('code', flat=True)
            )
            if codes:
                return codes

        return []

    def has_module_access(self, module_code):
        return module_code in self.get_accessible_module_codes()

    def get_accessible_modules_data(self):
        return [
            {'code': code, **MODULE_CONFIG[code]}
            for code in self.get_accessible_module_codes()
            if code in MODULE_CONFIG
        ]

    def get_default_module_code(self):
        codes = self.get_accessible_module_codes()
        if self.last_accessed_module in codes:
            return self.last_accessed_module
        return codes[0] if codes else None

    def is_scholar_admin(self):
        return self.has_module_access("scholar")

    def is_study_admin(self):
        return self.has_module_access("teaching")

    def is_planning_admin(self):
        return self.has_module_access("planning")


class Godfather(models.Model):
    """
    Modèle pour les parrains/tuteurs
    """
    # user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name='godfather_profile')
    full_name = models.CharField(max_length=200, verbose_name="Nom complet")
    occupation = models.CharField(max_length=200, blank=True, null=True, verbose_name="Profession")
    phone_number = models.CharField(max_length=20, verbose_name="Numéro de téléphone")
    email = models.EmailField(verbose_name="Adresse email")
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Parrain"
        verbose_name_plural = "Parrains"



