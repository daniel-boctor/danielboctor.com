from django import forms
from .models import User, Portfolio, RetsCSV
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms import BaseFormSet
from django.contrib.auth.forms import UserCreationForm

class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(MyUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs = {'class': 'form-control', 'placeholder':'Username'}
        self.fields['email'] = forms.EmailField(max_length=64, required=True, help_text='Required. Enter a valid email address.', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Email'}))
        self.fields['password1'].widget.attrs = {'class': 'form-control', 'placeholder':'Password'}
        self.fields['password2'].widget.attrs = {'class': 'form-control', 'placeholder':'Password Confirmation'}

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')
    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs = {'class': 'form-control', 'placeholder':'Username'}
        self.fields['email'].widget.attrs = {'class': 'form-control', 'placeholder':'Email'}

class MetaForm(forms.Form):
    granularity_choices = (
    ('1mo', 'Monthly'),
    ('1d', 'Daily')
    )
    cpi_choices = (
    ("None", 'Off'),
    ('CPALTT01USM657N', 'US CPI'),
    ('CPALCY01CAM661N', 'Canadian CPI')
    )
    fx_choices = (
    ("None", 'Off'),
    ('usd', 'USD Terms'),
    ('cad', 'CAD Terms')
    )
    portfolio_choices = (
    ('formset_block', 'Portfolios'),
    ('tickerform_block', 'Securities')
    )
    type = forms.ChoiceField(choices=portfolio_choices, initial="formset_block", widget=forms.Select(attrs={'class':'form-select'}))
    granularity = forms.ChoiceField(choices=granularity_choices, initial="1mo", widget=forms.Select(attrs={'class':'form-select'}))
    inflation_adj = forms.ChoiceField(choices=cpi_choices, initial="None", widget=forms.Select(attrs={'class':'form-select'}))
    currency_adj = forms.ChoiceField(choices=fx_choices, initial="None", widget=forms.Select(attrs={'class':'form-select'}))
    datestamp_start = forms.DateField(label="Start date", required=False, widget=forms.DateInput(attrs={'class':'form-control', 'type':'month', 'placeholder':'YYYY-MM'}))
    datestamp_end = forms.DateField(label="End date", required=False, widget=forms.DateInput(attrs={'class':'form-control', 'type':'month', 'placeholder':'YYYY-MM'}))

    def __init__(self, *args, **kwargs):
        template = kwargs.pop('template', None)
        super(MetaForm, self).__init__(*args, **kwargs)
        if template == "backtest":
            self.fields['initial_wealth'] = forms.IntegerField(required=False, validators=[MinValueValidator(1), MaxValueValidator(1000000000)], widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': '10,000'}))
        if template == "rolling":
            roll_period = (('12', '1 Year'), ('36', '3 Years'), ('60', '5 Years'), ('84', '7 Years'), ('120', '10 Years'))
            self.fields['roll_window'] = forms.ChoiceField(choices=roll_period, initial="12", widget=forms.Select(attrs={'class':'form-select'}))
        if template == "factors":
            self.fields.pop('inflation_adj')
            self.fields.pop('currency_adj')
            factor_model = (
                ('F-F_Research_Data_Factors', 'FF US 3 Factor Model'),
                ('F-F_Research_Data_5_Factors_2x3', 'FF US 5 Factor Model'),
                ('F-F_Momentum_Factor', 'FF US 5 Factor Model + Mom'),
                ('Developed_3_Factors', 'FF Developed 3 Factor Model'),
                ('Developed_5_Factors', 'FF Developed 5 Factor Model'),
                ('Developed_Mom_Factor', 'FF Developed 5 Factor Model + Mom'),
                ('Emerging_5_Factors', 'FF Emerging 5 Factor Model'),
                ('Emerging_MOM_Factor', 'FF Emerging 5 Factor Model + Mom')
            )
            rolling_regression = (('False', 'Off'), ('12', '1 Year'), ('36', '3 Years'), ('60', '5 Years'), ('84', '7 Years'), ('120', '10 Years'))
            self.fields['factor_model'] = forms.ChoiceField(choices=factor_model, initial="F-F_Research_Data_5_Factors_2x3", widget=forms.Select(attrs={'class':'form-select'}))
            self.fields['granularity'] = forms.ChoiceField(choices=(('1mo', 'Monthly'),), initial="1mo", widget=forms.Select(attrs={'class':'form-select'}))
            self.fields['rolling_regression'] = forms.ChoiceField(choices=rolling_regression, widget=forms.Select(attrs={'class':'form-select'}))    

    def clean(self):
        cleaned_data = super().clean()
        datestamp_start = cleaned_data.get("datestamp_start") 
        datestamp_end = cleaned_data.get("datestamp_end")
        if datestamp_start and datestamp_end:
            # Only do something if both fields are valid so far.
            if datestamp_start > datestamp_end:
                raise ValidationError("Start date was greater than the end date.")

class TickerForm(forms.Form):
    ticker1 = forms.CharField(max_length=8, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Ticker'}))
    
    def __init__(self, *args, **kwargs):
        super(TickerForm, self).__init__(*args, **kwargs)
        for i in range(2, 9):
            self.fields['ticker' + str(i)] = forms.CharField(max_length=8, required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Ticker'}))
        
    def clean(self):
        cleaned_data = super().clean()
        for k, v in cleaned_data.items():
            if v:
                cleaned_data[k] = v.upper()
        return cleaned_data

class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        exclude = ('user',)
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control', 'placeholder':'Portfolio name'}),
        }
        for i in range(1, (len(model._meta.get_fields())-2)//2+1):
            widgets[f"ticker{i}"] = forms.TextInput(attrs={'class':'form-control', 'placeholder':'Ticker'})
            widgets[f"weight{i}"] = forms.TextInput(attrs={'class':'form-control', 'placeholder':'%'}) 
    
    def clean(self):
        cleaned_data = super().clean()
        ticker = []
        weight = []
        for k, v in cleaned_data.items():
            if v:
                if "ticker" in k:
                    cleaned_data[k] = v.upper()
                    ticker.append(v.upper())
                if "weight" in k:
                    weight.append(v)
        if len(ticker) != len(set(ticker)):
            raise ValidationError("Duplicate tickers entered.")
        if sum(weight) != 100:
            raise ValidationError("Weights do not sum to 100%.")
        if len(ticker) != len(weight):
            raise ValidationError("Mismatch between number of tickers and weights.")

class BasePortfolioFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return
        names = []
        count = 1
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            name = form.cleaned_data.get('name')
            if name in names:
                form.cleaned_data["name"] = f"{name} {count}"
            names.append(name)
            if not form.cleaned_data["name"]:
                form.cleaned_data["name"] = f"Portfolio {count}"
            count += 1

class RetsCSVForm(forms.ModelForm):
    class Meta:
        model = RetsCSV
        exclude = ('user',)
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control', 'placeholder':'Portfolio name'}),
        }
