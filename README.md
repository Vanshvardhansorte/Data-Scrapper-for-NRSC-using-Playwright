# 🦅 Data Scrapper for NRSC Pro

### Enterprise-Grade Document Discovery & Data Extraction Pipeline
[![Live Demo](https://img.shields.io/badge/Streamlit-Live%20Demo-red?style=for-the-badge&logo=streamlit)](https://data-scrapper-for-nrsc-using-playwright-ykjjnmpnnbuepxpvo4desj.streamlit.app/)

---

## 📖 Overview

The **Universal Website PDF Scraper** is a high-performance automated tool designed to **crawl entire domains**, identify **PDF documents**, download them, and **extract their textual content into structured formats**.

Built with a focus on **robustness and scalability**, the system handles **modern JavaScript-heavy websites** using **Playwright Chromium**.

---

## 🚀 Key Features

### 🔁 Recursive Deep Crawling

An intelligent **queue-based crawling system** with configurable crawl depth to prevent infinite loops.

### ⚡ Dynamic Content Handling

Uses **Playwright** to execute JavaScript, ensuring PDFs hidden behind buttons or dynamically loaded content are captured.

### 📄 Advanced Text Extraction

Utilizes **PyPDF** to parse documents with **memory-safe page-limit throttling**.

### 📊 Multi-Format Export

Outputs structured datasets in:

* **JSON**
* **CSV**
* **Professional PDF Summary Report**

### 📡 Live Telemetry Dashboard

Real-time dashboard including:

* Execution log terminal
* Progress metrics
* Data analytics

### 🔎 Keyword Filtering

Allows targeting documents by matching **file names against user-defined keywords**.

---

## 🛠️ Technology Stack

| Layer                 | Technology            |
| --------------------- | --------------------- |
| **Core Engine**       | Playwright (Chromium) |
| **Frontend**          | Streamlit             |
| **Data Processing**   | Pandas, PyPDF         |
| **Report Generation** | ReportLab             |
| **Networking**        | Requests, Urllib3     |

---

## 📥 Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/universal-pdf-scraper.git
cd universal-pdf-scraper
```

---

## ⚙️ Configuration Parameters

| Parameter           | Description                                                       |
| ------------------- | ----------------------------------------------------------------- |
| **Start URL**       | The root domain to begin crawling                                 |
| **Crawl Depth**     | Number of "clicks" away from the homepage the scraper travels     |
| **Max Page Limit**  | Total number of internal pages to scan before stopping            |
| **Keywords**        | Optional comma-separated filters (e.g., `invoice,2024,report`)    |
| **Download Folder** | Local directory to store downloaded `.pdf` files                  |
| **Output Folder**   | Directory where `.csv`, `.json`, and `.pdf` reports are generated |

---

## 📊 Data Pipeline Architecture

### 1️⃣ URL Discovery

Playwright navigates the site and extracts **internal links using native JavaScript execution**.

### 2️⃣ Detection

All URLs ending in **`.pdf`** are added to a **prioritized download queue**.

### 3️⃣ Extraction

Documents are downloaded via **streamed requests**, then **text is cleaned and normalized**.

### 4️⃣ Analytics

The system computes:

* Character counts
* Page counts
* Domain-wide statistics

### 5️⃣ Reporting

Data is packaged into **high-integrity formats** suitable for:

* Data analysis
* Document indexing
* LLM training pipelines

---

## ⚠️ Important Considerations

### 📜 Compliance

Ensure you have permission to crawl the target domain and follow the site's **robots.txt** policies.

### 💾 Memory Usage

For large domains, adjust the **Max Page Limit** according to your **system RAM capacity**.

---

## 📄 License

Distributed under the **MIT License**.
See `LICENSE` for more information.

---

## ❤️ Author

Developed by

**Vanshvardhan Sorte**  
Computer Science and Engineering  
Yeshwantrao Chavan College of Engineering
