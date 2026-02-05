#!/usr/bin/env python3
"""
RASO Codebase Cleanup Master Script
Complete orchestration of cleanup, reorganization, security hardening, and quality improvements.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import our cleanup modules
from cleanup_infrastructure import FileAnalyzer, BackupManager
from cleanup_orchestrator import CleanupOrchestrator
from structure_reorganizer import StructureReorganizer
from security_hardener import SecurityHardener

# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Set up logging configuration."""
    level = getattr(logging, log_level.upper())
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

logger = logging.getLogger(__name__)


class RASOMasterCleanup:
    """Master cleanup orchestrator for RASO codebase transformation."""
    
    def __init__(self, root_path: Path, dry_run: bool = False, backup_enabled: bool = True):
        """Initialize master cleanup orchestrator."""
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        self.backup_enabled = backup_enabled
        
        # Initialize components
        self.file_analyzer = FileAnalyzer(root_path)
        self.cleanup_orchestrator = CleanupOrchestrator(root_path, backup_enabled)
        self.structure_reorganizer = StructureReorganizer(root_path, dry_run)
        self.security_hardener = SecurityHardener(root_path, dry_run)
        
        # Set dry run mode for all components
        if dry_run:
            self.cleanup_orchestrator.set_dry_run(True)
        
        # Results tracking
        self.results = {
            'start_time': datetime.now().isoformat(),
            'phases': {},
            'summary': {},
            'errors': []
        }
    
    def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze current codebase state."""
        logger.info("🔍 Analyzing current codebase state")
        
        try:
            # File inventory
            inventory = self.file_analyzer.scan_directory()
            
            # Security scan
            secrets = self.security_hardener.scan_for_secrets()
            
            # Structure analysis
            structure_categories = self.structure_reorganizer.analyze_current_structure()
            
            analysis = {
                'total_files': inventory.total_files,
                'file_categories': {
                    'temporary': len(inventory.temporary_files),
                    'production': len(inventory.production_files),
                    'test': len(inventory.test_files),
                    'config': len(inventory.config_files),
                    'documentation': len(inventory.documentation_files)
                },
                'duplicates': {
                    'groups': len(inventory.duplicate_groups),
                    'total_duplicates': sum(len(files) - 1 for files in inventory.duplicate_groups.values())
                },
                'security': {
                    'secrets_found': len(secrets),
                    'secret_types': list(set(s.secret_type for s in secrets))
                },
                'structure': {
                    category: len(files) for category, files in structure_categories.items()
                }
            }
            
            self.results['phases']['analysis'] = {
                'status': 'completed',
                'data': analysis
            }
            
            logger.info("✅ Codebase analysis complete")
            return analysis
            
        except Exception as e:
            error_msg = f"Codebase analysis failed: {e}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            raise
    
    def execute_cleanup(self) -> Dict[str, Any]:
        """Execute file cleanup phase."""
        logger.info("🧹 Executing file cleanup phase")
        
        try:
            # Get cleanup preview
            preview = self.cleanup_orchestrator.get_cleanup_preview()
            
            # Execute temporary file cleanup
            temp_result = self.cleanup_orchestrator.cleanup_temporary_files()
            
            # Execute duplicate consolidation
            dup_result = self.cleanup_orchestrator.consolidate_duplicates(keep_strategy="primary")
            
            cleanup_results = {
                'preview': preview,
                'temporary_files': {
                    'removed': temp_result.files_removed,
                    'size_freed': temp_result.size_freed,
                    'backup_created': temp_result.backup_manifest is not None,
                    'validation_passed': temp_result.validation_passed,
                    'errors': len(temp_result.errors)
                },
                'duplicates': {
                    'groups_processed': dup_result.groups_processed,
                    'files_removed': dup_result.files_removed,
                    'size_saved': dup_result.size_saved,
                    'errors': len(dup_result.errors)
                },
                'total_impact': {
                    'files_removed': temp_result.files_removed + dup_result.files_removed,
                    'size_freed': temp_result.size_freed + dup_result.size_saved
                }
            }
            
            self.results['phases']['cleanup'] = {
                'status': 'completed',
                'data': cleanup_results
            }
            
            logger.info(f"✅ Cleanup complete: {cleanup_results['total_impact']['files_removed']} files removed")
            return cleanup_results
            
        except Exception as e:
            error_msg = f"File cleanup failed: {e}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            raise
    
    def execute_security_hardening(self) -> Dict[str, Any]:
        """Execute security hardening phase."""
        logger.info("🔒 Executing security hardening phase")
        
        try:
            # Execute complete security hardening
            security_result = self.security_hardener.secure_configuration()
            
            security_results = {
                'secrets_found': security_result.secrets_found,
                'secrets_replaced': security_result.secrets_replaced,
                'templates_created': security_result.templates_created,
                'config_files_secured': security_result.config_files_secured,
                'errors': len(security_result.errors)
            }
            
            self.results['phases']['security'] = {
                'status': 'completed',
                'data': security_results
            }
            
            logger.info(f"✅ Security hardening complete: {security_results['secrets_replaced']} secrets secured")
            return security_results
            
        except Exception as e:
            error_msg = f"Security hardening failed: {e}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            raise
    
    def execute_structure_reorganization(self) -> Dict[str, Any]:
        """Execute structure reorganization phase."""
        logger.info("🏗️ Executing structure reorganization phase")
        
        try:
            # Execute complete project reorganization
            structure_result = self.structure_reorganizer.reorganize_project()
            
            structure_results = {
                'directories_created': structure_result.directories_created,
                'files_moved': structure_result.files_moved,
                'imports_updated': structure_result.imports_updated,
                'errors': len(structure_result.errors)
            }
            
            self.results['phases']['structure'] = {
                'status': 'completed',
                'data': structure_results
            }
            
            logger.info(f"✅ Structure reorganization complete: {structure_results['files_moved']} files moved")
            return structure_results
            
        except Exception as e:
            error_msg = f"Structure reorganization failed: {e}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            raise
    
    def validate_final_state(self) -> Dict[str, Any]:
        """Validate the final state after cleanup."""
        logger.info("✅ Validating final codebase state")
        
        try:
            # Re-analyze codebase
            final_inventory = self.file_analyzer.scan_directory()
            
            # Count root directory files
            root_files = [f for f in self.root_path.iterdir() if f.is_file()]
            
            # Check for remaining issues
            remaining_secrets = self.security_hardener.scan_for_secrets()
            
            validation = {
                'final_file_count': final_inventory.total_files,
                'root_directory_files': len(root_files),
                'root_target_achieved': len(root_files) < 30,
                'remaining_temporary_files': len(final_inventory.temporary_files),
                'remaining_duplicates': sum(len(files) - 1 for files in final_inventory.duplicate_groups.values()),
                'remaining_secrets': len(remaining_secrets),
                'structure_compliant': self._check_structure_compliance()
            }
            
            self.results['phases']['validation'] = {
                'status': 'completed',
                'data': validation
            }
            
            logger.info("✅ Final state validation complete")
            return validation
            
        except Exception as e:
            error_msg = f"Final state validation failed: {e}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            raise
    
    def _check_structure_compliance(self) -> bool:
        """Check if project structure follows Python standards."""
        try:
            required_dirs = ['src/raso', 'tests', 'docs']
            
            for dir_path in required_dirs:
                full_path = self.root_path / dir_path
                if not full_path.exists():
                    return False
            
            # Check for __init__.py files
            raso_init = self.root_path / 'src' / 'raso' / '__init__.py'
            if not raso_init.exists():
                return False
            
            return True
            
        except Exception:
            return False
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report."""
        logger.info("📊 Generating summary report")
        
        self.results['end_time'] = datetime.now().isoformat()
        
        # Calculate totals
        total_files_removed = 0
        total_size_freed = 0
        
        if 'cleanup' in self.results['phases']:
            cleanup_data = self.results['phases']['cleanup']['data']
            total_files_removed = cleanup_data['total_impact']['files_removed']
            total_size_freed = cleanup_data['total_impact']['size_freed']
        
        # Generate summary
        summary = {
            'execution_mode': 'dry_run' if self.dry_run else 'actual',
            'backup_enabled': self.backup_enabled,
            'total_phases': len(self.results['phases']),
            'successful_phases': len([p for p in self.results['phases'].values() if p['status'] == 'completed']),
            'total_errors': len(self.results['errors']),
            'impact': {
                'files_removed': total_files_removed,
                'size_freed_mb': round(total_size_freed / (1024 * 1024), 2),
                'directories_created': self.results['phases'].get('structure', {}).get('data', {}).get('directories_created', 0),
                'files_moved': self.results['phases'].get('structure', {}).get('data', {}).get('files_moved', 0),
                'secrets_secured': self.results['phases'].get('security', {}).get('data', {}).get('secrets_replaced', 0)
            }
        }
        
        self.results['summary'] = summary
        
        return summary
    
    def save_results(self, output_path: Optional[Path] = None) -> Path:
        """Save complete results to JSON file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.root_path / f"raso_cleanup_results_{timestamp}.json"
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📄 Results saved to: {output_path}")
        return output_path
    
    def execute_complete_cleanup(self) -> Dict[str, Any]:
        """Execute the complete cleanup process."""
        logger.info("🚀 Starting RASO codebase transformation")
        
        try:
            # Phase 1: Analysis
            print("\n" + "="*60)
            print("📊 PHASE 1: CODEBASE ANALYSIS")
            print("="*60)
            analysis = self.analyze_codebase()
            self._print_analysis_summary(analysis)
            
            # Phase 2: Cleanup
            print("\n" + "="*60)
            print("🧹 PHASE 2: FILE CLEANUP")
            print("="*60)
            cleanup_results = self.execute_cleanup()
            self._print_cleanup_summary(cleanup_results)
            
            # Phase 3: Security
            print("\n" + "="*60)
            print("🔒 PHASE 3: SECURITY HARDENING")
            print("="*60)
            security_results = self.execute_security_hardening()
            self._print_security_summary(security_results)
            
            # Phase 4: Structure (only if not dry run)
            if not self.dry_run:
                print("\n" + "="*60)
                print("🏗️ PHASE 4: STRUCTURE REORGANIZATION")
                print("="*60)
                structure_results = self.execute_structure_reorganization()
                self._print_structure_summary(structure_results)
            
            # Phase 5: Validation
            print("\n" + "="*60)
            print("✅ PHASE 5: FINAL VALIDATION")
            print("="*60)
            validation = self.validate_final_state()
            self._print_validation_summary(validation)
            
            # Generate and save results
            summary = self.generate_summary_report()
            results_path = self.save_results()
            
            # Print final summary
            print("\n" + "="*60)
            print("🎉 CLEANUP COMPLETE!")
            print("="*60)
            self._print_final_summary(summary)
            print(f"\n📄 Detailed results: {results_path}")
            
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Cleanup process failed: {e}")
            self.results['status'] = 'failed'
            self.results['error'] = str(e)
            raise
    
    def _print_analysis_summary(self, analysis: Dict[str, Any]):
        """Print analysis phase summary."""
        print(f"📁 Total files: {analysis['total_files']}")
        print(f"🗑️ Temporary files: {analysis['file_categories']['temporary']}")
        print(f"📋 Production files: {analysis['file_categories']['production']}")
        print(f"🧪 Test files: {analysis['file_categories']['test']}")
        print(f"⚙️ Config files: {analysis['file_categories']['config']}")
        print(f"📚 Documentation: {analysis['file_categories']['documentation']}")
        print(f"👥 Duplicate groups: {analysis['duplicates']['groups']}")
        print(f"🔍 Secrets found: {analysis['security']['secrets_found']}")
    
    def _print_cleanup_summary(self, results: Dict[str, Any]):
        """Print cleanup phase summary."""
        print(f"🗑️ Temporary files removed: {results['temporary_files']['removed']}")
        print(f"👥 Duplicate files removed: {results['duplicates']['files_removed']}")
        print(f"💾 Total space freed: {results['total_impact']['size_freed']:,} bytes ({results['total_impact']['size_freed'] / (1024*1024):.1f} MB)")
        print(f"📦 Backup created: {'Yes' if results['temporary_files']['backup_created'] else 'No'}")
    
    def _print_security_summary(self, results: Dict[str, Any]):
        """Print security phase summary."""
        print(f"🔐 Secrets replaced: {results['secrets_replaced']}")
        print(f"📋 Templates created: {results['templates_created']}")
        print(f"⚙️ Config files secured: {results['config_files_secured']}")
    
    def _print_structure_summary(self, results: Dict[str, Any]):
        """Print structure phase summary."""
        print(f"📁 Directories created: {results['directories_created']}")
        print(f"📄 Files moved: {results['files_moved']}")
        print(f"🔗 Imports updated: {results['imports_updated']}")
    
    def _print_validation_summary(self, validation: Dict[str, Any]):
        """Print validation phase summary."""
        print(f"📁 Final file count: {validation['final_file_count']}")
        print(f"🏠 Root directory files: {validation['root_directory_files']}")
        print(f"🎯 Root target achieved: {'Yes' if validation['root_target_achieved'] else 'No'}")
        print(f"🗑️ Remaining temporary files: {validation['remaining_temporary_files']}")
        print(f"👥 Remaining duplicates: {validation['remaining_duplicates']}")
        print(f"🔐 Remaining secrets: {validation['remaining_secrets']}")
        print(f"🏗️ Structure compliant: {'Yes' if validation['structure_compliant'] else 'No'}")
    
    def _print_final_summary(self, summary: Dict[str, Any]):
        """Print final summary."""
        print(f"🎯 Execution mode: {summary['execution_mode']}")
        print(f"✅ Successful phases: {summary['successful_phases']}/{summary['total_phases']}")
        print(f"❌ Total errors: {summary['total_errors']}")
        print(f"🗑️ Files removed: {summary['impact']['files_removed']}")
        print(f"💾 Space freed: {summary['impact']['size_freed_mb']} MB")
        print(f"📁 Directories created: {summary['impact']['directories_created']}")
        print(f"📄 Files moved: {summary['impact']['files_moved']}")
        print(f"🔐 Secrets secured: {summary['impact']['secrets_secured']}")


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="RASO Codebase Cleanup Master Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python raso_cleanup_master.py --dry-run          # Preview changes
  python raso_cleanup_master.py --execute          # Execute cleanup
  python raso_cleanup_master.py --no-backup        # Execute without backup
        """
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Preview changes without executing them'
    )
    
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute the cleanup (required if not dry-run)'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Disable backup creation (not recommended)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='Log to file in addition to console'
    )
    
    parser.add_argument(
        '--root-path',
        type=str,
        default='.',
        help='Root path of the project (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.dry_run and not args.execute:
        parser.error("Must specify either --dry-run or --execute")
    
    if args.dry_run and args.execute:
        parser.error("Cannot specify both --dry-run and --execute")
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Initialize cleanup
    root_path = Path(args.root_path)
    backup_enabled = not args.no_backup
    
    cleanup = RASOMasterCleanup(
        root_path=root_path,
        dry_run=args.dry_run,
        backup_enabled=backup_enabled
    )
    
    try:
        # Execute cleanup
        results = cleanup.execute_complete_cleanup()
        
        # Exit with success
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n❌ Cleanup interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()