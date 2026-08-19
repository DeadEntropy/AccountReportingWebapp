import ast
import os
from datetime import datetime

import pandas as pd
from bkanalysis.ui import ui, ui_old


class FinancialData:
    """Class Holding all the data used in the webapp"""

    def __init__(self, path, ref_currency="USD", config=None):
        self.df_trans = df_trans = pd.read_csv(os.path.join(path, "df_trans.csv"), parse_dates=[ui.DATE])

        self.df_value = pd.read_csv(os.path.join(path, "df_values.csv"), parse_dates=[ui.DATE])
        df = pd.read_csv(os.path.join(path, "df.csv"), parse_dates=[ui.DATE])
        df.MemoMapped = df.MemoMapped.apply(ast.literal_eval)

        self.account_type_map = df_trans[["Account", "AccountType"]].drop_duplicates().sort_values("Account").set_index("Account").AccountType
        self.df = df
        self.df_exp = ui.add_mappings(df, ref_currency, config)

    def get_wealth_by_account_type(self, date_range):
        """Returns a DataFrame containing the value of each account type"""
        if date_range[1].date() > self.df_exp.Date.dt.date.max():
            date_range[1] = datetime.combine(self.df_exp.Date.dt.date.max(), datetime.min.time())

        df_cash_0 = (
            self.df_exp[self.df_exp.Date.dt.date == date_range[0].date()]
            .groupby(["Account", "Asset"])
            .agg({ui.CUMULATED_AMOUNT_CCY: "mean"})
            .groupby("Account")
            .agg({ui.CUMULATED_AMOUNT_CCY: "sum"})
        ).rename({ui.CUMULATED_AMOUNT_CCY: f"{date_range[0].date():%b-%y}"}, axis=1)

        df_cash_1 = (
            self.df_exp[self.df_exp.Date.dt.date == date_range[1].date()]
            .groupby(["Account", "Asset"])
            .agg({ui.CUMULATED_AMOUNT_CCY: "mean"})
            .groupby("Account")
            .agg({ui.CUMULATED_AMOUNT_CCY: "sum"})
        ).rename({ui.CUMULATED_AMOUNT_CCY: f"{date_range[1].date():%b-%y}"}, axis=1)

        df_cash = pd.concat([df_cash_0, df_cash_1], axis=1)

        df_cash_cols = df_cash.columns
        df_cash["AccountType"] = [self.account_type_map.loc[x] for x in df_cash.index]

        df_cash_account_type = (
            pd.pivot_table(df_cash.reset_index(), index="AccountType", values=df_cash_cols, aggfunc="sum").sort_values(df_cash_cols[1], ascending=False).reset_index()
        )

        return df_cash_account_type[["AccountType", f"{date_range[0].date():%b-%y}", f"{date_range[1].date():%b-%y}"]]

    def get_total_wealth(self, date_range, inc_reimbursement=False):
        """Returns the wealth at the beginning and end of period as well as the total spendings for the period"""
        df_wealth_by_account_type = self.get_wealth_by_account_type(date_range)
        total_value_end = df_wealth_by_account_type[df_wealth_by_account_type.columns[-1]].sum()
        total_value_start = df_wealth_by_account_type[df_wealth_by_account_type.columns[-2]].sum()
        total_spend = -ui_old.get_expenses(self.df_exp, date_range=date_range, values=ui.AMOUNT_CCY, inc_reimbursement=inc_reimbursement)[ui.AMOUNT_CCY].sum()

        return total_value_end, total_value_start, total_spend

    def get_capital_gain(self, date_range):
        """Return the capital Gain over the period"""
        df_range = self.df_exp[(self.df_exp.Date >= date_range[0]) & (self.df_exp.Date <= date_range[1])]
        return pd.pivot_table(df_range, index=["Account"], values="CapitalGain", aggfunc=sum).CapitalGain.sum()

    def get_category_breakdown(self, date_range, filter_key="FullSubType", filter_value="Grocery", index="MemoMapped", row_limit=10):
        """Return the top categories based on the provided filter"""
        df_exp_date = self.df_exp[(self.df_exp.Date >= date_range[0]) & (self.df_exp.Date <= date_range[1])]
        return pd.DataFrame(
            pd.pivot_table(df_exp_date[df_exp_date[filter_key] == filter_value], index=index, values=ui.AMOUNT_CCY, aggfunc="sum")
            .sort_values(ui.AMOUNT_CCY)[:row_limit]
            .to_records()
        )

    def get_all_categories(self, date_range, threshold=1000):
        """Returns the complete list of categories based on FullMasterType, FullType and FullSubType"""
        df_exp_date = self.df_exp[(self.df_exp.Date >= date_range[0]) & (self.df_exp.Date <= date_range[1])]
        df_exp_date = df_exp_date[(df_exp_date.FullMasterType != "Intra-Account Transfers")]

        df_fmt = pd.pivot_table(
            df_exp_date, index="FullMasterType", values=[ui.AMOUNT_CCY, "FullType"], aggfunc={ui.AMOUNT_CCY: sum, "FullType": lambda x: len(x.unique())}
        ).sort_values(ui.AMOUNT_CCY)
        df_fmt[ui.AMOUNT_CCY] = df_fmt[ui.AMOUNT_CCY].apply(abs)
        df_fmt = df_fmt[(df_fmt.AmountCcy > threshold) & (df_fmt.FullType > 1)].sort_values(ui.AMOUNT_CCY, ascending=False)
        df_fmt = pd.DataFrame(df_fmt.to_records()).rename({"FullMasterType": "index", ui.AMOUNT_CCY: "size", "FullType": "count"}, axis=1)
        df_fmt["index"] = [f"MasterType: {k}" for k in df_fmt["index"]]

        df_ft = pd.pivot_table(
            df_exp_date, index="FullType", values=[ui.AMOUNT_CCY, "FullSubType"], aggfunc={ui.AMOUNT_CCY: sum, "FullSubType": lambda x: len(x.unique())}
        ).sort_values(ui.AMOUNT_CCY)
        df_ft[ui.AMOUNT_CCY] = df_ft[ui.AMOUNT_CCY].apply(abs)
        df_ft = df_ft[(df_ft.AmountCcy > threshold) & (df_ft.FullSubType > 1)].sort_values(ui.AMOUNT_CCY, ascending=False)
        df_ft = pd.DataFrame(df_ft.to_records()).rename({"FullType": "index", ui.AMOUNT_CCY: "size", "FullSubType": "count"}, axis=1)
        df_ft["index"] = [f"Type: {k}" for k in df_ft["index"]]

        df_st = pd.pivot_table(
            df_exp_date, index="FullSubType", values=[ui.AMOUNT_CCY, "MemoMapped"], aggfunc={ui.AMOUNT_CCY: sum, "MemoMapped": lambda x: len(x.unique())}
        ).sort_values(ui.AMOUNT_CCY)
        df_st[ui.AMOUNT_CCY] = df_st[ui.AMOUNT_CCY].apply(abs)
        df_st = df_st[(df_st.AmountCcy > threshold) & (df_st.MemoMapped > 1)].sort_values(ui.AMOUNT_CCY, ascending=False)
        df_st = pd.DataFrame(df_st.to_records()).rename({"FullSubType": "index", ui.AMOUNT_CCY: "size", "MemoMapped": "count"}, axis=1)
        df_st["index"] = [f"SubType: {k}" for k in df_st["index"]]

        return pd.concat([df_fmt, df_ft, df_st])["index"]


def read_csv(path: str, ref_currency: str, config) -> FinancialData:
    """Load all the Data"""
    return FinancialData(path, ref_currency, config)
