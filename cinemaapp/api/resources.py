from cinemaapp.models import MyUser, CinemaHall, Session, Ticket, MyToken
from cinemaapp.api.serializers import (MyUserRegisterSerializer, CinemaHallSerializer, SessionCreateSerializer,
                                       SessionUpdateSerializer, TicketSerializer)
from rest_framework.response import Response
from rest_framework import viewsets, permissions, generics, pagination
from rest_framework.authtoken.views import ObtainAuthToken
from datetime import timedelta, datetime
from django.utils import timezone
from .permissions import CustomSessionUpdatePermisson, CustomCinemaHallUpdatePermisson
from django.db.models import Sum, Q
from rest_framework.decorators import action


class MyPageNumberPagination(pagination.PageNumberPagination):
    page_size = 3


class UserRegisterAPIView(generics.CreateAPIView):
    queryset = MyUser.objects.all()
    serializer_class = MyUserRegisterSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    http_method_names = ['post', 'put', 'patch']
    permission_classes = [permissions.IsAdminUser]
    pagination_class = MyPageNumberPagination

    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT']:
            self.permission_classes += [CustomCinemaHallUpdatePermisson]
        return super().get_permissions()


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionCreateSerializer
    http_method_names = ['get', 'post', 'put', 'patch']
    pagination_class = MyPageNumberPagination

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return SessionUpdateSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [permissions.IsAdminUser]
        elif self.request.method in ['PATCH', 'PUT']:
            self.permission_classes = [CustomSessionUpdatePermisson, permissions.IsAdminUser]
        return super().get_permissions()

    def get_queryset(self):
        q1 = Q(status=True,
               end_date__gte=timezone.now().date(),
               start_date__lte=timezone.now().date())
        q2 = Q()
        q3 = Q()
        if self.action == 'tomorrow':
            q1 = Q(status=True,
                   end_date__gte=timezone.now().date() + timedelta(days=1),
                   start_date__lte=timezone.now().date() + timedelta(days=1))
        if self.request.user.is_authenticated:
            price = self.request.query_params.get('price')
            start_time = self.request.query_params.get('start_time')
            hall = self.request.query_params.get('hall')
            time = self.request.query_params.get('time')
            if hall:
                q2 = Q(hall=hall)
            if time:
                time_list = time.split('-')
                start = datetime.strptime(time_list[0], '%H:%M').time()
                end = datetime.strptime(time_list[1], '%H:%M').time()
                q3 = Q(start_time__gte=start, end_time__lte=end)
            if price and start_time:
                return Session.objects.filter(
                    q1 & q2 & q3
                ).order_by('price', 'start_time').annotate(total=Sum('session_tickets__quantity'))
            elif price:
                return Session.objects.filter(
                    q1 & q2 & q3
                ).order_by('price').annotate(total=Sum('session_tickets__quantity'))
            elif start_time:
                return Session.objects.filter(
                    q1 & q2 & q3
                ).order_by('start_time').annotate(total=Sum('session_tickets__quantity'))
        return Session.objects.filter(
            q1 & q2 & q3
        ).annotate(total=Sum('session_tickets__quantity'))

    @action(detail=False, methods=['get'])
    def tomorrow(self, request):
        sessions = self.get_queryset()
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    http_method_names = ['get', 'post']
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MyPageNumberPagination

    def perform_create(self, serializer):
        user = self.request.user
        session = Session.objects.get(id=self.request.data['session'])
        quantity = self.request.data['quantity']
        user.total_price += session.price * quantity
        user.save()
        serializer.save(customer=user)

    def get_queryset(self):
        return Ticket.objects.filter(customer=self.request.user)


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = MyToken.objects.get_or_create(user=user)
        return Response({'token': token.key, 'time_to_die': '{}'.format(
            token.time_to_die + timedelta(minutes=5) if not user.is_superuser else None)})
