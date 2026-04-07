"""
Master Test Runner
Runs all test suites and generates comprehensive report
"""

import sys
import os
import subprocess
from datetime import datetime
import json

def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def run_command(command, description):
    """Run a command and return result"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Test timed out after 5 minutes"
    except Exception as e:
        return False, "", str(e)

def check_dependencies():
    """Check if required dependencies are installed"""
    print_header("CHECKING DEPENDENCIES")
    
    dependencies = {
        'Python': ['python', '--version'],
        'PostgreSQL': ['psql', '--version'],
    }
    
    all_ok = True
    for name, cmd in dependencies.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ {name}: {version}")
            else:
                print(f"⚠️  {name}: Not found")
                all_ok = False
        except FileNotFoundError:
            print(f"❌ {name}: Not installed")
            all_ok = False
    
    return all_ok

def check_database():
    """Check if database is accessible"""
    print_header("CHECKING DATABASE")
    
    try:
        # Try to import database module
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'core'))
        from database import db_manager
        
        session = db_manager.get_session()
        session.execute('SELECT 1')
        session.close()
        
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 To start database:")
        print("   cd docker")
        print("   docker-compose up -d postgres")
        return False

def run_unit_tests():
    """Run unit tests (no database required)"""
    print_header("UNIT TESTS (No Database Required)")
    
    success, stdout, stderr = run_command(
        f'python {os.path.join("tests", "test_comprehensive.py")}',
        "Running unit tests"
    )
    
    print(stdout)
    if stderr:
        print("STDERR:", stderr)
    
    return success

def run_integration_tests():
    """Run integration tests (database required)"""
    print_header("INTEGRATION TESTS (Database Required)")
    
    success, stdout, stderr = run_command(
        f'python {os.path.join("tests", "test_with_database.py")}',
        "Running integration tests"
    )
    
    print(stdout)
    if stderr:
        print("STDERR:", stderr)
    
    return success

def run_system_test():
    """Run existing system test"""
    print_header("SYSTEM TEST")
    
    if not os.path.exists(os.path.join("tests", "test_system.py")):
        print("⚠️  test_system.py not found, skipping")
        return True
    
    success, stdout, stderr = run_command(
        f'python {os.path.join("tests", "test_system.py")}',
        "Running system test"
    )
    
    print(stdout)
    if stderr:
        print("STDERR:", stderr)
    
    return success

def generate_report(results):
    """Generate test report"""
    print_header("TEST REPORT")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"Total Test Suites: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print()
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}  {test_name}")
    
    # Save report to file
    report = {
        'timestamp': datetime.now().isoformat(),
        'total': total,
        'passed': passed,
        'failed': failed,
        'results': {k: 'PASS' if v else 'FAIL' for k, v in results.items()}
    }
    
    report_file = os.path.join('tests', 'test_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_file}")
    
    return failed == 0

def main():
    """Main test runner"""
    print("=" * 80)
    print("  🔬 COMPREHENSIVE TEST SUITE")
    print("  Surveillance System - All Components")
    print("=" * 80)
    print(f"\n⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        print("\n⚠️  Some dependencies are missing. Tests may fail.")
        input("Press Enter to continue anyway, or Ctrl+C to abort...")
    
    # Check database
    db_available = check_database()
    
    # Run unit tests (always)
    results['Unit Tests'] = run_unit_tests()
    
    # Run integration tests (if database available)
    if db_available:
        results['Integration Tests'] = run_integration_tests()
    else:
        print_header("INTEGRATION TESTS (Database Required)")
        print("⚠️  Skipped: Database not available")
        results['Integration Tests'] = None  # Skipped
    
    # Run system test
    results['System Test'] = run_system_test()
    
    # Generate report
    all_passed = generate_report({k: v for k, v in results.items() if v is not None})
    
    # Final summary
    print_header("FINAL SUMMARY")
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ System is ready for deployment")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\n❌ Please review failures before deployment")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        print(f"\n⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
