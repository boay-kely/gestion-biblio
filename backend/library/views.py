from datetime import datetime, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Livre, Categorie, Emprunt, Membre, PENALITE_PAR_JOUR
from .permissions import IsStaffRole, ReadOnlyOrStaff
from .serializers import (
    LivreSerializer,
    CategorieSerializer,
    EmpruntSerializer,
    UserSerializer,
    MembreSerializer,
    RegisterSerializer,
    AlerteRetardSerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Pages HTML
# ---------------------------------------------------------------------------

def home_page(request):
    return render(request, 'library/dashboard.html', {'page': 'dashboard'})


def login_page(request):
    return render(request, 'library/login.html', {'page': 'login'})


def register_page(request):
    return render(request, 'library/register.html', {'page': 'register'})


def livres_page(request):
    return render(request, 'library/livres.html', {'page': 'livres'})


def membres_page(request):
    return render(request, 'library/membres.html', {'page': 'membres'})


def emprunts_page(request):
    return render(request, 'library/emprunts.html', {'page': 'emprunts'})


def categories_page(request):
    return render(request, 'library/categories.html', {'page': 'categories'})


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

class FivePerPagePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000


def get_membre_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return getattr(user, 'membre', None)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'detail': 'Compte client créé avec succès.',
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    pagination_class = FivePerPagePagination
    permission_classes = [IsStaffRole]

    def get_permissions(self):
        if self.action == 'me':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        user = request.user
        data = UserSerializer(user).data
        membre = get_membre_for_user(user)
        data['membre_id'] = membre.id if membre else None
        data['is_staff_role'] = user.is_staff_role
        data['is_client_role'] = user.is_client_role
        return Response(data)


class CategorieViewSet(viewsets.ModelViewSet):
    queryset = Categorie.objects.all().order_by('-id')
    serializer_class = CategorieSerializer
    pagination_class = FivePerPagePagination
    permission_classes = [ReadOnlyOrStaff]


class LivreViewSet(viewsets.ModelViewSet):
    queryset = Livre.objects.select_related('categorie').all().order_by('-id')
    serializer_class = LivreSerializer
    pagination_class = FivePerPagePagination
    permission_classes = [ReadOnlyOrStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get('search') or self.request.query_params.get('q')
        if search:
            search = search.strip()
            qs = qs.filter(
                Q(titre__icontains=search)
                | Q(auteur__icontains=search)
                | Q(isbn__icontains=search)
            )
        disponible = self.request.query_params.get('disponible')
        if disponible in ('1', 'true', 'True'):
            qs = qs.filter(quantite_disponible__gt=0)
        return qs


class EmpruntViewSet(viewsets.ModelViewSet):
    queryset = Emprunt.objects.select_related('membre', 'livre', 'membre__user').all().order_by('-id')
    serializer_class = EmpruntSerializer
    pagination_class = FivePerPagePagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if getattr(user, 'is_client_role', False) and not getattr(user, 'is_staff_role', False):
            membre = get_membre_for_user(user)
            if membre is None:
                return qs.none()
            qs = qs.filter(membre=membre)

        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)

        mes = self.request.query_params.get('mes')
        if mes in ('1', 'true', 'True'):
            membre = get_membre_for_user(user)
            if membre:
                qs = qs.filter(membre=membre)
            else:
                qs = qs.none()

        return qs

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        user = request.user

        if getattr(user, 'is_client_role', False) and not getattr(user, 'is_staff_role', False):
            membre = get_membre_for_user(user)
            if membre is None:
                return Response(
                    {'detail': "Aucun profil client associé à ce compte."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data['membre'] = membre.id
        else:
            if 'membre' not in data:
                alias_membre = (
                    data.get('user')
                    or data.get('utilisateur')
                    or data.get('utilisateur_id')
                    or data.get('membre_id')
                    or data.get('user_id')
                )
                if alias_membre is not None:
                    data['membre'] = alias_membre

        if 'livre' not in data:
            alias_livre = data.get('livre_id')
            if alias_livre is not None:
                data['livre'] = alias_livre

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        if not getattr(request.user, 'is_staff_role', False):
            return Response(
                {'detail': "Seuls les administrateurs peuvent supprimer un emprunt."},
                status=status.HTTP_403_FORBIDDEN,
            )

        emprunt = self.get_object()
        if emprunt.est_actif and emprunt.livre:
            emprunt.livre.quantite_disponible += 1
            emprunt.livre.save(update_fields=['quantite_disponible'])

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def alertes(self, request):
        membre = get_membre_for_user(request.user)
        if membre is None and not getattr(request.user, 'is_staff_role', False):
            return Response([])

        qs = Emprunt.objects.select_related('livre', 'membre').filter(
            est_rendu=False,
        ).exclude(statut='valide')

        if getattr(request.user, 'is_client_role', False) and not getattr(
            request.user, 'is_staff_role', False
        ):
            qs = qs.filter(membre=membre)

        alertes = []
        for emp in qs:
            if not emp.est_en_retard:
                continue
            jours = emp.jours_de_retard()
            penalite = emp.calculer_penalite()
            titre = emp.livre.titre if emp.livre_id else 'Livre inconnu'
            alertes.append(
                {
                    'emprunt_id': emp.id,
                    'livre_id': emp.livre_id,
                    'livre_titre': titre,
                    'date_retour_prevue': emp.date_retour_prevue,
                    'jours_retard': jours,
                    'penalite': penalite,
                    'message': (
                        f"Retard sur « {titre} » — pénalité estimée : "
                        f"{penalite} Ar ({jours} jour{'s' if jours > 1 else ''})."
                    ),
                }
            )

        serializer = AlerteRetardSerializer(alertes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='demander-retour')
    def demander_retour(self, request, pk=None):
        emprunt = self.get_object()
        user = request.user
        membre = get_membre_for_user(user)

        if getattr(user, 'is_client_role', False) and not getattr(user, 'is_staff_role', False):
            if membre is None or emprunt.membre_id != membre.id:
                return Response(
                    {'detail': "Vous ne pouvez demander le retour que de vos propres emprunts."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if emprunt.est_rendu or emprunt.statut == 'valide':
            return Response(
                {'detail': "Ce livre a déjà été rendu et validé."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if emprunt.statut == 'retour_en_attente':
            titre = emprunt.livre.titre if emprunt.livre_id else 'le livre'
            return Response(
                {
                    'detail': f"validation en attente pour le livre « {titre} »",
                    'emprunt': EmpruntSerializer(emprunt).data,
                },
                status=status.HTTP_200_OK,
            )

        emprunt.statut = 'retour_en_attente'
        emprunt.save(update_fields=['statut'])

        titre = emprunt.livre.titre if emprunt.livre_id else 'le livre'
        return Response(
            {
                'detail': f"validation en attente pour le livre « {titre} »",
                'emprunt': EmpruntSerializer(emprunt).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='valider-retour')
    def valider_retour(self, request, pk=None):
        if not getattr(request.user, 'is_staff_role', False):
            return Response(
                {'detail': "Seul un administrateur peut valider une restitution."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return self._finaliser_retour(request, self.get_object())

    @action(detail=True, methods=['post'])
    def retourner(self, request, pk=None):
        if not getattr(request.user, 'is_staff_role', False):
            return Response(
                {
                    'detail': (
                        "Les clients doivent utiliser demander-retour. "
                        "La validation est réservée à l'administrateur."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return self._finaliser_retour(request, self.get_object())

    def _finaliser_retour(self, request, emprunt):
        if emprunt.est_rendu or emprunt.statut == 'valide':
            return Response(
                {'detail': "Ce livre a déjà été rendu."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        etat = request.data.get('etat_retour', 'bon')
        etats_valides = {c[0] for c in Emprunt.ETAT_RETOUR_CHOICES}
        if etat not in etats_valides:
            return Response(
                {'etat_retour': f"Valeur invalide. Choix : {', '.join(sorted(etats_valides))}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notes = request.data.get('notes_retour', '') or ''

        date_retour_str = request.data.get('date_retour')
        if date_retour_str:
            try:
                d = datetime.strptime(str(date_retour_str)[:10], '%Y-%m-%d').date()
                date_retour = timezone.make_aware(datetime.combine(d, time(12, 0)))
            except (ValueError, TypeError):
                return Response(
                    {'date_retour': "Format invalide. Utilisez YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            date_retour = timezone.now()

        jours_retard = 0
        if emprunt.date_retour_prevue and date_retour.date() > emprunt.date_retour_prevue:
            jours_retard = (date_retour.date() - emprunt.date_retour_prevue).days

        if 'penalite' in request.data and request.data.get('penalite') not in (None, ''):
            try:
                penalite = Decimal(str(request.data.get('penalite')))
            except Exception:
                return Response(
                    {'penalite': "Montant de pénalité invalide."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            penalite = PENALITE_PAR_JOUR * jours_retard

        livre = emprunt.livre
        stock_restaure = False
        if livre and etat != 'perdu':
            livre.quantite_disponible += 1
            livre.save(update_fields=['quantite_disponible'])
            stock_restaure = True

        emprunt.est_rendu = True
        emprunt.statut = 'valide'
        emprunt.date_retour_effective = date_retour
        emprunt.etat_retour = etat
        emprunt.notes_retour = notes
        emprunt.penalite = penalite
        emprunt.save(
            update_fields=[
                'est_rendu',
                'statut',
                'date_retour_effective',
                'etat_retour',
                'notes_retour',
                'penalite',
            ]
        )

        return Response(
            {
                'detail': "Retour validé avec succès. L'alerte de retard a été levée.",
                'emprunt': EmpruntSerializer(emprunt).data,
                'jours_retard': jours_retard,
                'penalite': str(penalite),
                'stock_restaure': stock_restaure,
            },
            status=status.HTTP_200_OK,
        )


class MembreViewSet(viewsets.ModelViewSet):
    queryset = Membre.objects.select_related('user').all().order_by('-id')
    serializer_class = MembreSerializer
    pagination_class = FivePerPagePagination
    permission_classes = [IsStaffRole]

    def perform_create(self, serializer):
        membre = serializer.save()

        if membre.user_id:
            return

        base_username = f"{membre.nom.lower()}_{membre.prenom.lower()}".replace(' ', '_')
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        import secrets

        user = User.objects.create_user(
            username=username,
            first_name=membre.prenom,
            last_name=membre.nom,
            email=getattr(membre, 'email', '') or '',
            role='client',
            password=secrets.token_urlsafe(16),
        )
        membre.user = user
        membre.save(update_fields=['user'])

    def destroy(self, request, *args, **kwargs):
        membre = self.get_object()
        user = membre.user
        response = super().destroy(request, *args, **kwargs)
        if user is not None:
            user.delete()
        return response
