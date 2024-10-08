import json
import math
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from rest_framework import viewsets
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.core import mail
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from rest_framework.decorators import action
from django.core import serializers as serializer
from django.views.decorators.cache import cache_page
from .models import *
import environ
from .serializers import *  

env = environ.Env()
environ.Env.read_env()

CACHE_TTL = 60 * 60


def get_distance(state, lga):   

    geolocator = Nominatim(user_agent="nene", timeout=5)

    try:
        shop_location = geolocator.geocode("Jos North, Plateau")
    except:
        return None
    shop_lat, shop_lon = shop_location.latitude, shop_location.longitude

    # Geocode client address
    client_location = geolocator.geocode(f"{lga}, {state}")
    client_lat, client_lon= client_location.latitude,  client_location.longitude
   
    # Calculate distance
    distance = geodesic((shop_lat, shop_lon), (client_lat, client_lon)).km
    return math.ceil(distance * 15)


def filter_products(filter, queryset):

    if filter == 'desc':
        queryset = queryset.order_by('-unit_price')

    elif filter == 'asc':
        queryset = queryset.order_by('unit_price')

    return queryset

 
class ProductView(viewsets.ModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Products.objects.all()
        filter = self.request.query_params.get('filter_by')
        queryset = filter_products(filter, queryset)
        return queryset
    

    def dispatch(self, *args, **kwargs):
        return super(ProductView, self).dispatch(*args, **kwargs)
    

    @action(detail=False, methods=['get'])
    def get_product(self, request):
        parameter = self.request.query_params.get('pathname')
        filter = self.request.query_params.get('filter_by')
        product_type = ProductType.objects.get(parameter=parameter)
        queryset = queryset.filter(product_type=product_type)

        queryset = filter_products(filter, queryset)
        return queryset
    

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = self.request.query_params['query']
        matchedObjects = Products.objects.filter(name__icontains=query) 
        searchItems = [ProductSerializer(matchedObject).data for matchedObject in matchedObjects]

        return HttpResponse(
            json.dumps(
                searchItems)
            )

    

class ProductTypeView(viewsets.ModelViewSet):
    serializer_class = ProductTypeSerializer
    queryset = ProductType.objects.all()

    @method_decorator(cache_page(CACHE_TTL))
    def dispatch(self, *args, **kwargs):
        return super(ProductTypeView, self).dispatch(*args, **kwargs)
    


class CollectionView(viewsets.ModelViewSet):
    serializer_class = ProductSerializer

    @action(detail=False, methods=['get'])
    def get_queryset(self):
        queryset = Collection.objects.all()
        name = self.request.query_params.get('pathname')
        filter = self.request.query_params.get('filter_by')

        if name:
            collection = Collection.objects.get(name=name)
            queryset = Products.objects.filter(collection=collection)
        queryset = filter_products(filter, queryset)
        return queryset
   

    # @method_decorator(cache_page(CACHE_TTL))
    def dispatch(self, *args, **kwargs):
        return super(CollectionView, self).dispatch(*args, **kwargs)
    

class CartView(viewsets.ModelViewSet):

    serializer_class = CartItemSerializer
    queryset = Cartitem.objects.all()

    def dispatch(self, *args, **kwargs):
        return super(CartView, self).dispatch(*args, **kwargs)

 
    @action(detail=False, methods=['get'])
    def getCart(self, request):
        sessionid = self.request.query_params['sessionid']
        [cart, created] = Cart.objects.get_or_create(session_id=sessionid, ordered=False)
        Cartitem.objects.contains
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

        shipping = ShippingAddress.objects.get(session_id=sessionid)
        html_body = render_to_string("email-templates.html", {'order': cartitems, 
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

        try:
            address = ShippingAddress.objects.get(session_id=sessionID)
            serializer = ShippingSerializer(address).data
        except:
            return HttpResponse('none')
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
        print(request.data)
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
        variations = ProductVariation.objects.filter(product=product).values()
        for variation in variations:
            print(variation.keys())
        print('yes')
        return HttpResponse('yes')
    

class StatesView(viewsets.ModelViewSet):
    queryset = States.objects.all()
    serializer_class = StateSerialzer

    @method_decorator(cache_page(CACHE_TTL))
    def dispatch(self, *args, **kwargs):
        return super(StatesView, self).dispatch(*args, **kwargs)
