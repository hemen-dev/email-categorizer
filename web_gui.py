# web_gui.py - Save this in your project root
import os
import sys

# Add src directory to path so we can import email_categorizer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from flask import Flask, render_template_string, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not installed. Run: pip3 install flask")

if FLASK_AVAILABLE:
    app = Flask(__name__)

    HTML_TEMPLATE = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📧 Email Categorizer</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-top: 20px;
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            .subtitle {
                text-align: center;
                color: #7f8c8d;
                margin-bottom: 30px;
                font-size: 1.1em;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #2c3e50;
            }
            input[type="text"] {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input[type="text"]:focus {
                outline: none;
                border-color: #3498db;
            }
            .checkbox-group {
                display: flex;
                gap: 20px;
                margin: 20px 0;
            }
            .checkbox-item {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .process-btn {
                background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 18px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                width: 100%;
                transition: transform 0.2s, box-shadow 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            .process-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3);
            }
            .process-btn:active {
                transform: translateY(0);
            }
            .output {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                margin-top: 30px;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 14px;
                line-height: 1.5;
                white-space: pre-wrap;
                max-height: 400px;
                overflow-y: auto;
                border: 1px solid #e9ecef;
            }
            .loading {
                text-align: center;
                color: #3498db;
                font-style: italic;
            }
            .success { color: #27ae60; }
            .error { color: #e74c3c; }
            .emoji { font-size: 1.2em; }
            .directory-input {
                display: flex;
                gap: 10px;
            }
            .browse-btn {
                background: #95a5a6;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                cursor: pointer;
                white-space: nowrap;
            }
            .browse-btn:hover {
                background: #7f8c8d;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .stat-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #3498db;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
            .stat-label {
                font-size: 14px;
                color: #7f8c8d;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1><span class="emoji">📧</span> Email Categorizer</h1>
            <p class="subtitle">Automatically categorize volunteer application emails<br>Inspired by Toronto Animal Services</p>
            
            <form id="processForm">
                <div class="form-group">
                    <label for="directory">Email Directory:</label>
                    <div class="directory-input">
                        <input type="text" id="directory" name="directory" value="data/sample_emails" placeholder="Path to email files">
                        <button type="button" class="browse-btn" onclick="alert('Browse would open here. For now, enter path manually.')">Browse</button>
                    </div>
                    <small style="color: #7f8c8d; display: block; margin-top: 5px;">Folder containing .txt email files</small>
                </div>
                
                <div class="checkbox-group">
                    <div class="checkbox-item">
                        <input type="checkbox" id="report" name="report" checked>
                        <label for="report">Generate CSV Report</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="organize" name="organize">
                        <label for="organize">Organize into Folders</label>
                    </div>
                </div>
                
                <button type="submit" class="process-btn">
                    <span class="emoji">🚀</span> Process Emails
                </button>
            </form>
            
            <div id="output" class="output">
                <div class="loading">Ready to process emails...</div>
            </div>
            
            <div id="stats" class="stats-grid" style="display: none;"></div>
        </div>
        
        <script>
            document.getElementById('processForm').onsubmit = async (e) => {
                e.preventDefault();
                const form = e.target;
                const output = document.getElementById('output');
                const stats = document.getElementById('stats');
                
                output.innerHTML = '<div class="loading">Processing emails... <span class="emoji">⏳</span></div>';
                stats.style.display = 'none';
                
                const formData = new FormData(form);
                
                try {
                    const response = await fetch('/process', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        // Format output with colors
                        let formattedOutput = result.output.replace(/✅/g, '<span class="success">✅</span>')
                                                          .replace(/❌/g, '<span class="error">❌</span>')
                                                          .replace(/📊/g, '<span class="emoji">📊</span>')
                                                          .replace(/📁/g, '<span class="emoji">📁</span>')
                                                          .replace(/📧/g, '<span class="emoji">📧</span>')
                                                          .replace(/✓/g, '<span class="success">✓</span>')
                                                          .replace(/⚠️/g, '<span class="emoji">⚠️</span>');
                        
                        output.innerHTML = formattedOutput;
                        
                        // Show statistics if available
                        if (result.stats) {
                            stats.style.display = 'grid';
                            let statsHTML = '';
                            const categories = result.stats.categories || {};
                            
                            for (const [category, count] of Object.entries(categories)) {
                                const emoji = {
                                    'DOG_FOSTER': '🐶',
                                    'CAT_FOSTER': '🐱',
                                    'SMALL_ANIMAL': '🐰',
                                    'VOLUNTEER': '👤',
                                    'EVENTS': '🎪',
                                    'GENERAL_INQUIRY': '📧'
                                }[category] || '📄';
                                
                                statsHTML += `
                                    <div class="stat-card">
                                        <div class="stat-value">${emoji} ${count}</div>
                                        <div class="stat-label">${category.replace('_', ' ')}</div>
                                    </div>
                                `;
                            }
                            
                            // Add total card
                            statsHTML += `
                                <div class="stat-card" style="border-left-color: #27ae60;">
                                    <div class="stat-value">${result.stats.total || 0}</div>
                                    <div class="stat-label">Total Emails</div>
                                </div>
                            `;
                            
                            stats.innerHTML = statsHTML;
                        }
                    } else {
                        output.innerHTML = `<span class="error">${result.error || 'An error occurred'}</span>`;
                    }
                    
                } catch (error) {
                    output.innerHTML = `<span class="error">Network error: ${error.message}</span>`;
                }
            };
        </script>
    </body>
    </html>
    '''

    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE)

    @app.route('/process', methods=['POST'])
    def process():
        try:
            directory = request.form.get('directory', 'data/sample_emails')
            generate_report = 'report' in request.form
            organize = 'organize' in request.form
            
            output_lines = []
            
            # Check directory
            if not os.path.exists(directory):
                return jsonify({
                    'success': False,
                    'error': f'Directory not found: {directory}'
                })
            
            # Import here to avoid circular imports
            from email_categorizer import process_single_email, generate_statistics, save_report_to_csv, organize_emails
            from collections import defaultdict
            from datetime import datetime
            
            # Find email files
            email_files = []
            for file in os.listdir(directory):
                if file.endswith('.txt'):
                    email_files.append(os.path.join(directory, file))
            
            if not email_files:
                return jsonify({
                    'success': False,
                    'error': f'No .txt files found in {directory}'
                })
            
            output_lines.append(f"📁 Found {len(email_files)} email files in: {directory}")
            output_lines.append("=" * 50)
            
            # Process emails
            email_data = []
            processed_count = 0
            
            for filepath in email_files:
                result = process_single_email(filepath)
                if result:
                    email_data.append(result)
                    processed_count += 1
                    output_lines.append(f"✓ {result['filename']} → {result['category']}")
                else:
                    filename = os.path.basename(filepath)
                    output_lines.append(f"⚠️  Skipped: {filename} (see logs for details)")
            
            output_lines.append("=" * 50)
            output_lines.append(f"✅ Successfully processed: {processed_count}/{len(email_files)} emails")
            
            if not email_data:
                return jsonify({
                    'success': False,
                    'error': 'No emails were successfully processed. Check file formats and content.'
                })
            
            # Generate statistics
            stats = generate_statistics(email_data)
            output_lines.append(f"\n📊 STATISTICS")
            output_lines.append(f"Total emails: {stats.get('total_emails', 0)}")
            
            # Format category counts
            category_counts = {}
            for category, count in stats.get('counts', {}).items():
                percent = stats.get('percentages', {}).get(category, 0)
                output_lines.append(f"  {category}: {count} ({percent:.1f}%)")
                category_counts[category] = count
            
            # Most common category
            most_common = stats.get('most_common', {})
            if most_common.get('category') != 'N/A':
                output_lines.append(f"\n🏆 Most common: {most_common.get('category')} "
                                  f"({most_common.get('percentage', 0):.1f}%)")
            
            # Generate CSV report
            if generate_report:
                report_name = f"email_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                save_report_to_csv(email_data, stats, report_name)
                output_lines.append(f"\n📊 CSV report generated: {report_name}")
            
            # Organize emails
            if organize:
                output_dir = f"web_categorized_{datetime.now().strftime('%Y%m%d')}"
                count = organize_emails(email_data, output_dir)
                output_lines.append(f"\n📁 Organized {count} emails into: {output_dir}/")
            
            output_lines.append(f"\n🎉 Processing complete! Check logs/ folder for details.")
            
            return jsonify({
                'success': True,
                'output': '\n'.join(output_lines),
                'stats': {
                    'categories': category_counts,
                    'total': stats.get('total_emails', 0),
                    'most_common': most_common.get('category')
                }
            })
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in /process: {error_details}")  # For server logs
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            })

    if __name__ == '__main__':
        print("=" * 60)
        print("📧 Email Categorizer Web GUI")
        print("=" * 60)
        print("Starting server...")
        print("Open your browser and go to: http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        app.run(debug=True, port=5000)

else:
    print("Please install Flask first:")
    print("  pip3 install flask")
    print("\nThen run: python3 web_gui.py")