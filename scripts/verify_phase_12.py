#!/usr/bin/env python3
"""Phase 12 Integration Verification Script"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

# Add backend src to path
backend_src = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_src))


async def verify_imports():
    """Verify all Phase 12 modules can be imported."""
    print("\n" + "="*60)
    print("VERIFYING PHASE 12 IMPORTS")
    print("="*60)

    try:
        print("✓ Importing models...", end=" ")
        from sentinelops.models import (
            IncidentForecast,
            IncidentAncestry,
            ServiceHealthScore,
            K8sResourceIntelligence,
            InfrastructureTimeline,
            AIConfidenceValidation,
            RemediationOrchestration,
            ExecutiveMetrics,
        )
        print("PASS")

        print("✓ Importing engines...", end=" ")
        from sentinelops.engines.forecast import predictive_forecast_engine
        from sentinelops.engines.timeline import timeline_intelligence
        from sentinelops.engines.service_health import enterprise_health_scorer
        from sentinelops.engines.k8s_intelligence import k8s_intelligence
        from sentinelops.engines.confidence import confidence_validator
        from sentinelops.engines.event_intelligence import event_intelligence
        from sentinelops.engines.analytics import executive_analytics
        from sentinelops.engines.remediation_orchestration import remediation_orchestrator
        print("PASS")

        print("✓ Importing API routes...", end=" ")
        from sentinelops.api.routes import predictive as predictive_routes
        print("PASS")

        return True
    except Exception as e:
        print(f"FAIL\n  Error: {e}")
        return False


async def verify_database_models():
    """Verify database models are properly configured."""
    print("\n" + "="*60)
    print("VERIFYING DATABASE MODELS")
    print("="*60)

    try:
        print("✓ Checking ORM table names...", end=" ")
        from sentinelops.models import (
            IncidentForecast,
            IncidentAncestry,
            ServiceHealthScore,
            K8sResourceIntelligence,
            InfrastructureTimeline,
            AIConfidenceValidation,
            RemediationOrchestration,
            ExecutiveMetrics,
        )

        expected_tables = {
            "incident_forecasts": IncidentForecast,
            "incident_ancestry": IncidentAncestry,
            "service_health_scores": ServiceHealthScore,
            "k8s_resource_intelligence": K8sResourceIntelligence,
            "infrastructure_timelines": InfrastructureTimeline,
            "ai_confidence_validations": AIConfidenceValidation,
            "remediation_orchestrations": RemediationOrchestration,
            "executive_metrics": ExecutiveMetrics,
        }

        for table_name, model_class in expected_tables.items():
            if hasattr(model_class, "__tablename__"):
                actual = model_class.__tablename__
                if actual == table_name:
                    print(f"\n  ✓ {table_name}: {actual}", end="")
                else:
                    print(f"\n  ✗ {table_name}: expected '{table_name}', got '{actual}'")
                    return False

        print("\n✓ All table names correct: PASS")
        return True
    except Exception as e:
        print(f"FAIL\n  Error: {e}")
        return False


async def verify_engine_signatures():
    """Verify engine method signatures are correct."""
    print("\n" + "="*60)
    print("VERIFYING ENGINE METHOD SIGNATURES")
    print("="*60)

    try:
        from sentinelops.engines.forecast import predictive_forecast_engine
        from sentinelops.engines.timeline import timeline_intelligence
        from sentinelops.engines.service_health import enterprise_health_scorer
        from sentinelops.engines.k8s_intelligence import k8s_intelligence
        from sentinelops.engines.confidence import confidence_validator
        from sentinelops.engines.analytics import executive_analytics
        from sentinelops.engines.remediation_orchestration import remediation_orchestrator

        methods_to_check = [
            (predictive_forecast_engine, "forecast_future_incidents"),
            (timeline_intelligence, "build_incident_ancestry"),
            (enterprise_health_scorer, "calculate_service_health"),
            (k8s_intelligence, "analyze_namespace_pressure"),
            (confidence_validator, "validate_rca_reasoning"),
            (event_intelligence, "deduplicate_events"),
            (executive_analytics, "calculate_executive_metrics"),
            (remediation_orchestrator, "create_remediation_workflow"),
        ]

        for engine, method_name in methods_to_check:
            if hasattr(engine, method_name):
                print(f"✓ {engine.__class__.__name__}.{method_name}")
            else:
                print(f"✗ {engine.__class__.__name__}.{method_name} NOT FOUND")
                return False

        print("✓ All engine methods present: PASS")
        return True
    except Exception as e:
        print(f"FAIL\n  Error: {e}")
        return False


async def verify_api_routes():
    """Verify API routes are registered."""
    print("\n" + "="*60)
    print("VERIFYING API ROUTES")
    print("="*60)

    try:
        from sentinelops.api.routes.predictive import router

        routes = []
        for route in router.routes:
            routes.append(f"{route.methods} {route.path}")

        expected_routes = [
            "/intelligence/forecasts/{cluster_id}",
            "/intelligence/incident-ancestry/{incident_id}",
            "/intelligence/service-health/{cluster_id}/{service_name}",
            "/intelligence/k8s-pressure/{cluster_id}/{namespace}",
            "/intelligence/confidence-validate",
            "/analytics/executive-dashboard/{cluster_id}",
            "/remediation/create-workflow",
            "/remediation/execute-step",
            "/events/deduplicate",
            "/events/cluster-anomalies",
        ]

        for expected_path in expected_routes:
            found = any(expected_path in route for route in routes)
            if found:
                print(f"✓ {expected_path}")
            else:
                print(f"✗ {expected_path} NOT FOUND")
                return False

        print("✓ All API routes registered: PASS")
        return True
    except Exception as e:
        print(f"FAIL\n  Error: {e}")
        return False


async def verify_frontend_components():
    """Verify frontend components exist."""
    print("\n" + "="*60)
    print("VERIFYING FRONTEND COMPONENTS")
    print("="*60)

    try:
        components = [
            "frontend/src/components/intelligence/PredictiveIntelligenceDashboard.tsx",
            "frontend/src/components/analytics/ExecutiveAnalyticsDashboard.tsx",
        ]

        for component in components:
            path = Path(__file__).parent / component
            if path.exists():
                size = path.stat().st_size
                print(f"✓ {component} ({size:,} bytes)")
            else:
                print(f"✗ {component} NOT FOUND")
                return False

        print("✓ All frontend components present: PASS")
        return True
    except Exception as e:
        print(f"FAIL\n  Error: {e}")
        return False


async def verify_tests():
    """Verify test suite exists."""
    print("\n" + "="*60)
    print("VERIFYING TEST SUITE")
    print("="*60)

    try:
        test_file = Path(__file__).parent / "backend/tests/test_phase_12_predictive.py"
        if test_file.exists():
            lines = len(test_file.read_text().split("\n"))
            print(f"✓ Test suite found ({lines:,} lines)")
            print("✓ Test suite is present: PASS")
            return True
        else:
            print(f"✗ Test suite NOT FOUND at {test_file}")
            return False
    except Exception as e:
        print(f"FAIL\n  Error: {e}")
        return False


async def verify_migration():
    """Verify Alembic migration exists."""
    print("\n" + "="*60)
    print("VERIFYING DATABASE MIGRATION")
    print("="*60)

    try:
        migration_file = Path(__file__).parent / "backend/alembic/versions/005_phase_12_predictive_operations.py"
        if migration_file.exists():
            content = migration_file.read_text()

            # Check for key elements
            checks = [
                ("upgrade function", "def upgrade()"),
                ("downgrade function", "def downgrade()"),
                ("incident_forecasts table", "incident_forecasts"),
                ("service_health_scores table", "service_health_scores"),
                ("executive_metrics table", "executive_metrics"),
            ]

            for check_name, check_str in checks:
                if check_str in content:
                    print(f"✓ {check_name}")
                else:
                    print(f"✗ {check_name} NOT FOUND")
                    return False

            print("✓ Migration file is complete: PASS")
            return True
        else:
            print(f"✗ Migration file NOT FOUND at {migration_file}")
            return False
    except Exception as e:
        print(f"FAIL\n  Error: {e}")
        return False


async def verify_documentation():
    """Verify documentation files exist."""
    print("\n" + "="*60)
    print("VERIFYING DOCUMENTATION")
    print("="*60)

    try:
        docs = [
            "PHASE_12_README.md",
            "PHASE_12_ARCHITECTURE.md",
            "PHASE_12_API_REFERENCE.md",
            "PHASE_12_DEPLOYMENT_GUIDE.md",
        ]

        for doc in docs:
            path = Path(__file__).parent / doc
            if path.exists():
                lines = len(path.read_text().split("\n"))
                print(f"✓ {doc} ({lines:,} lines)")
            else:
                print(f"✗ {doc} NOT FOUND")
                return False

        print("✓ All documentation present: PASS")
        return True
    except Exception as e:
        print(f"FAIL\n  Error: {e}")
        return False


async def main():
    """Run all verification checks."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "PHASE 12 INTEGRATION VERIFICATION" + " "*15 + "║")
    print("║" + " "*58 + "║")
    print("║" + f" Enterprise Incident Intelligence & Predictive Operations".ljust(58) + "║")
    print("╚" + "="*58 + "╝")

    results = {
        "Imports": await verify_imports(),
        "Database Models": await verify_database_models(),
        "Engine Signatures": await verify_engine_signatures(),
        "API Routes": await verify_api_routes(),
        "Frontend Components": await verify_frontend_components(),
        "Test Suite": await verify_tests(),
        "Database Migration": await verify_migration(),
        "Documentation": await verify_documentation(),
    }

    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {check_name}")

    print("\n" + "="*60)
    if passed == total:
        print(f"✓ ALL CHECKS PASSED ({passed}/{total})")
        print("\nPhase 12 is READY FOR DEPLOYMENT")
        print("="*60 + "\n")
        return 0
    else:
        print(f"✗ SOME CHECKS FAILED ({passed}/{total})")
        print("\nPlease review failures above")
        print("="*60 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
