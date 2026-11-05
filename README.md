# 1TECH | ReconPilot Public Demo v0.2.1

A public, sample-data-only demonstration of ReconPilot's bank-vs-books reconciliation workflow.

## Public demo safety boundary

- This build contains **no file uploader**. Visitors cannot upload bank statements or books exports.
- The app loads only the fictional CSV examples in `sample_data/`.
- Review decisions exist only in the current Streamlit session; download the report to keep the demo output.
- There is no login, customer database, multi-tenant design, or production security review.
- Do not treat this demo as suitable for confidential or live financial records.
- The matching engine is an aid. Always independently verify results.

## Run locally

Windows:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Open `http://localhost:8501`.

## Deploy free with Streamlit Community Cloud

1. Create or sign in to a GitHub account.
2. Create a **new public repository** named `reconpilot-public-demo`.
3. Upload the contents of this folder to the repository root (not the parent folder).
4. Visit https://share.streamlit.io/ and sign in with GitHub.
5. Choose **Create app**.
6. Select the repository `reconpilot-public-demo`, branch `main`, and main file path `app.py`.
7. Optionally choose an available app subdomain such as `1tech-reconpilot`.
8. Click **Deploy**. The first build may take a few minutes.
9. Test the public app in a private/incognito browser window. Confirm that the sample rows load, Human review works, and the Excel demo report downloads.

The deployed app will have a `*.streamlit.app` address. Streamlit Community Cloud currently offers free app hosting; free service has platform limits and is not a service-level guarantee. See https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy.

## Repository contents

- `app.py` — public demo interface; no upload control
- `reconpilot/` — matching engine, review workflow, Excel report exporter
- `sample_data/` — fictional sample CSVs
- `tests/` — core matching and review tests

## Product boundary

This is a demonstration build, not a customer-ready hosted finance application. Before accepting live customer data, 1TECH must design and test authentication, authorization, tenant isolation, secure storage, encryption, retention/deletion, audit logging, backups, monitoring, incident response, and applicable legal/compliance obligations.
