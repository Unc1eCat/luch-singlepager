from django.urls import path
from django.views.generic import TemplateView
import luch_app.views as v
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', v.HomeView.as_view(), name='home'),
    path("thanks/<str:order_pk>", TemplateView.as_view(template_name='luch_app/html/thanks_for_ordering.html'), name="thanks_for_ordering"),
    path('order/<str:pk>', v.OrderDetailsView.as_view(), name='order_details'),
    # path('orders/<email:email>', ..., name='orders_for_email'),
    path('email_test', TemplateView.as_view(template_name='luch_app/html/mail/verify_order.html'), kwargs={'base64_key': '38f9832hf8hj84324v3nr9n23v=='})
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
