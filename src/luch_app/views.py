from re import sub
from typing import *

from django.core.mail import send_mail
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.views.generic.base import TemplateResponseMixin, View
from django.urls import reverse
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from base64 import urlsafe_b64encode

import luch_app.forms as f
import luch_app.models as m


def send_verification_mail(to_email: Sequence[str], key: bytes, from_email: str = None):
    ctx = {'base64_key': urlsafe_b64encode(key)}
    text_body = get_template('luch_app/mail/verify_order.txt').render(ctx)
    html_body = get_template('luch_app/mail/verify_order.html').render(ctx)
    msg = EmailMultiAlternatives(subject='Подтверждения заказа от Луч', from_email=from_email,
                                 to=to_email, body=text_body, alternatives=((html_body, 'text/html'),))
    msg.send()


class ForbidSlugOnSingleObjectMixin:
    def get_slug_field(self):
        raise NotImplementedError(f'{self} has `ForbidSlugSingleObjectMixin` but tried calling `get_slug_field` on it.')


class OrderAccessKeyMixin:
    def check_and_bind_key(self, email):
        ''' Checks if the request is authenticated with the email (i.e. it can access orders of the email). And also binds the key to the session. '''
        try:
            access_url_obj = m.OrderAccessKey.objects.get(pk=self.kwargs['key'])
        except m.OrderAccessKey.DoesNotExist() | m.OrderAccessKey.MultipleObjectsReturned:
            return False
        if access_url_obj.is_valid:
            if access_url_obj.session is None:
                access_url_obj.session = self.session
                return True
            else:
                return access_url_obj.session == self.request.session
        else:
            return False


class OrderDetailsView(OrderAccessKeyMixin, ForbidSlugOnSingleObjectMixin, TemplateResponseMixin, SingleObjectMixin, View):
    template_name = 'luch_app/html/order.html'
    model = m.Order
    context_object_name = 'orders'

    # This is for getting order details page.
    def get(self, request: HttpRequest):
        order_obj: m.Order = self.get_object()
        if not order_obj.is_email_verified:
            raise PermissionDenied('Tried accessing order which has an unverified email.')
        if not self.check_and_bind_key(order_obj.email):
            raise PermissionDenied('Invalid access key.')
        self.object = (order_obj,)
        return self.render_to_response(self.get_context_data())


class HomeView(FormView):
    form_class = f.OrderNowForm
    template_name = 'luch_app/html/home.html'
    prefix = 'order-now'

    def get_success_url(self) -> str:
        return reverse('thanks_for_ordering', args=(self.object.pk,))

    def form_valid(self, form: Any) -> HttpResponse:
        self.object = m.Order.objects.create(email=form.cleaned_data['email'], phone_number=form.cleaned_data['phone_number'], first_name=form.cleaned_data['first_name'], last_name=form.cleaned_data['last_name'])
        access_key_obj = m.OrderAccessKey.objects.create(email=self.object.email)
        send_verification_mail((self.object.email,), access_key_obj.key)
        return super().form_valid(form)


class OrdersByEmailView(OrderAccessKeyMixin, TemplateResponseMixin, View):
    template_name = 'luch_app/html/order.html'

    def get(self, request: HttpRequest, email):
        if not self.check_and_bind_key(email):
            raise PermissionDenied('Invalid key.')
        order_objs: Iterable[m.Order] = (i for i in m.Order.objects.filter(email__iexact=email) if i.is_email_verified)
        return self.render_to_response({'orders': order_objs})
