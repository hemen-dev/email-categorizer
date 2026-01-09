"""
Email Categorizer - Core Logic
Categorizes volunteer application emails based on keywords.
Inspired by manually sorting 600+ emails at Toronto Animal Services.
"""

import os
import re
from collections import defaultdict

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
# FILE PROCESSING
# ======================
def process_single_email(filepath):
    """Reads and categorizes a single email file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        category = categorize_email(content)
        filename = os.path.basename(filepath)
        
        # Get first line for preview
        lines = content.strip().split('\n')
        preview = lines[0] if lines else "No content"
        
        return {
            'filename': filename,
            'preview': preview[:60] + "..." if len(preview) > 60 else preview,
            'category': category
        }
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

# ======================
# STATISTICS
# ======================
def generate_statistics(email_data):
    """
    Generates summary statistics.
    
    Returns:
        dict: Category counts
    """
    stats = defaultdict(int)
    for email in email_data:
        if email:  # Skip None values
            stats[email['category']] += 1
    return dict(stats)

def print_statistics(stats):
    """Prints statistics in a clean format."""
    print("\n" + "="*50)
    print("📊 EMAIL CATEGORIZATION STATISTICS")
    print("="*50)
    
    total = 0
    for category, count in sorted(stats.items()):
        print(f"  {category:20} : {count:3}")
        total += count
    
    print("-"*50)
    print(f"  {'TOTAL':20} : {total:3}")
    print("="*50)

# ======================
# TESTING
# ======================
def run_tests():
    """Tests the categorizer with sample text."""
    print("🧪 Testing categorizer logic...")
    
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
            print(f"  ✅ '{text[:25]}...' → {result}")
            passed += 1
        else:
            print(f"  ❌ '{text[:25]}...' → {result} (expected {expected})")
    
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
    for filepath in email_files:
        result = process_single_email(filepath)
        if result:
            email_data.append(result)
            print(f"   📄 {result['filename']:20} → {result['category']}")
    
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
