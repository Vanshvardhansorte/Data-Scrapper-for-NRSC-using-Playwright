import sys
import asyncio
import os
import json
import time
import re
import requests
import pandas as pd
from datetime import datetime
from urllib.parse import urljoin, urlparse

# PyPDF for extraction
from pypdf import PdfReader

# ReportLab for PDF Report Generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# CRITICAL FIX FOR WINDOWS + PYTHON 3.13 + PLAYWRIGHT
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
from playwright.sync_api import sync_playwright

# --- UI STYLING ---
st.set_page_config(page_title="Data Scrapper for NRSC", page_icon="🦅", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .terminal { 
        background-color: #000000; color: #00ff00; padding: 15px; 
        border-radius: 5px; font-family: 'Courier New', monospace; 
        height: 350px; overflow-y: auto; font-size: 12px; border: 1px solid #333;
    }
    .success-text { color: #238636; font-weight: bold; }
    .error-text { color: #da3633; }
    </style>
    """, unsafe_allow_html=True)

# --- CORE ENGINE ---
class EnterpriseHarvester:
    def __init__(self, config):
        self.config = config
        self.visited_urls = set()
        self.found_pdfs = set()
        self.data_store = []
        self.start_time = time.time()
        
        # Ensure workspace exists
        for path in [config['dl_dir'], config['out_dir']]:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)

    def clean_text(self, text):
        """Removes junk characters and collapses whitespace."""
        if not text: return ""
        text = re.sub(r'\s+', ' ', text)
        text = "".join(i for i in text if 31 < ord(i) < 127)
        return text.strip()

    def download_pdf(self, url, log_callback):
        """Handles the physical download of the PDF file."""
        try:
            filename = os.path.basename(urlparse(url).path)
            if not filename.endswith('.pdf'): filename += ".pdf"
            
            save_path = os.path.join(self.config['dl_dir'], filename)
            
            # Skip if already exists to save bandwidth
            if os.path.exists(save_path):
                return save_path, "Existing"

            response = requests.get(url, timeout=20, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return save_path, "Downloaded"
        except Exception as e:
            log_callback(f"Download Error: {url} -> {str(e)}", "error")
        return None, None

    def extract_content(self, path):
        """Extracts text and metadata from the PDF."""
        try:
            reader = PdfReader(path)
            meta = reader.metadata
            full_text = ""
            # Process first 50 pages to prevent memory spikes
            pages_to_read = min(len(reader.pages), 50)
            for i in range(pages_to_read):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    full_text += page_text + " "
            
            return {
                "text": self.clean_text(full_text),
                "pages": len(reader.pages),
                "author": meta.author if meta and meta.author else "Unknown"
            }
        except:
            return {"text": "", "pages": 0, "author": "N/A"}

    def generate_final_reports(self):
        """Generates JSON, CSV, and the PDF Summary Report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df = pd.DataFrame(self.data_store)
        
        # 1. Export JSON
        json_path = os.path.join(self.config['out_dir'], f"scraped_data_{timestamp}.json")
        with open(json_path, 'w') as f:
            json.dump(self.data_store, f, indent=4)
            
        # 2. Export CSV
        csv_path = os.path.join(self.config['out_dir'], f"scraped_data_{timestamp}.csv")
        df.to_csv(csv_path, index=False)
        
        # 3. Export PDF Report
        pdf_report_path = os.path.join(self.config['out_dir'], f"summary_report_{timestamp}.pdf")
        self._create_pdf_report(pdf_report_path, df)
        
        return json_path, csv_path, pdf_report_path

    def _create_pdf_report(self, path, df):
        """Internal helper to build the ReportLab PDF."""
        doc = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=20)
        elements.append(Paragraph("Scraping Execution Summary", title_style))
        
        # Metadata Table
        meta_data = [
            ["Source Domain", self.config['domain']],
            ["Execution Date", datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["Total PDFs Processed", str(len(df))],
            ["Total Characters Extracted", str(df['text_length'].sum() if not df.empty else 0)]
        ]
        t = Table(meta_data, colWidths=[150, 300])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('PADDING', (0,0), (-1,-1), 6)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
        # Document List Table
        if not df.empty:
            elements.append(Paragraph("Top Document List", styles['Heading2']))
            list_data = [["ID", "File Name", "Pages", "Length"]]
            for _, row in df.head(20).iterrows():
                list_data.append([row['document_id'], row['file_name'][:40], row['pages'], row['text_length']])
            
            lt = Table(list_data, colWidths=[50, 250, 50, 70])
            lt.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.dodgerblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
            ]))
            elements.append(lt)

        doc.build(elements)

# --- STREAMLIT UI LAYOUT ---
def main():
    st.title("🦅 Data Scrapper for NRSC")
    st.markdown("---")

    # SIDEBAR CONFIGURATION
    with st.sidebar:
        st.header("🔍 Targeted Extraction")
        target_url = st.text_input("Start URL", placeholder="https://example.com")
        
        st.header("⚙️ Crawl Control")
        crawl_depth = st.slider("Crawl Depth", 1, 5, 2, help="How many links deep to follow?")
        max_scans = st.number_input("Max Page Limit", 10, 1000, 50)
        
        st.header("📂 Data Storage")
        dl_folder = st.text_input("PDF Download Folder", "downloads")
        out_folder = st.text_input("Report Output Folder", "output")
        
        st.header("🎯 Filtering")
        kw_input = st.text_input("Keywords (e.g. 2024, invoice)")
        keywords = [k.strip() for k in kw_input.split(",")] if kw_input else []
        
        execute = st.button("🚀 START SCRAPING", use_container_width=True)

    # MAIN DASHBOARD AREA
    if execute and target_url:
        if not target_url.startswith("http"):
            st.error("Invalid URL. Please include http:// or https://")
            return

        domain = urlparse(target_url).netloc
        harvester = EnterpriseHarvester({
            'domain': domain, 'dl_dir': dl_folder, 'out_dir': out_folder,
            'keywords': keywords, 'depth': crawl_depth
        })

        # Statistics Cards
        c1, c2, c3, c4 = st.columns(4)
        stat_scanned = c1.metric("Pages Scanned", "0")
        stat_discovered = c2.metric("PDFs Found", "0")
        stat_processed = c3.metric("Processed", "0")
        stat_timer = c4.metric("Elapsed Time", "0s")

        # Logging Console
        st.subheader("🖥️ Live Execution Log")
        log_container = st.empty()
        log_entries = []

        def add_log(msg, style="info"):
            timestamp = datetime.now().strftime("%H:%M:%S")
            css = "success-text" if style == "success" else ("error-text" if style == "error" else "")
            log_entries.append(f'<div>[{timestamp}] <span class="{css}">{msg}</span></div>')
            log_container.markdown(f'<div class="terminal">{"".join(log_entries[::-1])}</div>', unsafe_allow_html=True)

        # CRAWLING LOGIC
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                queue = [(target_url, 0)]
                
                while queue and len(harvester.visited_urls) < max_scans:
                    curr_url, curr_depth = queue.pop(0)
                    if curr_url in harvester.visited_urls: continue
                    
                    harvester.visited_urls.add(curr_url)
                    stat_scanned.metric("Pages Scanned", len(harvester.visited_urls))
                    stat_timer.metric("Elapsed Time", f"{int(time.time() - harvester.start_time)}s")
                    
                    add_log(f"Scanning Page: {curr_url}")
                    
                    try:
                        page.goto(curr_url, timeout=30000, wait_until="domcontentloaded")
                        
                        # Get all links
                        links = page.evaluate("""() => Array.from(document.querySelectorAll('a')).map(a => a.href)""")
                        
                        for link in links:
                            full_url = urljoin(curr_url, link)
                            # 1. If it's a PDF
                            if full_url.lower().endswith(".pdf"):
                                if full_url not in harvester.found_pdfs:
                                    harvester.found_pdfs.add(full_url)
                                    stat_discovered.metric("PDFs Found", len(harvester.found_pdfs))
                                    
                                    # Process the PDF immediately
                                    path, status = harvester.download_pdf(full_url, add_log)
                                    if path:
                                        content_data = harvester.extract_content(path)
                                        harvester.data_store.append({
                                            "document_id": f"DOC_{len(harvester.data_store)+1:03d}",
                                            "file_name": os.path.basename(path),
                                            "source_url": full_url,
                                            "pages": content_data['pages'],
                                            "author": content_data['author'],
                                            "text_length": len(content_data['text']),
                                            "content": content_data['text']
                                        })
                                        stat_processed.metric("Processed", len(harvester.data_store))
                                        add_log(f"Processed: {os.path.basename(path)}", "success")
                            
                            # 2. If it's an internal link, add to queue
                            elif urlparse(full_url).netloc == domain:
                                if full_url not in harvester.visited_urls and curr_depth < crawl_depth:
                                    queue.append((full_url, curr_depth + 1))
                                    
                    except Exception as e:
                        add_log(f"Page Skip: {str(e)}", "error")
                
                browser.close()

            # --- POST-PROCESSING ---
            if harvester.data_store:
                st.balloons()
                add_log("Generating Final Reports...", "info")
                json_p, csv_p, pdf_p = harvester.generate_final_reports()
                
                st.success("✅ Scraping Complete!")
                
                # Report Section
                st.subheader("📊 Extraction Analytics")
                df_final = pd.DataFrame(harvester.data_store)
                
                col_a1, col_a2 = st.columns(2)
                col_a1.dataframe(df_final[['document_id', 'file_name', 'pages', 'text_length']], use_container_width=True)
                
                # Charting
                if len(df_final) > 1:
                    col_a2.bar_chart(df_final.set_index('file_name')['text_length'])

                # Download Buttons
                st.subheader("📥 Download Results")
                d_col1, d_col2, d_col3 = st.columns(3)
                
                with open(json_p, "rb") as f:
                    d_col1.download_button("💾 Download JSON Manifest", f, file_name="data.json", use_container_width=True)
                with open(csv_p, "rb") as f:
                    d_col2.download_button("📊 Download CSV Table", f, file_name="data.csv", use_container_width=True)
                with open(pdf_p, "rb") as f:
                    d_col3.download_button("📄 Download PDF Summary", f, file_name="report.pdf", use_container_width=True)
                
            else:
                st.warning("No PDF files were discovered. Try increasing Crawl Depth or checking the URL.")

        except Exception as e:
            st.error(f"A critical error occurred: {str(e)}")

    elif execute:
        st.warning("Please enter a starting URL in the sidebar.")

if __name__ == "__main__":
    main()