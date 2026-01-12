"""
Email Categorizer - Core Logic
Categorizes volunteer application emails based on keywords.
Inspired by manually sorting 600+ emails at Toronto Animal Services.
"""

import os
import re
import logging
import csv
import argparse
from collections import defaultdict
from datetime import datetime

# ======================
# LOGGING SETUP
# ======================
def setup_logging():
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(logs_dir, 'email_categorizer.log')),
            logging.StreamHandler()  # Also print to console
        ]
    )
    return logging.getLogger(__name__)

# Initialize logger
logger = setup_logging()

# ======================
# CATEGORY DEFINITIONS
# ======================
# Based on my real work sorting emails for TAS!
CATEGORIES = {
    "DOG_FOSTER": ["dog", "dogs", "puppy", "puppies", "canine", "hound"],
    "CAT_FOSTER": ["cat", "cats", "kitten", "kittens", "feline"],
    "SMALL_ANIMAL": ["rabbit", "rabbits", "guinea pig", "hamster", "small animal"],
    "VOLUNTEER": ["volunteer", "volunteers", "cuddle", "socialize", "help"],
    "EVENTS": ["event", "events", "outreach", "community", "festival"],
    "GENERAL_INQUIRY": []  # Default category
}

# ======================
# CORE FUNCTION - FIXED VERSION
# ======================
def categorize_email(content):
    """
    Categorizes email content based on keyword matching.
    
    Args:
        content (str): Email text
    
    Returns:
        str: Category name
    """
    content_lower = content.lower()
    
    # Simple and effective: check for keywords
    if any(word in content_lower for word in ["dog", "dogs", "puppy", "puppies"]):
        return "DOG_FOSTER"
    elif any(word in content_lower for word in ["cat", "cats", "kitten", "kittens"]):
        return "CAT_FOSTER"
    elif any(word in content_lower for word in ["rabbit", "guinea pig", "hamster", "small animal"]):
        return "SMALL_ANIMAL"
    elif any(word in content_lower for word in ["volunteer", "cuddle", "socialize", "help"]):
        return "VOLUNTEER"
    elif any(word in content_lower for word in ["event", "outreach", "community", "festival"]):
        return "EVENTS"
    else:
        return "GENERAL_INQUIRY"

# ======================
# FILE PROCESSING WITH ERROR HANDLING
# ======================
def process_single_email(filepath):
    """Reads and categorizes a single email file with error handling."""
    filename = os.path.basename(filepath)
    
    try:
        # 1. Check if file exists
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filename}")
            return None
        
        # 2. Check file size (skip empty files)
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            logger.warning(f"Empty file: {filename}")
            return None
        
        # 3. Warn about large files (optional)
        if file_size > 1024 * 1024:  # 1MB
            logger.info(f"Large file: {filename} ({file_size/1024:.1f} KB)")
        
        # 4. Read file with error handling
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 5. Check if file has actual content
        if not content.strip():
            logger.warning(f"No content in: {filename}")
            return None
        
        # 6. Categorize the content
        category = categorize_email(content)
        logger.info(f"Processed: {filename} → {category}")
        
        # 7. Extract subject from email (better preview)
        subject = "No subject"
        for line in content.strip().split('\n'):
            if line.lower().startswith('subject:'):
                subject = line[8:].strip()  # Remove 'Subject: '
                break
        
        # If no subject found, use first non-empty line
        if subject == "No subject":
            lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
            if lines:
                subject = lines[0][:50]  # First 50 chars of first line
        
        return {
            'filename': filename,
            'subject': subject[:60] + "..." if len(subject) > 60 else subject,
            'category': category,
            'filepath': filepath,
            'size_bytes': file_size
        }
        
    except UnicodeDecodeError:
        # Handle files that aren't UTF-8 encoded
        logger.error(f"Encoding error: {filename} (not UTF-8)")
        return None
    except PermissionError:
        logger.error(f"Permission denied: {filename}")
        return None
    except IsADirectoryError:
        logger.error(f"Is a directory: {filename}")
        return None
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error with {filename}: {type(e).__name__} - {str(e)[:50]}")
        return None

# ======================
# ENHANCED STATISTICS
# ======================
def generate_statistics(email_data):
    """
    Generates comprehensive statistics.
    
    Returns:
        dict: Detailed statistics including percentages and insights
    """
    if not email_data:
        logger.warning("No email data provided for statistics")
        return {}
    
    stats = defaultdict(int)
    category_previews = defaultdict(list)
    total_size = 0
    categories_found = set()
    
    # Collect data
    for email in email_data:
        if email:
            category = email['category']
            stats[category] += 1
            categories_found.add(category)
            total_size += email.get('size_bytes', 0)
            
            # Store preview (subject) for each category
            preview = email.get('subject', 'No subject')
            if len(category_previews[category]) < 3:  # Keep only 3 previews per category
                category_previews[category].append(preview)
    
    total_emails = sum(stats.values())
    
    # Calculate percentages
    percentages = {}
    for category, count in stats.items():
        percentages[category] = (count / total_emails) * 100 if total_emails > 0 else 0
    
    # Find most common category
    most_common = max(stats.items(), key=lambda x: x[1]) if stats else ("N/A", 0)
    
    return {
        'counts': dict(stats),
        'percentages': percentages,
        'total_emails': total_emails,
        'total_size_bytes': total_size,
        'total_size_mb': total_size / (1024 * 1024) if total_size > 0 else 0,
        'categories_found': sorted(list(categories_found)),
        'most_common': {
            'category': most_common[0],
            'count': most_common[1],
            'percentage': percentages.get(most_common[0], 0)
        },
        'previews': dict(category_previews),
        'processed_at': datetime.now().isoformat(),
        'processing_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def print_statistics(stats):
    """Prints detailed statistics in a clean format."""
    if not stats or stats.get('total_emails', 0) == 0:
        print("\n📭 No email data to display")
        logger.warning("No statistics to display")
        return
    
    counts = stats.get('counts', {})
    percentages = stats.get('percentages', {})
    total_emails = stats.get('total_emails', 0)
    most_common = stats.get('most_common', {})
    
    print("\n" + "="*70)
    print("📊 DETAILED EMAIL CATEGORIZATION REPORT")
    print("="*70)
    print(f"📅 Generated: {stats.get('processing_time', 'N/A')}")
    print(f"📧 Total emails processed: {total_emails:,}")
    
    if stats.get('total_size_mb', 0) > 0:
        print(f"💾 Total data size: {stats.get('total_size_mb', 0):.2f} MB")
    
    if most_common.get('category') != 'N/A':
        print(f"🏆 Most common category: {most_common.get('category', 'N/A')} "
              f"({most_common.get('count', 0)} emails, {most_common.get('percentage', 0):.1f}%)")
    
    print("-"*70)
    
    # Header
    print(f"{'CATEGORY':20} {'COUNT':>8} {'PERCENTAGE':>12} {'SAMPLE':>30}")
    print("-"*70)
    
    # Sort categories by count (descending)
    sorted_categories = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    
    for category, count in sorted_categories:
        percent = percentages.get(category, 0)
        
        # Get a sample subject for this category
        previews = stats.get('previews', {}).get(category, [])
        sample = previews[0] if previews else "No samples"
        
        # Truncate sample if too long
        if len(sample) > 28:
            sample = sample[:25] + "..."
        
        # Print row with emoji based on category
        emoji = {
            'DOG_FOSTER': '🐶',
            'CAT_FOSTER': '🐱',
            'SMALL_ANIMAL': '🐰',
            'VOLUNTEER': '👤',
            'EVENTS': '🎪',
            'GENERAL_INQUIRY': '📧'
        }.get(category, '📄')
        
        print(f"{emoji} {category:18} {count:8,} {percent:11.1f}%  {sample:30}")
    
    print("="*70)
    
    # Log the statistics
    logger.info(f"Statistics generated: {total_emails} emails processed across {len(counts)} categories")
    logger.info(f"Most common category: {most_common.get('category')} ({most_common.get('percentage', 0):.1f}%)")

def save_report_to_csv(email_data, stats, filename="email_report.csv"):
    """
    Saves detailed report to CSV - just like Excel tracking sheets!
    
    Args:
        email_data: List of processed email dictionaries
        stats: Statistics dictionary from generate_statistics()
        filename: Output CSV filename
    """
    if not email_data:
        logger.warning("No email data to save to CSV")
        print("📭 No data to save to CSV")
        return
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # ===== HEADER SECTION =====
            writer.writerow(["EMAIL CATEGORIZATION REPORT"])
            writer.writerow([f"Generated: {stats.get('processing_time', 'N/A')}"])
            writer.writerow([f"Total Emails Processed: {stats.get('total_emails', 0)}"])
            writer.writerow([f"Total Data Size: {stats.get('total_size_mb', 0):.2f} MB"])
            writer.writerow([])  # Empty row
            
            # ===== SUMMARY STATISTICS =====
            writer.writerow(["SUMMARY STATISTICS"])
            writer.writerow(["Category", "Count", "Percentage"])
            
            counts = stats.get('counts', {})
            percentages = stats.get('percentages', {})
            
            for category in sorted(counts.keys()):
                writer.writerow([
                    category,
                    counts[category],
                    f"{percentages.get(category, 0):.1f}%"
                ])
            
            writer.writerow(["TOTAL", stats.get('total_emails', 0), "100%"])
            writer.writerow([])  # Empty row
            
            # ===== DETAILED EMAIL LIST =====
            writer.writerow(["DETAILED EMAIL LIST"])
            writer.writerow(["Filename", "Category", "Subject", "Size (KB)", "Filepath"])
            
            for email in email_data:
                size_kb = email.get('size_bytes', 0) / 1024
                writer.writerow([
                    email.get('filename', 'N/A'),
                    email.get('category', 'N/A'),
                    email.get('subject', 'No subject'),
                    f"{size_kb:.1f}",
                    email.get('filepath', 'N/A')
                ])
            
            writer.writerow([])  # Empty row
            
            # ===== PROCESSING NOTES =====
            writer.writerow(["PROCESSING NOTES"])
            writer.writerow(["This report was generated by Email Categorizer v1.0"])
            writer.writerow(["Inspired by volunteer management at Toronto Animal Services"])
            writer.writerow(["GitHub: https://github.com/hemen-dev/email-categorizer"])
        
        logger.info(f"CSV report saved to: {filename}")
        print(f"📊 CSV report saved: {filename}")
        
    except Exception as e:
        logger.error(f"Failed to save CSV report: {e}")
        print(f"❌ Error saving CSV report: {e}")

def organize_emails(email_data, output_dir="categorized_emails"):
    """
    Organizes emails into category folders - just like you did manually!
    
    Args:
        email_data: List of processed email dictionaries
        output_dir: Root directory for organized emails
    """
    if not email_data:
        logger.warning("No email data to organize")
        print("📭 No emails to organize")
        return
    
    try:
        # Create main output directory
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Organizing emails into: {output_dir}/")
        
        organized_count = 0
        skipped_count = 0
        
        for email in email_data:
            category = email.get('category', 'UNCATEGORIZED')
            source_path = email.get('filepath', '')
            
            if not source_path or not os.path.exists(source_path):
                logger.warning(f"Source file not found: {email.get('filename')}")
                skipped_count += 1
                continue
            
            # Create category folder
            category_dir = os.path.join(output_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            
            # Copy (not move) the file to keep original
            dest_path = os.path.join(category_dir, email.get('filename'))
            
            try:
                import shutil
                shutil.copy2(source_path, dest_path)
                organized_count += 1
                logger.info(f"Copied: {email.get('filename')} → {category}/")
                
                # Optional: Also create a metadata file for each email
                metadata_path = dest_path + ".meta.txt"
                with open(metadata_path, 'w') as meta:
                    meta.write(f"Category: {category}\n")
                    meta.write(f"Original: {source_path}\n")
                    meta.write(f"Processed: {datetime.now().isoformat()}\n")
                    meta.write(f"Subject: {email.get('subject', 'N/A')}\n")
                    
            except Exception as e:
                logger.error(f"Failed to copy {email.get('filename')}: {e}")
                skipped_count += 1
        
        # Create a summary file in the output directory
        summary_path = os.path.join(output_dir, "ORGANIZATION_SUMMARY.txt")
        with open(summary_path, 'w') as summary:
            summary.write("EMAIL ORGANIZATION SUMMARY\n")
            summary.write("=" * 50 + "\n")
            summary.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            summary.write(f"Source: {len(email_data)} emails\n")
            summary.write(f"Organized: {organized_count} emails\n")
            summary.write(f"Skipped: {skipped_count} emails\n")
            summary.write(f"Categories created: {len(set(e.get('category') for e in email_data))}\n")
            summary.write("\nCategory breakdown:\n")
            
            # Count by category
            category_counts = defaultdict(int)
            for email in email_data:
                category_counts[email.get('category')] += 1
            
            for category, count in sorted(category_counts.items()):
                summary.write(f"  {category}: {count} emails\n")
        
        logger.info(f"Organization complete: {organized_count} emails organized into {output_dir}/")
        print(f"📁 Organized {organized_count} emails into: {output_dir}/")
        
        if skipped_count > 0:
            print(f"   ⚠️  Skipped {skipped_count} files (see log for details)")
        
        return organized_count
        
    except Exception as e:
        logger.error(f"Failed to organize emails: {e}")
        print(f"❌ Error organizing emails: {e}")
        return 0

# ======================
# TESTING
# ======================
def run_tests():
    """Tests the categorizer with sample text."""
    logger.info("Running categorization tests...")
    
    tests = [
        ("I want to foster a dog", "DOG_FOSTER"),
        ("Interested in cats", "CAT_FOSTER"),
        ("Looking for a rabbit", "SMALL_ANIMAL"),
        ("Want to volunteer", "VOLUNTEER"),
        ("Event participation", "EVENTS"),
        ("What time do you open?", "GENERAL_INQUIRY"),
    ]
    
    passed = 0
    for text, expected in tests:
        result = categorize_email(text)
        if result == expected:
            logger.debug(f"Test passed: '{text[:25]}...' → {result}")
            passed += 1
            print(f"  ✅ '{text[:25]}...' → {result}")
        else:
            logger.error(f"Test failed: '{text[:25]}...' → {result} (expected {expected})")
            print(f"  ❌ '{text[:25]}...' → {result} (expected {expected})")
    
    logger.info(f"Tests passed: {passed}/{len(tests)}")
    print(f"\n  Tests passed: {passed}/{len(tests)}")
    return passed == len(tests)

def test_organization():
    """Test the file organization."""
    print("\n🧪 Testing file organization...")
    
    # Create a test email file
    test_dir = "test_organization"
    os.makedirs(test_dir, exist_ok=True)
    
    test_file = os.path.join(test_dir, "test_email.txt")
    with open(test_file, 'w') as f:
        f.write("Subject: Test Dog Application\n")
        f.write("I want to foster a dog\n")
    
    # Create test data
    test_email = {
        'filename': 'test_email.txt',
        'category': 'DOG_FOSTER',
        'subject': 'Test Dog Application',
        'filepath': test_file,
        'size_bytes': 100
    }
    
    # Organize it
    count = organize_emails([test_email], "test_output")
    
    if count > 0 and os.path.exists("test_output/DOG_FOSTER/test_email.txt"):
        print("✅ File organization test passed!")
        
        # Clean up
        import shutil
        shutil.rmtree("test_output")
        shutil.rmtree(test_dir)
        return True
    else:
        print("❌ File organization test failed!")
        return False
    
def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Email Application Categorizer',
        epilog='Inspired by Toronto Animal Services'
    )
    
    parser.add_argument(
        '--report', '-r',
        action='store_true',
        help='Generate CSV report'
    )
    
    parser.add_argument(
        '--organize', '-org',
        action='store_true',
        help='Organize emails into category folders'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal console output'
    )
    
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Run tests only'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='categorized_emails',
        help='Output directory for organized emails'
    )
    
    return parser.parse_args()
    
# ======================
# MAIN EXECUTION
# ======================
def main():
    """Main function to run the categorizer."""
    args = parse_arguments()
    
    if args.test:
        print("🧪 Running tests...")
        if run_tests() and test_csv_report() and test_organization():
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
        return
    
    if not args.quiet:
        print("="*60)
        print("📧 EMAIL APPLICATION CATEGORIZER")
        print("="*60)
    
    # 1. Run tests (quick validation)
    if not args.quiet:
        print("\n[1/3] Running tests...")
    if not run_tests():
        if not args.quiet:
            print("\n⚠️  Tests failed! Fix logic before continuing.")
        return
    
    # 2. Check for email files
    email_dir = args.input_dir
    if not os.path.exists(email_dir):
        print(f"\n❌ Directory '{email_dir}' not found!")
        print("   Please create it and add some .txt files.")
        return
    
    # Get all .txt files
    email_files = []
    for file in os.listdir(email_dir):
        if file.endswith('.txt'):
            email_files.append(os.path.join(email_dir, file))
    
    if not email_files:
        print(f"\n❌ No .txt files found in '{email_dir}'")
        return
    
    if not args.quiet:
        print(f"\n[2/3] Found {len(email_files)} email files:")
    
    # 3. Process each file
    email_data = []
    successful = 0
    for filepath in email_files:
        result = process_single_email(filepath)
        if result:
            email_data.append(result)
            successful += 1
            if not args.quiet:
                print(f"   📄 {result['filename']:20} → {result['category']}")
    
    # Show processing summary
    if successful < len(email_files) and not args.quiet:
        print(f"   ⚠️  Successfully processed: {successful}/{len(email_files)} emails")
    
    if not email_data:
        print("\n❌ No emails were successfully processed.")
        return
    
    # 4. Show statistics
    if not args.quiet:
        print(f"\n[3/3] Generating report...")
    stats = generate_statistics(email_data)
    
    if not args.quiet:
        print_statistics(stats)
    
    # 5. Save CSV report if requested
    if args.report or not args.quiet:
        report_name = f"email_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        save_report_to_csv(email_data, stats, report_name)
    
    # 6. Organize emails if requested
    if args.organize:
        organized_count = organize_emails(email_data, args.output)
        if not args.quiet:
            print(f"\n📁 Organized {organized_count} emails into: {args.output}/")
    
    if not args.quiet:
        print("\n🎉 Processing complete!")
        
        # Show next steps
        print("\n💡 Next steps:")
        if args.report or not args.quiet:
            print(f"   • View CSV report: {report_name}")
        if args.organize:
            print(f"   • Browse organized emails: {args.output}/")
        print("   • Check logs: logs/email_categorizer.log")

def test_csv_report():
    """Test the CSV report generation."""
    print("\n🧪 Testing CSV report generation...")
    
    # Create test data
    test_emails = [
        {
            'filename': 'test1.txt',
            'category': 'DOG_FOSTER',
            'subject': 'Dog foster application',
            'size_bytes': 1024,
            'filepath': '/path/to/test1.txt'
        },
        {
            'filename': 'test2.txt',
            'category': 'CAT_FOSTER',
            'subject': 'Cat volunteer inquiry',
            'size_bytes': 2048,
            'filepath': '/path/to/test2.txt'
        }
    ]
    
    test_stats = {
        'counts': {'DOG_FOSTER': 1, 'CAT_FOSTER': 1},
        'percentages': {'DOG_FOSTER': 50.0, 'CAT_FOSTER': 50.0},
        'total_emails': 2,
        'total_size_bytes': 3072,
        'total_size_mb': 0.003,
        'processing_time': '2024-01-08 20:00:00'
    }
    
    # Generate report
    save_report_to_csv(test_emails, test_stats, "test_report.csv")
    
    if os.path.exists("test_report.csv"):
        print("✅ CSV report test passed!")
        # Show first few lines
        with open("test_report.csv", 'r') as f:
            print("First 5 lines of CSV:")
            for i, line in enumerate(f):
                if i < 5:
                    print(f"  {line.strip()}")
                else:
                    break
        # Clean up
        os.remove("test_report.csv")
        return True
    else:
        print("❌ CSV report test failed!")
        return False

# ======================
# ENTRY POINT
# ======================
if __name__ == "__main__":
    main()