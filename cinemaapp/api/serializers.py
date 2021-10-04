from rest_framework import serializers
from django.db.models import Sum
from django.contrib.auth.password_validation import validate_password
from cinemaapp.models import MyUser, CinemaHall, Session, Ticket


class MyUserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = MyUser
        fields = ('id', 'username', 'password', 'password2')
        read_only = ('id', 'total_price')

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError('Пароли не совпадают')
        return data

    def create(self, validated_data):
        user = MyUser.objects.create(username=validated_data['username'])
        user.set_password(validated_data['password'])
        user.save()
        return user


class CinemaHallSerializer(serializers.ModelSerializer):

    class Meta:
        model = CinemaHall
        fields = ('id', 'name', 'size')
        read_only = ('id', )


class SessionCreateSerializer(serializers.ModelSerializer):
    free_places = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Session
        fields = (
            'id', 'hall', 'start_time', 'end_time', 'start_date', 'end_date',
            'show_date', 'price', 'status', 'free_places'
        )
        read_only = ('id', 'show_date', 'status')

    def get_free_places(self, obj):
        try:
            return obj.hall.size - obj.total
        except (AttributeError, TypeError):
            return obj.hall.size

    def validate(self, data):
        hall = data['hall']
        start_date = data['start_date']
        end_date = data['end_date']
        start_time = data['start_time']
        end_time = data['end_time']
        if start_time >= end_time or start_date >= end_date:
            raise serializers.ValidationError('Начало не может быть больше конца')
        sessions_that_overlap = hall.sessions.filter(status=True, end_date__gte=start_date, start_date__lte=end_date)
        if sessions_that_overlap:
            if sessions_that_overlap.filter(end_time__gte=start_time, start_time__lte=end_time):
                raise serializers.ValidationError('Зал в это время занят')
        return data


class SessionUpdateSerializer(serializers.ModelSerializer):
    free_places = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Session
        fields = (
            'id', 'hall', 'start_time', 'end_time', 'start_date',
            'end_date', 'show_date', 'price', 'status', 'free_places'
        )
        read_only = ('id', 'show_date', 'status')

    def get_free_places(self, obj):
        try:
            return obj.hall.size - obj.total
        except (AttributeError, TypeError):
            return obj.hall.size

    def validate(self, data):
        session = self.instance
        hall = data.get('hall')
        if not hall:
            hall = session.hall
        start_date = data.get('start_date')
        if not start_date:
            start_date = session.start_date
        end_date = data.get('end_date')
        if not end_date:
            end_date = session.end_date
        start_time = data.get('start_time')
        if not start_time:
            start_time = session.start_time
        end_time = data.get('end_time')
        if not end_time:
            end_time = session.end_time
        if start_time >= end_time or start_date >= end_date:
            raise serializers.ValidationError('Начало не может быть больше конца')
        sessions_that_overlap = hall.sessions.filter(status=True, end_date__gte=start_date, start_date__lte=end_date).exclude(id=session.pk)
        if sessions_that_overlap:
            if sessions_that_overlap.filter(end_time__gte=start_time, start_time__lte=end_time):
                raise serializers.ValidationError('Зал в это время занят')
        return data


class TicketSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Ticket
        fields = ('id', 'customer', 'session', 'quantity', 'total_price')
        read_only = ('id', 'customer')

    def get_total_price(self, obj):
        return obj.customer.total_price

    def validate(self, data):
        quantity = data['quantity']
        session = data['session']
        hall_size = session.hall.size
        session_tickets = session.session_tickets.aggregate(Sum('quantity'))['quantity__sum']
        if not session_tickets:
            session_tickets = 0
        free_places = hall_size - session_tickets
        if free_places < quantity:
            raise serializers.ValidationError(f'Мест не хватает! Свободных мест: {free_places}')
        return data
