import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os
import numpy as np
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeMLAnalyzer:
    """
    Machine Learning analyzer untuk memprediksi risiko bug berdasarkan metrik kode.
    Menggunakan Random Forest Classifier untuk analisis kualitas kode.
    """
    
    def __init__(self):
        """Initialize ML Analyzer dengan path untuk model dan data."""
        self.model_path = 'tools/bug_predictor.joblib'
        self.data_path = 'code_metrics_data.csv'
        self.model = None
        self.is_trained = False
        
        # Train model saat inisialisasi
        self._train_model()
    
    def _train_model(self):
        """Train Random Forest model menggunakan dataset CSV."""
        try:
            if not os.path.exists(self.data_path):
                logger.error(f"Dataset tidak ditemukan: {self.data_path}")
                return False
            
            # Load dan prepare data
            df = pd.read_csv(self.data_path)
            logger.info(f"Dataset loaded: {df.shape[0]} samples, {df.shape[1]} features")
            
            # Prepare features dan target
            feature_columns = ['complexity', 'loc', 'dependencies']
            X = df[feature_columns]
            y = df['bug']
            
            # Train Random Forest model
            self.model = RandomForestClassifier(
                n_estimators=100, 
                random_state=42,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2
            )
            
            self.model.fit(X, y)
            self.is_trained = True
            
            # Save model
            joblib.dump(self.model, self.model_path)
            logger.info("Model berhasil dilatih dan disimpan")
            
            # Print feature importance
            feature_importance = dict(zip(feature_columns, self.model.feature_importances_))
            logger.info(f"Feature importance: {feature_importance}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saat training model: {str(e)}")
            self.is_trained = False
            return False
    
    def load_model(self):
        """Load pre-trained model jika tersedia."""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                logger.info("Model berhasil dimuat")
                return True
            else:
                logger.warning("Model file tidak ditemukan")
                return False
        except Exception as e:
            logger.error(f"Error saat load model: {str(e)}")
            return False
    
    def analyze_risk(self, complexity, loc, dependencies):
        """
        Analisis risiko bug berdasarkan metrik kode.
        
        Args:
            complexity (int/float): Complexitas siklomatis kode
            loc (int): Lines of code
            dependencies (int): Jumlah dependencies
            
        Returns:
            dict: Hasil analisis dengan risk_score dan recommendation
        """
        try:
            if not self.is_trained:
                # Coba load model jika belum trained
                if not self.load_model():
                    return {
                        "error": "Model belum dilatih atau tidak dapat dimuat",
                        "risk_score": 0.0,
                        "recommendation": "ERROR - Model tidak tersedia"
                    }
            
            # FIXED: Wrap input dalam DataFrame sesuai FINAL_MISSION_INTEGRATION.md
            X_input = pd.DataFrame([[complexity, loc, dependencies]], 
                                  columns=['complexity', 'loc', 'dependencies'])
            probability = self.model.predict_proba(X_input)[0][1]
            
            # Determine recommendation
            if probability > 0.7:
                recommendation = "REJECT - Very High Risk"
                risk_level = "CRITICAL"
            elif probability > 0.5:
                recommendation = "REJECT - High Risk"
                risk_level = "HIGH"
            elif probability > 0.3:
                recommendation = "REVIEW - Medium Risk"
                risk_level = "MEDIUM"
            else:
                recommendation = "APPROVE - Low Risk"
                risk_level = "LOW"
            
            result = {
                "risk_score": round(float(probability), 3),
                "risk_level": risk_level,
                "recommendation": recommendation,
                "features_analyzed": {
                    "complexity": complexity,
                    "lines_of_code": loc,
                    "dependencies": dependencies
                },
                "confidence": round(float(max(self.model.predict_proba(X_input)[0])), 3)
            }
            
            logger.info(f"Risk analysis: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error saat analisis risiko: {str(e)}")
            return {
                "error": str(e),
                "risk_score": 0.0,
                "recommendation": "ERROR - Analisis gagal"
            }
    
    def batch_analyze(self, metrics_list):
        """
        Analisis risiko untuk multiple samples.
        
        Args:
            metrics_list (list): List of dict dengan keys complexity, loc, dependencies
            
        Returns:
            list: List hasil analisis untuk setiap sample
        """
        results = []
        for metrics in metrics_list:
            result = self.analyze_risk(
                metrics['complexity'],
                metrics['loc'],
                metrics['dependencies']
            )
            results.append(result)
        
        return results
    
    def get_model_info(self):
        """Informasi tentang model yang sedang digunakan."""
        if not self.is_trained:
            return {"error": "Model belum dilatih"}
        
        info = {
            "model_type": "Random Forest Classifier",
            "is_trained": self.is_trained,
            "features": ["complexity", "loc", "dependencies"],
            "target": "bug (0=no, 1=yes)",
            "model_path": self.model_path,
            "data_path": self.data_path
        }
        
        # Feature importance jika tersedia
        if hasattr(self.model, 'feature_importances_'):
            feature_names = ["complexity", "loc", "dependencies"]
            info["feature_importance"] = dict(zip(
                feature_names, 
                self.model.feature_importances_.round(3)
            ))
        
        return info

# Global instance untuk digunakan oleh agent lain
ml_analyzer = CodeMLAnalyzer()

if __name__ == "__main__":
    # Test functionality
    print("=== Code ML Analyzer Test ===")
    
    # Initialize analyzer
    analyzer = CodeMLAnalyzer()
    
    # Test single analysis
    print("\n--- Single Analysis Test ---")
    result = analyzer.analyze_risk(complexity=15, loc=500, dependencies=10)
    print(f"Result: {result}")
    
    # Test batch analysis
    print("\n--- Batch Analysis Test ---")
    test_metrics = [
        {"complexity": 5, "loc": 120, "dependencies": 2},
        {"complexity": 20, "loc": 600, "dependencies": 12},
        {"complexity": 8, "loc": 200, "dependencies": 3}
    ]
    batch_results = analyzer.batch_analyze(test_metrics)
    for i, result in enumerate(batch_results):
        print(f"Sample {i+1}: {result}")
    
    # Model info
    print("\n--- Model Information ---")
    model_info = analyzer.get_model_info()
    print(f"Model Info: {model_info}")
