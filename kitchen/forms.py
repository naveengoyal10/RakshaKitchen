from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

from .models import CustomerInquiry, Order, OrderInquiry


class CustomerInquiryForm(forms.ModelForm):
    class Meta:
        model = CustomerInquiry
        fields = ("name", "mobile", "email", "event_type", "event_date", "number_of_people", "food_requirements", "budget", "address", "additional_notes")
        widgets = {
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "food_requirements": forms.Textarea(attrs={"rows": 4, "placeholder": "Tell us about the dishes, dietary needs, or menu ideas."}),
            "additional_notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "mobile": "Mobile number",
            "event_type": "What are you celebrating?",
            "event_date": "Event date",
            "number_of_people": "Number of people",
            "food_requirements": "Food requirements",
            "additional_notes": "Additional notes",
        }

    def clean_mobile(self):
        mobile = self.cleaned_data["mobile"].strip()
        digits = "".join(character for character in mobile if character.isdigit())
        if not 10 <= len(digits) <= 15 or not mobile.replace("+", "").replace(" ", "").replace("-", "").isdigit():
            raise forms.ValidationError("Enter a valid mobile number.")
        return mobile

    def clean_event_date(self):
        event_date = self.cleaned_data["event_date"]
        if event_date < timezone.localdate():
            raise forms.ValidationError("Event date cannot be in the past.")
        return event_date

    def clean_number_of_people(self):
        number = self.cleaned_data["number_of_people"]
        if not 1 <= number <= 10000:
            raise forms.ValidationError("Enter a number between 1 and 10,000.")
        return number


class OrderForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email address")
    cart_data = forms.CharField(required=False, max_length=10000, widget=forms.HiddenInput())
    submission_token = forms.UUIDField(required=True, widget=forms.HiddenInput())

    class Meta:
        model = Order
        fields = ("customer_name", "mobile", "email", "address", "building_society", "flat_number", "preferred_date", "preferred_time", "order_type", "notes", "cart_data")
        widgets = {
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "preferred_time": forms.TimeInput(attrs={"type": "time"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "customer_name": "Full name",
            "mobile": "Mobile number",
            "address": "Street / area",
            "building_society": "Building / society",
            "flat_number": "Flat / apartment number",
            "preferred_date": "Preferred date",
            "preferred_time": "Preferred time",
            "order_type": "Delivery or pickup",
            "notes": "Additional instructions",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["building_society"].required = True
        self.fields["flat_number"].required = True
        self.fields["preferred_date"].required = True
        self.fields["preferred_time"].required = True

    def clean_mobile(self):
        mobile = self.cleaned_data["mobile"].strip()
        digits = "".join(character for character in mobile if character.isdigit())
        if not 10 <= len(digits) <= 15 or not mobile.replace("+", "").replace(" ", "").replace("-", "").isdigit():
            raise forms.ValidationError("Enter a valid mobile number.")
        return mobile

    def clean_preferred_date(self):
        preferred_date = self.cleaned_data.get("preferred_date")
        if preferred_date and preferred_date < timezone.localdate():
            raise forms.ValidationError("Preferred date cannot be in the past.")
        return preferred_date

    def clean(self):
        cleaned_data = super().clean()
        preferred_date = cleaned_data.get("preferred_date")
        preferred_time = cleaned_data.get("preferred_time")
        if preferred_date and preferred_time:
            requested_delivery = timezone.make_aware(
                datetime.combine(preferred_date, preferred_time),
                timezone.get_current_timezone(),
            )
            if requested_delivery < timezone.now() + timedelta(hours=4):
                self.add_error("preferred_time", "Orders must be scheduled at least 4 hours in advance.")
        return cleaned_data


class OrderInquiryForm(forms.ModelForm):
    selected_items = forms.CharField(required=False, max_length=4000, widget=forms.HiddenInput())

    class Meta:
        model = OrderInquiry
        fields = ("name", "phone", "email", "address", "event_date", "preferred_time", "fulfillment_method", "servings", "message", "selected_items")
        widgets = {
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "preferred_time": forms.TimeInput(attrs={"type": "time"}),
            "message": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "phone": "Mobile number",
            "event_date": "Preferred date",
            "preferred_time": "Preferred delivery / pickup time",
            "fulfillment_method": "Delivery or pickup",
            "servings": "Number of servings",
            "message": "Additional instructions",
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not phone.replace("+", "").replace(" ", "").replace("-", "").isdigit():
            raise forms.ValidationError("Enter a valid mobile number.")
        digits = "".join(character for character in phone if character.isdigit())
        if not 10 <= len(digits) <= 15:
            raise forms.ValidationError("Enter a valid mobile number.")
        return phone

    def clean_event_date(self):
        event_date = self.cleaned_data.get("event_date")
        if event_date and event_date < timezone.localdate():
            raise forms.ValidationError("Preferred date cannot be in the past.")
        return event_date

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) > 3000:
            raise forms.ValidationError("Additional instructions are too long.")
        return message
