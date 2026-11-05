from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from reconpilot.engine import reconcile
from reconpilot.review import (
    DECISION_OPTIONS,
    create_review_workspace,
    empty_decision_log,
    latest_decision_counts,
    record_review_changes,
)
from reconpilot.io_utils import standardize_transactions
from reconpilot.report import build_excel_report

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="ReconPilot | 1TECH",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.8rem; padding-bottom: 3rem; max-width: 1440px;}
      .brand {font-size: .8rem; letter-spacing: .18em; text-transform: uppercase; color: #8b93a7; font-weight: 700;}
      .hero {padding: 1.35rem 1.5rem; border: 1px solid rgba(130,140,170,.22); border-radius: 18px;
             background: linear-gradient(120deg, rgba(91,74,190,.13), rgba(55,165,160,.09));}
      .hero h1 {margin: .15rem 0 .35rem 0; font-size: 2.25rem;}
      .hero p {color: #aeb6c8; margin: 0;}
      .small-muted {color: #929bad; font-size: .88rem;}
      div[data-testid="stMetric"] {background: rgba(125,135,160,.07); padding: 14px 16px; border-radius: 14px; border: 1px solid rgba(125,135,160,.15);}
    </style>
    """,
    unsafe_allow_html=True,
)


def load_demo_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load bundled fictional examples. The public demo intentionally accepts no uploads."""
    bank_raw = pd.read_csv(ROOT / "sample_data" / "bank_statement.csv")
    books_raw = pd.read_csv(ROOT / "sample_data" / "books_export.csv")

    bank_mapping = {
        "date_col": "Date",
        "amount_col": "Amount",
        "debit_col": None,
        "credit_col": None,
        "reference_col": "Reference",
        "description_col": "Description",
        "dayfirst": True,
    }
    books_mapping = {
        "date_col": "Voucher Date",
        "amount_col": "Net Amount",
        "debit_col": None,
        "credit_col": None,
        "reference_col": "Voucher Ref",
        "description_col": "Particulars",
        "dayfirst": True,
    }
    bank = standardize_transactions(bank_raw, bank_mapping, "Demo bank")
    books = standardize_transactions(books_raw, books_mapping, "Demo books")
    return bank, books


def run_demo(amount_tolerance: float, date_tolerance: int) -> None:
    bank, books = load_demo_data()
    result = reconcile(
        bank,
        books,
        amount_tolerance=float(amount_tolerance),
        date_tolerance_days=int(date_tolerance),
    )
    st.session_state["recon_result"] = result
    st.session_state["review_decision_log"] = empty_decision_log()
    st.session_state["recon_meta"] = {
        "bank_rows": len(bank),
        "books_rows": len(books),
        "amount_tolerance": float(amount_tolerance),
        "date_tolerance": int(date_tolerance),
    }
    st.session_state.pop("review_editor", None)


st.markdown('<div class="brand">1TECH · FINANCIAL WORKFLOW TOOLS</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="hero">
      <h1>🧭 ReconPilot</h1>
      <p>Reconciliation that shows its work. Explore matching, exceptions, human review, and an audit-friendly Excel report.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

st.info(
    "PUBLIC DEMO · This version uses fictional sample transactions bundled with the app. "
    "File uploads are disabled. Do not enter or share personal, banking, or confidential business data."
)

with st.sidebar:
    st.header("Demo settings")
    amount_tolerance = st.number_input(
        "Amount tolerance", min_value=0.0, value=0.01, step=0.01,
        help="Maximum absolute difference treated as an amount match. Use 0 for exact matching.",
    )
    date_tolerance = st.number_input(
        "Date tolerance (days)", min_value=0, max_value=365, value=3, step=1,
        help="Maximum difference between transaction dates for a suggested match.",
    )
    if st.button("Run demo reconciliation", type="primary", use_container_width=True):
        run_demo(amount_tolerance, date_tolerance)
        st.rerun()
    st.divider()
    st.caption("Sample data is fictional and included in the source repository.")
    st.caption("Public demonstration · v0.2.1")

if "recon_result" not in st.session_state:
    run_demo(amount_tolerance, date_tolerance)

bank_raw = pd.read_csv(ROOT / "sample_data" / "bank_statement.csv")
books_raw = pd.read_csv(ROOT / "sample_data" / "books_export.csv")
with st.expander("View fictional sample files"):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Sample bank statement**")
        st.dataframe(bank_raw, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("**Sample books export**")
        st.dataframe(books_raw, use_container_width=True, hide_index=True)

result = st.session_state["recon_result"]
meta = st.session_state.get("recon_meta", {})
st.divider()
st.subheader("Reconciliation results")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Confirmed matches", len(result["matched"]))
m2.metric("Needs review", len(result["review"]))
m3.metric("Unmatched bank", len(result["unmatched_bank"]))
m4.metric("Unmatched books", len(result["unmatched_books"]))
st.caption(
    f"Compared {meta.get('bank_rows', 0):,} fictional bank rows with {meta.get('books_rows', 0):,} fictional books rows · "
    f"Amount tolerance: {meta.get('amount_tolerance', 0)} · Date tolerance: {meta.get('date_tolerance', 0)} days"
)
st.warning(
    "Only unique reference + amount + date matches are confirmed automatically. "
    "All other pairings are suggestions for a person to inspect."
)

decision_log = st.session_state.setdefault("review_decision_log", empty_decision_log())
decision_counts = latest_decision_counts(decision_log)
r1, r2, r3 = st.columns(3)
r1.metric("Manually approved", decision_counts["Approve pair"])
r2.metric("Manually rejected", decision_counts["Reject pair"])
r3.metric(
    "Still pending",
    max(0, len(result["review"]) - decision_counts["Approve pair"] - decision_counts["Reject pair"]),
)

t1, t2, t3, t4 = st.tabs(["Confirmed matches", "Human review", "Unmatched bank", "Unmatched books"])
with t1:
    st.caption("Rule-confirmed matches use a unique reference, amount, and date within the selected tolerances.")
    st.dataframe(result["matched"], use_container_width=True, hide_index=True)
with t2:
    st.caption("Try approving or rejecting a suggested pair. Add a note, then save your decision.")
    if result["review"].empty:
        st.success("No review candidates in this demo run.")
    else:
        workspace = create_review_workspace(result["review"], decision_log)
        editable_columns = ["Decision", "Reviewer note"]
        locked_columns = [col for col in workspace.columns if col not in editable_columns]
        edited_workspace = st.data_editor(
            workspace,
            use_container_width=True,
            hide_index=True,
            disabled=locked_columns,
            column_config={
                "Decision": st.column_config.SelectboxColumn(
                    "Decision", options=DECISION_OPTIONS, required=True,
                    help="This records a review decision only. It does not post an accounting entry.",
                ),
                "Reviewer note": st.column_config.TextColumn(
                    "Reviewer note", help="Optional reason for the decision.",
                ),
            },
            key="review_editor",
        )
        if st.button("Save review decisions", type="primary", key="save_review_decisions"):
            try:
                updated_log = record_review_changes(edited_workspace, decision_log)
                added = len(updated_log) - len(decision_log)
                st.session_state["review_decision_log"] = updated_log
                if added:
                    st.success(f"Saved {added} review event(s). Download the workbook to keep this demo session's history.")
                else:
                    st.info("No decision changes to save.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not save review decisions: {exc}")
    if not decision_log.empty:
        with st.expander("Decision history"):
            st.dataframe(decision_log, use_container_width=True, hide_index=True)
with t3:
    st.dataframe(result["unmatched_bank"], use_container_width=True, hide_index=True)
with t4:
    st.dataframe(result["unmatched_books"], use_container_width=True, hide_index=True)

report = build_excel_report(result, meta, decision_log=decision_log)
st.download_button(
    "⬇ Download sample Excel reconciliation report",
    data=report,
    file_name="ReconPilot_Demo_Reconciliation_Report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
    use_container_width=True,
)

st.divider()
st.markdown(
    "<p class='small-muted'>ReconPilot is an experimental demonstration, not production accounting software. "
    "It does not connect to banks or Tally, post entries, file returns, move money, or replace professional review. "
    "All included transactions are fictional. Public demo uploads are disabled.</p>",
    unsafe_allow_html=True,
)
