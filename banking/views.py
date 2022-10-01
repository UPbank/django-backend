from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets, mixins
from rest_framework.exceptions import ValidationError

from .models import Account, Transfer
from .serializers import *

class AccountViewSet(viewsets.ModelViewSet):
	'''Allows user to manage their own accounts'''
	queryset = Account.objects.all()
	serializer_class = AccountSerializer

	def get_queryset(self):
		if self.request.user.is_anonymous:
			return Account.objects.none()
		return self.queryset.filter(user=self.request.user)

class TransferViewSet(viewsets.ModelViewSet):
	queryset = Transfer.objects.all()
	serializer_class = TransferSerializer

	def get_queryset(self):
		'''Given a min date, a max date, a type ("SEND" or "RECEIVE") and a sender/reciever, returns a list of transfers'''
		if self.request.user.is_anonymous:
			return Transfer.objects.none()
		user_account = Account.objects.get(user=self.request.user)
		result = self.queryset.prefetch_related('sender', 'receiver')
		type = self.request.query_params.get('type', None)
		if (type is not None):
			if (type == "SEND"):
				result = result.filter(sender=user_account)
			elif (type == "RECEIVE"):
				result = result.filter(receiver=user_account)
			else:
				raise ValidationError(f"Invalid transfer type: {type}")
		else:
			result = result.filter(sender=user_account) | self.queryset.filter(receiver=user_account)

		min_date = self.request.query_params.get('min_date', None)
		if (min_date is not None):
			result = result.filter(date__gte=min_date)
		
		max_date = self.request.query_params.get('max_date', None)
		if (max_date is not None):
			result = result.filter(date__lte=max_date)
		
		sender_receiver = self.request.query_params.get('sender_receiver', None)
		if (sender_receiver is not None):
			result = result.filter(sender__full_name__icontains=sender_receiver) | result.filter(receiver__full_name__icontains=sender_receiver)
		
		return result
