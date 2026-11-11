from flask import Flask, render_template, jsonify
import yfinance as yf
import requests
import re
import time
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup

app = Flask(__name__)

BTC_HOLDINGS = 818_869        # as of ~May 12 2026 per SEC 8-K ($61.86B total)
AVG_COST_BASIS = 75_540       # $61.86B / 818,869 BTC per SEC 8-K filings
BTC_TOTAL_SUPPLY = 21_000_000
BTC_YIELD_YTD = 11.0          # % — Q1 2026 10-Q filing

EDGAR_CIK = "1050446"
EDGAR_HEADERS = {"User-Agent": "StrategyTracker contact@strategytracker.app"}

_cache = {}
_cache_ts = {}


def cache_get(key, ttl=30):
    if key in _cache and time.time() - _cache_ts.get(key, 0) < ttl:
        return _cache[key]
    return None


def cache_set(key, val):
    _cache[key] = val
    _cache_ts[key] = time.time()


def get_mstr_info():
    cached = cache_get("mstr_info")
    if cached:
        return cached

    ticker = yf.Ticker("MSTR")
    info = ticker.info
    price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
    prev_close = info.get("regularMarketPreviousClose") or price
    shares = info.get("sharesOutstanding", 0)
    market_cap = info.get("marketCap") or (price * shares if price and shares else 0)
    change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0

    # Diluted shares from most recent quarterly income statement
    diluted_shares = shares
    try:
        stmt = ticker.quarterly_income_stmt
        for row in ("Diluted Average Shares", "Diluted Shares", "DilutedAverageShares"):
            if row in stmt.index:
                val = stmt.loc[row].dropna().iloc[0]
                if val and val > 0:
                    diluted_shares = int(val)
                    break
    except Exception:
        pass

    # Total obligations = debt + preferred equity (STRK/STRF/STRP have liquidation preference)
    total_debt = info.get("totalDebt") or 0
    pref_stock = 0
    try:
        bs = ticker.quarterly_balance_sheet
        for row in ("Preferred Stock", "Redeemable Preferred Stock", "PreferredStock",
                    "Redeemable Preferred", "Preferred Securities"):
            if row in bs.index:
                val = bs.loc[row].dropna()
                if not val.empty and val.iloc[0] > 0:
                    pref_stock = int(val.iloc[0])
                    break
    except Exception:
        pass
    total_obligations = total_debt + pref_stock

    earnings_date = None
    for k in ("earningsTimestamp", "earningsTimestampStart"):
        ts = info.get(k)
        if ts:
            try:
                earnings_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            except Exception:
                pass
            break

    result = {
        "price": price,
        "change_pct": round(change_pct, 2),
        "shares_outstanding": shares,
        "diluted_shares": diluted_shares,
        "market_cap": market_cap,
        "week_52_high": info.get("fiftyTwoWeekHigh"),
        "week_52_low": info.get("fiftyTwoWeekLow"),
        "volume": info.get("regularMarketVolume") or info.get("volume"),
        "avg_volume": info.get("averageVolume"),
        "short_interest": info.get("sharesShort"),
        "short_ratio": info.get("shortRatio"),
        "beta": info.get("beta"),
        "institutional_ownership": info.get("heldPercentInstitutions"),
        "target_high": info.get("targetHighPrice"),
        "target_low": info.get("targetLowPrice"),
        "target_mean": info.get("targetMeanPrice"),
        "earnings_date": earnings_date,
        "total_debt": total_debt,
        "pref_stock": pref_stock,
        "total_obligations": total_obligations,
    }
    cache_set("mstr_info", result)
    return result


def get_btc_data():
    cached = cache_get("btc_full")
    if cached:
        return cached
    r = requests.get(
        "https://api.coingecko.com/api/v3/coins/bitcoin",
        params={"localization": "false", "tickers": "false",
                "community_data": "false", "developer_data": "false"},
        timeout=12,
    )
    r.raise_for_status()
    md = r.json().get("market_data", {})
    dominance = None
    try:
        rg = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        rg.raise_for_status()
        dominance = rg.json().get("data", {}).get("market_cap_percentage", {}).get("btc")
    except Exception:
        pass
    result = {
        "price": md.get("current_price", {}).get("usd"),
        "change_24h": md.get("price_change_percentage_24h"),
        "change_7d": md.get("price_change_percentage_7d"),
        "change_30d": md.get("price_change_percentage_30d"),
        "ath": md.get("ath", {}).get("usd"),
        "ath_change_pct": md.get("ath_change_percentage", {}).get("usd"),
        "volume_24h": md.get("total_volume", {}).get("usd"),
        "market_cap": md.get("market_cap", {}).get("usd"),
        "dominance": round(dominance, 2) if dominance else None,
        "circulating_supply": md.get("circulating_supply"),
    }
    cache_set("btc_full", result)
    return result


def get_strc_data():
    cached = cache_get("strc")
    if cached:
        return cached
    try:
        t = yf.Ticker("STRC")
        info = t.info
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        prev  = info.get("regularMarketPreviousClose") or price
        change_pct = ((price - prev) / prev * 100) if prev else 0
        div_rate  = info.get("dividendRate")
        div_yield_raw = info.get("dividendYield")
        # yfinance sometimes returns preferred stock yield as raw percent (11.5) not decimal (0.115)
        if div_yield_raw and div_yield_raw > 1:
            div_yield_pct = round(div_yield_raw, 2)
        elif div_yield_raw:
            div_yield_pct = round(div_yield_raw * 100, 2)
        else:
            div_yield_pct = None
        result = {
            "price": price,
            "change_pct": round(change_pct, 2),
            "volume": info.get("regularMarketVolume") or info.get("volume"),
            "avg_volume": info.get("averageVolume"),
            "market_cap": info.get("marketCap"),
            "dividend_rate": div_rate,
            "dividend_yield_pct": div_yield_pct,
            "par_value": 100,
            "premium_to_par": round((price - 100) / 100 * 100, 2) if price else None,
        }
        cache_set("strc", result)
        return result
    except Exception:
        return {}


def parse_8k_text(html, filing_date):
    # Strategy 8-Ks are inline iXBRL — table headers are empty due to namespace
    # tags. Full-text extraction via soup.get_text() works correctly.
    soup = BeautifulSoup(html, "html.parser")
    r = {"date": filing_date}
    text = soup.get_text(" ", strip=True)

    def _n(s):
        s = str(s).replace(",", "").replace("$", "").strip()
        if s in ("-", "—", "–", ""):
            return None
        try:
            return float(s)
        except Exception:
            return None

    # ── Period dates ──────────────────────────────────────────────────────
    m = re.search(
        r"(?:Period|From|Between)\s+([\w]+\s+\d{1,2},?\s*\d{4})\s+(?:to|through|and|[–-])\s+([\w]+\s+\d{1,2},?\s*\d{4})",
        text, re.I,
    )
    if m:
        r["period_start"] = m.group(1).strip()
        r["period_end"]   = m.group(2).strip()

    # ── BTC data ──────────────────────────────────────────────────────────
    # Column headers: BTC Acquired (N) | Agg Purchase Price (in millions) (N) |
    #   Avg Purchase Price (N) | Agg BTC Holdings | Agg Purchase Price (in billions) (N) | Avg Purchase Price (N)
    # Data row (after 2nd "Average Purchase Price (N)"):
    #   {btc|-} $ {cost_M|-} $ {avg_price|-}  {total_btc} $ {total_cost_B} $ {total_avg}
    if re.search(r"BTC\s+Acquired", text, re.I):
        parts = re.split(r"Average\s+Purchase\s+Price\s*\([^)]*\d[^)]*\)", text, flags=re.I)
        if len(parts) >= 3:
            dp = parts[2].strip()
            m2 = re.match(
                r"([\d,]+|-)\s*\$\s*([\d,.]+|-)\s*\$\s*([\d,]+|-)\s+"
                r"([\d,]+)\s*\$\s*([\d,.]+)\s*\$\s*([\d,]+)",
                dp
            )
            if m2:
                btc = _n(m2.group(1))
                if btc and btc > 0:
                    r["btc_purchased"] = int(btc)
                    cost = _n(m2.group(2))
                    avg  = _n(m2.group(3))
                    if cost: r["btc_cost_usd"]  = cost * 1e6
                    if avg:  r["btc_avg_price"]  = int(avg)
                snap = _n(m2.group(4))
                if snap:
                    r["snapshot_total_btc"] = int(snap)
                    sc = _n(m2.group(5))
                    sa = _n(m2.group(6))
                    if sc: r["snapshot_total_cost"] = sc * 1e9
                    if sa: r["snapshot_avg_price"]  = int(sa)

    # ── ATM data ──────────────────────────────────────────────────────────
    # Format: "SECURITY Stock {shares|-} $ {notional|-} $ {net_proceeds|-} $ {available}"
    for sec, key_sh, key_not, key_proc in [
        ("STRC", "strc_shares_sold", "strc_notional", "strc_net_proceeds"),
        ("MSTR", "mstr_shares_sold", None,            "mstr_proceeds"),
    ]:
        m = re.search(
            rf"{sec}\s+Stock\s+([\d,]+|-)\s*\$\s*([\d,.]+|-)\s*\$\s*([\d,.]+|-)\s*\$",
            text, re.I
        )
        if not m or m.group(1) in ("-", ""):
            continue
        v = _n(m.group(1))
        if v: r[key_sh] = int(v)
        if key_not:
            v = _n(m.group(2))
            if v: r[key_not] = v * 1e6
        v = _n(m.group(3))  # net proceeds (col 3)
        if v: r[key_proc] = v * 1e6

    return r if len(r) > 2 else None


def get_8k_history():
    cached = cache_get("edgar_8k", ttl=3600)
    if cached:
        return cached

    results = []
    try:
        cik_padded = EDGAR_CIK.zfill(10)
        sub = requests.get(
            f"https://data.sec.gov/submissions/CIK{cik_padded}.json",
            headers=EDGAR_HEADERS, timeout=15
        )
        sub.raise_for_status()
        data = sub.json()

        recent       = data["filings"]["recent"]
        forms        = recent["form"]
        dates        = recent["filingDate"]
        accessions   = recent["accessionNumber"]
        primary_docs = recent.get("primaryDocument", [])

        k8_idxs = [i for i, f in enumerate(forms[:300]) if f == "8-K"][:20]

        for idx in k8_idxs:
            try:
                acc_dashed = accessions[idx]
                acc_plain  = acc_dashed.replace("-", "")
                primary    = primary_docs[idx] if idx < len(primary_docs) else ""
                sec_base   = f"https://www.sec.gov/Archives/edgar/data/{EDGAR_CIK}/{acc_plain}"

                doc_text = None

                # Method 1: parse filing index to find EX-99.1 link reliably
                try:
                    ix = requests.get(
                        f"{sec_base}/{acc_dashed}-index.htm",
                        headers=EDGAR_HEADERS, timeout=10
                    )
                    if ix.status_code == 200:
                        for a in BeautifulSoup(ix.text, "html.parser").find_all("a", href=True):
                            href = a["href"]
                            if any(x in href.lower() for x in ("ex99", "ex-99", "ex991", "exhibit99")):
                                ex_url = href if href.startswith("http") else f"https://www.sec.gov{href}"
                                dr = requests.get(ex_url, headers=EDGAR_HEADERS, timeout=12)
                                if dr.status_code == 200 and len(dr.text) > 500:
                                    doc_text = dr.text
                                    break
                except Exception:
                    pass

                # Method 2: guess exhibit name from primary document filename
                if not doc_text and primary:
                    # Self-filed: mstr-20260308x8k.htm → mstr-20260308x8kxex991.htm
                    # Agent-filed: d122015d8k.htm → d122015dex991.htm
                    candidates = []
                    p = primary.lower()
                    if "x8k.htm" in p:
                        candidates.append(re.sub(r"x8k\.htm", "x8kxex991.htm", primary, flags=re.I))
                    if "d8k.htm" in p:
                        candidates.append(re.sub(r"d8k\.htm", "dex991.htm", primary, flags=re.I))
                    if "8k.htm" in p and not any(c for c in candidates):
                        candidates.append(re.sub(r"8k\.htm", "ex991.htm", primary, flags=re.I))
                    candidates.append(primary)  # last resort: 8-K wrapper itself
                    for name in dict.fromkeys(filter(None, candidates)):
                        try:
                            dr = requests.get(f"{sec_base}/{name}", headers=EDGAR_HEADERS, timeout=10)
                            if dr.status_code == 200 and len(dr.text) > 500:
                                doc_text = dr.text
                                break
                        except Exception:
                            pass

                if doc_text:
                    parsed = parse_8k_text(doc_text, dates[idx])
                    if parsed and parsed.get("btc_purchased"):
                        results.append(parsed)

                time.sleep(0.15)
            except Exception:
                pass
    except Exception:
        pass

    results.sort(key=lambda x: x["date"], reverse=True)
    cache_set("edgar_8k", results)
    return results


def estimate_issuance(history, current_btc_price):
    if not history or not current_btc_price:
        return {}
    # Include every filing where BTC was actually purchased, regardless of which
    # ATM vehicle funded it (STRC, MSTR, STRD, STRK, etc.)
    valid = [h for h in history if h.get("btc_purchased")]
    if not valid:
        return {}

    total_btc = sum(h["btc_purchased"] for h in valid)
    # Use btc_cost_usd (actual spend) when available; fall back to parsed ATM proceeds
    total_capital = 0
    for h in valid:
        if h.get("btc_cost_usd"):
            total_capital += h["btc_cost_usd"]
        else:
            total_capital += (h.get("strc_notional") or 0) + (h.get("mstr_proceeds") or 0)
    n = len(valid)

    avg_weekly_btc     = total_btc / n
    avg_weekly_capital = total_capital / n
    avg_daily_btc      = avg_weekly_btc / 7
    implied_weekly_btc = avg_weekly_capital / current_btc_price
    implied_daily_btc  = implied_weekly_btc / 7

    btc_price_avg = sum(h.get("btc_avg_price") or current_btc_price for h in valid) / n
    scale = current_btc_price / btc_price_avg if btc_price_avg else 1.0
    scaled_daily_btc = ((avg_weekly_capital * scale) / current_btc_price) / 7

    return {
        "n_periods": n,
        "avg_weekly_btc": round(avg_weekly_btc, 0),
        "avg_daily_btc": round(avg_daily_btc, 1),
        "avg_weekly_capital_usd": avg_weekly_capital,
        "implied_daily_btc_at_current_price": round(implied_daily_btc, 1),
        "scaled_daily_btc": round(scaled_daily_btc, 1),
        "btc_price_scale_factor": round(scale, 2),
        "annual_btc_at_current_pace": round(avg_weekly_btc * 52, 0),
        "annual_btc_scaled": round(scaled_daily_btc * 365, 0),
    }


def get_history():
    cached = cache_get("history", ttl=300)
    if cached:
        return cached
    start = (datetime.now() - timedelta(days=210)).strftime("%Y-%m-%d")
    mh = yf.Ticker("MSTR").history(start=start)
    bh = yf.Ticker("BTC-USD").history(start=start)
    # Strip timezone info so MSTR (NY) and BTC-USD (UTC) align on plain dates
    mh.index = pd.to_datetime(mh.index.date)
    bh.index = pd.to_datetime(bh.index.date)
    result = (mh, bh)
    cache_set("history", result)
    return result


def calc_rsi(closes, period=14):
    # Wilder's smoothing (EMA alpha=1/period), not simple rolling mean
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = (-delta.clip(upper=0))
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return round(float((100 - 100 / (1 + rs)).iloc[-1]), 1)


def calc_realized_vol(closes, days=30):
    returns = closes.pct_change().dropna()
    return round(float(returns.tail(days).std() * np.sqrt(252) * 100), 1)


def calc_beta_corr(mstr_closes, btc_closes, days=30):
    mr = mstr_closes.pct_change().dropna()
    br = btc_closes.pct_change().dropna()
    aligned = pd.concat([mr, br], axis=1, join="inner").tail(days).dropna()
    if len(aligned) < 10:
        return None, None, None
    m, b = aligned.iloc[:, 0].values, aligned.iloc[:, 1].values
    cov = np.cov(m, b)
    beta = cov[0, 1] / cov[1, 1]
    corr = np.corrcoef(m, b)[0, 1]
    return round(float(beta), 2), round(float(corr), 3), round(float(corr ** 2), 3)


def get_signals(mstr_price, btc_value, total_obligations):
    cached = cache_get("signals", ttl=300)
    if cached:
        return cached

    mh, bh = get_history()
    mc = mh["Close"]
    bc = bh["Close"]

    rsi = calc_rsi(mc)
    ma_50 = round(float(mc.tail(50).mean()), 2)
    ma_200 = round(float(mc.tail(200).mean()), 2) if len(mc) >= 200 else None
    pct_from_50 = round((mstr_price - ma_50) / ma_50 * 100, 1) if ma_50 else None
    pct_from_200 = round((mstr_price - ma_200) / ma_200 * 100, 1) if ma_200 else None

    rvol_mstr = calc_realized_vol(mc, 30)
    rvol_btc = calc_realized_vol(bc, 30)
    beta, corr, r_sq = calc_beta_corr(mc, bc, 30)

    # Options — use expiry closest to 30 days out for standard 30-day IV
    iv_atm, pcr = None, None
    try:
        t = yf.Ticker("MSTR")
        exps = t.options
        if exps:
            today = date.today()
            exp = min(exps, key=lambda e: abs(
                (datetime.strptime(e, "%Y-%m-%d").date() - today).days - 30
            ))
            chain = t.option_chain(exp)
            calls, puts = chain.calls, chain.puts
            idx = (calls["strike"] - mstr_price).abs().idxmin()
            iv_atm = round(float(calls.loc[idx, "impliedVolatility"]) * 100, 1)
            co = calls["openInterest"].sum()
            po = puts["openInterest"].sum()
            if co > 0:
                pcr = round(float(po / co), 2)
    except Exception:
        pass

    # Leverage — use total_obligations (debt + preferred equity)
    leverage_ratio = round(total_obligations / btc_value * 100, 1) if total_obligations and btc_value else None
    danger_floor = round(total_obligations / BTC_HOLDINGS) if total_obligations else None

    result = {
        "rsi_14": rsi,
        "ma_50": ma_50,
        "ma_200": ma_200,
        "pct_from_50ma": pct_from_50,
        "pct_from_200ma": pct_from_200,
        "rvol_mstr_30d": rvol_mstr,
        "rvol_btc_30d": rvol_btc,
        "beta_to_btc": beta,
        "corr_to_btc": corr,
        "r_sq_to_btc": r_sq,
        "iv_atm": iv_atm,
        "put_call_ratio": pcr,
        "total_obligations": total_obligations,
        "leverage_ratio": leverage_ratio,
        "danger_floor": danger_floor,
    }
    cache_set("signals", result)
    return result


def get_performance():
    cached = cache_get("perf", ttl=300)
    if cached:
        return cached
    mh, bh = get_history()
    # Align on common dates before slicing — MSTR and BTC-USD trade on different calendars
    aligned = pd.concat([mh["Close"], bh["Close"]], axis=1, join="inner")
    aligned.columns = ["mstr", "btc"]
    result = {}
    for label, days in [("30d", 30), ("90d", 90), ("365d", 365)]:
        try:
            window = aligned.tail(days)
            if len(window) > 5:
                mr = (window["mstr"].iloc[-1] / window["mstr"].iloc[0] - 1) * 100
                br = (window["btc"].iloc[-1]  / window["btc"].iloc[0]  - 1) * 100
                result[label] = {"mstr": round(mr, 2), "btc": round(br, 2), "diff": round(mr - br, 2)}
        except Exception:
            pass
    cache_set("perf", result)
    return result


def get_purchase_history():
    cached = cache_get("purchases", ttl=600)
    if cached:
        return cached
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get("https://www.strategy.com/purchases", headers=headers, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if tag:
            data = json.loads(tag.string)
            props = data.get("props", {}).get("pageProps", {})
            for k in ("purchases", "data", "transactions"):
                raw = props.get(k)
                if raw and isinstance(raw, list) and len(raw) > 0:
                    result = [{
                        "date": p.get("date") or p.get("Date") or p.get("announcementDate"),
                        "btc_purchased": p.get("btcPurchased") or p.get("btc_purchased"),
                        "total_btc": p.get("totalBtc") or p.get("total_btc"),
                        "price_per_btc": p.get("pricePerBtc") or p.get("price_per_btc"),
                        "total_cost": p.get("totalCost") or p.get("total_cost"),
                    } for p in raw[:50]]
                    cache_set("purchases", result)
                    return result
        for table in soup.find_all("table")[:2]:
            hr = table.find("tr")
            if not hr:
                continue
            cols = [th.get_text(strip=True).lower() for th in hr.find_all(["th", "td"])]
            rows = []
            for tr in table.find_all("tr")[1:51]:
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) >= 2:
                    rows.append(dict(zip(cols, cells)) if cols else {"raw": cells})
            if rows:
                cache_set("purchases", rows)
                return rows
        raise ValueError("no data")
    except Exception:
        return []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    try:
        mstr = get_mstr_info()
        btc = get_btc_data()
        btc_price = btc["price"]
        btc_value = BTC_HOLDINGS * btc_price
        market_cap = mstr["market_cap"]
        total_obligations = mstr["total_obligations"]

        equity_nav = btc_value - total_obligations
        mnav = market_cap / equity_nav if equity_nav else None
        btc_per_share = BTC_HOLDINGS / mstr["diluted_shares"] if mstr["diluted_shares"] else None
        unrealized_pnl = (btc_price - AVG_COST_BASIS) * BTC_HOLDINGS
        unrealized_pnl_pct = (btc_price - AVG_COST_BASIS) / AVG_COST_BASIS * 100
        nav_premium = market_cap - equity_nav
        breakeven_btc = (market_cap + total_obligations) / BTC_HOLDINGS if BTC_HOLDINGS else None

        return jsonify({
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "mstr_price": mstr["price"],
            "mstr_change_pct": mstr["change_pct"],
            "market_cap": market_cap,
            "shares_outstanding": mstr["shares_outstanding"],
            "diluted_shares": mstr["diluted_shares"],
            "week_52_high": mstr["week_52_high"],
            "week_52_low": mstr["week_52_low"],
            "volume": mstr["volume"],
            "avg_volume": mstr["avg_volume"],
            "short_interest": mstr["short_interest"],
            "short_ratio": mstr["short_ratio"],
            "beta": mstr["beta"],
            "institutional_ownership": mstr["institutional_ownership"],
            "target_high": mstr["target_high"],
            "target_low": mstr["target_low"],
            "target_mean": mstr["target_mean"],
            "earnings_date": mstr["earnings_date"],
            "btc_price": btc_price,
            "btc_change_24h": btc["change_24h"],
            "btc_change_7d": btc["change_7d"],
            "btc_change_30d": btc["change_30d"],
            "btc_ath": btc["ath"],
            "btc_ath_change_pct": btc["ath_change_pct"],
            "btc_volume_24h": btc["volume_24h"],
            "btc_market_cap": btc["market_cap"],
            "btc_dominance": btc["dominance"],
            "btc_circulating_supply": btc["circulating_supply"],
            "btc_holdings": BTC_HOLDINGS,
            "btc_value_usd": btc_value,
            "avg_cost_basis": AVG_COST_BASIS,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
            "btc_per_share": round(btc_per_share, 6) if btc_per_share else None,
            "mnav": round(mnav, 3) if mnav else None,
            "nav_premium_usd": nav_premium,
            "total_obligations": total_obligations,
            "pref_stock": mstr["pref_stock"],
            "pct_of_supply": round(BTC_HOLDINGS / BTC_TOTAL_SUPPLY * 100, 3),
            "breakeven_btc_price": round(breakeven_btc) if breakeven_btc else None,
            "btc_yield_ytd": BTC_YIELD_YTD,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/signals")
def api_signals():
    try:
        mstr = get_mstr_info()
        btc = get_btc_data()
        btc_value = BTC_HOLDINGS * btc["price"]
        signals = get_signals(mstr["price"], btc_value, mstr["total_obligations"])
        return jsonify(signals)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/performance")
def api_performance():
    try:
        return jsonify(get_performance())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/purchases")
def api_purchases():
    try:
        return jsonify({"purchases": get_purchase_history()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/strc")
def api_strc():
    try:
        strc = get_strc_data()
        history = get_8k_history()
        btc = get_btc_data()
        estimates = estimate_issuance(history, btc.get("price"))
        return jsonify({
            "strc": strc,
            "history": history,
            "estimates": estimates,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chart_data")
def api_chart_data():
    try:
        cached = cache_get("chart_data", ttl=3600)
        if cached:
            return jsonify(cached)
        start = (datetime.now() - timedelta(days=365 * 5 + 10)).strftime("%Y-%m-%d")
        mh = yf.Ticker("MSTR").history(start=start)
        mh.index = pd.to_datetime(mh.index.date)
        mstr_ohlc, mstr_line = [], []
        for dt, row in mh.iterrows():
            t = dt.strftime("%Y-%m-%d")
            o, h, l, c = (round(float(row[k]), 2) for k in ("Open", "High", "Low", "Close"))
            mstr_ohlc.append({"time": t, "open": o, "high": h, "low": l, "close": c})
            mstr_line.append({"time": t, "value": c})
        result = {"mstr_ohlc": mstr_ohlc, "mstr_line": mstr_line}
        cache_set("chart_data", result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/edgar_debug")
def api_edgar_debug():
    """One-shot debug: shows what the EDGAR fetch is actually doing."""
    out = []
    try:
        cik_padded = EDGAR_CIK.zfill(10)
        sub = requests.get(
            f"https://data.sec.gov/submissions/CIK{cik_padded}.json",
            headers=EDGAR_HEADERS, timeout=15
        )
        out.append({"step": "submissions_api", "status": sub.status_code})
        sub.raise_for_status()
        data = sub.json()
        recent       = data["filings"]["recent"]
        forms        = recent["form"]
        dates        = recent["filingDate"]
        accessions   = recent["accessionNumber"]
        primary_docs = recent.get("primaryDocument", [])
        k8_idxs = [i for i, f in enumerate(forms[:300]) if f == "8-K"][:5]
        out.append({"step": "k8_count_found", "count": len(k8_idxs),
                    "first_5_dates": [dates[i] for i in k8_idxs]})

        for idx in k8_idxs:
            acc_dashed = accessions[idx]
            acc_plain  = acc_dashed.replace("-", "")
            primary    = primary_docs[idx] if idx < len(primary_docs) else ""
            sec_base   = f"https://www.sec.gov/Archives/edgar/data/{EDGAR_CIK}/{acc_plain}"
            entry = {"date": dates[idx], "acc": acc_dashed, "primary": primary}

            # Fetch index.htm — show ALL document links, not just ex99
            try:
                ix_url = f"{sec_base}/{acc_dashed}-index.htm"
                ix = requests.get(ix_url, headers=EDGAR_HEADERS, timeout=8)
                entry["index_status"] = ix.status_code
                if ix.status_code == 200:
                    all_links, ex99_links = [], []
                    for a in BeautifulSoup(ix.text, "html.parser").find_all("a", href=True):
                        href = a["href"]
                        if "/Archives/" in href:
                            all_links.append({"href": href, "text": a.get_text(strip=True)})
                            if any(x in href.lower() for x in ("ex99", "ex-99", "ex991", "exhibit99")):
                                ex99_links.append(href)
                    entry["all_archive_links"] = all_links
                    entry["ex99_links"] = ex99_links
            except Exception as e:
                entry["index_error"] = str(e)

            # Try fetching first ex99 link, then fall back to primary doc
            doc_text, doc_source = None, None
            ex99_links = entry.get("ex99_links", [])
            if ex99_links:
                try:
                    href = ex99_links[0]
                    ex_url = href if href.startswith("http") else f"https://www.sec.gov{href}"
                    dr = requests.get(ex_url, headers=EDGAR_HEADERS, timeout=8)
                    entry["exhibit_status"] = dr.status_code
                    entry["exhibit_len"] = len(dr.text) if dr.status_code == 200 else 0
                    if dr.status_code == 200:
                        doc_text, doc_source = dr.text, "ex99"
                except Exception as e:
                    entry["exhibit_error"] = str(e)

            # Method 2: primary doc fallback if no exhibit found
            if not doc_text and primary:
                try:
                    dr = requests.get(f"{sec_base}/{primary}", headers=EDGAR_HEADERS, timeout=8)
                    entry["primary_status"] = dr.status_code
                    entry["primary_len"] = len(dr.text) if dr.status_code == 200 else 0
                    if dr.status_code == 200 and len(dr.text) > 500:
                        doc_text, doc_source = dr.text, "primary"
                except Exception as e:
                    entry["primary_error"] = str(e)

            if doc_text:
                parsed = parse_8k_text(doc_text, dates[idx])
                entry["parsed"] = parsed
                entry["doc_source"] = doc_source
                entry["has_btc_purchased"] = bool(parsed and parsed.get("btc_purchased"))
                # Show text snippets around BTC Acquired and STRC for regex design
                _full = BeautifulSoup(doc_text, "html.parser").get_text(" ", strip=True)
                _m = re.search(r"BTC\s+Acquired", _full, re.I)
                if _m:
                    entry["btc_text"] = _full[max(0, _m.start()-50):_m.start()+600]
                else:
                    entry["btc_text"] = "NOT FOUND"
                _s = re.search(r"STRC\s+Stock", _full, re.I)
                if _s:
                    entry["strc_text"] = _full[max(0, _s.start()-100):_s.start()+300]
                else:
                    entry["strc_text"] = "NOT FOUND"

            out.append(entry)
            time.sleep(0.15)
    except Exception as e:
        out.append({"step": "outer_error", "error": str(e)})
    return jsonify(out)


if __name__ == "__main__":
    app.run(port=3000, debug=True)
