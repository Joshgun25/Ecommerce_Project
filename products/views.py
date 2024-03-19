from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from rest_framework import status
from django.utils.decorators import method_decorator
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import redirect
from django.utils.http import urlsafe_base64_decode
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode 
from django.utils.encoding import force_bytes


from authentication.models import CustomUser
from .models import Product
from .forms import ProductForm
from .serializers import ProductSerializer, CommentSerializer


class ProductListView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'product_list.html'

    def get(self, request):
        products = Product.objects.filter(is_active=True)
        paginator = Paginator(products, 10) 

        page_number = request.GET.get('page')
        try:
            products_page = paginator.page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            products_page = paginator.page(1)
        except EmptyPage:
            products_page = paginator.page(paginator.num_pages)

        # Pass user authentication status to the renderer context
        user = not isinstance(get_user(request), AnonymousUser)
        return Response({'products': products_page, 'paginator': paginator, 'user': user})
    

class ProductDetailView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'product_detail.html'

    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            comments = product.comments.all().order_by('-created_at')[:10]
        except Product.DoesNotExist:
            raise Http404

        serializer = ProductSerializer(product)
        return Response({'product': serializer.data, 'comments': comments})


class CreateProductView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'product_create.html'

    def get(self, request):
        form = ProductForm()
        return Response({'form': form})

    def post(self, request):
        form = ProductForm(request.data, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            email = get_user(request)
            try:
                creator = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            product.creator = creator  # Set the creator as the current user
            product.is_active = True  # Set the product as active
            product.creator_email = creator.email   # Set the creator's email
            product.save()
            return redirect('product-list')

        return Response({'form': form}, status=status.HTTP_400_BAD_REQUEST)


class ActivateProductAPIView(APIView):
    def get(self, request, token):

        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product_id = urlsafe_base64_decode(token).decode()
            product = Product.objects.get(id=product_id)
        except (TypeError, ValueError, OverflowError, Product.DoesNotExist):
            return Response({'error': 'Invalid token or UID'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the product is already activated
        if product.is_active:
            messages.error(request, 'This product is already activated.')
            return redirect('product-list')

        # Validate the token
        token_generator = urlsafe_base64_encode(force_bytes(product.id))
        if token_generator != token:
            messages.error(request, 'Invalid activation link.')
            return redirect('product-list')
        
        # Check if the current user has access to activate
        if get_user(request) != product.creator:
            return redirect('product-list')
        else:
            # Activate the product
            product.is_active = True
            product.save()
            messages.success(request, 'Product activated successfully.')
            return redirect('product-list')
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    

class AddCommentAPIView(APIView):
    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            raise Http404

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product, user_email=get_user(request))
            return redirect('product-detail', pk=pk)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)