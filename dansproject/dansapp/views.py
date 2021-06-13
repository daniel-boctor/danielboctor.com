from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from .models import User, Portfolio
from django.contrib.auth.decorators import login_required
from .forms import MyUserCreationForm, UserUpdateForm, MetaForm, PortfolioForm, TickerForm, BasePortfolioFormSet
from django.forms import modelformset_factory
import pandas as pd
from pandas_datareader import data as pdr
from .financelib import *

pd.options.plotting.backend = "plotly"

# Create your views here.

def index(request):
    return render(request, "dansapp/index.html")

def register(request):
    if request.method == "POST":
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            messages.success(request, f"Account created for {username}", extra_tags="Success!")
            return HttpResponseRedirect(reverse("index"))
    else:
        form = MyUserCreationForm()
    return render(request, "dansapp/user/register.html", {"form": form})

@login_required
def user(request, username):
    if request.user.username == username:
        if request.method == "POST":
            form = UserUpdateForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, f"Info saved.", extra_tags="Success!")
                return HttpResponseRedirect(reverse("user", args=[request.user.username]))
        else:
            form = UserUpdateForm(instance=request.user)
        return render(request, "dansapp/user/user.html", {"form": form})

@login_required
def portfolios(request, username):
    if request.user.username == username:
        from django.forms import modelformset_factory
        PortfolioFormSet = modelformset_factory(Portfolio, form=PortfolioForm, extra=1, max_num=20, absolute_max=20, can_delete=True)

        if request.method == "GET":
            return render(request, "dansapp/user/portfolios.html", {
                "formset": PortfolioFormSet(queryset=Portfolio.objects.filter(user=request.user))
            })

        if request.method == "POST":
            portfolioformset = PortfolioFormSet(request.POST)
            if portfolioformset.is_valid():
                instances = portfolioformset.save(commit=False)
                for obj in portfolioformset.deleted_objects:
                    obj.delete()
                    messages.success(request, f"{obj.name} was successfully deleted.", extra_tags="Success!")
                for instance in instances:
                    if Portfolio.objects.filter(user=request.user, name=instance.name).exists():
                        if Portfolio.objects.get(user=request.user, name=instance.name).id != instance.id:
                            messages.error(request, f"Portfolio named {instance.name} already exisits.", extra_tags="Error!")
                            continue
                    #non duplicate
                    if not instance.name:
                        messages.error(request, f"No name entered.", extra_tags="Error!")
                        continue
                    tickers = []
                    for fieldname in instance._meta.get_fields():
                        if "ticker" in fieldname.name:
                            if getattr(instance, fieldname.name):
                                tickers.append(getattr(instance, fieldname.name))
                    df = generate_return_series(tickers)   
                    invalid_tickers = False     
                    if not isinstance(df, pd.DataFrame):
                        for error in df:
                            messages.error(request, f"Invalid ticker entered: {error}", extra_tags="Error!")
                            invalid_tickers = True
                    if invalid_tickers:
                        continue
                    instance.user = request.user
                    instance.save()
                    messages.success(request, f"{instance.name} was successfully saved.", extra_tags="Success!")
            for form in portfolioformset:
                for error in form.non_field_errors():
                    messages.error(request, f"{error}", extra_tags="Validation error:")
                for field in form:
                    for error in field.errors:
                        messages.error(request, f"{error}", extra_tags=f"{field.label}")
            return render(request, "dansapp/user/portfolios.html", {
                "formset": PortfolioFormSet(queryset=Portfolio.objects.filter(user=request.user))
            })

def faq(request):
    return render(request, "dansapp/faq.html")

def portfolio_api(request, name):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    return JsonResponse({k: v for k, v in Portfolio.objects.filter(user=request.user, name=name).values()[0].items() if v is not None and not k in ["id", "user_id"]})

def backtest(request):
    PortfolioFormSet = modelformset_factory(Portfolio, form=PortfolioForm, formset=BasePortfolioFormSet, extra=1, max_num=5, absolute_max=5)
    saved = []
    if request.user.is_authenticated:
        saved = Portfolio.objects.filter(user=request.user).values_list("name", flat=True)
    if request.method == "GET":
        return render(request, "dansapp/backtest.html", {
            "form": MetaForm(wealth=True),
            "formset": PortfolioFormSet(),
            "tickerform": TickerForm,
            "saved": saved
    })

    if request.method == "POST":
        formset = PortfolioFormSet(request.POST)
        tickerform = TickerForm(request.POST)
        #append a "-01" onto the datestamp if granularity == 1mo
        updated_request = request.POST.copy()
        if updated_request["granularity"] == "1mo":
            if updated_request["datestamp_start"]:
                updated_request.update({'datestamp_start': updated_request["datestamp_start"] + "-01"})
            if updated_request["datestamp_end"]:
                updated_request.update({'datestamp_end': updated_request["datestamp_end"] + "-01"})
        form = MetaForm(updated_request, wealth=True)
        if not form.is_valid():
            return render(request, "dansapp/backtest.html", {
                "form": form,
                "formset": formset,
                "tickerform": tickerform,
                "saved": saved
            })
        if not form.cleaned_data["initial_wealth"]:
            form.cleaned_data["initial_wealth"] = 10000

        return_vals = create_master_dataframe(request, form, formset, tickerform)
        if not return_vals:
            return render(request, "dansapp/backtest.html", {
            "form": form,
            "formset": formset,
            "tickerform": tickerform,
            "saved": saved
        })
        master_dataframe, periods_per_year, variable = return_vals

    #PLOTTING AND STATS
    graph = form.cleaned_data["initial_wealth"]*(master_dataframe+1).cumprod()
    graph.index = graph.index.astype(str)
    fig = graph.plot(template="simple_white", labels=dict(index="Date", value="Balance", variable=variable))
    fig.update_layout(legend=dict(y=0.99 ,x=0.01), 
        legend_title_text = variable,
        margin = dict(l=0, r=0),
        hovermode = "x unified"
    )
    graph = fig.to_html(full_html=False, include_plotlyjs="cdn")
    range = sample_date_range(master_dataframe)
    summary = summary_stats(master_dataframe, periods_per_year=periods_per_year) 
    key = key_stats(master_dataframe, periods_per_year=periods_per_year) 
    horse = horserace(master_dataframe, wealth=form.cleaned_data["initial_wealth"]) 
    return render(request, "dansapp/backtest.html", {
        "form": form,
        "formset": formset,
        "tickerform": tickerform,
        "saved": saved,
        "range": range,
        "summary_stats": summary.to_html(classes=["table table-hover table-fit"], border=0,  justify="unset"),
        "key_stats": key.to_html(classes=["table table-hover table-fit"], border=0,  justify="unset"),
        "horserace": horse.to_html(classes=["table table-hover table-fit"], border=0,  justify="unset"),
        "graph": graph
    })

def rolling(request):
    PortfolioFormSet = modelformset_factory(Portfolio, form=PortfolioForm, formset=BasePortfolioFormSet, extra=1, max_num=5, absolute_max=5)
    saved = []
    if request.user.is_authenticated:
        saved = Portfolio.objects.filter(user=request.user).values_list("name", flat=True)
    if request.method == "GET":
        return render(request, "dansapp/rolling.html", {
            "form": MetaForm(rolling=True),
            "formset": PortfolioFormSet(),
            "tickerform": TickerForm,
            "saved": saved
    })

    if request.method == "POST":
        formset = PortfolioFormSet(request.POST)
        tickerform = TickerForm(request.POST)
        #append a "-01" onto the datestamp if granularity == 1mo
        updated_request = request.POST.copy()
        if updated_request["granularity"] == "1mo":
            if updated_request["datestamp_start"]:
                updated_request.update({'datestamp_start': updated_request["datestamp_start"] + "-01"})
            if updated_request["datestamp_end"]:
                updated_request.update({'datestamp_end': updated_request["datestamp_end"] + "-01"})
        form = MetaForm(updated_request, rolling=True)
        if not form.is_valid():
            return render(request, "dansapp/rolling.html", {
                "form": form,
                "formset": formset,
                "tickerform": tickerform,
                "saved": saved
            })

        return_vals = create_master_dataframe(request, form, formset, tickerform)
        if not return_vals:
            return render(request, "dansapp/rolling.html", {
                "form": form,
                "formset": formset,
                "tickerform": tickerform,
                "saved": saved
            })
        master_dataframe, periods_per_year, variable = return_vals
        if periods_per_year == 12:
            roll_window = int(form.cleaned_data["roll_window"])
        else:
            roll_window = (int(form.cleaned_data["roll_window"]) // 12) * 253

        #PLOTTING AND STATS
        rolling = rolling_rets(master_dataframe, roll_window=roll_window, periods_per_year=periods_per_year)
        if not isinstance(rolling, pd.DataFrame):
            messages.error(request, f"Not enough data available for the selected roll window ({roll_window} {'Months' if periods_per_year==12 else 'Days'}).", extra_tags="Error!")
            return render(request, "dansapp/rolling.html", {
                "form": form,
                "formset": formset,
                "tickerform": tickerform,
                "saved": saved
            })
        stats = rolling_stats(rolling)

        rolling.index = rolling.index.astype(str)
        fig = rolling.plot(template="simple_white", labels=dict(index="Date", value="Annualized Return", variable=variable))
        fig.update_layout(legend=dict(y=0.99 ,x=0.01), 
            legend_title_text = variable,
            margin = dict(l=0, r=0),
            hovermode = "x unified",
            title = f"Annualized Rolling Returns ({roll_window} {'Months' if periods_per_year==12 else 'Days'})"
        )
        graph = fig.to_html(full_html=False, include_plotlyjs="cdn")
        range = sample_date_range(master_dataframe)
        return render(request, "dansapp/rolling.html", {
            "form": form,
            "formset": formset,
            "tickerform": tickerform,
            "saved": saved,
            "range": range,
            "stats": stats.to_html(classes=["table table-hover table-fit"], border=0,  justify="unset"),
            "graph": graph
        })

def factors(request):
    PortfolioFormSet = modelformset_factory(Portfolio, form=PortfolioForm, formset=BasePortfolioFormSet, extra=1, max_num=5, absolute_max=5)
    saved = []
    if request.user.is_authenticated:
        saved = Portfolio.objects.filter(user=request.user).values_list("name", flat=True)
    if request.method == "GET":
        return render(request, "dansapp/factors.html", {
            "form": MetaForm(factors=True),
            "formset": PortfolioFormSet(),
            "tickerform": TickerForm,
            "saved": saved
    })

    if request.method == "POST":
        formset = PortfolioFormSet(request.POST)
        tickerform = TickerForm(request.POST)
        #append a "-01" onto the datestamp if granularity == 1mo
        updated_request = request.POST.copy()
        if updated_request["granularity"] == "1mo":
            if updated_request["datestamp_start"]:
                updated_request.update({'datestamp_start': updated_request["datestamp_start"] + "-01"})
            if updated_request["datestamp_end"]:
                updated_request.update({'datestamp_end': updated_request["datestamp_end"] + "-01"})
        form = MetaForm(updated_request, factors=True)
        if not form.is_valid():
            return render(request, "dansapp/factors.html", {
                "form": form,
                "formset": formset,
                "tickerform": tickerform,
                "saved": saved
            })

        return_vals = create_master_dataframe(request, form, formset, tickerform)
        if not return_vals:
            return render(request, "dansapp/factors.html", {
                "form": form,
                "formset": formset,
                "tickerform": tickerform,
                "saved": saved
            })
        master_dataframe, periods_per_year, variable = return_vals

        #PLOTTING AND STATS
        factor_model = pdr.DataReader(form.cleaned_data["factor_model"], 'famafrench', start="1926")[0]/100
        factor_num = "5" if "5" in form.cleaned_data['factor_model'] else "3"
        geo = "Developed" if "Developed" in form.cleaned_data['factor_model'] else "US"
        if "Emerging" in form.cleaned_data['factor_model']:
            geo = "Emerging"
        range = sample_date_range(master_dataframe)
        if factor_model.shape[1] == 1:
            if geo == "Developed":
                five_factor = "Developed_5_Factors"
            elif geo == "Emerging":
                five_factor = "Emerging_5_Factors"
            else:
                five_factor = "F-F_Research_Data_5_Factors_2x3"
            factor_num = "5 + Mom"
            mom = factor_model
            factor_model = pdr.DataReader(five_factor, 'famafrench', start="1926")[0]/100
            mom = mom[factor_model.index.values[0]:factor_model.index.values[-1]]
            factor_model = factor_model[mom.index.values[0]:mom.index.values[-1]]
            factor_model.insert(loc=5, column="Mom", value=mom[mom.columns.values[0]])

        title = f"Fama French {geo} {factor_num} Factor Regression"
        factor_loadings = factor_regression(master_dataframe, factor_model)
        
        graphs = None
        if form.cleaned_data['rolling_regression'] != "False":
            graphs = []
            for col in master_dataframe:
                rolling = rolling_regression(pd.DataFrame(master_dataframe[col]), factor_model, roll_window=int(form.cleaned_data['rolling_regression']))
                if not isinstance(rolling, pd.DataFrame):
                    messages.error(request, f"Not enough data available for the selected roll window ({form.cleaned_data['rolling_regression']} {'Months' if periods_per_year==12 else 'Days'}).", extra_tags="Error!")
                    return render(request, "dansapp/factors.html", {
                        "form": form,
                        "formset": formset,
                        "tickerform": tickerform,
                        "saved": saved
                    })
                rolling.index = rolling.index.astype(str)
                fig = rolling.plot(template="simple_white", labels=dict(index="Date", value="Factor Loading", variable=variable))
                fig.update_layout(legend=dict(y=0.99 ,x=0.01), 
                    legend_title_text = variable,
                    margin = dict(l=0, r=0),
                    #hovermode = "x unified",
                    title = f"Rolling Factor Loadings ({form.cleaned_data['rolling_regression']} Months) on {col}"
                )
                graphs.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))


        return render(request, "dansapp/factors.html", {
            "form": form,
            "formset": formset,
            "tickerform": tickerform,
            "saved": saved,
            "range": range,
            "title": title,
            "stats": factor_loadings.to_html(classes=["table table-hover table-fit"], border=0,  justify="unset"),
            "graphs": graphs
        })