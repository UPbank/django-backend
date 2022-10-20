
from rest_framework import viewsets, mixins, pagination
from rest_framework.exceptions import ValidationError

from banking.permissions import IsAuthenticatedOrCreating
from . import serializers, models

from django.db import transaction

class AccountView(viewsets.ModelViewSet):
	'''Allows user to manage their own accounts'''
	queryset = models.Account.objects.all()
	serializer_class = serializers.AccountSerializer
	permission_classes = (IsAuthenticatedOrCreating,)

	def get_queryset(self):
		if self.request.user.is_anonymous:
			return models.Account.objects.none()
		return self.queryset.filter(user=self.request.user)
	
	def perform_destroy(self, instance):
		with transaction.atomic():
			if instance.select_for_update().balance != 0:
				raise ValidationError('errors.account_has_balance')
			return super().perform_destroy(instance)

class TransferPagination(pagination.CursorPagination):
	page_size = 10
	page_size_query_param = 'pageSize'
	max_page_size = 50
	ordering = '-id'

class TransferView(viewsets.ModelViewSet):
	queryset = models.Transfer.objects.prefetch_related('sender', 'receiver')
	serializer_class = serializers.TransferSerializer
	pagination_class = TransferPagination

	def get_queryset(self):
		'''Given a min date, a max date, a type ("EXPENSE" or "INCOME") and a sender/reciever, returns a list of transfers'''
		if self.request.user.is_anonymous:
			return models.Transfer.objects.none()
		user_account = models.Account.objects.get(user=self.request.user)
		result = self.queryset
		transfer_type = self.request.query_params.get('type', None)
		if (transfer_type is not None):
			if (transfer_type == "EXPENSE"):
				result = result.filter(sender=user_account)
			elif (transfer_type == "INCOME"):
				result = result.filter(receiver=user_account)
			else:
				raise ValidationError(f"Invalid transfer type: {transfer_type}")
		else:
			result = result.filter(sender=user_account) | self.queryset.filter(receiver=user_account)

		min_date = self.request.query_params.get('minDate', None)
		if (min_date is not None):
			result = result.filter(date__gte=min_date)
		
		max_date = self.request.query_params.get('maxDate', None)
		if (max_date is not None):
			result = result.filter(date__lte=max_date)
		
		sender_receiver = self.request.query_params.get('fromTo', None)
		if (sender_receiver is not None):
			result = result.filter(sender__full_name__icontains=sender_receiver) | result.filter(receiver__full_name__icontains=sender_receiver)
		
		return result

class BankTransferView(mixins.CreateModelMixin, viewsets.GenericViewSet):
	serializer_class = serializers.BankTransferSerializer

class ServicePaymentView(mixins.CreateModelMixin, viewsets.GenericViewSet):
	serializer_class = serializers.ServicePaymentSerializer

class GovernmentPaymentView(mixins.CreateModelMixin, viewsets.GenericViewSet):
	serializer_class = serializers.GovernmentPaymentSerializer

class TelcoPaymentView(mixins.CreateModelMixin, viewsets.GenericViewSet):
	serializer_class = serializers.TelcoPaymentSerializer

class TelcoProviderView(mixins.ListModelMixin, viewsets.GenericViewSet):
	serializer_class = serializers.TelcoProviderSerializer
	queryset = models.TelcoProvider.objects.all()

class StandingOrderView(viewsets.ModelViewSet):
	serializer_class = serializers.StandingOrderSerializer
	
	def get_queryset(self):
		return models.StandingOrder.objects.filter(sender=self.request.user.account).prefetch_related('receiver')

class DirectDebitView(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
	serializer_class = serializers.DirectDebitSerializer
	
	def get_queryset(self):
		return models.DirectDebit.objects.filter(sender=self.request.user.account).prefetch_related('receiver')

class CardView(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
	serializer_class = serializers.CardSerializer
	
	def get_queryset(self):
		return models.Card.objects.filter(account=self.request.user.account)