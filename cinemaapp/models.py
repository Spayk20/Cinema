from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from rest_framework.authtoken.models import Token


months = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December'
]


class MyUser(AbstractUser):
    total_price = models.PositiveIntegerField(verbose_name='Amount', default=0, blank=True)


class CinemaHall(models.Model):

    class Meta:
        verbose_name = 'Hall'
        verbose_name_plural = 'Halls'

    name = models.CharField(max_length=50, verbose_name='Hall name')
    size = models.PositiveSmallIntegerField(verbose_name='Hall size')

    def __str__(self):
        return self.name


class Session(models.Model):

    class Meta:
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'

    hall = models.ForeignKey(CinemaHall, on_delete=models.CASCADE, related_name='sessions', verbose_name='Hall')
    start_time = models.TimeField(verbose_name='Start time')
    end_time = models.TimeField(verbose_name='End time')
    start_date = models.DateField(verbose_name='Start date')
    end_date = models.DateField(verbose_name='End date')
    price = models.PositiveSmallIntegerField(verbose_name='Ticket price')
    free_seats = models.PositiveSmallIntegerField(default=0)
    status = models.BooleanField(default=True, verbose_name='Status', blank=True)

    @property
    def get_show_date(self):
        return f'From {self.start_date.day} ' \
               f'{months[self.start_date.month - 1]} ' \
               f'{self.start_date.year} ' \
               f"{'year to '}" \
               f'{self.end_date.day} ' \
               f'{months[self.end_date.month - 1]} {self.end_date.year} ' \
               f"{'year'}"

    def check_status(self):
        if self.end_date < timezone.now().date():
            self.status = False
        return self.status

    def __str__(self):
        return f'Session {self.id}'

    def save(self, *args, **kwargs):
        self.check_status()
        super().save(*args, **kwargs)


class Ticket(models.Model):

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'

    customer = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='purchased_tickets',
        verbose_name='Purchase', blank=True
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='session_tickets',
        verbose_name='Session',
        blank=True
    )
    quantity = models.PositiveSmallIntegerField(verbose_name='Quantity ticket')

    def __str__(self):
        return f'Ticket {self.id}'


class MyToken(Token):
    time_to_die = models.DateTimeField(default=timezone.now)