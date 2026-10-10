from django.db import transaction
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Livre, Categorie, Emprunt, Membre

User = get_user_model()


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = '__all__'


class LivreSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    fichier_pdf = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Livre
        fields = '__all__'

    def update(self, instance, validated_data):
        # Ne pas effacer le PDF existant si aucun nouveau fichier n'est envoyé
        if 'fichier_pdf' in validated_data and not validated_data['fichier_pdf']:
            validated_data.pop('fichier_pdf')
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if instance.fichier_pdf:
            url = instance.fichier_pdf.url
            data['fichier_pdf'] = request.build_absolute_uri(url) if request else url
        else:
            data['fichier_pdf'] = None
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['id', 'role']


class RegisterSerializer(serializers.Serializer):
    """Inscription publique : rôle forcé à client, jamais admin."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    email = serializers.EmailField(required=False, allow_blank=True, default='')
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    date_naissance = serializers.DateField(required=False, allow_null=True)
    lieu_naissance = serializers.CharField(
        max_length=150, required=False, allow_blank=True, default=''
    )

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

    def validate(self, attrs):
        # Sécurité : ignorer toute tentative d'attribution de rôle via payload
        if self.initial_data.get('role') in ('admin', 'bibliothecaire'):
            # Ne pas faire échouer pour ne pas révéler, mais le rôle sera ignoré
            pass
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password')
        date_naissance = validated_data.pop('date_naissance', None)
        lieu_naissance = validated_data.pop('lieu_naissance', '') or ''
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email') or '',
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='client',  # obligatoirement client
        )

        Membre.objects.create(
            user=user,
            nom=last_name,
            prenom=first_name,
            date_naissance=date_naissance,
            lieu_naissance=lieu_naissance,
        )
        return user


class MembreSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default=None)

    class Meta:
        model = Membre
        fields = [
            'id',
            'user',
            'username',
            'nom',
            'prenom',
            'date_naissance',
            'lieu_naissance',
            'a_propos',
            'date_inscription',
        ]
        read_only_fields = ['id', 'date_inscription', 'username']


class EmpruntSerializer(serializers.ModelSerializer):
    membre = serializers.PrimaryKeyRelatedField(queryset=Membre.objects.all())
    livre = serializers.PrimaryKeyRelatedField(queryset=Livre.objects.all())
    message_statut = serializers.SerializerMethodField()
    penalite_estimee = serializers.SerializerMethodField()
    est_en_retard = serializers.SerializerMethodField()
    jours_retard = serializers.SerializerMethodField()

    class Meta:
        model = Emprunt
        fields = [
            'id',
            'membre',
            'livre',
            'date_emprunt',
            'date_retour_prevue',
            'date_retour_effective',
            'est_rendu',
            'statut',
            'etat_retour',
            'notes_retour',
            'penalite',
            'message_statut',
            'penalite_estimee',
            'est_en_retard',
            'jours_retard',
        ]
        read_only_fields = [
            'id',
            'date_emprunt',
            'date_retour_effective',
            'est_rendu',
            'statut',
            'etat_retour',
            'notes_retour',
            'penalite',
            'message_statut',
            'penalite_estimee',
            'est_en_retard',
            'jours_retard',
        ]

    def get_message_statut(self, obj):
        if obj.statut == 'retour_en_attente':
            titre = obj.livre.titre if obj.livre_id else 'ce livre'
            return f"validation en attente pour le livre « {titre} »"
        labels = dict(Emprunt.STATUT_CHOICES)
        return labels.get(obj.statut, obj.statut)

    def get_penalite_estimee(self, obj):
        if obj.est_rendu:
            return str(obj.penalite)
        return str(obj.calculer_penalite())

    def get_est_en_retard(self, obj):
        return obj.est_en_retard

    def get_jours_retard(self, obj):
        if obj.est_rendu:
            return obj.jours_de_retard(
                obj.date_retour_effective.date() if obj.date_retour_effective else None
            )
        return obj.jours_de_retard()

    def validate_livre(self, livre):
        if livre.quantite_disponible <= 0:
            raise serializers.ValidationError(
                "Ce livre n'est plus disponible en stock."
            )
        return livre

    def validate(self, attrs):
        membre = attrs.get('membre') or getattr(self.instance, 'membre', None)

        if membre is not None:
            actifs = Emprunt.objects.filter(membre=membre, est_rendu=False).exclude(
                statut='valide'
            )
            if self.instance is not None:
                actifs = actifs.exclude(pk=self.instance.pk)
            if actifs.exists():
                raise serializers.ValidationError(
                    "Ce membre a déjà un emprunt en cours. "
                    "Il doit d'abord retourner son livre précédent avant d'en emprunter un autre."
                )

        return attrs

    def create(self, validated_data):
        emprunt = Emprunt.objects.create(statut='en_cours', **validated_data)
        livre = validated_data['livre']
        livre.quantite_disponible = max(0, livre.quantite_disponible - 1)
        livre.save(update_fields=['quantite_disponible'])
        return emprunt

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        try:
            if instance.membre_id and instance.membre:
                representation['membre_detail'] = MembreSerializer(instance.membre).data
            else:
                representation['membre_detail'] = None
        except Exception:
            representation['membre_detail'] = None

        try:
            if instance.livre_id and instance.livre:
                representation['livre_detail'] = {
                    'id': instance.livre.id,
                    'titre': instance.livre.titre,
                    'auteur': getattr(instance.livre, 'auteur', ''),
                    'isbn': getattr(instance.livre, 'isbn', ''),
                    'description': getattr(instance.livre, 'description', ''),
                    'quantite_disponible': getattr(
                        instance.livre, 'quantite_disponible', 0
                    ),
                    'fichier_pdf': (
                        instance.livre.fichier_pdf.url
                        if instance.livre.fichier_pdf
                        else None
                    ),
                }
            else:
                representation['livre_detail'] = None
        except Exception:
            representation['livre_detail'] = None

        return representation


class AlerteRetardSerializer(serializers.Serializer):
    emprunt_id = serializers.IntegerField()
    livre_id = serializers.IntegerField()
    livre_titre = serializers.CharField()
    date_retour_prevue = serializers.DateField()
    jours_retard = serializers.IntegerField()
    penalite = serializers.DecimalField(max_digits=10, decimal_places=2)
    message = serializers.CharField()
