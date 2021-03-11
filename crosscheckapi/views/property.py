"""View module for handling requests about properties"""
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import HttpResponseServerError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from crosscheckapi.models import Property, Landlord, Payment, PaymentType, TenantPropertyRel

class Properties(ViewSet):
    """Cross Check Properties"""

    def create(self, request):
        """Handle POST operations for properties
        Returns:
            Response -- JSON serialized property instance
        """
        # landlord = authenticated user
        landlord = Landlord.objects.get(user=request.auth.user)

        rental = Property()
        rental.street = request.data["street"]
        rental.city = request.data["city"]
        rental.state = request.data["state"]
        rental.postal_code = request.data["postal_code"]
        rental.landlord = landlord

        rental.save()

        serializer = PropertySerializer(
            rental, context={'request': request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """Handle GET requests for single property
        Returns:
            Response -- JSON serialized property instance
        """
        try:
            rental = Property.objects.get(pk=pk)
            serializer = PropertySerializer(
                rental, context={'request': request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex, status=status.HTTP_404_NOT_FOUND)

    def list(self, request):
        """Handle GET requests to property resource
        Returns:
            Response -- JSON serialized list of properties
        """
        properties = Property.objects.all()
        landlord = Landlord.objects.get(user=request.auth.user)
        current_users_properties = Property.objects.filter(landlord=landlord)

        serializer = PropertySerializer(
            current_users_properties, many=True, context={'request': request})

        return Response(serializer.data)

    def update(self, request, pk=None):
        """Handle PUT requests for properties
        Returns:
            Response -- Empty body with 204 status code
        """
        # landlord = authenticated user
        landlord = Landlord.objects.get(user=request.auth.user)

        rental = Property.objects.get(pk=pk)
        rental.street = request.data["street"]
        rental.city = request.data["city"]
        rental.state = request.data["state"]
        rental.postal_code = request.data["postal_code"]
        rental.landlord = landlord

        rental.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        """Handle DELETE requests for properties
        Returns:
            Response -- 204, 404, or 500 status code
        """
        try:
            rental = Property.objects.get(pk=pk)
            rental.delete()

            return Response({}, status=status.HTTP_204_NO_CONTENT)

        except Property.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PropertySerializer(serializers.ModelSerializer):
    """JSON serializer for properties"""
    class Meta:
        model = Property
        fields = ('id', 'street', 'city', 
        'state', 'postal_code', 'landlord')