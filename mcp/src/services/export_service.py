"""
Export service using xhtml2pdf - Windows compatible alternative
Maintains hybrid approach with analysis_service.py
"""
import os
import sys
import re
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
from io import BytesIO, StringIO
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.identity import DefaultAzureCredential, AzureCliCredential, DeviceCodeCredential, ClientSecretCredential
import concurrent.futures
import threading
import tempfile               
import asyncio

from dotenv import load_dotenv

load_dotenv()
# xhtml2pdf for HTML to PDF conversion (Windows compatible)
from xhtml2pdf import pisa
from jinja2 import Template
from playwright.async_api import async_playwright


class BlobExportService:
    """Service for exporting query results and Agent responses to Azure Blob Storage."""
    
    def __init__(self, storage_account: str = None, container_name: str = None):
        """Initialize the blob export service."""
        self.storage_account = storage_account or os.getenv("BLOB_STORAGE_ACCOUNT", "dlsdemo")
        self.container_name = container_name or os.getenv("BLOB_CONTAINER_NAME", "data-agent")
        self.account_url = f"https://{self.storage_account}.blob.core.windows.net"
        
        # Initialize Azure Blob Storage client with multi-method authentication
        self.blob_service_client = None
        try:
            credential = self._get_credential()
            self.blob_service_client = BlobServiceClient(
                account_url=self.account_url,
                credential=credential
            )
            print(f"Blob service initialized: {self.storage_account}/{self.container_name}", file=sys.stderr)
        except Exception as e:
            print(f"WARNING: Blob service initialization failed: {e}", file=sys.stderr)
            print("Export functionality will be disabled. Check your Azure credentials.", file=sys.stderr)
            # Don't set blob_service_client - it will remain None
            # This allows the server to continue running without export functionality
        
        print("xhtml2pdf PDF service initialized (Windows compatible)", file=sys.stderr)

    def _get_credential(self):
        """Get Azure credential using multi-method strategy."""
        from azure.identity import AzureCliCredential
        credential = None

        # 1. Try Service Principal from environment variables
        if os.getenv("AZURE_TENANT_ID") and os.getenv("AZURE_CLIENT_ID") and os.getenv("AZURE_CLIENT_SECRET"):
            try:
                print(f"Trying Service Principal authentication for Blob Storage...", file=sys.stderr)
                credential = ClientSecretCredential(
                    tenant_id=os.getenv("AZURE_TENANT_ID"),
                    client_id=os.getenv("AZURE_CLIENT_ID"),
                    client_secret=os.getenv("AZURE_CLIENT_SECRET")
                )
                # Test credential by creating BlobServiceClient
                test_client = BlobServiceClient(
                    account_url=self.account_url,
                    credential=credential
                )
                # Try to list containers to validate credential
                containers = test_client.list_containers()
                next(iter(containers), None)  # Get first item or None
                print(f"Blob Storage authenticated successfully using Service Principal", file=sys.stderr)
                return credential
            except Exception as sp_error:
                print(f"Service Principal failed for Blob Storage: {sp_error}", file=sys.stderr)
                credential = None

        # 2. Try Azure CLI credentials (from az login)
        if not credential:
            try:
                print(f"Trying Azure CLI authentication for Blob Storage...", file=sys.stderr)
                credential = AzureCliCredential()
                # Test credential by creating BlobServiceClient
                test_client = BlobServiceClient(
                    account_url=self.account_url,
                    credential=credential
                )
                # Try to list containers to validate credential
                containers = test_client.list_containers()
                next(iter(containers), None)  # Get first item or None
                print(f"Blob Storage authenticated successfully using Azure CLI", file=sys.stderr)
                return credential
            except Exception as cli_error:
                print(f"Azure CLI authentication failed for Blob Storage: {cli_error}", file=sys.stderr)
                credential = None

        # 3. Try Device Code Flow (works in Docker and headless environments)
        # Note: Don't validate immediately as it requires user interaction
        if not credential:
            try:
                print(f"Using Device Code authentication for Blob Storage...", file=sys.stderr)
                print(f"You will need to authenticate in a browser when prompted", file=sys.stderr)
                credential = DeviceCodeCredential(
                    tenant_id=os.getenv("AZURE_TENANT_ID", "ee671ff4-00bc-4321-b324-449896173882")
                )
                print(f"Device Code credential initialized - authentication will occur on first use", file=sys.stderr)
                return credential
            except Exception as device_error:
                print(f"Device Code credential initialization failed for Blob Storage: {device_error}", file=sys.stderr)
                credential = None

        # 4. Last resort: DefaultAzureCredential
        if not credential:
            print(f"Trying DefaultAzureCredential for Blob Storage as last resort...", file=sys.stderr)
            credential = DefaultAzureCredential()

        return credential

    def _create_enhanced_agent_html(self, agent_response: str, title: str,
                           query: str = None, timestamp: str = None) -> str:
        """Create enhanced HTML with better CSS for format preservation."""
        
        template_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>{{ title }}</title>
            <style type="text/css">
                /* Enhanced CSS optimized for xhtml2pdf format preservation */
                @page {
                    size: A4;
                    margin: 2cm 1.5cm;
                }
                
                body {
                    font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
                    font-size: 11pt;
                    line-height: 1.6;
                    color: #000000;
                    margin: 0;
                    padding: 0;
                    word-wrap: break-word;
                }
                
                .document {
                    width: 100%;
                }
                
                /* Header Styles - Mejorado y simplificado */
                .document-header {
                    border-bottom: 3px solid #2c3e50;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                    page-break-after: avoid;
                }
                
                .main-title {
                    color: #1a1a1a;
                    margin: 0 0 15px 0;
                    font-size: 24pt;
                    font-weight: bold;
                    line-height: 1.3;
                    letter-spacing: -0.5px;
                }
                
                .meta-info {
                    background-color: #f5f5f5;
                    padding: 15px;
                    border-left: 4px solid #2c3e50;
                    font-size: 9pt;
                    margin-top: 15px;
                    border-radius: 4px;
                }
                
                .meta-row {
                    margin-bottom: 6px;
                }
                
                .meta-label {
                    font-weight: bold;
                    color: #2c3e50;
                }
                
                .meta-value {
                    color: #555555;
                }
                
                /* Section Styles - Mejorado */
                .query-section, .response-section {
                    margin-bottom: 30px;
                    page-break-inside: avoid;
                }
                
                .section-title {
                    color: #2c3e50;
                    font-size: 16pt;
                    font-weight: bold;
                    margin: 25px 0 15px 0;
                    border-bottom: 2px solid #2c3e50;
                    padding-bottom: 8px;
                    page-break-after: avoid;
                }
                
                .query-content {
                    background-color: #f8f9fa;
                    padding: 18px;
                    border-left: 4px solid #3498db;
                    font-style: italic;
                    color: #333333;
                    margin: 15px 0;
                    border-radius: 4px;
                    line-height: 1.7;
                }
                
                /* Response Content Styles - TODO EN NEGRO */
                .response-content {
                    line-height: 1.7;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    color: #000000;
                }
                
                .response-content h1, 
                .response-content h2, 
                .response-content h3,
                .response-content h4,
                .response-content h5,
                .response-content h6 {
                    color: #000000;
                    font-weight: bold;
                    page-break-after: avoid;
                    margin-top: 22px;
                    margin-bottom: 12px;
                    line-height: 1.3;
                }
                
                .response-content h1 { 
                    font-size: 18pt; 
                    border-bottom: 2px solid #000000;
                    padding-bottom: 8px;
                }
                .response-content h2 { 
                    font-size: 16pt; 
                    border-bottom: 1px solid #333333;
                    padding-bottom: 5px;
                }
                .response-content h3 { 
                    font-size: 14pt;
                }
                .response-content h4 { 
                    font-size: 12pt;
                }
                
                .response-content p {
                    margin-bottom: 12px;
                    text-align: justify;
                    orphans: 2;
                    widows: 2;
                    color: #000000;
                }
                
                .response-content ul, 
                .response-content ol {
                    margin: 15px 0;
                    padding-left: 30px;
                    page-break-inside: avoid;
                }
                
                .response-content li {
                    margin-bottom: 8px;
                    line-height: 1.6;
                    color: #000000;
                }
                
                /* Enhanced Table Styles - Negro y elegante */
                .response-content table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: 10pt;
                    page-break-inside: avoid;
                    border: 2px solid #000000;
                }
                
                .response-content th, 
                .response-content td {
                    border: 1px solid #333333;
                    padding: 10px 12px;
                    text-align: left;
                    vertical-align: top;
                    word-wrap: break-word;
                }
                
                .response-content th {
                    background-color: #2c3e50 !important;
                    color: white !important;
                    font-weight: bold;
                    font-size: 10pt;
                    text-align: center;
                }
                
                .response-content tr:nth-child(even) {
                    background-color: #f5f5f5 !important;
                }
                
                .response-content tr:nth-child(odd) {
                    background-color: white !important;
                }
                
                .response-content td {
                    color: #000000;
                }
                
                /* Enhanced Code Styles - Negro */
                .response-content code {
                    background-color: #f5f5f5;
                    padding: 3px 6px;
                    font-family: 'Courier New', Courier, monospace;
                    font-size: 9pt;
                    color: #000000;
                    border-radius: 3px;
                    border: 1px solid #cccccc;
                }
                
                .response-content pre {
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-left: 4px solid #2c3e50;
                    margin: 20px 0;
                    font-family: 'Courier New', Courier, monospace;
                    font-size: 9pt;
                    overflow: visible;
                    word-wrap: break-word;
                    white-space: pre-wrap;
                    page-break-inside: avoid;
                    border-radius: 4px;
                }
                
                .response-content pre code {
                    background: none;
                    padding: 0;
                    color: #000000;
                    border: none;
                }
                
                /* Enhanced Quote Styles - Negro */
                .response-content blockquote {
                    border-left: 4px solid #2c3e50;
                    margin: 20px 0;
                    padding: 15px 20px;
                    color: #000000;
                    font-style: italic;
                    background-color: #f8f9fa;
                    border-radius: 0 6px 6px 0;
                    page-break-inside: avoid;
                }
                
                /* Enhanced Strong and Emphasis - Negro */
                .response-content strong {
                    font-weight: bold;
                    color: #000000;
                }
                
                .response-content em {
                    font-style: italic;
                    color: #000000;
                }
                
                .response-content a {
                    color: #2c3e50;
                    text-decoration: underline;
                }
                
                /* Footer - Mejorado */
                .document-footer {
                    margin-top: 40px;
                    padding-top: 15px;
                    border-top: 2px solid #cccccc;
                    text-align: center;
                    color: #666666;
                    font-size: 9pt;
                    page-break-inside: avoid;
                }
            </style>
        </head>
        <body>
            <div class="document">
                <header class="document-header">
                    <h1 class="main-title">{{ title }}</h1>
                    <div class="meta-info">
                        <div class="meta-row">
                            <span class="meta-label">Generado:</span>
                            <span class="meta-value">{{ timestamp }}</span>
                        </div>
                        <div class="meta-row">
                            <span class="meta-label">Fuente:</span>
                            <span class="meta-value">AI Agent</span>
                        </div>
                    </div>
                </header>
                
                {% if query %}
                <section class="query-section">
                    <h2 class="section-title">Consulta Original</h2>
                    <div class="query-content">{{ query }}</div>
                </section>
                {% endif %}
                
                <section class="response-section">
                    <div class="response-content">
                        {{ agent_response|safe }}
                    </div>
                </section>
                
                <footer class="document-footer">
                    <p>Documento generado automáticamente y exportado a formato PDF</p>
                </footer>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_html)
        return template.render(
            title=title,
            agent_response=agent_response,
            query=query,
            timestamp=timestamp
        )
    
    def _convert_markdown_tables_to_html(self, content: str) -> str:
        """Convert Markdown tables to proper HTML tables."""
        
        # Pattern to match markdown tables
        # Looks for lines starting with | and containing |
        lines = content.split('\n')
        result = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this line looks like a table row (contains |)
            if line.startswith('|') and line.endswith('|'):
                # Found potential table, collect all table rows
                table_lines = []
                
                # Collect all consecutive lines that look like table rows
                while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                
                # Process the table
                if len(table_lines) >= 2:  # Need at least header + separator
                    html_table = self._parse_markdown_table(table_lines)
                    result.append(html_table)
                else:
                    # Not a valid table, add lines as-is
                    result.extend(table_lines)
            else:
                result.append(lines[i])
                i += 1
        
        return '\n'.join(result)

    def _parse_markdown_table(self, table_lines: list) -> str:
        """Parse markdown table lines into HTML table."""
        if len(table_lines) < 2:
            return '\n'.join(table_lines)
        
        # First line is header
        header_line = table_lines[0]
        # Second line is separator (|---|---|)
        separator_line = table_lines[1]
        # Rest are data rows
        data_lines = table_lines[2:] if len(table_lines) > 2 else []
        
        # Parse header
        headers = [cell.strip() for cell in header_line.split('|')[1:-1]]
        
        # Check alignment from separator
        separators = [cell.strip() for cell in separator_line.split('|')[1:-1]]
        alignments = []
        for sep in separators:
            if sep.startswith(':') and sep.endswith(':'):
                alignments.append('center')
            elif sep.endswith(':'):
                alignments.append('right')
            else:
                alignments.append('left')
        
        # Build HTML table
        html_parts = ['<table>']
        
        # Add header
        html_parts.append('<thead>')
        html_parts.append('<tr>')
        for i, header in enumerate(headers):
            align = alignments[i] if i < len(alignments) else 'left'
            # Clean markdown formatting from headers
            clean_header = self._clean_markdown_formatting(header)
            html_parts.append(f'<th style="text-align: {align};">{clean_header}</th>')
        html_parts.append('</tr>')
        html_parts.append('</thead>')
        
        # Add body
        if data_lines:
            html_parts.append('<tbody>')
            for data_line in data_lines:
                cells = [cell.strip() for cell in data_line.split('|')[1:-1]]
                html_parts.append('<tr>')
                for i, cell in enumerate(cells):
                    align = alignments[i] if i < len(alignments) else 'left'
                    # Clean markdown formatting from cells
                    clean_cell = self._clean_markdown_formatting(cell)
                    html_parts.append(f'<td style="text-align: {align};">{clean_cell}</td>')
                html_parts.append('</tr>')
            html_parts.append('</tbody>')
        
        html_parts.append('</table>')
        
        return '\n'.join(html_parts)

    def _clean_markdown_formatting(self, text: str) -> str:
        """Clean markdown formatting from text and convert to HTML."""
        import re
        
        # Convert **bold** to <strong>
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        
        # Convert *italic* to <em>
        text = re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', r'<em>\1</em>', text)
        
        # Convert `code` to <code>
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        return text
    def _fix_table_structure(self, html_content: str) -> str:
        """Fix table structure to ensure proper PDF rendering."""
        import re
        
        # Pattern to find tables
        table_pattern = r'<table[^>]*>(.*?)</table>'
        
        def fix_single_table(match):
            table_content = match.group(1)
            
            # Ensure table has proper tbody if it doesn't exist
            if '<tbody>' not in table_content and '<tr>' in table_content:
                # Find all tr elements
                tr_pattern = r'<tr[^>]*>.*?</tr>'
                tr_matches = re.findall(tr_pattern, table_content, re.DOTALL)
                
                if tr_matches:
                    # Assume first row with th elements is header
                    header_rows = []
                    body_rows = []
                    
                    for tr in tr_matches:
                        if '<th>' in tr or '<th ' in tr:
                            header_rows.append(tr)
                        else:
                            body_rows.append(tr)
                    
                    new_table_content = ''
                    if header_rows:
                        new_table_content += '<thead>' + ''.join(header_rows) + '</thead>'
                    if body_rows:
                        new_table_content += '<tbody>' + ''.join(body_rows) + '</tbody>'
                    
                    return f'<table>{new_table_content}</table>'
            
            return match.group(0)
        
        return re.sub(table_pattern, fix_single_table, html_content, flags=re.DOTALL)
    
    def _preprocess_agent_html(self, agent_response: str) -> str:
        """Preprocess Agent's HTML/Markdown response for better PDF formatting."""


        # Start with the original response
        processed = agent_response
        
        # 1. Convert Markdown tables to HTML first (CRITICAL)
        processed = self._convert_markdown_tables_to_html(processed)
        
        # 2. Handle markdown-style formatting
        # Split into lines to preserve structure
        lines = processed.split('\n')
        html_parts = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Skip if line is already HTML (table, etc.)
            if line.startswith('<table>'):
                # Find the closing </table>
                table_html = [line]
                i += 1
                while i < len(lines) and '</table>' not in lines[i-1]:
                    table_html.append(lines[i])
                    i += 1
                html_parts.append('\n'.join(table_html))
                continue
            
            # Check if it's a header
            if line.startswith('### '):
                clean_text = self._clean_markdown_formatting(line[4:].strip())
                html_parts.append(f'<h3>{clean_text}</h3>')
                i += 1
                
            elif line.startswith('## '):
                clean_text = self._clean_markdown_formatting(line[3:].strip())
                html_parts.append(f'<h2>{clean_text}</h2>')
                i += 1
                
            elif line.startswith('# '):
                clean_text = self._clean_markdown_formatting(line[2:].strip())
                html_parts.append(f'<h1>{clean_text}</h1>')
                i += 1
            
            # Check for list items
            elif line.startswith(('- ', '* ')):
                list_items = []
                while i < len(lines) and lines[i].strip().startswith(('- ', '* ')):
                    item_text = lines[i].strip()[2:]
                    clean_item = self._clean_markdown_formatting(item_text)
                    list_items.append(f'<li>{clean_item}</li>')
                    i += 1
                
                html_parts.append('<ul>')
                html_parts.extend(list_items)
                html_parts.append('</ul>')
            
            # Check for numbered list
            elif re.match(r'^\d+\. ', line):
                list_items = []
                while i < len(lines) and re.match(r'^\d+\. ', lines[i].strip()):
                    item_text = re.sub(r'^\d+\. ', '', lines[i].strip())
                    clean_item = self._clean_markdown_formatting(item_text)
                    list_items.append(f'<li>{clean_item}</li>')
                    i += 1
                
                html_parts.append('<ol>')
                html_parts.extend(list_items)
                html_parts.append('</ol>')
            
            else:
                # Regular paragraph
                para_lines = []
                while i < len(lines) and lines[i].strip() and \
                    not lines[i].strip().startswith(('#', '- ', '* ', '<table>')) and \
                    not re.match(r'^\d+\. ', lines[i].strip()) and \
                    not (lines[i].strip().startswith('|') and lines[i].strip().endswith('|')):
                    para_lines.append(lines[i].strip())
                    i += 1
                
                if para_lines:
                    para_text = ' '.join(para_lines)
                    clean_para = self._clean_markdown_formatting(para_text)
                    html_parts.append(f'<p>{clean_para}</p>')
        
        processed = '\n'.join(html_parts)
        
        # 3. Fix any remaining table structures
        processed = self._fix_table_structure(processed)
        
        # 4. Add line breaks for better readability
        processed = processed.replace('</p>', '</p>\n')
        processed = processed.replace('</h1>', '</h1>\n')
        processed = processed.replace('</h2>', '</h2>\n')
        processed = processed.replace('</h3>', '</h3>\n')
        processed = processed.replace('</ul>', '</ul>\n')
        processed = processed.replace('</ol>', '</ol>\n')
        processed = processed.replace('</table>', '</table>\n')
        
        return processed

    async def export_agent_response_to_pdf_async(self,
                                                agent_response: str,
                                                query: str = None,
                                                filename: str = None,
                                                title: str = "Agent Analysis Report") -> Dict[str, Any]:
        """
        Export Agent's response to PDF using Playwright (Chromium) - Async version.
        Falls back to HTML export if PDF generation fails.
        """
        try:
            if not self.blob_service_client:
                return {"error": "Blob service not available"}
            
            if not agent_response:
                return {"error": "No Agent response provided"}

            # Generate filename
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"agent_response_{timestamp}.pdf"
            
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            
            print(f"Processing Agent response for PDF export: {len(agent_response)} characters", file=sys.stderr)

            # Enhanced HTML preprocessing
            processed_response = self._preprocess_agent_html(agent_response)
            
            print(f"Preprocessed response: {len(processed_response)} characters", file=sys.stderr)
            
            # Create HTML content
            html_content = self._create_enhanced_agent_html(
                agent_response=processed_response,
                title=title,
                query=query,
                timestamp=datetime.now().strftime("%B %d, %Y at %I:%M %p")
            )
            
            if isinstance(html_content, dict):
                return {"error": f"HTML generation failed: {html_content.get('error', 'Unknown error')}"}
            
            if not isinstance(html_content, str):
                return {"error": f"HTML generation returned unexpected type: {type(html_content)}"}
            
            print(f"Generated HTML content: {len(html_content)} characters", file=sys.stderr)
            
            # Try to generate PDF using Playwright
            pdf_bytes = None
            pdf_method = None
            error_details = None
            
            try:

                
                print("Starting Playwright (Chromium) PDF generation...", file=sys.stderr)
                
                # Create temp HTML file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(html_content)
                    temp_html_path = f.name
                
                temp_html_uri = None
                
                try:
                    # Convert path to file:// URI
                    temp_html_uri = f'file:///{temp_html_path.replace(os.sep, "/")}'
                    
                    print(f"Loading HTML from: {temp_html_uri}", file=sys.stderr)
                    
                    async with async_playwright() as p:
                        # Launch Chromium browser in headless mode
                        browser = await p.chromium.launch(
                            headless=True,
                            args=['--no-sandbox', '--disable-setuid-sandbox']
                        )
                        
                        print("Browser launched successfully", file=sys.stderr)
                        
                        # Create new page
                        page = await browser.new_page()
                        
                        # Load HTML file
                        await page.goto(temp_html_uri, wait_until='networkidle', timeout=30000)
                        
                        print("HTML loaded, generating PDF...", file=sys.stderr)
                        
                        # Generate PDF with comprehensive options
                        pdf_bytes = await page.pdf(
                            format='A4',
                            margin={
                                'top': '20mm',
                                'right': '15mm',
                                'bottom': '20mm',
                                'left': '15mm'
                            },
                            print_background=True,
                            prefer_css_page_size=False,
                            display_header_footer=False
                        )
                        
                        # Close browser
                        await browser.close()
                        
                        pdf_method = "Playwright (Chromium)"
                        print(f"✓ PDF generated successfully with Playwright: {len(pdf_bytes)} bytes", file=sys.stderr)
                    
                finally:
                    # Clean up temp file
                    try:
                        if os.path.exists(temp_html_path):
                            os.unlink(temp_html_path)
                            print("Temp HTML file cleaned up", file=sys.stderr)
                    except Exception as cleanup_error:
                        print(f"Warning: Could not delete temp file: {cleanup_error}", file=sys.stderr)
            
            except ImportError as import_error:
                error_details = "Playwright not installed"
                print(f"✗ Playwright not available: {import_error}", file=sys.stderr)
                print("Install with: pip install playwright && python -m playwright install chromium", file=sys.stderr)
            
            except Exception as playwright_error:
                error_details = str(playwright_error)
                print(f"✗ Playwright PDF generation failed: {playwright_error}", file=sys.stderr)
                import traceback
                print(f"Traceback:\n{traceback.format_exc()}", file=sys.stderr)
            
            # If PDF generation failed, fall back to HTML export
            if not pdf_bytes:
                print("=" * 60, file=sys.stderr)
                print("PDF generation failed, falling back to HTML export", file=sys.stderr)
                print("=" * 60, file=sys.stderr)
                
                html_filename = filename.replace('.pdf', '.html')
                
                return self._fallback_html_export(
                    html_content=html_content,
                    filename=html_filename,
                    title=title,
                    error_reason=error_details or "PDF generation failed"
                )
            
            # Upload PDF to blob storage
            print("Uploading PDF to blob storage...", file=sys.stderr)
            
            pdf_blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=filename
            )
            
            pdf_blob_client.upload_blob(
                data=pdf_bytes,
                overwrite=True,
                content_settings=ContentSettings(content_type='application/pdf')
            )
            
            # Generate download URL
            download_url = f"{self.account_url}/{self.container_name}/{filename}"
            
            print(f"✓ PDF uploaded successfully: {filename}", file=sys.stderr)
            print(f"Download URL: {download_url}", file=sys.stderr)
            
            return {
                "status": "success",
                "message": f"Agent response exported to PDF successfully using {pdf_method}",
                "download_url": download_url,
                "blob_name": filename,
                "title": title,
                "file_size_mb": round(len(pdf_bytes) / (1024 * 1024), 2),
                "file_size_bytes": len(pdf_bytes),
                "generated_at": datetime.now().isoformat(),
                "format": "PDF",
                "engine": pdf_method,
                "css3_support": "full",
                "processing_notes": "Generated with Chromium engine - Full CSS3 and modern web standards support"
            }

        except Exception as e:
            error_msg = f"Agent response PDF export error: {str(e)}"
            print(f"✗ PDF export failed: {type(e).__name__}: {e}", file=sys.stderr)
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}", file=sys.stderr)
            return {"error": error_msg}


    def export_agent_response_to_pdf(self,
                                    agent_response: str,
                                    query: str = None,
                                    filename: str = None,
                                    title: str = "Agent Analysis Report") -> Dict[str, Any]:
        """
        Synchronous wrapper for PDF export using Playwright.
        Handles both sync and async contexts automatically.
        Falls back to HTML if PDF generation fails.
        """

        
        try:
            # Try to get the current event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, need to run in a new thread

                
                print("Detected running event loop, using thread executor", file=sys.stderr)
                
                result = None
                exception = None
                
                def run_async():
                    nonlocal result, exception
                    try:
                        # Create a new event loop for this thread
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            result = new_loop.run_until_complete(
                                self.export_agent_response_to_pdf_async(
                                    agent_response, query, filename, title
                                )
                            )
                        finally:
                            new_loop.close()
                    except Exception as e:
                        exception = e
                
                thread = threading.Thread(target=run_async)
                thread.start()
                thread.join(timeout=60)  # 60 second timeout
                
                if thread.is_alive():
                    print("PDF generation timed out", file=sys.stderr)
                    html_filename = (filename or f"agent_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf").replace('.pdf', '.html')
                    return self._fallback_html_export(
                        html_content=self._create_enhanced_agent_html(
                            agent_response=self._preprocess_agent_html(agent_response),
                            title=title,
                            query=query,
                            timestamp=datetime.now().strftime("%B %d, %Y at %I:%M %p")
                        ),
                        filename=html_filename,
                        title=title,
                        error_reason="PDF generation timed out after 60 seconds"
                    )
                
                if exception:
                    raise exception
                
                return result
                
            except RuntimeError:
                # No event loop running, we can create one
                print("No running event loop detected, creating new one", file=sys.stderr)
                return asyncio.run(
                    self.export_agent_response_to_pdf_async(
                        agent_response, query, filename, title
                    )
                )
                
        except Exception as e:
            error_msg = f"PDF export wrapper error: {str(e)}"
            print(f"✗ Export wrapper failed: {type(e).__name__}: {e}", file=sys.stderr)
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}", file=sys.stderr)
            
            # Last resort fallback to HTML
            try:
                html_filename = (filename or f"agent_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf").replace('.pdf', '.html')
                processed_response = self._preprocess_agent_html(agent_response)
                html_content = self._create_enhanced_agent_html(
                    agent_response=processed_response,
                    title=title,
                    query=query,
                    timestamp=datetime.now().strftime("%B %d, %Y at %I:%M %p")
                )
                return self._fallback_html_export(
                    html_content=html_content,
                    filename=html_filename,
                    title=title,
                    error_reason=error_msg
                )
            except:
                return {"error": error_msg}


    def _fallback_html_export(self, 
                            html_content: str, 
                            filename: str, 
                            title: str, 
                            error_reason: str) -> Dict[str, Any]:
        """
        Fallback method to export HTML when PDF generation fails.
        Provides a working alternative that users can view in browser or convert later.
        """
        try:
            print(f"Executing HTML fallback export due to: {error_reason}", file=sys.stderr)
            
            # Ensure .html extension
            if not filename.lower().endswith('.html'):
                if filename.lower().endswith('.pdf'):
                    filename = filename[:-4] + '.html'
                else:
                    filename += '.html'
            
            print(f"HTML fallback filename: {filename}", file=sys.stderr)
            
            # Upload HTML to blob storage
            html_blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=filename
            )
            
            html_bytes = html_content.encode('utf-8')
            
            html_blob_client.upload_blob(
                data=html_bytes,
                overwrite=True,
                content_settings=ContentSettings(content_type='text/html; charset=utf-8')
            )
            
            download_url = f"{self.account_url}/{self.container_name}/{filename}"
            
            print(f"✓ HTML fallback exported successfully: {filename}", file=sys.stderr)
            print(f"Download URL: {download_url}", file=sys.stderr)
            
            return {
                "status": "fallback_success",
                "message": "PDF generation failed - exported as HTML instead (can be printed to PDF from browser)",
                "download_url": download_url,
                "blob_name": filename,
                "title": title,
                "file_size_mb": round(len(html_bytes) / (1024 * 1024), 2),
                "file_size_bytes": len(html_bytes),
                "generated_at": datetime.now().isoformat(),
                "format": "HTML",
                "original_format_requested": "PDF",
                "fallback_reason": error_reason,
                "user_instructions": "Open this HTML file in a browser. You can print it to PDF using your browser's Print > Save as PDF feature.",
                "processing_notes": "HTML export with full CSS3 styling - viewable in any modern browser"
            }
            
        except Exception as fallback_error:
            error_msg = f"Both PDF and HTML export failed: {str(fallback_error)}"
            print(f"✗ HTML fallback also failed: {fallback_error}", file=sys.stderr)
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}", file=sys.stderr)
            return {
                "error": error_msg,
                "original_error": error_reason,
                "fallback_error": str(fallback_error)
            }

    def export_to_pdf_report(self, data: List[Dict], filename: str = None, 
                             report_title: str = "Executive Data Analysis Report") -> Dict[str, Any]:
        """Generate executive report with automatic data analysis using analysis_service.py"""
        try:
            if not self.blob_service_client:
                return {"error": "Blob service not available"}
            
            if not data or not isinstance(data, list):
                return {"error": "No valid data to export"}
            
            # Generate filename
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"executive_report_{timestamp}.pdf"
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            
            print(f"Starting executive report generation for {len(data)} records...", file=sys.stderr)
            
            # Import analysis service for automatic data analysis
            from .analysis_service import data_analyzer, report_generator
            
            # Perform data analysis
            print("Performing data analysis...", file=sys.stderr)
            analysis = data_analyzer.profile_dataset(data)
            
            # Create visualizations
            print("Creating visualizations...", file=sys.stderr)
            visualizations = data_analyzer.create_visualizations(data)
            
            # Generate PDF report using analysis_service.py (ReportLab)
            print("Generating PDF report with analysis_service...", file=sys.stderr)
            pdf_buffer = report_generator.generate_executive_report(
                data, analysis, visualizations, report_title
            )
            
            # Upload PDF to blob storage
            pdf_content = pdf_buffer.getvalue()
            pdf_blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=filename
            )
            pdf_blob_client.upload_blob(data=pdf_content, overwrite=True)
            
            # Generate URL
            download_url = f"{self.account_url}/{self.container_name}/{filename}"
            
            print(f"Executive report uploaded successfully: {filename}", file=sys.stderr)
            
            return {
                "status": "success",
                "message": "Executive PDF report generated successfully with automatic analysis",
                "download_url": download_url,
                "blob_name": filename,
                "report_title": report_title,
                "analysis_summary": {
                    "total_rows": analysis.get('basic_info', {}).get('total_rows', 0),
                    "total_columns": analysis.get('basic_info', {}).get('total_columns', 0),
                    "data_quality_score": analysis.get('data_quality', {}).get('completeness_score', 0),
                    "key_insights_count": len(analysis.get('insights', []))
                },
                "file_size_mb": round(len(pdf_content) / (1024 * 1024), 2),
                "export_method": "analysis_service",
                "pdf_engine": "reportlab"
            }
            
        except Exception as e:
            error_msg = f"Executive report generation error: {str(e)}"
            print(f"Executive report failed: {type(e).__name__}: {e}", file=sys.stderr)
            return {"error": error_msg}
    
    # Keep all existing methods (CSV, Excel, file management) unchanged
    def export_to_csv(self, data: List[Dict], filename: str = None, 
                     include_metadata: bool = True) -> Dict[str, Any]:
        """Export to CSV - unchanged"""
        try:
            if not self.blob_service_client:
                return {"error": "Blob service not available"}
            
            if not data or not isinstance(data, list):
                return {"error": "No valid data to export"}
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"query_results_{timestamp}.csv"
            if not filename.lower().endswith('.csv'):
                filename += '.csv'
            
            df = pd.DataFrame(data)
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue().encode('utf-8')
            csv_buffer.close()
            
            csv_blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=filename
            )
            csv_blob_client.upload_blob(data=csv_content, overwrite=True)
            
            download_url = f"{self.account_url}/{self.container_name}/{filename}"
            print(f"CSV uploaded successfully: {filename}", file=sys.stderr)
            
            return {
                "status": "success",
                "message": "CSV exported successfully to Azure Blob Storage",
                "download_url": download_url,
                "blob_name": filename,
                "rows_exported": len(data),
                "columns_exported": len(df.columns),
                "file_size_mb": round(len(csv_content) / (1024 * 1024), 2)
            }
            
        except Exception as e:
            error_msg = f"CSV export error: {str(e)}"
            print(f"CSV export failed: {type(e).__name__}: {e}", file=sys.stderr)
            return {"error": error_msg}
    
    def export_to_excel(self, data: List[Dict], filename: str = None, 
                       sheet_name: str = "Query Results", include_metadata: bool = True,
                       auto_adjust_columns: bool = True) -> Dict[str, Any]:
        """Export to Excel - unchanged"""
        try:
            if not self.blob_service_client:
                return {"error": "Blob service not available"}
            
            if not data or not isinstance(data, list):
                return {"error": "No valid data to export"}
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"query_results_{timestamp}.xlsx"
            if not filename.lower().endswith(('.xlsx', '.xls')):
                filename += '.xlsx'
            
            df = pd.DataFrame(data)
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, sheet_name=sheet_name, index=False, engine='openpyxl')
            excel_content = excel_buffer.getvalue()
            excel_buffer.close()
            
            excel_blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=filename
            )
            excel_blob_client.upload_blob(data=excel_content, overwrite=True)
            
            download_url = f"{self.account_url}/{self.container_name}/{filename}"
            print(f"Excel uploaded successfully: {filename}", file=sys.stderr)
            
            return {
                "status": "success",
                "message": "Excel exported successfully to Azure Blob Storage",
                "download_url": download_url,
                "blob_name": filename,
                "sheet_name": sheet_name,
                "rows_exported": len(data),
                "columns_exported": len(df.columns),
                "file_size_mb": round(len(excel_content) / (1024 * 1024), 2)
            }
            
        except Exception as e:
            error_msg = f"Excel export error: {str(e)}"
            print(f"Excel export failed: {type(e).__name__}: {e}", file=sys.stderr)
            return {"error": error_msg}
    
    def list_exported_files(self) -> Dict[str, Any]:
        """List files in the container."""
        try:
            if not self.blob_service_client:
                return {"error": "Blob service not available"}
            
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            files = []
            for blob in container_client.list_blobs():
                if blob.name.lower().endswith(('.csv', '.xlsx', '.xls', '.pdf')):
                    files.append({
                        "filename": blob.name,
                        "download_url": f"{self.account_url}/{self.container_name}/{blob.name}",
                        "size_mb": round(blob.size / (1024 * 1024), 2) if blob.size else 0,
                        "created": blob.creation_time.isoformat() if blob.creation_time else None,
                        "file_type": self._detect_file_type(blob.name)
                    })
            
            files.sort(key=lambda x: x["filename"], reverse=True)
            
            return {
                "storage_account": self.storage_account,
                "container": self.container_name,
                "total_files": len(files),
                "files": files
            }
            
        except Exception as e:
            print(f"List files error: {e}", file=sys.stderr)
            return {"error": f"Failed to list files: {str(e)}"}
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect file type based on filename."""
        filename_lower = filename.lower()
        if "agent_response_" in filename_lower and filename_lower.endswith('.pdf'):
            return "Agent PDF Report (Enhanced xhtml2pdf)"
        elif "executive_report_" in filename_lower and filename_lower.endswith('.pdf'):
            return "Executive Data Report (ReportLab)"
        elif filename_lower.endswith('.pdf'):
            return "PDF Report"
        elif filename_lower.endswith(('.xlsx', '.xls')):
            return "Excel"
        elif filename_lower.endswith('.csv'):
            return "CSV"
        else:
            return "Unknown"
        
    def delete_exported_file(self, filename: str) -> Dict[str, Any]:
        """Delete a file from the container."""
        try:
            if not self.blob_service_client:
                return {"error": "Blob service not available"}
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=filename
            )
            
            blob_client.delete_blob()
            
            return {
                "status": "success",
                "message": f"File '{filename}' deleted successfully"
            }
            
        except Exception as e:
            print(f"Delete file error: {e}", file=sys.stderr)
            return {"error": f"Failed to delete file: {str(e)}"}
    
    def get_file_info(self, filename: str) -> Dict[str, Any]:
        """Get detailed information about a specific file in blob storage."""
        try:
            if not self.blob_service_client:
                return {"error": "Blob service not available"}
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=filename
            )
            
            properties = blob_client.get_blob_properties()
            
            return {
                "filename": filename,
                "download_url": f"{self.account_url}/{self.container_name}/{filename}",
                "size_mb": round(properties.size / (1024 * 1024), 2),
                "created": properties.creation_time.isoformat(),
                "last_modified": properties.last_modified.isoformat(),
                "content_type": properties.content_settings.content_type,
                "file_type": self._detect_file_type(filename)
            }
            
        except Exception as e:
            print(f"Get file info error: {e}", file=sys.stderr)
            return {"error": f"Failed to get file info: {str(e)}"}
    
    def generate_data_analysis(self, data: List[Dict]) -> Dict[str, Any]:
        """Perform comprehensive data analysis on query results."""
        try:
            if not data or not isinstance(data, list):
                return {"error": "No valid data to analyze"}
            
            from .analysis_service import data_analyzer
            analysis = data_analyzer.profile_dataset(data)
            
            return {
                "status": "success",
                "analysis": analysis
            }
            
        except Exception as e:
            error_msg = f"Data analysis error: {str(e)}"
            print(f"Data analysis failed: {type(e).__name__}: {e}", file=sys.stderr)
            return {"error": error_msg}

# Global instance
try:
    export_service = BlobExportService()
    if export_service.blob_service_client is not None:
        print("Export service global instance created with full Azure functionality", file=sys.stderr)
    else:
        print("Export service created without Azure functionality (authentication failed)", file=sys.stderr)
except Exception as e:
    print(f"Failed to create export service: {e}", file=sys.stderr)
    export_service = None