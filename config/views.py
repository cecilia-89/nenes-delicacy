import json
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from rest_framework import viewsets
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from .models import *
import environ
from .serializers import *  
import stripe

env = environ.Env()

CACHE_TTL = 60 * 60
stripe.api_key = env('STRIPE_TEST_API_KEY')


def email(request):
    cart = Cart.objects.get(session_id='499a29c8-4614-4952-958d-775eadeed8b0', ordered=False)
    cartitems = Cartitem.objects.filter(cart=cart)

    context={'order': cartitems}
    return render(request, 'email-templates.html', context)



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
    return distance * 15

  
@api_view(['POST'])
def payment(request):
 
    intent = stripe.PaymentIntent.create(
        amount=request.data['amount'],
        receipt_email=request.data['email'],
        shipping=request.data['shipping'],
        currency='ngn',
        payment_method_types = ["card"]
    )
    return HttpResponse(intent.client_secret)
    

class ProductView(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Products.objects.all()


    @method_decorator(cache_page(CACHE_TTL)) 
    def dispatch(self, *args, **kwargs):
        return super(ProductView, self).dispatch(*args, **kwargs)
    

class ProductTypeView(viewsets.ModelViewSet):
    serializer_class = ProductTypeSerializer
    queryset = ProductType.objects.all()

    @method_decorator(cache_page(CACHE_TTL))
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
        cart = Cart.objects.get(session_id=sessionid, ordered=False)
        query = Cartitem.objects.filter(cart=cart)

        total = sum([item.item.unit_price * item.quantity for item in query])
        return HttpResponse(
            {
                'cartitems': json.dumps(CartItemSerializer(query).data),
                'total': total
            })


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
        cart.ordered = True

        html_body = render_to_string("email-templates.html", {'order': cartitems})
        message = EmailMultiAlternatives(
        subject='Your Order Confirmation',
        body="",
        to=[self.request.query_params['email']]  
        )

        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)

        return HttpResponse('order confirmed')
    

class ShippingView(viewsets.ModelViewSet):
    serializer_class = ShippingSerializer
    queryset = ShippingAddress.objects.all()
         
    def dispatch(self, *args, **kwargs):
        return super(ShippingView, self).dispatch(*args, **kwargs)
    

    @action(detail=False, methods=['get'])
    def get_shipping(self, request):
        sessionID = self.request.query_params.get('sessionID')
        address = ShippingAddress.objects.get(session_id=sessionID)
        serializer = ShippingSerializer(address).data
        return HttpResponse(json.dumps(serializer))


    @action(detail=False, methods=['post'])
    def add_shipping(self, request):
        sessionID = self.request.query_params.get('sessionID')
        [shipping, created] = ShippingAddress.objects.get_or_create(session_id=sessionID)
        
        shipping.__dict__.update(request.data)
        distance = get_distance(request.data['lga'], request.data['state'])
        shipping.price = distance
        shipping.save()
        return HttpResponse('updated')
    
    
    @action(detail=False, methods=['put'])
    def update_shipping(self, request):
        sessionID = self.request.query_params.get('sessionID')
        shipping = ShippingAddress.objects.get(session_id=sessionID)
        shipping.deliveryDate = request.data['selected']
        shipping.save()
        return HttpResponse('date updated')

    
    
class ToppingView(viewsets.ModelViewSet):
    queryset = Topping.objects.all()
    serializer_class = ToppingSerializer


class SizeView(viewsets.ModelViewSet):
    queryset = Sizes.objects.all()
    serializer_class = ToppingSerializer

    @method_decorator(cache_page(CACHE_TTL))
    def dispatch(self, *args, **kwargs):
        return super(SizeView, self).dispatch(*args, **kwargs)


class IcingView(viewsets.ModelViewSet):
    queryset = Icing.objects.all()
    serializer_class = ToppingSerializer


class StatesView(viewsets.ModelViewSet):
    queryset = States.objects.all()
    serializer_class = StateSerialzer

    @method_decorator(cache_page(CACHE_TTL))
    def dispatch(self, *args, **kwargs):
        return super(StatesView, self).dispatch(*args, **kwargs)
