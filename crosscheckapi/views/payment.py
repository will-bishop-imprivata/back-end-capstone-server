"""View module for handling requests about payments"""
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import HttpResponseServerError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from datetime import datetime
import operator
from crosscheckapi.models import Tenant, Landlord, Payment, PaymentType, TenantPropertyRel

class Payments(ViewSet):
    """ Cross Check payments """

    def create(self, request):
        """Handle POST operations for payments
        Returns:
            Response -- JSON serialized payment instance
        """
        # landlord = authenticated user
        landlord = Landlord.objects.get(user=request.auth.user)
        tenant_id = int(request.data["full_name"])
        tenant = Tenant.objects.get(pk=tenant_id )
        payment = Payment()

        # Splitting the datetime string on the T to save the date
        date_string_list = request.data["date"].split('T')
        date = date_string_list[0]
        payment.date = date

        # This field is looking for an integer.
        # If the user includes a $, the string will
        # split, be converted to an integer and saved
        try:
            payment.amount = int(request.data["amount"])
        except ValueError:
            try:
                amount_string_list = request.data["amount"].split('$')
                float_amount = float(amount_string_list[1])
                amount = int(float_amount)
                payment.amount = amount
            except IndexError:
                float_amount = float(request.data["amount"])
                amount = int(float_amount)
                payment.amount = amount
        
        payment.ref_num = request.data["ref_num"]
        payment.tenant = tenant

        # Find the associated lease to assign the property
        # rather than having the user select both the
        # tenant and property
        # try:
        #     lease = TenantPropertyRel.objects.get(tenant=int(request.data["full_name"]))
        #     payment.rented_property = lease.rented_property
        # except TenantPropertyRel.DoesNotExist:
        #     payment.rented_property = None
        
        # Retrieve the payment type and attach a
        # Payment Type instance to the payment
        payment_type = PaymentType.objects.get(pk=int(request.data["type"]))
        payment.payment_type = payment_type

        payment.landlord = landlord
        payment.save()

        serializer = PaymentSerializer(
            payment, context={'request': request}
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """Handle GET requests for single payment
        Returns:
            Response -- JSON serialized payment instance
        """
        try:
            payment = Payment.objects.get(pk=pk)

            serializer = PaymentSerializer(
                payment, context={'request': request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex, status=status.HTTP_404_NOT_FOUND)

    def list(self, request):
        """Handle GET requests to payments resource
        Returns:
            Response -- JSON serialized list of payments
        """
        landlord = Landlord.objects.get(user=request.auth.user)
        users_payments = Payment.objects.filter(landlord=landlord)

        # Sort the payments by date starting with the most recent
        payments = sorted(users_payments, key=operator.attrgetter('date'), reverse=True)
        
        # Search keyword query parameter.
        # Allows the user to search by ref_num or name
        # using the same search input.
        keyword = self.request.query_params.get('keyword', None)
        if keyword is not None:
            payments = payments.filter(ref_num__icontains=keyword
                        ) | payments.filter(tenant__full_name__icontains=keyword) 

        # Date range query parameter
        # Check for the parameter to distinguigh the fetch
        # Use the values sent in the body for the range
        date_range = self.request.query_params.get('date', None)
        if date_range is not None:
            d1 = request.data["startDate"]
            d2 = request.data["endDate"]
            payments = payments.filter(date__range=(d1,d2))

        serializer = PaymentSerializer(
            payments, many=True, context={'request': request})

        return Response(serializer.data)

    def update(self, request, pk=None):
        """Handle PUT requests for payments
        Returns:
            Response -- Empty body with 204 status code
        """
        # landlord = authenticated user
        landlord = Landlord.objects.get(user=request.auth.user)
        tenant = Tenant.objects.get(pk=request.data["full_name"])

        payment = Payment.objects.get(pk=pk)

        # Splitting the datetime string on the T to save the date
        date_string_list = request.data["date"].split('T')
        date = date_string_list[0]
        payment.date = date

        # This field is looking for an integer.
        # If the user includes a $, the string will
        # split, be converted to an integer and saved
        try:
            payment.amount = int(request.data["amount"])
        except ValueError:
            try:
                amount_string_list = request.data["amount"].split('$')
                float_amount = float(amount_string_list[1])
                amount = int(float_amount)
                payment.amount = amount
            except IndexError:
                float_amount = float(request.data["amount"])
                amount = int(float_amount)
                payment.amount = amount

        payment.ref_num = request.data["ref_num"]
        payment.tenant = tenant

        # Find the associated lease to assign the property
        # rather than having the user select both the
        # tenant and property
        # lease = TenantPropertyRel.objects.get(tenant=request.data["full_name"])
        # payment.rented_property = lease.rented_property
        
        # Retrieve the payment type and attach a 
        # Payment Type instance to the payment
        payment_type = PaymentType.objects.get(pk=request.data["type"])
        payment.payment_type = payment_type

        payment.landlord = landlord
        payment.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        """Handle DELETE requests for payments
        Returns:
            Response -- 204, 404, or 500 status code
        """
        try:
            payment = Payment.objects.get(pk=pk)
            payment.delete()
            
            return Response({}, status=status.HTTP_204_NO_CONTENT)

        except Payment.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TenantSerializer(serializers.ModelSerializer):
    """JSON serializer for tenants"""
    
    class Meta:
        model = Tenant
        fields = ('id', 'phone_number', 'email',
                    'landlord', 'full_name')

class PaymentSerializer(serializers.ModelSerializer):
    """JSON serializer for payments"""
    tenant = TenantSerializer(many=False)
    class Meta:
        model = Payment
        fields = ('id', 'date', 'amount',
                    'ref_num', 'tenant', 
                    'payment_type')
        depth=2