#!/usr/bin/env python3
"""
Execute RASO Codebase Cleanup
Performs the actual cleanup operations with safety measures.
"""

import json
import logging
from pathlib import Path
from cleanup_orchestrator import CleanupOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Execute the cleanup process."""
    root_path = Path(".")
    
    # Initialize orchestrator with backup enabled
    orchestrator = CleanupOrchestrator(root_path, backup_enabled=True)
    
    print("🧹 RASO Codebase Cleanup")
    print("=" * 50)
    
    # Get preview first
    print("\n📊 Analyzing codebase...")
    preview = orchestrator.get_cleanup_preview()
    
    print(f"\n📋 Cleanup Preview:")
    print(f"  • Temporary files: {preview['temporary_files']['count']} files ({preview['temporary_files']['size_bytes']:,} bytes)")
    print(f"  • Duplicate groups: {preview['duplicate_files']['groups']} groups")
    print(f"  • Total duplicates: {preview['duplicate_files']['total_duplicates']} files")
    print(f"  • Total space to free: {preview['total_impact']['total_size_freed']:,} bytes ({preview['total_impact']['total_size_freed'] / (1024*1024):.1f} MB)")
    
    # Ask for confirmation
    response = input(f"\n❓ Proceed with cleanup? This will remove {preview['total_impact']['files_to_remove']} files. (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Cleanup cancelled by user.")
        return
    
    print("\n🚀 Starting cleanup process...")
    
    # Step 1: Clean temporary files
    print("\n1️⃣ Removing temporary files...")
    temp_result = orchestrator.cleanup_temporary_files()
    
    if temp_result.validation_passed:
        print(f"   ✅ Removed {temp_result.files_removed} temporary files")
        print(f"   💾 Freed {temp_result.size_freed:,} bytes")
        if temp_result.backup_manifest:
            print(f"   📦 Backup created: {temp_result.backup_manifest}")
    else:
        print(f"   ❌ Temporary file cleanup failed")
        if temp_result.errors:
            for error in temp_result.errors[:5]:  # Show first 5 errors
                print(f"      • {error}")
        return
    
    # Step 2: Consolidate duplicates
    print("\n2️⃣ Consolidating duplicate files...")
    dup_result = orchestrator.consolidate_duplicates(keep_strategy="primary")
    
    print(f"   ✅ Processed {dup_result.groups_processed} duplicate groups")
    print(f"   🗑️ Removed {dup_result.files_removed} duplicate files")
    print(f"   💾 Saved {dup_result.size_saved:,} bytes")
    
    if dup_result.errors:
        print(f"   ⚠️ {len(dup_result.errors)} errors occurred:")
        for error in dup_result.errors[:3]:  # Show first 3 errors
            print(f"      • {error}")
    
    # Step 3: Validate final state
    print("\n3️⃣ Validating cleanup results...")
    
    # Count remaining files in root
    root_files = [f for f in root_path.iterdir() if f.is_file()]
    print(f"   📁 Root directory now has {len(root_files)} files")
    
    if len(root_files) < 30:
        print(f"   ✅ Root directory file count target achieved (<30 files)")
    else:
        print(f"   ⚠️ Root directory still has many files (target: <30)")
    
    # Calculate total impact
    total_removed = temp_result.files_removed + dup_result.files_removed
    total_saved = temp_result.size_freed + dup_result.size_saved
    
    print(f"\n🎉 Cleanup Complete!")
    print(f"   📊 Total files removed: {total_removed}")
    print(f"   💾 Total space freed: {total_saved:,} bytes ({total_saved / (1024*1024):.1f} MB)")
    
    # Save cleanup report
    report = {
        "timestamp": temp_result.backup_manifest or "no_backup",
        "temporary_files": {
            "removed": temp_result.files_removed,
            "size_freed": temp_result.size_freed,
            "errors": len(temp_result.errors)
        },
        "duplicate_files": {
            "groups_processed": dup_result.groups_processed,
            "files_removed": dup_result.files_removed,
            "size_saved": dup_result.size_saved,
            "errors": len(dup_result.errors)
        },
        "final_state": {
            "root_files_count": len(root_files),
            "total_files_removed": total_removed,
            "total_size_freed": total_saved
        }
    }
    
    report_path = Path("cleanup_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"   📄 Cleanup report saved: {report_path}")
    
    if temp_result.backup_manifest:
        print(f"\n💡 Backup available at: {temp_result.backup_manifest}")
        print(f"   To restore if needed: python -c \"from cleanup_orchestrator import CleanupOrchestrator; CleanupOrchestrator('.').rollback_cleanup(Path('{temp_result.backup_manifest}/manifest.json'))\"")


if __name__ == "__main__":
    main()