from .models import RetsCSV
from django.contrib import messages
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
import statsmodels.api as sm
import pandas_datareader.data as web
import datetime

def generate_return_series(tickers, start=None, end=None, granularity="1mo", cpi="None", fx="None", name=None, weights=None):
    securities = yf.download(tickers=tickers, interval=granularity)[["Adj Close"]]
    if len(securities.columns) == 1:
        securities.columns = tickers
    else:
        securities.columns = securities.columns.droplevel()
    error = []
    for col in securities:
        if securities[col].isnull().all() == True:
            error.append(''.join(col))
    if error:
        return error
    if granularity == "1mo":
        securities = securities.dropna().to_period('M')
        if securities.index[[-1]] == securities.index[[-2]]:
            securities = securities[:-1]

    securities = securities.pct_change().dropna()
    #securities = securities.resample('M').apply(compound).to_period('M')
    securities = securities[start:end]

    if cpi != "None":
        securities = cpi_adjust(securities, granularity, cpi)
        if not isinstance(securities, pd.DataFrame):
            return securities
    if fx != "None":
        securities = fx_adjust(securities, granularity, fx)
        if not isinstance(securities, pd.DataFrame):
            return securities
 
    if name and weights:
        weights = pd.Series(weights, index=securities.columns)
        weights = weights / 100
        portfolio = (securities * weights)
        portfolio = portfolio.agg(['sum'], axis="columns")
        portfolio.columns = [name]
        return portfolio
        
    return securities

def cpi_adjust(df, granularity, cpi):
    #FRED US CPI CPALTT01USM657N
    #FRED CANADA CPI CPALCY01CAM661N
    start = datetime.datetime(1900, 1, 1)
    if cpi == "CPALTT01USM657N":
        cpi = web.DataReader(["CPALTT01USM657N"], 'fred', start).to_period('M')/100
    elif cpi == "CPALCY01CAM661N":
        cpi = web.DataReader(["CPALCY01CAM661N"], 'fred', start).to_period('M').pct_change().dropna()

    df = df[str(cpi.index[0]):str(cpi.index[-1])]
    if df.shape[0] == 0:
        return f"Not enough data available for the selected sample. CPI data available from {cpi.index[0]} to {cpi.index[-1]}."
    cpi = cpi[str(df.index[0]):str(df.index[-1])]

    if granularity == "1d":
        cpi_daily = pd.DataFrame(index=df.index)
        cpi_daily["cpi"] = np.nan
        for num, time in enumerate(cpi.index):
            num_days = len(df.loc[str(time)])
            cpi_daily.loc[str(time)] = (1+cpi.iloc[num].values[0])**(1/num_days)-1
        cpi = cpi_daily
    
    df = (df+1).div((cpi+1).squeeze(), axis=0)-1
    return df
    

def fx_adjust(df, granularity, fx_type):
    #FRED CAD to 1 USD DEXCAUS
    start = datetime.datetime(1900, 1, 1)
    fx = web.DataReader(["DEXCAUS"], 'fred', start).pct_change().dropna()
    fx = fx.resample('M').apply(compound).to_period('M')

    df = df[str(fx.index[0]):str(fx.index[-1])]
    if df.shape[0] == 0:
        return f"Not enough data available for the selected sample. FX data available from {fx.index[0]} to {fx.index[-1]}."
    fx = fx[str(df.index[0]):str(df.index[-1])]

    if granularity == "1d":
        fx_daily = pd.DataFrame(index=df.index)
        fx_daily["fx"] = np.nan
        for num, time in enumerate(fx.index):
            num_days = len(df.loc[str(time)])
            fx_daily.loc[str(time)] = (1+fx.iloc[num].values[0])**(1/num_days)-1
        fx = fx_daily
    
    #CAD securities in USD terms
    if fx_type == "usd":
        for security in [security for security in df if security[-3:].lower() == ".to"]:
            df[security] = (df[security]+1).div((fx+1).squeeze(), axis=0)-1
    
    #USD securities in CAD terms
    if fx_type == "cad":
        for security in [security for security in df if security[-3:].lower() != ".to"]:
            df[security] = (df[security]+1).div((1/(fx+1)).squeeze(), axis=0)-1
    return df

def create_master_dataframe(request, form, formset, tickerform, csvs):
    if form.cleaned_data["type"] == "formset_block":
        master_dataframe = []
        if formset.data["form-0-ticker1"]:
            if formset.is_valid():
                for f in formset:
                    if f.cleaned_data:
                        ticker = []
                        weight = []
                        for k, v in f.cleaned_data.items():
                            if v:
                                if "name" in k:
                                    name = v
                                if "ticker" in k:
                                    ticker.append(v)
                                if "weight" in k:
                                    weight.append(v)
                        master_dataframe.append([name, ticker, weight])
            if not formset.is_valid():
                return False
            #dataframe of valid tickers, errors returned for invalid
            tmp_portfolio_list = []
            for portfolio in master_dataframe:
                master_dataframe = generate_return_series(portfolio[1], name=portfolio[0], weights=portfolio[2], start=form.cleaned_data["datestamp_start"], end=form.cleaned_data["datestamp_end"], granularity=form.cleaned_data["granularity"], cpi=form.cleaned_data["inflation_adj"], fx=form.cleaned_data["currency_adj"])        
                if isinstance(master_dataframe, list):
                    for error in master_dataframe:
                        messages.error(request, f"Invalid ticker entered: {error}", extra_tags="Error!")
                    return False
                if isinstance(master_dataframe, str):
                    messages.error(request, master_dataframe, extra_tags="Error!")
                    return False
                tmp_portfolio_list.append(master_dataframe)
            master_dataframe = pd.concat(tmp_portfolio_list, axis=1).dropna()
        variable = "Portfolio"

    if form.cleaned_data["type"] == "tickerform_block":
        if tickerform.data["ticker1"]:
            if not tickerform.is_valid():
                return False
            #list of available tickers
            tickers = []
            for value in tickerform.cleaned_data.values():
                if value:
                    tickers.append(value)
            #dataframe of valid tickers, errors returned for invalid
            master_dataframe = generate_return_series(tickers, start=form.cleaned_data["datestamp_start"], end=form.cleaned_data["datestamp_end"], granularity=form.cleaned_data["granularity"], cpi=form.cleaned_data["inflation_adj"], fx=form.cleaned_data["currency_adj"])        
            if isinstance(master_dataframe, list):
                for error in master_dataframe:
                    messages.error(request, f"Invalid ticker entered: {error}", extra_tags="Error!")
                return False
            if isinstance(master_dataframe, str):
                messages.error(request, master_dataframe, extra_tags="Error!")
                return False
        variable = "Security"
    
    if csvs:
        if isinstance(master_dataframe, list):
            master_dataframe = pd.DataFrame()

        for csv in csvs:
            if csv:
                tmp = RetsCSV.objects.filter(user=request.user, name=csv)
                if not tmp.exists():
                    messages.error(request, f"{csv} does not exit", extra_tags="Error!")
                    return False
                rets = pd.read_csv(tmp[0].return_series,
                        header=0, index_col=0, parse_dates=True)
                #rets = rets/100
                if str(rets.index[0])[8:9] == str(rets.index[1])[8:9] and form.cleaned_data["granularity"]=="1d":
                    messages.error(request, f"Granularity between CSV and live data are not the same.", extra_tags="Error!")
                    return False
                if str(rets.index[0])[8:9] != str(rets.index[1])[8:9] and form.cleaned_data["granularity"]=="1mo":
                    messages.error(request, f"Granularity between CSV and live data are not the same.", extra_tags="Error!")
                    return False
                if form.cleaned_data["granularity"] == "1d":
                    rets.index = rets.index.to_period('D')
                if form.cleaned_data["granularity"] == "1mo":
                    rets.index = rets.index.to_period('M')

                #if form.cleaned_data["inflation_adj"] != "None":
                #    rets = cpi_adjust(rets, form.cleaned_data["granularity"], form.cleaned_data["inflation_adj"])
                #if form.cleaned_data["currency_adj"] != "None":
                #    rets = fx_adjust(rets, form.cleaned_data["granularity"], form.cleaned_data["currency_adj"])

                master_dataframe = pd.concat([master_dataframe, rets], axis=1).dropna()
                master_dataframe = master_dataframe[form.cleaned_data["datestamp_start"]:form.cleaned_data["datestamp_end"]]

    #no errors   
    if form.cleaned_data["granularity"] == "1mo":
        periods_per_year = 12
    elif form.cleaned_data["granularity"] == "1d":
        periods_per_year = 253
    
    return master_dataframe, periods_per_year, variable


def sample_date_range(rets):
    return [str(rets.index.min()).split()[0], str(rets.index.max()).split()[0]]

def compound(r):
    return np.expm1(np.log1p(r).sum())

def annualize_rets(r, periods_per_year=12):
    compounded_growth = (1+r).prod()
    n_periods = r.shape[0]
    return compounded_growth**(periods_per_year/n_periods)-1

def annualize_vol(r, periods_per_year=12):
    return r.std()*(periods_per_year**0.5)

def sharpe_ratio(r, riskfree_rate, periods_per_year):
    rf_per_period = (1+riskfree_rate)**(1/periods_per_year)-1
    excess_ret = r - rf_per_period
    ann_ex_ret = annualize_rets(excess_ret, periods_per_year)
    ann_vol = annualize_vol(r, periods_per_year)
    return ann_ex_ret/ann_vol

def drawdown(return_series: pd.Series):
    wealth_index = (1+return_series).cumprod()
    previous_peaks = wealth_index.cummax()
    drawdowns = (wealth_index - previous_peaks)/previous_peaks
    return pd.DataFrame({"Wealth": wealth_index, 
                         "Previous Peak": previous_peaks, 
                         "Drawdown": drawdowns})

def skewness(r):
    demeaned_r = r - r.mean()
    # use the population standard deviation, so set dof=0
    sigma_r = r.std(ddof=0)
    exp = (demeaned_r**3).mean()
    return exp/sigma_r**3


def kurtosis(r):
    demeaned_r = r - r.mean()
    # use the population standard deviation, so set dof=0
    sigma_r = r.std(ddof=0)
    exp = (demeaned_r**4).mean()
    return exp/sigma_r**4

def var_historic(r, level=5):
    if isinstance(r, pd.DataFrame):
        return r.aggregate(var_historic, level=level)
    elif isinstance(r, pd.Series):
        return -np.percentile(r, level)
    else:
        raise TypeError("Expected r to be a Series or DataFrame")


def cvar_historic(r, level=5):
    if isinstance(r, pd.Series):
        is_beyond = r <= -var_historic(r, level=level)
        return -r[is_beyond].mean()
    elif isinstance(r, pd.DataFrame):
        return r.aggregate(cvar_historic, level=level)
    else:
        raise TypeError("Expected r to be a Series or DataFrame")


def var_gaussian(r, level=5, modified=False):
    # compute the Z score assuming it was Gaussian
    z = norm.ppf(level/100)
    if modified:
        # modify the Z score based on observed skewness and kurtosis
        s = skewness(r)
        k = kurtosis(r)
        z = (z +
                (z**2 - 1)*s/6 +
                (z**3 -3*z)*(k-3)/24 -
                (2*z**3 - 5*z)*(s**2)/36
            )
    return -(r.mean() + z*r.std(ddof=0))




def summary_stats(r, riskfree_rate=0, periods_per_year=12):
    ann_r = r.aggregate(annualize_rets, periods_per_year=periods_per_year)
    ann_vol = r.aggregate(annualize_vol, periods_per_year=periods_per_year)
    ann_sr = r.aggregate(sharpe_ratio, riskfree_rate=riskfree_rate, periods_per_year=periods_per_year)
    skew = r.aggregate(skewness)
    kurt = r.aggregate(kurtosis)
    cf_var5 = r.aggregate(var_gaussian, modified=True)
    hist_cvar5 = r.aggregate(cvar_historic)
    dd = r.aggregate(only_drawdown)
    du = r.aggregate(drawup)
    wealth_index = (r+1).cumprod()
    return pd.DataFrame({
        "Annualized Return": round(ann_r*100, 2).astype(str) + "%",
        "Annualized Vol": round(ann_vol*100, 2).astype(str) + "%",
        "Max Drawdown": round(dd.min()*100, 2).astype(str) + "%",
        "Max Drawdown Date": dd.idxmin(),
        "Current Drawdown": round(dd.iloc[-1]*100, 2).astype(str) + "%",
        "Trough to Present": round(du.iloc[-1]*100, 2).astype(str) + "%",
        "Peak Date": wealth_index.idxmax(),
        "Trough Date": wealth_index.idxmin(),
        "Skewness": round(skew, 2),
        "Kurtosis": round(kurt, 2),
        "Cornish-Fisher VaR (5% level)": round(cf_var5*100, 2).astype(str) + "%",
        "Historic CVaR (5% level)": round(hist_cvar5*100, 2).astype(str) + "%",
        "Sharpe Ratio (raw)": round(ann_sr, 2)
    })

def only_drawdown(rets):
    wealth_index = pd.concat([pd.Series([1]), (1+rets).cumprod()])
    previous_peaks = wealth_index.cummax()
    drawdowns = (wealth_index - previous_peaks)/previous_peaks
    return drawdowns

def drawup(rets):
    wealth_index = pd.concat([pd.Series([1]), (1+rets).cumprod()])
    previous_troughs = wealth_index.cummin()
    drawups = (wealth_index - previous_troughs)/previous_troughs
    return drawups

def horserace(rets, wealth=10000):
    horserace = pd.DataFrame(index=(rets.columns))
    horserace["Cumulative Return"] = round(((1+rets).prod() - 1) * 100, 2).astype(str) + "%"
    horserace["Initial Wealth"] = f"${wealth:,}"
    horserace["Terminal Wealth"] = round(wealth*(1+rets).prod(), 2).map("${:,}".format)

    return horserace

def rolling_rets(r, roll_window=36, periods_per_year=12):
    if r.shape[0] <= roll_window:
        return False
    for asset in r:
        n_periods = r[[asset]].shape[0]
        windows = [(start, start+roll_window) for start in range(n_periods-roll_window)]
        if asset == r.columns[0]:
            results = pd.DataFrame([annualize_rets(r[[asset]].iloc[win[0]:win[1]], periods_per_year=periods_per_year).iloc[0] for win in windows], columns=[asset], index=r.iloc[roll_window:].index)
        else:    
            results = pd.concat([pd.DataFrame([annualize_rets(r[[asset]].iloc[win[0]:win[1]], periods_per_year=periods_per_year).iloc[0] for win in windows], columns=[asset], index=r.iloc[roll_window:].index), results], axis=1)
            
    return results

def rolling_stats(rolling_rets):
    rolling_stats = pd.DataFrame(index=(rolling_rets.columns))
    rolling_stats["Mean Annualized Return"] = round(rolling_rets.mean() * 100, 2).astype(str) + "%"
    rolling_stats["Max Return"] = round(rolling_rets.max() * 100, 2).astype(str) + "%"
    rolling_stats["Min Return"] = round(rolling_rets.min() * 100, 2).astype(str) + "%"

    return rolling_stats

def regress(dependent_variable, explanatory_variables, alpha=True):
    if alpha:
        explanatory_variables = explanatory_variables.copy()
        explanatory_variables["Alpha"] = 1

    lm = sm.OLS(dependent_variable, explanatory_variables).fit()
    return lm

def single_period_ann_rets(r, periods_per_year=12):
    return (1+r)**periods_per_year-1

def factor_regression(tickers, factor_model):
    factor_model = factor_model[tickers.index.values[0]:tickers.index.values[-1]]
    tickers = tickers[factor_model.index.values[0]:factor_model.index.values[-1]]
    tickers_excess = tickers - factor_model[["RF"]].values
    
    factor_loadings = pd.DataFrame(regress(tickers_excess, factor_model[factor_model.columns.values[:-1]]).params)
    factor_loadings.columns = tickers.columns
    annualized_alpha = factor_loadings.loc[["Alpha"]].aggregate(single_period_ann_rets)
    annualized_alpha.index = ["Annualized Alpha"]
    factor_loadings.iloc[0:-1] = factor_loadings.iloc[0:-1].round(2)
    annualized_alpha.loc["Annualized Alpha"] =  round(annualized_alpha.loc["Annualized Alpha"] * 100, 2).astype(str) + "%"
    #alpha in %
    factor_loadings.loc[["Alpha"]] = round(factor_loadings.loc[["Alpha"]] * 100, 2).astype(str) + "%"
    factor_loadings = pd.concat([factor_loadings, annualized_alpha])
    return factor_loadings

def regression_per_window(ticker, factor_model):
    factor_model = factor_model[ticker.index.values[0]:ticker.index.values[-1]]
    tickers = ticker[factor_model.index.values[0]:factor_model.index.values[-1]]
    tickers_excess = tickers - factor_model[["RF"]].values
    
    return pd.DataFrame(regress(tickers_excess, factor_model[factor_model.columns.values[:-1]], alpha=False).params)

def rolling_regression(ticker, factor_model, roll_window):
    if ticker.shape[0] <= roll_window:
        return False
    n_periods = ticker.shape[0]
    windows = [(start, start+roll_window) for start in range(n_periods-roll_window)]
    tmp = []
    for win in windows:
        df = pd.DataFrame(regression_per_window(ticker.iloc[win[0]:win[1]], factor_model=factor_model).transpose())
        df.index = [ticker.index[win[1]]]
        tmp.append(df)
    return pd.concat(tmp)
