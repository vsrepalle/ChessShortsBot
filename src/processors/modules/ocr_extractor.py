"""
OCR Extractor Module - Extracts text from images using OCR
"""

import logging
import re
from pathlib import Path
from src.ocr.extractor import OCRExtractor

class OCRExtractorModule:
    """Handles OCR extraction and text processing"""
    
    def __init__(self):
        self.ocr = OCRExtractor()
    
    def extract_text(self, image_path):
        try:
            text = self.ocr.extract(image_path)
            return text
        except Exception as e:
            logging.error(f"OCR failed: {e}")
            return "Chess Tournament Brochure"
    
    def extract_tournament_info(self, text):
        info = {
            "raw_text": text,
            "tournament_name": self.find_tournament(text) or "Chess Tournament",
            "venue": self.find_venue(text) or "Online Classes Available",
            "dates": self.find_dates(text) or [],
            "entry_fee": self.find_entry_fee(text) or "",
            "prize_fund": self.find_prize(text) or "",
            "contact": self.find_contact(text) or [],
            "email": self.find_email(text) or [],
            "website": self.find_website(text) or [],
            "categories": self.find_categories(text) or []
        }
        return info
    
    def find_tournament(self, text):
        lines = text.splitlines()
        for line in lines:
            line = line.strip()
            if line and ("CHESS" in line.upper() or "TOURNAMENT" in line.upper() or "OPEN" in line.upper()):
                cleaned = re.sub(r'^(?:CHESS|TOURNAMENT|OPEN)\s*', '', line, flags=re.IGNORECASE)
                if cleaned and len(cleaned) > 3:
                    return cleaned
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) > 5 and not re.match(r'^[\d\s,]+$', line):
                return line
        return "Chess Tournament"
    
    def find_dates(self, text):
        patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2,4}',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{2,4}',
            r'\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2,4}'
        ]
        
        dates = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        seen = set()
        unique_dates = []
        for date in dates:
            if date not in seen:
                seen.add(date)
                unique_dates.append(date)
        
        return unique_dates[:3]
    
    def find_contact(self, text):
        patterns = [
            r'(?:\+91[- ]?)?[6-9]\d{9}',
            r'(?:\+91[- ]?)?[0-9]{10}',
            r'(?:0[1-9]\d{9})'
        ]
        
        contacts = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            contacts.extend(matches)
        
        return list(set(contacts))[:3]
    
    def find_email(self, text):
        pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
        emails = re.findall(pattern, text)
        return list(set(emails))[:3]
    
    def find_website(self, text):
        patterns = [
            r'https?://[^\s]+',
            r'www\.[^\s]+',
            r'[A-Za-z0-9-]+\.[A-Za-z]{2,}(?:/\S*)?'
        ]
        
        websites = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            websites.extend(matches)
        
        cleaned = []
        for site in websites:
            site = re.sub(r'[,.;!?]$', '', site)
            if site and site not in cleaned:
                cleaned.append(site)
        
        return cleaned[:3]
    
    def find_entry_fee(self, text):
        patterns = [
            r'(?:Entry Fee|Registration Fee|Fee|Reg Fee)\s*:?\s*[₹$€£]?\s*([\d,]+)',
            r'(?:Entry Fee|Registration Fee|Fee|Reg Fee)\s*:?\s*([\d,]+)\s*(?:Rupees|Rs\.?|INR)',
            r'Fee\s*:?\s*[₹$€£]?\s*([\d,]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fee = match.group(1).replace(',', '')
                if fee.isdigit():
                    return fee
        
        return ""
    
    def find_prize(self, text):
        patterns = [
            r'(?:Prize Fund|Total Prize|Prize Money|Prize Pool)\s*:?\s*[₹$€£]?\s*([\d,]+)',
            r'(?:Prize Fund|Total Prize|Prize Money|Prize Pool)\s*:?\s*([\d,]+)\s*(?:Rupees|Rs\.?|INR)',
            r'Prize\s*:?\s*[₹$€£]?\s*([\d,]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                prize = match.group(1).replace(',', '')
                if prize.isdigit():
                    return prize
        
        return ""
    
    def find_categories(self, text):
        categories = []
        age_groups = ["U7","U8","U9","U10","U11","U12","U13","U14","U15","U16","U17","U18","U19","U21","U23","U25"]
        other = ["Open","Women","Girls","Boys","Junior","Senior","Veteran"]
        
        upper_text = text.upper()
        
        for cat in age_groups:
            if cat in upper_text:
                categories.append(cat)
        
        for cat in other:
            if cat.upper() in upper_text:
                categories.append(cat)
        
        return list(dict.fromkeys(categories))
    
    def find_venue(self, text):
        keywords = ["VENUE", "LOCATION", "ADDRESS", "AT", "PLACE", "HALL", "STADIUM", "GROUND"]
        lines = text.split("\n")
        
        for i, line in enumerate(lines):
            for key in keywords:
                if key in line.upper():
                    venue_line = line.strip()
                    venue = re.sub(rf'^{key}\s*:?\s*', '', venue_line, flags=re.IGNORECASE).strip()
                    if venue and len(venue) > 3:
                        return venue
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and len(next_line) > 3:
                            return next_line
        
        return "Online Classes Available"
