cd services/approval-request; pytest; cd ../..
python scripts/run_cedar_cli_tests.py
python scripts/test_cognito_auth.py
python scripts/phase9_approval_integration.py
cd infrastructure/cdk
npm run test
cd ../..
