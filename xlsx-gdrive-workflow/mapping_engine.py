#!/usr/bin/env python3
"""
Mapping Engine untuk konversi data ekstraksi arsip ke format spreadsheet GSheets.
Membaca konfigurasi dari column_mapping.json dan menerapkan transformasi.
"""
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class MappingEngine:
    """Engine untuk mapping data arsip ke kolom spreadsheet."""
    
    def __init__(self, config_path: str = None):
        """
        Inisialisasi mapping engine dengan konfigurasi.
        
        Args:
            config_path: Path ke file JSON konfigurasi mapping
        """
        if config_path is None:
            config_path = Path(__file__).parent / "column_mapping.json"
        
        self.config = self._load_config(config_path)
        self.column_mapping = self.config["column_mapping"]
        self.available_fields = self.config["available_fields"]
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load konfigurasi mapping dari file JSON."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def transform_value(self, column_mapping: Dict, data: Dict) -> str:
        """
        Terapkan transformasi sesuai konfigurasi kolom.
        
        Args:
            column_mapping: Konfigurasi mapping untuk satu kolom
            data: Data ekstraksi arsip (structured JSON)
            
        Returns:
            String value untuk sel spreadsheet
        """
        transform = column_mapping.get("transform", "direct")
        
        if transform == "direct":
            field_name = column_mapping.get("field_name", "")
            if field_name == "uraian":
                return self._transform_urian(data)
            return self._transform_direct(field_name, data)
        elif transform == "empty":
            return ""
        elif transform == "constant":
            return column_mapping.get("value", "")
        elif transform == "concat":
            return self._transform_concat(column_mapping["fields"], data)
        elif transform == "truncate":
            return self._transform_truncate(
                column_mapping["field_name"], 
                column_mapping.get("max_length", 50),
                data
            )
        elif transform == "date_format":
            return self._transform_date_format(
                column_mapping["field_name"],
                column_mapping.get("format", "%Y-%m"),
                data
            )
        elif transform == "extract_classification":
            return self._transform_extract(
                column_mapping["field_name"],
                column_mapping.get("regex_pattern", ""),
                data
            )
        else:
            raise ValueError(f"Unknown transform type: {transform}")
    
    def _transform_direct(self, field_name: str, data: Dict) -> str:
        """Ambil nilai field langsung tanpa perubahan."""
        value = data.get(field_name, "")
        return str(value) if value is not None else ""
    
    def _transform_urian(self, data: Dict) -> str:
        """Extract uraian: prioritas dari sptjb.rincian_pembayaran, lalu fallback ke field uraian."""
        # Cek apakah ada sptjb data
        sptjb = data.get('sptjb', {})
        rincian = sptjb.get('rincian_pembayaran', [])
        
        if rincian:
            # Gabungkan semua uraian dari rincian pembayaran
            uraian_list = [r.get('uraian', '') for r in rincian if r.get('uraian')]
            if uraian_list:
                return '; '.join(uraian_list)[:200]
        
        # Fallback ke field uraian langsung
        uraian = data.get('uraian', '')
        if uraian:
            return str(uraian)[:200]
        
        # Fallback terakhir ke doc_type + satker
        doc_type = data.get('doc_type', '')
        satker = data.get('satker', '')[:50]
        if doc_type and satker:
            return f"{doc_type} - {satker}"[:200]
        
        return ""
    
    def _transform_truncate(self, field_name: str, max_length: int, data: Dict) -> str:
        """Potong string ke panjang maksimum."""
        value = data.get(field_name, "")
        return str(value)[:max_length] if value else ""
    
    def _transform_date_format(self, field_name: str, date_format: str, data: Dict) -> str:
        """Format tanggal sesuai pattern."""
        value = data.get(field_name, "")
        if not value:
            return ""
        
        try:
            dt = datetime.fromisoformat(value)
            return dt.strftime(date_format)
        except (ValueError, TypeError):
            return str(value)[:7]  # Fallback: ambil 7 karakter pertama (YYYY-MM)
    
    def _transform_extract(self, field_name: str, regex_pattern: str, data: Dict) -> str:
        """Ekstrak informasi menggunakan regex pattern."""
        value = data.get(field_name, "")
        if not value or not regex_pattern:
            return ""
        
        match = re.search(regex_pattern, value)
        if match:
            return match.group(1) if match.lastindex else match.group(0)
        return ""
    
    def transform_row(self, data: Dict, columns: List[str] = None) -> List[str]:
        """
        Transform seluruh baris data arsip ke list value spreadsheet.
        
        Args:
            data: Data ekstraksi arsip (structured JSON)
            columns: Daftar kolom yang ingin diproses (default: semua dari A-O)
            
        Returns:
            List of string values (satu untuk setiap kolom)
        """
        if columns is None:
            columns = sorted(self.column_mapping.keys())
        
        row = []
        for col_letter in columns:
            col_config = self.column_mapping.get(col_letter)
            if col_config is None:
                row.append("")
                continue
            
            value = self.transform_value(col_config, data)
            row.append(value)
        
        return row
    
    def get_column_headers(self, columns: List[str] = None) -> Dict[str, str]:
        """
        Dapatkan header kolom sesuai konfigurasi.
        
        Returns:
            Dict mapping column letter -> header name
        """
        headers = {}
        cols = columns or sorted(self.column_mapping.keys())
        
        for col_letter in cols:
            col_config = self.column_mapping.get(col_letter)
            if col_config:
                headers[col_letter] = col_config.get("column_header", "")
        
        return headers
    
    def get_full_row_with_headers(self, data: Dict, columns: List[str] = None) -> Dict[str, Any]:
        """
        Dapatkan baris lengkap dengan header sebagai key.
        
        Args:
            data: Data ekstraksi arsip
            columns: Daftar kolom
            
        Returns:
            Dict dengan column header sebagai key
        """
        headers = self.get_column_headers(columns)
        values = self.transform_row(data, columns)
        
        result = {}
        for i, (col_letter, header) in enumerate(headers.items()):
            result[header or col_letter] = values[i] if i < len(values) else ""
        
        return result
    
    def validate_data(self, data: Dict) -> List[str]:
        """
        Validasi data arsip terhadap konfigurasi mapping.
        
        Returns:
            List of validation error messages (empty jika valid)
        """
        errors = []
        
        for col_letter, col_config in self.column_mapping.items():
            validation = col_config.get("validation")
            if not validation:
                continue
            
            field_name = col_config.get("field_name")
            if not field_name:
                continue
            
            value = data.get(field_name)
            
            if validation.get("required") and not value:
                errors.append(
                    f"Column {col_letter} ({col_config.get('column_header', '')}): "
                    f"required field '{field_name}' is missing or empty"
                )
            
            if validation.get("max_length") and value and len(str(value)) > validation["max_length"]:
                errors.append(
                    f"Column {col_letter} ({col_config.get('column_header', '')}): "
                    f"field '{field_name}' exceeds max length {validation['max_length']}"
                )
        
        return errors


class ArsipDataLoader:
    """Loader untuk data arsip dari file JSON terstruktur."""
    
    def __init__(self, extracted_dir: str = "arsip-extracted"):
        self.extracted_dir = Path(extracted_dir)
    
    def load_all(self) -> List[Dict]:
        """Load semua file *_structured.json dari direktori ekstraksi."""
        if not self.extracted_dir.exists():
            print(f"⚠️ Extracted directory not found: {self.extracted_dir}")
            return []
        
        data_list = []
        for json_file in self.extracted_dir.glob("*_structured.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    content = data.get("content", {})
                    if content:
                        data_list.append(content)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️ Error loading {json_file}: {e}")
        
        return data_list
    
    def load_single(self, doc_id: str) -> Optional[Dict]:
        """Load satu file structured JSON berdasarkan doc_id."""
        json_file = self.extracted_dir / f"{doc_id}_structured.json"
        if not json_file.exists():
            return None
        
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("content", {})
        except (json.JSONDecodeError, KeyError):
            return None
    
    def count(self) -> int:
        """Count jumlah file structured JSON."""
        if not self.extracted_dir.exists():
            return 0
        return len(list(self.extracted_dir.glob("*_structured.json")))


def main():
    """Test dan demo mapping engine."""
    print("=" * 60)
    print("ARSIP MAPPING ENGINE DEMO")
    print("=" * 60)
    
    # Init engine
    engine = MappingEngine()
    loader = ArsipDataLoader()
    
    print(f"\n📊 Found {loader.count()} structured files")
    
    # Load data
    all_data = loader.load_all()
    if not all_data:
        print("⚠️ Tidak ada data arsip ditemukan!")
        return
    
    print(f"\n📋 Available fields:")
    for field_name, field_info in engine.available_fields.items():
        print(f"  - {field_name}: {field_info.get('description', '')}")
    
    print(f"\n📐 Column mapping ({len(engine.column_mapping)} columns):")
    for col_letter, col_config in sorted(engine.column_mapping.items()):
        header = col_config.get("column_header", "")
        transform = col_config.get("transform", "direct")
        print(f"  {col_letter}: {header or '(empty)'} → {transform}")
    
    print(f"\n📝 Sample data transformation:")
    print("-" * 60)
    for i, data in enumerate(all_data, 1):
        print(f"\nDoc {i}: {data.get('doc_id', 'unknown')}")
        print(f"  Type: {data.get('doc_type', 'unknown')}")
        print(f"  Nomor: {data.get('nomor_surat', 'unknown')}")
        
        # Transform row
        row = engine.transform_row(data)
        print(f"\n  Row values:")
        for j, (col_letter, value) in enumerate(zip(sorted(engine.column_mapping.keys()), row)):
            header = engine.column_mapping[col_letter].get("column_header", col_letter)
            print(f"    {col_letter} ({header}): {value[:40] + '...' if len(str(value)) > 40 else value}")
        
        # Validate
        errors = engine.validate_data(data)
        if errors:
            print(f"\n  ⚠️ Validation errors: {errors}")
        else:
            print(f"\n  ✅ Valid")
        
        if i >= 3:  # Batasi demo
            print(f"\n... (remaining {len(all_data) - i} documents not shown)")
            break
    
    print(f"\n{'=' * 60}")
    print("Mapping engine demo selesai!")


if __name__ == "__main__":
    main()