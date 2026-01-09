"""
Email Categorizer - Core Logic
Categorizes volunteer application emails based on keywords.
Inspired by manually sorting 600+ emails at Toronto Animal Services.
"""

import os
import re
import logging
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

# ======================
# MAIN EXECUTION
# ======================
def main():
    """Main function to run the categorizer."""
    print("="*60)
    print("📧 EMAIL APPLICATION CATEGORIZER")
    print("="*60)
    
    # 1. Run tests
    print("\n[1/3] Running tests...")
    if not run_tests():
        print("\n⚠️  Tests failed! Fix logic before continuing.")
        return
    
    # 2. Check for email files
    email_dir = "data/sample_emails"
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
    
    print(f"\n[2/3] Found {len(email_files)} email files:")
    
    # 3. Process each file
    email_data = []
    successful = 0
    for filepath in email_files:
        result = process_single_email(filepath)
        if result:
            email_data.append(result)
            successful += 1
            print(f"   📄 {result['filename']:20} → {result['category']}")
    
    # Show processing summary
    if successful < len(email_files):
        print(f"   ⚠️  Successfully processed: {successful}/{len(email_files)} emails")
    
    # 4. Show statistics
    print(f"\n[3/3] Generating report...")
    stats = generate_statistics(email_data)
    print_statistics(stats)
    
    print("\n🎉 Processing complete! Ready for Phase 2.")

# ======================
# ENTRY POINT
# ======================
if __name__ == "__main__":
    main()