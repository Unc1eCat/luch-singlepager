from itertools import accumulate
from typing import *
from django import forms as f
from luch_app import models as m


class LabelToPlaceholderMixin(f.Form):
    def __init__(self,*args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for i in self.fields.values():
            i: f.Field
            if i.label:
                i.widget.attrs['placeholder'] = i.label
                i.label = ''

class FilledMinimumTogetherMixin(f.Form):
    @staticmethod
    def _filled_fields_accumulator(acc, e):
        if e:
            return acc + 1
        else:
            return acc

    def clean(self):
        cleaned_data = super().clean()

        try:
            conf = self.Meta.minimum_filled_together
        except AttributeError:
            return cleaned_data

        for fields, count in conf:
            relevant_fields = {k: v for k, v in cleaned_data if k in fields}
            if accumulate(relevant_fields.values(), FilledMinimumTogetherMixin._filled_fields_accumulator, 0) < count:
                self.add_error(None, f.ValidationError(f'At least {count} of fields {fields} must be filled.',
                               'filled-minimum-together', {'relevant_fields': relevant_fields}))
                for i in relevant_fields:
                    del cleaned_data[i]

        return cleaned_data


class GetOrderForm(f.Form):
    ''' Validates if the provided key authorizes to access the provided order. '''
    vkey = f.CharField(max_length=32, validators=(m.VKEY_VALIDATOR,))
    order = f.IntegerField(min_value=0)

    def clean_order(self):
        obj = m.Order.objects.get(pk_exact=self.cleaned_data['order'])
        if not obj.is_email_verified:
            raise f.ValidationError("Tried accessing order which has unverified email.")
        return obj

    def clean_vkey(self):
        obj = m.VerificationKey.objects.get(key_iexact=self.cleaned_data['vkey'])
        if not obj.is_valid:
            raise f.ValidationError("Invalid or expired verification key.")
        print("ASDDDDDDDDDDDDDDDDDDDDD")
        return obj

    def clean(self):
        super().clean()

        if self.cleaned_data['vkey'].email != self.cleaned_data['order'].email:
            raise f.ValidationError('Invalid or expired verification key.')
        else:
            return self.cleaned_data


class FindOrderForm(f.Form):
    """ Takes email or pk and puts corresponding order objects in `cleaned_data` with key `orders`. """
    email = f.EmailField()
    order = f.IntegerField(min_value=0, required=True)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('email') and cleaned_data.get('order'):
            raise f.ValidationError('Must provide only one: email or order ID. Can\'t provide both or none.')
        elif cleaned_data.get('email'):
            order_objs = m.Order.objects.filter(email__iexact=self.data['email'])
            cleaned_data['order'] = order_objs
        elif cleaned_data.get('order'):
            order_objs = m.Order.objects.filter(pk__exact=self.data['order'])
            cleaned_data['order'] = order_objs
        else:
            raise f.ValidationError('Must provide email or order ID.')

        cleaned_data['orders'] = order_objs

        return cleaned_data


class OrderNowForm(LabelToPlaceholderMixin, f.Form):
    email = f.EmailField(label='Электронная почта')
    phone_number = f.RegexField(r'^\+?\d{5,15}$', label='Номер телефона', error_messages={'invalid': 'Введите правильный номер телефона'})
    first_name = f.CharField(max_length=30, label='Имя')
    last_name = f.CharField(max_length=30, label='Фамилия')
