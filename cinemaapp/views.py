from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, ListView, UpdateView
from cinemaapp.models import MyUser, CinemaHall, Session, Ticket
from cinemaapp.forms import (MyUserCreationForm, CreateCinemaHallForm, CreateSessionForm, QuantityTicketForm,
                             UpdateSessionForm, FilterForm)
from django.utils import timezone
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib import messages
from datetime import timedelta
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Sum


class UserLoginView(LoginView):
    success_url = reverse_lazy('index')
    template_name = 'login.html'

    def get_success_url(self):
        return self.success_url

    def form_valid(self, form):
        self.request.session['time_action'] = str(timezone.now())
        return super().form_valid(form=form)


class UserRegisterView(CreateView):
    model = MyUser
    form_class = MyUserCreationForm
    success_url = reverse_lazy('index')
    template_name = 'register.html'


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('index')


class SessionListView(ListView):
    model = Session
    template_name = 'index.html'
    context_object_name = 'sessions'
    extra_context = {'quantity': QuantityTicketForm}
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['filter'] = FilterForm
        return context

    def get_queryset(self):
        if self.request.user.is_authenticated:
            price = self.request.GET.get('filter_price')
            start_time = self.request.GET.get('filter_start_time')
            if price and start_time:
                return Session.objects.filter(
                    status=True,
                    end_date__gte=timezone.now().date(),
                    start_date__lte=timezone.now().date()).order_by('price', 'start_time').annotate(total=Sum('session_tickets__quantity'))
            elif price:
                return Session.objects.filter(
                    status=True,
                    end_date__gte=timezone.now().date(),
                    start_date__lte=timezone.now().date()).order_by('price').annotate(total=Sum('session_tickets__quantity'))
            elif start_time:
                return Session.objects.filter(
                    status=True,
                    end_date__gte=timezone.now().date(),
                    start_date__lte=timezone.now().date()).order_by('start_time').annotate(total=Sum('session_tickets__quantity'))
        return Session.objects.filter(
            status=True,
            end_date__gte=timezone.now().date(),
            start_date__lte=timezone.now().date()).annotate(total=Sum('session_tickets__quantity'))


class CreateCinemaHallView(PermissionRequiredMixin, CreateView):
    permission_required = 'is_superuser'
    login_url = reverse_lazy('login')
    model = CinemaHall
    form_class = CreateCinemaHallForm
    success_url = reverse_lazy('index')
    template_name = 'create_cinema_hall.html'


class CreateSessionView(PermissionRequiredMixin, CreateView):
    permission_required = 'is_superuser'
    login_url = reverse_lazy('login')
    model = Session
    form_class = CreateSessionForm
    success_url = reverse_lazy('index')
    template_name = 'create_session.html'


class CreateTicketView(LoginRequiredMixin, CreateView):
    login_url = reverse_lazy('login')
    model = Ticket
    form_class = QuantityTicketForm
    success_url = reverse_lazy('index')
    template_name = 'index.html'

    def form_valid(self, form):
        object = form.save(commit=False)
        quantity = int(form.data['quantity'])
        user = self.request.user
        object.customer = user
        session = Session.objects.get(id=self.request.POST['session'])
        object.session = session
        hall = session.hall
        total_quantity = session.session_tickets.aggregate(Sum('quantity'))['quantity__sum']
        if not total_quantity:
            total_quantity = 0
        free_places = hall.size - total_quantity
        if free_places < quantity:
            messages.error(self.request, f'Мест не хватает! Свободных мест: {free_places}')
            return HttpResponseRedirect(self.success_url)
        user.total_price += quantity * session.price
        user.save()
        return super().form_valid(form=form)


class UserPurchaseListView(LoginRequiredMixin, ListView):
    login_url = reverse_lazy('login')
    template_name = 'purchases.html'
    model = Ticket
    paginate_by = 3

    def get_queryset(self):
        return super().get_queryset().filter(customer=self.request.user)


class UpdateCinemaHallView(PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    permission_required = 'is_superuser'
    login_url = reverse_lazy('login')
    model = CinemaHall
    success_url = reverse_lazy('index')
    form_class = CreateCinemaHallForm
    template_name = 'update_cinema_hall.html'

    def test_func(self):
        sessions = self.get_object().sessions.filter(status=True)
        if sessions:
            for session in sessions:
                if session.session_tickets.exists():
                    return False
        return True


class UpdateSessionView(PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    permission_required = 'is_superuser'
    login_url = reverse_lazy('login')
    model = Session
    success_url = reverse_lazy('index')
    form_class = UpdateSessionForm
    template_name = 'update_session.html'

    def test_func(self):
        session = self.get_object()
        if session.session_tickets.exists():
            return False
        return True


class SessionForTomorrowListView(ListView):
    model = Session
    template_name = 'session_for_tomorrow.html'
    extra_context = {'quantity': QuantityTicketForm}
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['filter'] = FilterForm
        return context

    def get_queryset(self):
        if self.request.user.is_authenticated:
            price = self.request.GET.get('filter_price')
            start_time = self.request.GET.get('filter_start_time')
            if price and start_time:
                return Session.objects.filter(
                    status=True,
                    end_date__gte=timezone.now().date() + timedelta(days=1),
                    start_date__lte=timezone.now().date() + timedelta(days=1)).order_by('price', 'start_time').annotate(
                    total=Sum('session_tickets__quantity'))
            elif price:
                return Session.objects.filter(status=True, end_date__gte=timezone.now().date() + timedelta(days=1),
                    start_date__lte=timezone.now().date() + timedelta(days=1)).order_by('price').annotate(
                    total=Sum('session_tickets__quantity'))
            elif start_time:
                return Session.objects.filter(
                    status=True,
                    end_date__gte=timezone.now().date() + timedelta(days=1),
                    start_date__lte=timezone.now().date() + timedelta(days=1)).order_by('start_time').annotate(total=Sum('session_tickets__quantity'))
        return Session.objects.filter(
            status=True,
            end_date__gte=timezone.now().date() + timedelta(days=1),
            start_date__lte=timezone.now().date() + timedelta(days=1)).annotate(total=Sum('session_tickets__quantity'))
