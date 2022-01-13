from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from .models import User, Portfolio, RetsCSV
from django.contrib.auth.decorators import login_required
from .forms import MyUserCreationForm, UserUpdateForm, MetaForm, PortfolioForm, TickerForm, BasePortfolioFormSet, RetsCSVForm, NBForm
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
        RetsCSVFormSet = modelformset_factory(RetsCSV, form=RetsCSVForm, extra=1, max_num=10, absolute_max=10, can_delete=True)

        if request.method == "GET":
            return render(request, "dansapp/user/portfolios.html", {
                "formset": PortfolioFormSet(queryset=Portfolio.objects.filter(user=request.user)),
                "csvform": RetsCSVFormSet(queryset=RetsCSV.objects.filter(user=request.user))
            })

        if request.method == "POST":
            if request.POST["form-MAX_NUM_FORMS"] == "20":
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

            if request.POST["form-MAX_NUM_FORMS"] == "10":
                csvformset = RetsCSVFormSet(request.POST,request.FILES)
                if csvformset.is_valid():
                    instances = csvformset.save(commit=False)
                    for obj in csvformset.deleted_objects:
                        obj.delete()
                        messages.success(request, f"{obj.name} was successfully deleted.", extra_tags="Success!")
                    for instance in instances:
                        tmp = pd.read_csv(instance.return_series, header=0, index_col=0, parse_dates=True)
                        if tmp.index.dtype == "O" or tmp.index.dtype != 'datetime64[ns]':
                            messages.error(request, f"Invalid index entered. Index (column 0) needs to be YYYY-MM-DD or YYYY-MM", extra_tags="Error!")
                        elif tmp.shape != tmp._get_numeric_data().shape:
                            messages.error(request, f"All data, exclusing the index and the column headers, must be numeric.", extra_tags="Error!")
                        else:
                            instance.user = request.user
                            instance.save()
                            messages.success(request, f"{instance.name} was successfully saved.", extra_tags="Success!")
                for form in csvformset:
                    for error in form.non_field_errors():
                        messages.error(request, f"{error}", extra_tags="Validation error:")
                    for field in form:
                        for error in field.errors:
                            messages.error(request, f"{error}", extra_tags=f"{field.label}")
                
            return render(request, "dansapp/user/portfolios.html", {
                "formset": PortfolioFormSet(queryset=Portfolio.objects.filter(user=request.user)),
                "csvform": RetsCSVFormSet(queryset=RetsCSV.objects.filter(user=request.user))
            })

def faq(request):
    return render(request, "dansapp/faq.html")

def portfolio_api(request, name):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    return JsonResponse({k: v for k, v in Portfolio.objects.filter(user=request.user, name=name).values()[0].items() if v is not None and not k in ["id", "user_id"]})

def prep_data(request, template):
    PortfolioFormSet = modelformset_factory(Portfolio, form=PortfolioForm, formset=BasePortfolioFormSet, extra=1, max_num=5, absolute_max=5)
    saved = []
    saved_csvs = []
    if request.user.is_authenticated:
        saved = Portfolio.objects.filter(user=request.user).values_list("name", flat=True)
        saved_csvs = RetsCSV.objects.filter(user=request.user).values_list("name", flat=True)
    if request.method == "GET":
        return render(request, f"dansapp/{template}.html", {
            "form": MetaForm(template=template),
            "formset": PortfolioFormSet(),
            "tickerform": TickerForm,
            "saved": saved,
            "saved_csvs": saved_csvs
    })

    if request.method == "POST":
        formset = PortfolioFormSet(request.POST)
        if request.POST["type"] == "tickerform_block":
            tickerform = TickerForm(request.POST)
        else:
            tickerform = TickerForm
        #append a "-01" onto the datestamp if granularity == 1mo
        updated_request = request.POST.copy()
        if updated_request["granularity"] == "1mo":
            if updated_request["datestamp_start"]:
                updated_request.update({'datestamp_start': updated_request["datestamp_start"] + "-01"})
            if updated_request["datestamp_end"]:
                updated_request.update({'datestamp_end': updated_request["datestamp_end"] + "-01"})
        form = MetaForm(updated_request, template=template)
        if not form.is_valid():
            return render(request, f"dansapp/{template}.html", {
                "form": form,
                "formset": formset,
                "tickerform": tickerform,
                "saved": saved,
                "saved_csvs": saved_csvs
            })
        
        csvs = {v for k, v in updated_request.items() if 'csv' in k}
        if not "inflation_adj" in form.cleaned_data:
            form.cleaned_data["inflation_adj"] = "None"
        if not "currency_adj" in form.cleaned_data:
            form.cleaned_data["currency_adj"] = "None"
        return_vals = create_master_dataframe(request, form, formset, tickerform, csvs)
        if not return_vals:
            return render(request, "dansapp/backtest.html", {
            "form": form,
            "formset": formset,
            "tickerform": tickerform,
            "saved": saved,
            "saved_csvs": saved_csvs
        })
        master_dataframe, periods_per_year, variable = return_vals
        return master_dataframe, periods_per_year, variable, form, formset, tickerform, saved, saved_csvs

def backtest(request):
    tmp = prep_data(request, "backtest")
    if type(tmp) == HttpResponse:
        return tmp
    master_dataframe, periods_per_year, variable, form, formset, tickerform, saved, saved_csvs = tmp
    if not form.cleaned_data["initial_wealth"]:
        form.cleaned_data["initial_wealth"] = 10000

    #PLOTTING AND STATS
    graph = form.cleaned_data["initial_wealth"]*(master_dataframe+1).cumprod()
    graph.index = graph.index.astype(str)
    fig = graph.plot(template="simple_white", labels=dict(index="Date", value="Balance", variable=variable))
    fig.update_layout(legend=dict(y=0.99 ,x=0.01), 
        legend_title_text = variable,
        margin = dict(l=0, r=20),
        hovermode = "x unified"
    )
    graph = fig.to_html(full_html=False, include_plotlyjs="cdn")
    range = sample_date_range(master_dataframe)
    summary = summary_stats(master_dataframe, periods_per_year=periods_per_year) 
    key = summary[["Annualized Return", "Annualized Vol", "Max Drawdown"]]
    horse = horserace(master_dataframe, wealth=form.cleaned_data["initial_wealth"]) 
    return render(request, "dansapp/backtest.html", {
        "form": form,
        "formset": formset,
        "tickerform": tickerform,
        "saved": saved,
        "saved_csvs": saved_csvs,
        "range": range,
        "summary_stats": summary.to_html(classes=["table table-hover table-fit"], border=0,  justify="unset"),
        "key_stats": key.to_html(classes=["table table-hover table-fit"], border=0,  justify="unset"),
        "horserace": horse.to_html(classes=["table table-hover table-fit"], border=0,  justify="unset"),
        "graph": graph
    })

def rolling(request):
    tmp = prep_data(request, "rolling")
    if type(tmp) == HttpResponse:
        return tmp
    master_dataframe, periods_per_year, variable, form, formset, tickerform, saved, saved_csvs = tmp
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
            "saved": saved,
            "saved_csvs": saved_csvs
        })
    stats = rolling_stats(rolling)

    rolling.index = rolling.index.astype(str)
    fig = rolling.plot(template="simple_white", labels=dict(index="Date", value="Annualized Return", variable=variable))
    fig.update_layout(legend=dict(y=0.99 ,x=0.01), 
        legend_title_text = variable,
        margin = dict(l=0, r=20),
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
        "saved_csvs": saved_csvs,
        "range": range,
        "stats": stats.to_html(classes=["table table-hover table-fit"], border=0,  justify="unset"),
        "graph": graph
    })

def factors(request):
    tmp = prep_data(request, "factors")
    if type(tmp) == HttpResponse:
        return tmp
    master_dataframe, periods_per_year, variable, form, formset, tickerform, saved, saved_csvs = tmp

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
                    "saved": saved,
                    "saved_csvs": saved_csvs
                })
            rolling.index = rolling.index.astype(str)
            fig = rolling.plot(template="simple_white", labels=dict(index="Date", value="Factor Loading", variable=variable))
            fig.update_layout(legend=dict(y=0.99 ,x=0.01), 
                legend_title_text = variable,
                margin = dict(l=0, r=20),
                #hovermode = "x unified",
                title = f"Rolling Factor Loadings ({form.cleaned_data['rolling_regression']} Months) on {col}"
            )
            graphs.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))


    return render(request, "dansapp/factors.html", {
        "form": form,
        "formset": formset,
        "tickerform": tickerform,
        "saved": saved,
        "saved_csvs": saved_csvs,
        "range": range,
        "title": title,
        "stats": factor_loadings.to_html(classes=["table table-hover table-fit"], border=0,  justify="unset"),
        "graphs": graphs
    })

def norberts_gambit(request):
    if request.method == "GET":
        return render(request, "dansapp/norberts_gambit.html", {"form": NBForm})
        
    else:
        form = NBForm(request.POST)
        if form.is_valid():
            params = {k: float(form.cleaned_data[k]) for k in list(form.cleaned_data)[6:] if form.cleaned_data[k] != None}
            output_transactions, output_total, output_explicit_costs, output_ECN, output_commissions  = \
            norbits_gambit_cost_calc(params, float(form.cleaned_data["DLR_TO"]), float(form.cleaned_data["DLR_U_TO"]), form.cleaned_data["buy_FX"], form.cleaned_data["sell_FX"], float(form.cleaned_data["initial"]), form.cleaned_data["initial_fx"], form.cleaned_data["incur_buy_side_ecn"], form.cleaned_data["incur_sell_side_ecn"])

            return JsonResponse({
                "output_transactions": output_transactions.to_html(classes=["table table-hover table-fit-center"], border=0,  justify="unset"),
                "output_total": output_total.to_html(classes=["table table-hover table-fit-center"], border=0,  justify="unset"),
                "output_costs": output_explicit_costs.to_html(classes=["table table-hover table-fit-center"], border=0,  justify="unset"),
                "output_ECN": output_ECN.to_html(classes=["table table-hover table-fit-center"], border=0,  justify="unset"),
                "output_commissions": output_commissions.to_html(classes=["table table-hover table-fit-center"], border=0,  justify="unset"),
            })
        else:
            return JsonResponse({"ERROR": form.errors})