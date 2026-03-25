#!/usr/bin/env python3
"""
Document Management System - Document Classifier
================================================
Auto-labeling untuk dokumen pemerintah berbasis pattern matching.
Mendukung: UU, PP, Perpres, Permen, Perda, Kepmen, Surat Edaran, dll.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from ..core.config import GOVERNMENT_PATTERNS, INSTANSI_PATTERNS


@dataclass
class LabelResult:
    """Result dari classification"""
    label_type: str
    label_value: str
    confidence: float
    source: str = 'auto'
    matched_pattern: str = None


class DocumentClassifier:
    """Classifier untuk dokumen pemerintahan"""
    
    def __init__(self):
        self.gov_patterns = GOVERNMENT_PATTERNS
        self.instansi_patterns = INSTANSI_PATTERNS
        
        # Compile regex patterns
        self._compiled_patterns = {}
        for key, config in self.gov_patterns.items():
            self._compiled_patterns[key] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in config['patterns']
            ]
        
        for key, patterns in self.instansi_patterns.items():
            self._compiled_patterns[key] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in patterns
            ]
    
    def classify_document(self, document: Dict) -> List[LabelResult]:
        """Classify document and return labels"""
        labels = []
        
        # Get text to analyze
        filename = document.get('file_name', '')
        text = document.get('extracted_text', '')[:2000]  # First 2000 chars
        
        # Combine for analysis
        combined_text = f"{filename}\n{text}"
        
        # Classify jenis dokumen
        jenis_labels = self._classify_jenis_dokumen(combined_text)
        labels.extend(jenis_labels)
        
        # Classify instansi
        instansi_labels = self._classify_instansi(combined_text)
        labels.extend(instansi_labels)
        
        # Classify tahun
        tahun_labels = self._classify_tahun(filename, text)
        labels.extend(tahun_labels)
        
        # Classify nomor dokumen
        nomor_labels = self._classify_nomor_dokumen(combined_text, jenis_labels)
        labels.extend(nomor_labels)
        
        return labels
    
    def _classify_jenis_dokumen(self, text: str) -> List[LabelResult]:
        """Classify jenis dokumen (UU, PP, Perpres, dll)"""
        labels = []
        
        for key, config in self.gov_patterns.items():
            for pattern in self._compiled_patterns[key]:
                match = pattern.search(text)
                if match:
                    confidence = self._calculate_confidence(match, text, key)
                    labels.append(LabelResult(
                        label_type='jenis_dokumen',
                        label_value=config['jenis'],
                        confidence=confidence,
                        matched_pattern=match.group(0)
                    ))
                    
                    # Also add category label
                    labels.append(LabelResult(
                        label_type='category',
                        label_value=config['category'],
                        confidence=confidence
                    ))
                    break  # Stop at first match for this type
        
        return labels
    
    def _classify_instansi(self, text: str) -> List[LabelResult]:
        """Classify instansi pembuat dokumen"""
        labels = []
        
        for instansi, patterns in self.instansi_patterns.items():
            for pattern in self._compiled_patterns[instansi]:
                match = pattern.search(text)
                if match:
                    labels.append(LabelResult(
                        label_type='instansi',
                        label_value=instansi,
                        confidence=0.85,
                        matched_pattern=match.group(0)
                    ))
                    break
        
        return labels
    
    def _classify_tahun(self, filename: str, text: str) -> List[LabelResult]:
        """Extract tahun from filename and text"""
        labels = []
        
        # Pattern: 4 digit number that looks like a year (19xx-20xx)
        year_pattern = re.compile(r'\b(19|20)\d{2}\b')
        
        # Search in filename first (higher confidence)
        matches = year_pattern.findall(filename)
        if matches:
            year = matches[0] + year_pattern.search(filename).group(0)[2:]
            labels.append(LabelResult(
                label_type='tahun',
                label_value=year,
                confidence=0.9,
                matched_pattern=year
            ))
        else:
            # Search in text
            match = year_pattern.search(text[:500])
            if match:
                year = match.group(0)
                labels.append(LabelResult(
                    label_type='tahun',
                    label_value=year,
                    confidence=0.7,
                    matched_pattern=year
                ))
        
        return labels
    
    def _classify_nomor_dokumen(self, text: str, 
                                jenis_labels: List[LabelResult]) -> List[LabelResult]:
        """Extract nomor dokumen"""
        labels = []
        
        # Pattern: "Nomor X" or "No. X" followed by tahun
        nomor_patterns = [
            r'(?:Nomor|No\.?|Nomor)\s*[:\s]*(\d+)\s*(?:Tahun|Tahun)?\s*(\d{4})?',
            r'(?:Nomor|No\.?|Nomor)\s*[:\s]*(\d+)',
        ]
        
        for pattern in nomor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nomor = match.group(1)
                labels.append(LabelResult(
                    label_type='nomor_dokumen',
                    label_value=nomor,
                    confidence=0.8,
                    matched_pattern=match.group(0)
                ))
                break
        
        return labels
    
    def _calculate_confidence(self, match: re.Match, text: str, 
                              doc_type: str) -> float:
        """Calculate confidence score for match"""
        base_confidence = 0.7
        
        # Higher confidence if match is at beginning of text
        if match.start() < 200:
            base_confidence += 0.15
        
        # Higher confidence for specific keywords
        specific_keywords = {
            'UU': ['undang-undang', 'republik indonesia'],
            'PP': ['peraturan pemerintah'],
            'PERPRES': ['peraturan presiden'],
            'PERMEN': ['peraturan menteri'],
        }
        
        text_lower = text.lower()
        for keyword in specific_keywords.get(doc_type, []):
            if keyword in text_lower:
                base_confidence += 0.1
                break
        
        return min(base_confidence, 1.0)
    
    def extract_government_metadata(self, document: Dict) -> Dict:
        """Extract government-specific metadata"""
        filename = document.get('file_name', '')
        text = document.get('extracted_text', '')[:3000]
        combined = f"{filename}\n{text}"
        
        metadata = {}
        
        # Extract jenis dokumen
        for key, config in self.gov_patterns.items():
            for pattern in self._compiled_patterns[key]:
                if pattern.search(combined):
                    metadata['jenis_dokumen'] = config['jenis']
                    break
            if metadata.get('jenis_dokumen'):
                break
        
        # Extract nomor
        nomor_match = re.search(r'(?:Nomor|No\.?)\s*[:\s]*(\d+)', combined, re.IGNORECASE)
        if nomor_match:
            metadata['nomor_dokumen'] = nomor_match.group(1)
        
        # Extract tahun
        tahun_match = re.search(r'\b(19|20)\d{2}\b', filename)
        if tahun_match:
            metadata['tahun_dokumen'] = int(tahun_match.group(0))
        
        # Extract instansi
        for instansi, patterns in self.instansi_patterns.items():
            for pattern in self._compiled_patterns[instansi]:
                if pattern.search(combined):
                    metadata['instansi_pembuat'] = instansi
                    break
            if metadata.get('instansi_pembuat'):
                break
        
        # Extract tentang (after "Tentang" keyword)
        tentang_match = re.search(r'Tentang\s+(.+?)(?:\n|Dengan|$)', combined, re.IGNORECASE | re.DOTALL)
        if tentang_match:
            metadata['tentang'] = tentang_match.group(1).strip()[:200]
        
        # Extract judul (first meaningful line)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            metadata['judul'] = lines[0][:200]
        
        return metadata
    
    def classify_batch(self, documents: List[Dict]) -> Dict[int, List[LabelResult]]:
        """Classify multiple documents"""
        results = {}
        for doc in documents:
            doc_id = doc.get('id')
            if doc_id:
                results[doc_id] = self.classify_document(doc)
        return results


def main():
    """Test classifier"""
    classifier = DocumentClassifier()
    
    # Test documents
    test_docs = [
        {
            'id': 1,
            'file_name': 'UU_Nomor_12_Tahun_2023.pdf',
            'extracted_text': 'UNDANG-UNDANG REPUBLIK INDONESIA NOMOR 12 TAHUN 2023 TENTANG KEPOLISIAN'
        },
        {
            'id': 2,
            'file_name': 'PP_No_5_2024.pdf',
            'extracted_text': 'PERATURAN PEMERINTAH REPUBLIK INDONESIA NOMOR 5 TAHUN 2024 TENTANG PENYELENGGARAAN PEMERINTAHAN'
        },
        {
            'id': 3,
            'file_name': 'PERMENKUMHAM_2024.pdf',
            'extracted_text': 'PERATURAN MENTERI HUKUM DAN HAK ASASI MANUSIA REPUBLIK INDONESIA'
        },
    ]
    
    print("🧪 Document Classifier Test")
    print("=" * 60)
    
    for doc in test_docs:
        print(f"\n📄 {doc['file_name']}")
        print("-" * 40)
        
        labels = classifier.classify_document(doc)
        for label in labels:
            print(f"  {label.label_type}: {label.label_value} (confidence: {label.confidence:.2f})")
        
        metadata = classifier.extract_government_metadata(doc)
        print(f"  Metadata: {metadata}")


if __name__ == "__main__":
    main()