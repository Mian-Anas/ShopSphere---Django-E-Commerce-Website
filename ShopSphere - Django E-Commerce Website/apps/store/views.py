"""
Store Views — Home, Shop, Product Detail, Search API, Review.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST

from .models import Category, Brand, Product, ProductImage, Review
from .forms import ReviewForm
from apps.orders.models import OrderItem


def home_view(request):
    featured_products = Product.objects.filter(
        is_active=True, is_featured=True
    ).select_related('category', 'brand').prefetch_related('images')[:8]

    latest_products = Product.objects.filter(
        is_active=True
    ).select_related('category', 'brand').prefetch_related('images').order_by('-created_at')[:8]

    categories = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('children')[:6]

    context = {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
    }
    return render(request, 'store/home.html', context)


def shop_view(request):
    products = Product.objects.filter(is_active=True).select_related(
        'category', 'brand'
    ).prefetch_related('images')

    # Search
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(brand__name__icontains=query)
        )

    # Category filter
    category_slug = request.GET.get('category', '')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        # Include subcategory products
        cat_ids = [selected_category.pk] + list(
            selected_category.children.values_list('pk', flat=True)
        )
        products = products.filter(category__pk__in=cat_ids)

    # Brand filter
    brand_slug = request.GET.get('brand', '')
    selected_brand = None
    if brand_slug:
        selected_brand = get_object_or_404(Brand, slug=brand_slug)
        products = products.filter(brand=selected_brand)

    # Price range filter
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Sorting
    sort = request.GET.get('sort', '-created_at')
    sort_map = {
        'price_asc': 'price',
        'price_desc': '-price',
        'name_asc': 'name',
        'newest': '-created_at',
        'featured': '-is_featured',
    }
    products = products.order_by(sort_map.get(sort, '-created_at'))

    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    categories = Category.objects.filter(is_active=True, parent__isnull=True)
    brands = Brand.objects.filter(is_active=True)

    context = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': categories,
        'brands': brands,
        'query': query,
        'selected_category': selected_category,
        'selected_brand': selected_brand,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
        'total_count': paginator.count,
    }
    return render(request, 'store/shop.html', context)


def product_detail_view(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand').prefetch_related('images', 'reviews__user'),
        slug=slug, is_active=True
    )

    images = product.images.all()
    reviews = product.reviews.filter(is_approved=True).select_related('user').order_by('-created_at')
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    # Check if user is a verified buyer (has ordered this product)
    user_has_purchased = False
    user_review = None
    review_form = None

    if request.user.is_authenticated:
        user_has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__status__in=['paid', 'shipped', 'delivered'],
            product=product
        ).exists()
        user_review = reviews.filter(user=request.user).first()
        if not user_review:
            review_form = ReviewForm()

    # Related products (same category, exclude current)
    related_products = Product.objects.filter(
        is_active=True, category=product.category
    ).exclude(pk=product.pk).select_related('brand').prefetch_related('images')[:4]

    context = {
        'product': product,
        'images': images,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'user_has_purchased': user_has_purchased,
        'user_review': user_review,
        'review_form': review_form,
        'related_products': related_products,
        'star_range': range(1, 6),
    }
    return render(request, 'store/product_detail.html', context)


@login_required
@require_POST
def submit_review_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)

    # Only verified buyers can review
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__status__in=['paid', 'shipped', 'delivered'],
        product=product
    ).exists()

    if not has_purchased:
        messages.error(request, 'You must purchase this product before leaving a review.')
        return redirect('store:product_detail', slug=slug)

    # Prevent duplicate reviews
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, 'You have already reviewed this product.')
        return redirect('store:product_detail', slug=slug)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        messages.success(request, 'Your review has been submitted and is pending approval.')
    else:
        messages.error(request, 'Please correct the errors in your review.')

    return redirect('store:product_detail', slug=slug)


def search_api_view(request):
    """Live search autocomplete endpoint returning JSON."""
    q = request.GET.get('q', '').strip()
    results = []
    if len(q) >= 2:
        products = Product.objects.filter(
            is_active=True,
            name__icontains=q
        ).select_related('category').prefetch_related('images')[:8]

        for product in products:
            img = product.get_primary_image()
            results.append({
                'id': product.pk,
                'name': product.name,
                'price': str(product.get_effective_price()),
                'url': product.get_absolute_url(),
                'image': img.image.url if img else '',
                'category': product.category.name if product.category else '',
            })
    return JsonResponse({'results': results})
