import re
import logging
from typing import List

logger = logging.getLogger(__name__)

class TextUtils:
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def is_psikologi_related(question: str) -> bool:
        """Check if question is related to psychology/mental health topics"""
        psikologi_keywords = [
            # Mental health
            'depresi', 'kecemasan', 'burnout', 'stres', 'stress', 'psikologi', 'psikolog', 'terapi',
            'kesehatan mental', 'emosi', 'perasaan', 'well-being', 'gangguan', 'distres', 'trauma',
            'self-care', 'kesejahteraan', 'motivasi', 'intimidasi', 'perundungan', 'bullying',
            'kesehatan jiwa', 'konseling', 'dukungan', 'pemulihan', 'coping', 'resiliensi',
            'relaksasi', 'tidur', 'insomnia', 'mood', 'energi', 'kepercayaan diri', 'penghargaan diri',
            'hubungan sosial', 'interaksi sosial', 'pekerjaan', 'work-life balance', 'burnout',
            'WHO-5', 'GAD-7', 'MBI', 'NAQ-R', 'K10',
            # Kesehatan umum
            'kesehatan', 'nutrisi', 'olahraga', 'diet', 'gizi', 'aktivitas fisik', 'istirahat', 'pola hidup',
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in psikologi_keywords)
    
    @staticmethod
    def format_response(text: str) -> str:
        """Format the response text for better readability"""
        if not text:
            return "Maaf, saya tidak dapat memberikan jawaban saat ini."
        
        # Ensure the response ends with proper punctuation
        text = text.strip()
        if not text.endswith(('.', '!', '?')):
            text += '.'
            
        return text