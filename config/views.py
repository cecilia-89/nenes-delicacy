import json
import math
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.forms.models import model_to_dict
from django.core import mail
from .pagination import StandardResultsSetPagination
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from rest_framework.decorators import action
from django.shortcuts import render
from django.core import serializers as serializer
from django.views.decorators.cache import cache_page
from .utils.filter import filter_products
from .utils.distance import get_distance
from .models import *
import environ
from .serializers import *  


env = environ.Env()
environ.Env.read_env()

CACHE_TTL = 60 * 60

# def send_email(request):
#     sessionid = '0028ea17-8525-4239-a9d8-3eb6be5e1417'
#     cart = Cart.objects.get(session_id=sessionid, ordered=False)
#     cartitems = Cartitem.objects.filter(cart=cart)
#     total = sum([int(item.price) for item in cartitems])

#     shipping = ShippingAddress.objects.get(session_id=sessionid)

#     cartitems = [
#         {
#             'item': model_to_dict(item.item, fields=['unit_price', 'image', 'name']),
#             'quantity': item.quantity,
#         }
#         for item in cartitems
#     ]

#     data = {'cartitems': cartitems, 
#             'shipping': shipping,
#             'total': total,
#             'id': 'uioy'}

#     return render(request, 'email-templates.html', data)


class ProductView(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    queryset = Products.objects.all()
    
    def get_queryset(self):
        filter = self.request.query_params.get('filter_by')
        queryset = filter_products(filter, self.queryset)
        return queryset
    
    def dispatch(self, *args, **kwargs):
        return super(ProductView, self).dispatch(*args, **kwargs)
    

    @action(detail=False, methods=['get'])
    def get_product(self, request):
        paginator = self.pagination_class()
        parameter = self.request.query_params.get('pathname')
        filter = self.request.query_params.get('filter_by')
        isCollection = False

        try:
            product_type = ProductType.objects.get(parameter=parameter)
            queryset = self.queryset.filter(product_type=product_type)
        except ProductType.DoesNotExist:
            product_type = None
            isCollection = True

        try:
            collection = Collection.objects.get(name=parameter)
            queryset = self.queryset.filter(collection=collection)
        except Collection.DoesNotExist:
            collection = None

        if not product_type and not collection:
            return JsonResponse("Not found", status=404, safe=False)
        
        filtered_queryset = filter_products(filter, queryset)

        paginated_queryset = paginator.paginate_queryset(filtered_queryset, request)
        serialized_queryset = ProductSerializer(paginated_queryset, many=True)
        response = paginator.get_paginated_response(serialized_queryset.data, isCollection)

        return response
    

    @action(detail=False, methods=['get'])
    def get_item(self, request):
        try:
            name = self.request.query_params.get('name')
            item = Products.objects.get(name=name)
            item = ProductSerializer(item).data
        except Products.DoesNotExist:
            return JsonResponse("Not found", status=404, safe=False)
        
        return HttpResponse(
            json.dumps(item)
        )


    @action(detail=False, methods=['get'])
    def search(self, request):
        query = self.request.query_params['query']
        filter = self.request.query_params.get('filter_by')
        matchedObjects = Products.objects.filter(name__icontains=query) 
        filteredObjects = filter_products(filter, matchedObjects)

        paginator = self.pagination_class()
        paginated_objects = paginator.paginate_queryset(filteredObjects, request)

        serializedObjects = ProductSerializer(paginated_objects, many=True)
        return paginator.get_paginated_response(serializedObjects.data)

    
class ProductTypeView(viewsets.ModelViewSet):
    serializer_class = ProductTypeSerializer
    queryset = ProductType.objects.all()


    @action(detail=False, methods=['get'])
    def collection(self, request):
        queryset = Collection.objects.all()
        serialized_queryset = CollectionSerializer(queryset, many=True)
        return Response(serialized_queryset.data)

    
    # @method_decorator(cache_page(CACHE_TTL))
    def dispatch(self, *args, **kwargs):
        return super(ProductTypeView, self).dispatch(*args, **kwargs)
    

class CartView(viewsets.ModelViewSet):

    serializer_class = CartItemSerializer
    queryset = Cartitem.objects.all()

    def dispatch(self, *args, **kwargs):
        return super(CartView, self).dispatch(*args, **kwargs)

 
    @action(detail=False, methods=['get'])
    def getCart(self, request):
        sessionid = self.request.query_params['sessionid']
        [cart, created] = Cart.objects.get_or_create(session_id=sessionid, ordered=False)
        query = Cartitem.objects.filter(cart=cart)

        total = sum([float(item.price) for item in query])
        cartitems = [CartItemSerializer(item).data for item in query]

        return HttpResponse(
            json.dumps({
                'cartitems': cartitems,
                'total': str(math.ceil(total))
            })
        )


    @action(detail=False, methods=['get'])
    def createCart(self, request):

        sessionid = request.query_params.get('sessionid')
        [cart, completed] = Cart.objects.get_or_create(session_id=sessionid)

        if completed:
            cart.save()
        return HttpResponse('cart created')
    
     
    @action(detail=False, methods=['post'])
    def addToCart(self, request):

        cart = Cart.objects.get(session_id=request.data['sessionid'])
        item = Products.objects.get(id=request.data['item'])
  
        try:
            cartitem = Cartitem.objects.get(item=item, cart=cart)
            cartitem.quantity += request.data['quantity']

        except Cartitem.DoesNotExist:
            
            cartitem = Cartitem.objects.create(
                quantity=request.data['quantity'], 
                cart=cart,
                item=item
            )

        cartitem.save()
        serializer = CartItemSerializer(cartitem).data
        return HttpResponse(json.dumps(serializer))
    

    @action(detail=False, methods=['put'])
    def updateCartItem(self, request):
        cartitem = Cartitem.objects.get(id=request.data['item'])
        cartitem.quantity = request.data['quantity']
        cartitem.save()

        return HttpResponse('cartitem updated')

    
    @action(detail=False, methods=['delete'])
    def deleteCartItem(self, request):
        itemId = request.query_params.get('itemId')
        cartitem = Cartitem.objects.get(pk=itemId)
        cartitem.delete()

        return HttpResponse('cartitem deleted')
    

    @action(detail=False, methods=['get'])
    def createOrder(self, request): 
        sessionid = self.request.query_params['sessionid']
        cart = Cart.objects.get(session_id=sessionid, ordered=False)
        cartitems = Cartitem.objects.filter(cart=cart)
        total = sum([int(item.price) for item in cartitems])
        cart.ordered = True
        cart.save()

        shipping = ShippingAddress.objects.get(session_id=sessionid)

        cartitems = [
            {
                'item': model_to_dict(item.item, fields=['unit_price', 'image', 'name']),
                'quantity': item.quantity,
            }
            for item in cartitems
        ]

        html_body = render_to_string("email-templates.html", {'cartitems': cartitems, 
                                                              'shipping': shipping,
                                                              'total': total,
                                                            'id': 'uioy'})
        message = strip_tags(html_body)
        subject=f"{shipping.firstName}'s Order Confirmation"
        from_email = 'catabong89@gmail.com'
        to = 'catabong89@gmail.com'
       
        mail.send_mail(subject, message, from_email, [to], html_message=html_body)
        return HttpResponse('Success')
    

class ShippingView(viewsets.ModelViewSet): 
    serializer_class = ShippingSerializer
    queryset = ShippingAddress.objects.all()
         
    def dispatch(self, *args, **kwargs):
        return super(ShippingView, self).dispatch(*args, **kwargs)
    

    @action(detail=False, methods=['get'])
    def get_shipping(self, request):
        sessionID = self.request.query_params.get('sessionID')
        address, created = ShippingAddress.objects.get_or_create(session_id=sessionID)
        serializer = ShippingSerializer(address).data
    
        return HttpResponse(json.dumps(serializer))


    @action(detail=False, methods=['post'])
    def add_shipping(self, request):
        sessionID = self.request.query_params.get('sessionID')
        [shipping, created] = ShippingAddress.objects.get_or_create(session_id=sessionID)
        
        shipping.__dict__.update(request.data)
        distance = get_distance(request.data['lga'], request.data['state'])
        
        if not distance:
            return HttpResponse('Bad Internet connection', status=500)
        
        shipping.price = distance
        shipping.save()
        serializer = ShippingSerializer(shipping).data
        return HttpResponse(json.dumps(serializer))
    
    
    @action(detail=False, methods=['put'])
    def update_shipping(self, request):
        sessionID = self.request.query_params.get('sessionID')
        shipping = ShippingAddress.objects.get(session_id=sessionID)
        shipping.deliveryDate = request.data['selected']
        shipping.save()
        return HttpResponse('date updated')
    
    @action(detail=False, methods=['put'])
    def route_protection(self, request):
        sessionID = self.request.data['sessionID']
        shipping = ShippingAddress.objects.get(session_id=sessionID)
        shipping.routeProtection = not(shipping.routeProtection)
        shipping.save()
        return HttpResponse(shipping.routeProtection)
    

class EmailsView(viewsets.ModelViewSet):
    queryset = CustomerEmail.objects.all()
    serializer_class = EmailSerializer

    def dispatch(self, *args, **kwargs):
        return super(EmailsView, self).dispatch(*args, **kwargs)
    
    @action(detail=False, methods=['post'])
    def add_email(self, request):
        try: 
            CustomerEmail.objects.get(email=request.data['email'])
            return HttpResponse("You're already subscribed to our newsletter.")

        except CustomerEmail.DoesNotExist:
            email = CustomerEmail.objects.create(
                email=request.data['email']
            )

            email.save()

        return HttpResponse('Thank you for subscribing to our newsletter!')
    

class ProductVariationView(viewsets.ModelViewSet):
    queryset = ProductVariation.objects.all()
    serializer_class = ProductVariationSerializer

    # @method_decorator(cache_page(CACHE_TTL))
    def dispatch(self, *args, **kwargs):
        return super(ProductVariationView, self).dispatch(*args, **kwargs)
    

    @action(detail=False, methods=['get'])
    def get_variation(self, request):
        product_id = self.request.query_params.get('productID')
        product = Products.objects.get(id=product_id)
        variations = ProductVariation.objects.filter(product=product)
        return Response({})
    

class StatesView(viewsets.ModelViewSet):
    queryset = States.objects.all()
    serializer_class = StateSerialzer

    # @method_decorator(cache_page(CACHE_TTL))
    def dispatch(self, *args, **kwargs):
        return super(StatesView, self).dispatch(*args, **kwargs)
