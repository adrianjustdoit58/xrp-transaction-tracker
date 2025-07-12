import pdfplumber
import json
import re

# PDF path from user
pdf_path = '/Users/adria/Desktop/Crypto Fraud/Polizei/Akteneinsicht Staatsanwaltschaft.pdf'

# Patterns
tx_hash_pattern = re.compile(r'[0-9A-Fa-f]{64}')
wallet_pattern = re.compile(r'r[0-9A-Za-z]{33}')
ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

extracted_data = []

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        text = page.extract_text()
        tx_hashes = tx_hash_pattern.findall(text)
        wallets = wallet_pattern.findall(text)
        ips = ip_pattern.findall(text)
        
        contexts = []
        if 'SwopSpace' in text or 'ChangeNow' in text or 'Binance' in text or 'VPN' in text:
            contexts.append(text[:500])  # Snippet for context
        
        if tx_hashes or wallets or ips:
            extracted_data.append({
                'page': page_num,
                'tx_hashes': tx_hashes,
                'wallets': wallets,
                'ips': ips,
                'contexts': contexts
            })

# Save to JSON
with open('pdf_extracted.json', 'w') as f:
    json.dump(extracted_data, f, indent=4)
print('Extraction complete. Data saved to pdf_extracted.json')